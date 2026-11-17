#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas
#
# A host that is told to end closes every JACK client it opened, end to end, in a PipeWire of its own: the script re-runs
# itself in a private user, net, pid and mount namespace, starts pipewire on a private runtime dir and runs the host
# under tests/jack_xrun_shim.so, which writes each jack_activate and jack_client_close to a log. A JACK client that dies
# without jack_client_close strands the mutexes of its metadata environment in jackd for good (the pool is fixed, nine to
# a client), so for each of SIGTERM, SIGINT and SIGHUP the host, with a plugin loaded, must exit on its own and have
# closed every client it had activated. Nothing here touches the PipeWire of the session that runs it.
#
# OMX_CLAP_HOST:    the binary (default ./omx-clap-host)
# JACK_E2E_PORT:    the socket port (default 5584)

set -u

here=$(cd "$(dirname "$0")" && pwd)
. "${PLUGIN_HOSTD_TESTS_LIB:-$here/../../plugin-hostd/tests/lib}/protocol.sh"
root=$(dirname "$here")
host=${OMX_CLAP_HOST:-$root/omx-clap-host}
port=${JACK_E2E_PORT:-5584}
shim=$here/jack_xrun_shim.so
fake=$here/fake.clap

if [ -z "${JACK_E2E_INSIDE:-}" ]; then
    for f in "$host" "$shim" "$fake"; do
        [ -e "$f" ] || { echo "missing $f" >&2; exit 2; }
    done
    JACK_E2E_INSIDE=1 OMX_CLAP_HOST=$host JACK_E2E_PORT=$port \
        exec unshare --user --map-root-user --net --pid --fork --mount-proc "$0" "$@"
fi

failures=0
step() {
    if [ "$1" -eq 0 ]; then
        echo "ok   $2"
    else
        echo "FAIL $2"
        failures=$((failures + 1))
        tail -5 "$runtime/host.log" 2>/dev/null | sed 's/^/     host: /'
    fi
}

runtime=$(mktemp -d /tmp/omx-clap-host-close.XXXXXX)
export XDG_RUNTIME_DIR=$runtime PIPEWIRE_RUNTIME_DIR=$runtime PULSE_RUNTIME_PATH=$runtime/pulse
unset DBUS_SESSION_BUS_ADDRESS
pids=()
cleanup() {
    exec 3>&- 2>/dev/null
    for p in "${pids[@]}"; do kill "$p" 2>/dev/null; done
    # everything left in the namespace, only ever from pid 1 of it: anywhere else -1 is every process the user may signal
    if [ "$$" = 1 ]; then kill -TERM -- -1 2>/dev/null; fi
    wait 2>/dev/null
    rm -rf "${runtime:?}"
}
trap cleanup EXIT
rc=1
if [ "$$" = 1 ]; then rc=0; fi
step "$rc" "pid 1 of a private pid namespace"

ip link set lo up

pipewire >"$runtime/pw.log" 2>&1 &
pids+=($!)
for _ in $(seq 50); do [ -S "$runtime/pipewire-0" ] && break; sleep 0.1; done
[ -S "$runtime/pipewire-0" ] || { echo "pipewire did not come up" >&2; cat "$runtime/pw.log" >&2; exit 2; }
step 0 "private pipewire on $runtime"

shimlog=$runtime/shim.log

# one_signal <name>: a host with a plugin, sent the signal; it leaves, and closed every client it activated
one_signal() {
    local name=$1 opened closed rc
    : >"$shimlog"
    LD_PRELOAD=$shim JACK_XRUN_SHIM_LOG=$shimlog "$host" -n -p "$port" >"$runtime/host.log" 2>&1 &
    host_pid=$!
    pids+=("$host_pid")
    protocol_wait_ready "$runtime/host.log"
    step $? "SIG$name: omx-clap-host ready"
    exec 3<>"/dev/tcp/127.0.0.1/$port"
    reply=$(send "add clap:$fake#org.omx-clap-host.test.passthrough 1")
    rc=1
    if [ "$reply" = "resp 1" ]; then rc=0; fi
    step "$rc" "SIG$name: a plugin added: $reply"
    for _ in $(seq 50); do grep -q '^activate ' "$shimlog" && break; sleep 0.1; done
    grep -q '^activate ' "$shimlog"; step $? "SIG$name: the plugin's client is active"
    kill -"$name" "$host_pid"
    for _ in $(seq 100); do kill -0 "$host_pid" 2>/dev/null || break; sleep 0.1; done
    ! kill -0 "$host_pid" 2>/dev/null; step $? "SIG$name: the host left"
    wait "$host_pid" 2>/dev/null
    exec 3>&-
    opened=$(sed -n 's/^activate //p' "$shimlog" | sort -u)
    closed=$(sed -n 's/^close //p' "$shimlog" | sort -u)
    [ -n "$opened" ] && [ -z "$(comm -23 <(echo "$opened") <(echo "$closed"))" ]; rc=$?
    step "$rc" "SIG$name: every client it activated was closed: activated ${opened//$'\n'/ }, closed ${closed//$'\n'/ }"
}

one_signal TERM
one_signal INT
one_signal HUP

echo "$failures failure(s)"
[ "$failures" -eq 0 ]
