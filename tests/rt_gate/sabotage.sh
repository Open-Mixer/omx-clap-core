#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# sabotage.sh <omx-rt-gate> <cc>: the gate's tables emptied one at a time in a copy (make test-rt-gate-sabotage), and
# tests/rt_gate/control.sh run on each: it must go red every time. The forbidden list emptied: the gate judges nothing;
# the class table emptied: the bounded copy a root makes is red; the CLAP and LV2 roles emptied: no root. The copy
# unchanged first, green, so a red is the sabotage's.
set -u
gate=${1:?usage: sabotage.sh <omx-rt-gate> <cc>}; cc=${2:?usage: sabotage.sh <omx-rt-gate> <cc>}
here=$(cd "$(dirname "$0")" && pwd)
path=$(command -v "$gate") || { echo "FAIL no $gate"; exit 1; }
src=$(cd "$(dirname "$path")/../share/omxdsp/rt-gate/tables" 2>/dev/null && pwd) \
  || { echo "FAIL no tables beside $path"; exit 1; }
work=$(mktemp -d) || exit 1
trap 'rm -rf "$work"' EXIT

cp -r "$src" "$work/tables"
RT_GATE_TABLES="$work/tables" "$here/control.sh" "$gate" "$cc" > "$work/log" \
  || { cat "$work/log"; echo "FAIL the control on an unchanged copy of the tables"; exit 1; }
for f in forbidden.tbl classes.tbl 'clap.abi lv2.abi'; do
  rm -rf "$work/tables" && cp -r "$src" "$work/tables"
  for t in $f; do : > "$work/tables/$t"; done
  if RT_GATE_TABLES="$work/tables" "$here/control.sh" "$gate" "$cc" > "$work/log"; then
    cat "$work/log"; echo "FAIL $f emptied: the control still passed"; exit 1
  fi
  echo "ok   $f emptied: the control is red ($(grep -m1 '^FAIL' "$work/log"))"
done
