#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# omx-clap-host's command socket against tests/socket_conformance.py, in a PipeWire of its own: the script re-runs
# itself in a private user, net, pid and mount namespace (where /proc is masked, a container's: user and net, a session of
# its own), starts pipewire on a private runtime dir, starts the host
# and runs every framing case of the conformance script against its socket (a command of exactly the receive buffer
# size, many commands in one write, one command over many writes, clients that leave mid-command, the size limit,
# a random chunking fuzz). The host's protocol library is what is checked: omx-clap-host only links it.
#
# OMX_CLAP_HOST:           the binary (default ./omx-clap-host)
# SOCKET_E2E_PORT:         the socket port (default 5570)
# SOCKET_CONFORMANCE_ARGS: extra arguments for the conformance script (--seed N to repeat a fuzz run)

set -u

here=$(cd "$(dirname "$0")" && pwd)
. "${PLUGIN_HOSTD_TESTS_LIB:-$here/../../plugin-hostd/tests/lib}/protocol.sh"
root=$(dirname "$here")
host=${OMX_CLAP_HOST:-$root/omx-clap-host}
port=${SOCKET_E2E_PORT:-5570}

if [ -z "${SOCKET_E2E_INSIDE:-}" ]; then
    [ -e "$host" ] || { echo "missing $host" >&2; exit 2; }
    export SOCKET_E2E_INSIDE=1 OMX_CLAP_HOST=$host SOCKET_E2E_PORT=$port
    if unshare --user --map-root-user --net --pid --fork --mount-proc true 2>/dev/null; then
        exec unshare --user --map-root-user --net --pid --fork --mount-proc "$0" "$@"
    fi
    # a container whose /proc is masked refuses a /proc of its own (`unshare: mount /proc failed: Permission denied`,
    # stage wave f45t 2026-11-23): no pid namespace, the run its own session, and its cleanup that session's processes
    # alone (chain_identity.sh, chain_host_e2e.sh)
    SOCKET_E2E_SESSION=1 exec unshare --user --map-root-user --net setsid -w "$0" "$@"
fi

runtime=$(mktemp -d /tmp/omx-clap-host-socket.XXXXXX)
export XDG_RUNTIME_DIR=$runtime PIPEWIRE_RUNTIME_DIR=$runtime PULSE_RUNTIME_PATH=$runtime/pulse
unset DBUS_SESSION_BUS_ADDRESS
cleanup() {
    if [ -n "${SOCKET_E2E_SESSION:-}" ]; then
        trap '' TERM
        kill -TERM -- -$$ 2>/dev/null
    else
        kill -TERM -- -1 2>/dev/null
    fi
    wait 2>/dev/null
    rm -rf "${runtime:?}"
}
trap cleanup EXIT
if [ -n "${SOCKET_E2E_SESSION:-}" ]; then
    # the process group from /proc/<pid>/stat (the third field after the command's ')'), no ps: a stage box has no procps
    pgid=$(sed 's/.*) //' /proc/$$/stat | cut -d' ' -f3)
    [ "$pgid" = $$ ] || { echo "not a session of its own (process group ${pgid:-unread}, pid $$): its cleanup would reach past it" >&2; exit 2; }
    echo "a session of its own (the container refuses a pid namespace's /proc)"
fi

ip link set lo up

pipewire >"$runtime/pw.log" 2>&1 &
for _ in $(seq 50); do [ -S "$runtime/pipewire-0" ] && break; sleep 0.1; done
[ -S "$runtime/pipewire-0" ] || { echo "pipewire did not come up" >&2; cat "$runtime/pw.log" >&2; exit 2; }

"$host" -n -p "$port" >"$runtime/host.log" 2>&1 &
pid=$!
protocol_wait_ready "$runtime/host.log" || { echo "omx-clap-host did not come up" >&2; cat "$runtime/host.log" >&2; exit 2; }
echo "omx-clap-host on port $port, protocol library: $(grep -o '/[^ ]*libplugin-hostd-protocol[^ ]*' /proc/$pid/maps | sort -u)"

# shellcheck disable=SC2086
python3 -I "$here/socket_conformance.py" --port "$port" --pid "$pid" ${SOCKET_CONFORMANCE_ARGS:-}
status=$?
kill -0 "$pid" 2>/dev/null || { echo "omx-clap-host is gone:"; tail -5 "$runtime/host.log"; status=1; }
exit $status
