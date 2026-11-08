#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# control.sh <omx-rt-gate> <cc>: the gate against tests/rt_gate/host_roots.c as this tree binds it (make
# test-rt-gate-control). Every host root is derived with its role; the clean unit reads green; a malloc, a lock and a
# sleep planted in try_push, and a malloc planted in respond, each read red with its code. RT_GATE_TABLES=<dir> runs it
# on other tables (tests/rt_gate/sabotage.sh). Exit 0 when all hold, 1 on the first that does not.
set -u
gate=${1:?usage: control.sh <omx-rt-gate> <cc>}; cc=${2:?usage: control.sh <omx-rt-gate> <cc>}
here=$(cd "$(dirname "$0")" && pwd)
tables=()
[ -n "${RT_GATE_TABLES:-}" ] && tables=(--tables "$RT_GATE_TABLES")
out=$(mktemp -d) || exit 1
trap 'rm -rf "$out"' EXIT
fail() { echo "FAIL $*"; exit 1; }

# <plant>: the gate's stdout in $out/<plant>, its exit status returned
run() {
  "$gate" "${tables[@]}" --abi clap:host --abi lv2:host --list-roots -- "$cc" -std=gnu99 -D_GNU_SOURCE -pthread \
    -DRT_GATE_PLANT="$1" "$here/host_roots.c" > "$out/$1" 2> "$out/$1.err"
}

run 0; rc=$?
[ "$rc" = 0 ] || { cat "$out/0" "$out/0.err"; fail "the clean host roots read exit $rc, not 0"; }
for want in 'try_push\[audio\] clap_output_events.try_push' 'in_size\[audio\] clap_input_events.size' \
            'in_get\[audio\] clap_input_events.get' 'request_exec\[audio\] clap_host_thread_pool.request_exec' \
            'tail_changed\[audio\] clap_host_tail.changed' 'request_flush\[audio\] clap_host_params.request_flush' \
            'schedule_work\[audio\] LV2_Worker_Schedule.schedule_work' 'log_printf\[audio\] LV2_Log_Log.printf' \
            'respond\[worker\] LV2_Worker_Interface.work'; do
  grep -q "^ROOT $want " "$out/0" || fail "no root $want"
done
grep -q '^SUMMARY roots=9 audio=8 worker=1 .* red=0$' "$out/0" || fail "the clean summary: $(grep SUMMARY "$out/0")"
echo "ok   9 host roots derived (8 audio, 1 worker), the clean unit green"

for case in '1 RT-ALLOC malloc try_push\[audio\]' '2 RT-LOCK pthread_mutex_lock try_push\[audio\]' \
            '3 RT-BLOCK nanosleep try_push\[audio\]' '4 RT-ALLOC malloc respond\[worker\]'; do
  set -- $case
  run "$1"; rc=$?
  [ "$rc" = 1 ] || { cat "$out/$1" "$out/$1.err"; fail "plant $1 ($3 in ${4%%\\*}) read exit $rc, not 1"; }
  grep -q "^$2 $3 at .*host_roots.c:[0-9]*:[0-9]* via $4" "$out/$1" || fail "plant $1: no '$2 $3 ... via $4' line"
  echo "ok   plant $1: $2 $3 via ${4//\\/} reads red"
done
