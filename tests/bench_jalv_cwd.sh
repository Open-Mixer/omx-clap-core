#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# A jalv the bench starts leaves no state directory where the bench was started. jalv makes its state directory with a
# relative mkdtemp("jalvXXXXXX") (jalv 1.8.0 src/jalv.c:872), in its working directory, and removes it only at a clean
# exit; the bench ends its jalvs with SIGTERM and its namespace with SIGKILL, so each one left a jalvXXXXXX in the
# caller's working directory. bench/lib.sh starts them in its run directory instead, which goes when the run ends: at
# its exit, and on SIGINT, SIGTERM or SIGHUP, the signal then ending the run.
#
# Run against a jalv stand-in that makes the same relative directory and ignores SIGTERM, the bench's path "jalv"
# sourced as bench/run-one.sh sources it (a session of its own), from a caller standing in a private home.
set -uo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
fail=0
ok() { echo "ok   $1"; }
bad() { echo "FAIL $1"; fail=1; }

mkdir -p "$work/bin" "$work/stub"
# a jalv that never reaches its own cleanup: it ignores SIGTERM and dies after two seconds without removing its
# directory, as a jalv the bench's namespace or a timeout kills
printf '#!/bin/sh\nmktemp -d jalvXXXXXX >/dev/null || exit 9\ntrap "" TERM\nsleep 2\nexit 0\n' >"$work/bin/jalv"
chmod +x "$work/bin/jalv"
# the bench's own helpers this path reaches: its client's ports are in the graph at once, and no protocol client
printf 'print("effect_0:out")\n' >"$work/stub/stats.py"
: >"$work/stub/protocol.sh"

# one run: add a jalv, quit it as the path does, then end by exit or by a signal to the run itself
run() {
    local how=$1 home=$work/home-$1
    mkdir -p "$home" "$work/raw-$1"
    cat >"$work/caller-$1.sh" <<EOF
cd "$home" || exit 2
echo \$\$ >"$work/pid-$how"
here=$work/stub root=$repo path=jalv rate=48000 quantum=256 out=$work/raw-$how raw=$work/raw-$how
BENCH_SESSION=1 JALV=$work/bin/jalv PLUGIN_HOSTD_TESTS_LIB=$work/stub
. "$repo/bench/lib.sh"
echo "\$runtime" >"$work/runtime-$how"
send "add urn:x 0" >/dev/null
sleep 0.3
send quit >/dev/null
sleep 0.3
[ "$how" = exit ] && exit 0
kill -s "$how" \$\$
sleep 5
exit 0
EOF
    HOME=$home setsid -w bash "$work/caller-$1.sh"
    local rc=$? pid
    pid=$(cat "$work/pid-$how")
    kill -KILL -- "-$pid" 2>/dev/null
    local want=0 n
    case $how in INT) want=130 ;; TERM) want=143 ;; HUP) want=129 ;; esac
    [ "$rc" = "$want" ] && ok "a run ended by $how ends as it would have ($rc)" || bad "a run ended by $how exits $rc, not $want"
    n=$(find "$home" -name 'jalv??????' | wc -l)
    [ "$n" = 0 ] && ok "a run ended by $how leaves no state directory in its caller's home" ||
        bad "a run ended by $how leaves $n state directory(ies) in its caller's home"
    [ ! -e "$(cat "$work/runtime-$how")" ] && ok "a run ended by $how leaves no run directory" ||
        bad "a run ended by $how leaves its run directory $(cat "$work/runtime-$how")"
    rm -rf "$(cat "$work/runtime-$how")"
}

PATH=$work/bin:$PATH
for how in exit INT TERM HUP; do run "$how"; done
[ "$fail" = 0 ] && echo "bench jalv cwd ok" || echo "FAIL bench jalv cwd"
exit "$fail"
