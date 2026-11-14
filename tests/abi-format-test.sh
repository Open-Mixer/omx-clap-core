#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# tests/abi-check.sh where libabigail writes another ABI-XML format than the committed baseline's (fedora:45's abidw writes
# format 2, the baseline is format 3, and abidiff cannot compare the two at all; ruling of 2026-11-14 on #73): the
# baseline is compared on the ABI cell abi.yml declares (OMX_ABI_CELL), whose abidw writes the baseline's format; another
# cell prints a measured skip naming both formats; on the ABI cell, or with no ABI cell named, a mismatch is red, never a
# silent pass. Stub abidw and abidiff stand in for libabigail; the baseline is planted.
set -u
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
fails=0
check() { if [ "$1" = 0 ]; then echo "ok   $2"; else echo "FAIL $2"; fails=$((fails + 1)); fi; }

mkdir -p "$work/bin" "$work/root/usr/lib" "$work/inc"
lib=$work/root/usr/lib/libomx-clap-core.so.0.33.0
: >"$lib"
cat >"$work/bin/abidw" <<'EOF'
#!/bin/sh
while [ $# -gt 1 ]; do [ "$1" = --out-file ] && out=$2; shift; done
printf "<abi-corpus version='2.3' path='%s' architecture='elf-amd-x86_64' soname='libomx-clap-core.so.1'>\n</abi-corpus>\n" "$1" >"$out"
EOF
cat >"$work/bin/abidiff" <<'EOF'
#!/bin/sh
echo "abidiff: incompatible format version between the two input files"
exit 1
EOF
chmod +x "$work/bin/abidw" "$work/bin/abidiff"
printf "<abi-corpus version='3.0' path='build/abi/usr/lib/libomx-clap-core.so.0.25.0' architecture='elf-amd-x86_64' soname='libomx-clap-core.so.1'>\n</abi-corpus>\n" >"$work/baseline.abi"

run() { # <cell> <abi cell>: the check's output, then its exit status on the last line
    PATH="$work/bin:$PATH" OMX_CELL=$1 OMX_ABI_CELL=$2 sh "$here/abi-check.sh" "$lib" "$work/inc" "$work/baseline.abi" 2>&1
    echo "rc=$?"
}

out=$(run 45 44)
echo "$out" | grep -q "^VERIFY-SKIP abi: abidw writes format 2, the baseline format 3" && echo "$out" | grep -q "^rc=0$"
check $? "another cell than the ABI cell: a measured skip naming both formats, the check passes: $(echo "$out" | tail -2 | tr '\n' ' ')"
out=$(run 44 44)
echo "$out" | grep -q "^FAIL" && echo "$out" | grep -q "^rc=1$"
check $? "the ABI cell itself: a format mismatch is red: $(echo "$out" | tail -2 | tr '\n' ' ')"
out=$(run 45 "")
echo "$out" | grep -q "^FAIL" && echo "$out" | grep -q "^rc=1$"
check $? "no ABI cell named: a format mismatch is red, never a silent pass: $(echo "$out" | tail -2 | tr '\n' ' ')"

[ "$fails" = 0 ] && echo "abi format: ok" || echo "abi format: $fails failed"
[ "$fails" = 0 ]
