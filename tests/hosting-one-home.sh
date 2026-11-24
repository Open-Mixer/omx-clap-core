#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# One home per word: the HOSTING_*_CODES items live in the hosting domain alone (contract.d/hosting/hosting.json), the
# stage's numbers in data/hosting.json and the verb hosts in data/hosting/verb-hosts.json. A hosting code item put back
# into data/ is a second home, and the read refuses it by name (contract.item.duplicate); the verb hosts declared again in
# the domain make one data file with two sources (contract.manifest.mismatch). Each arm is planted in a scratch copy of the
# committed tree, installed with make install-contract and read back with tests/contract-dir-check.sh; the clean copy reads
# back green first.
#   usage: tests/hosting-one-home.sh <omx-contract checkout or /usr/lib/omx-contract> <install-contract-dir.sh>
set -u
oc=${1:?usage: hosting-one-home.sh <omx-contract dir> <install-contract-dir.sh>}
installer=${2:?usage: hosting-one-home.sh <omx-contract dir> <install-contract-dir.sh>}
root=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
version=$(cat "$root/VERSION")
fail=0

# copy <name>: the committed tree, as git has it, under $tmp/<name>
copy() {
    mkdir -p "$tmp/$1" && git -C "$root" archive --format=tar HEAD | tar -x -C "$tmp/$1"
}
# readback <name>: install the copy's contract tree and read it back; prints the read's output, returns its status
readback() {
    make -s --no-print-directory -C "$tmp/$1" install-contract DESTDIR= DATADIR="$tmp/$1/build/share" \
        CONTRACTDIR="$tmp/$1/build/dir" INSTALL_CONTRACT_DIR="$installer" >/dev/null 2>&1 || { echo "install-contract failed"; return 3; }
    (cd "$tmp/$1" && OMX_CONTRACT_SCRIPT="$installer" sh tests/contract-dir-check.sh "$oc" build/dir "$version" 2>&1)
}

copy clean
out=$(readback clean); rc=$?
if [ $rc -eq 0 ]; then echo "ok   the committed tree reads back green"; else echo "FAIL the control: the committed tree reads back red ($rc): $(printf '%s' "$out" | grep -v '^install-contract-dir' | head -3)"; exit 1; fi

# arm <name> <python edit, run in the copy's root> <label> <the code the read refuses it by>
arm() {
    copy "$1"
    (cd "$tmp/$1" && python3 -I -c "$2") || { echo "FAIL $3: the plant did not apply"; fail=1; return; }
    out=$(readback "$1"); rc=$?
    if [ $rc -ne 0 ] && printf '%s' "$out" | grep -q "$4"; then
        echo "ok   $3: refused ($4)"
    else
        echo "FAIL $3: rc=$rc, $(printf '%s' "$out" | grep -v '^install-contract-dir' | head -2)"; fail=1
    fi
}

arm data-copy '
import json
d = json.load(open("data/hosting.json"))
it = json.load(open("contract.d/hosting/hosting.json"))["components"]["schemas"]["HOSTING_IDLE_CODES"]
d["HOSTING_IDLE_CODES"] = {"kind": "codes", "doc": it["description"], "codes": {w["title"]: {"code": w["const"], "text": {"en": w["x-text"]}} for w in it["oneOf"]}}
open("data/hosting.json", "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
' "a hosting code item put back into data/hosting.json" contract.item.duplicate

arm domain-copy '
import json
p = "contract.d/hosting/hosting.json"
d = json.load(open(p))
d["components"]["schemas"]["HOSTING_VERB_HOSTS"] = dict(d["components"]["schemas"]["HOSTING_IDLE_CODES"], **{"x-file": "hosting/verb-hosts.json"})
open(p, "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
' "the verb hosts declared again in the hosting domain" contract.manifest.mismatch

[ $fail = 0 ] && echo "hosting-one-home: ok"
exit $fail
