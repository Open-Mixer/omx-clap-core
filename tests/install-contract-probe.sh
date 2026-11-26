#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# make install-contract probes the omx-contract installer it found, before any install step, for the --domain form its
# calls make (four arguments: the domain, the contract directory and the package that installs it), never a version (no
# floor): a dry `install-contract-dir.sh --domain` prints the installer's usage and installs nothing. An installer whose
# usage has no four-argument --domain (one with no --domain mode, or the three-argument one omx-contract released first)
# is refused by name before any call, instead of printing its usage half-way through the domains (#214).
#   arm 1: a stub with no --domain mode -> refused by name, no install call made;
#   arm 2: a stub with the three-argument --domain -> refused by name, no install call made (the package mode, which every
#          form has, is never run before the probe);
#   arm 3: a stub with the four-argument --domain -> the probe passes and the domains are installed through it.
# A stub records each install call (three or more arguments); the probe's dry call, with none, is no install.
# usage: tests/install-contract-probe.sh
set -u
root=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0

# stub <file> <usage lines>: an installer that prints the usage on a dry call and records every install call
stub() {
    {
        echo '#!/bin/sh'
        echo 'if [ "$#" -lt 3 ]; then cat >&2 <<"USAGE"'
        printf '%s\n' "$2"
        echo 'USAGE'
        echo 'exit 2; fi'
        echo 'echo "called $*" >>"${STUB_LOG:?}"'
        echo "$3"
    } >"$1"
}
stub "$tmp/none.sh" '#   install-contract-dir.sh <package> <version> <schema major> <from dir> <contractdir> [<tree>]' \
    '[ "$1" = --domain ] && { echo "install-contract-dir.sh: no package --domain" >&2; exit 2; }; exit 0'
stub "$tmp/three.sh" '#   install-contract-dir.sh <package> <version> <schema major> <from dir> <contractdir> [<tree>]
#   install-contract-dir.sh --domain <path>/contract.d/<domain> <contractdir>' \
    '[ "$1" = --domain ] && [ "$#" -ne 3 ] && { echo "install-contract-dir.sh: --domain needs <path>/contract.d/<domain> and <contractdir>" >&2; exit 2; }; exit 0'
stub "$tmp/four.sh" '#   install-contract-dir.sh <package> <version> <schema major> <from dir> <contractdir> [<tree>]
#   install-contract-dir.sh --domain <path>/contract.d/<domain> <contractdir> <package>' 'exit 0'

refused() {
    : >"$tmp/$1.log"
    out=$(STUB_LOG="$tmp/$1.log" make -s -C "$root" install-contract INSTALL_CONTRACT_DIR="$tmp/$1.sh" DESTDIR="$tmp/dest" 2>&1)
    rc=$?
    if [ $rc -ne 0 ] && printf '%s' "$out" | grep -qF "install-contract: $tmp/$1.sh has no --domain mode: the omx-contract installer found is older than the contract tree" && [ ! -s "$tmp/$1.log" ]; then
        echo "ok   $2 is refused by name, before any install call"
    else
        echo "FAIL $2: rc=$rc, install calls: $(wc -l <"$tmp/$1.log"), output: $(printf '%s' "$out" | tail -2)"
        fail=1
    fi
}
refused none "an installer with no --domain mode"
refused three "an installer with the three-argument --domain"

: >"$tmp/four.log"
out=$(STUB_LOG="$tmp/four.log" make -s -C "$root" install-contract INSTALL_CONTRACT_DIR="$tmp/four.sh" DESTDIR="$tmp/dest" 2>&1)
rc=$?
if [ $rc -eq 0 ] && grep -q -- '--domain contract.d/scan .* omx-clap$' "$tmp/four.log"; then
    echo "ok   an installer with the four-argument --domain passes the probe and installs the domains"
else
    echo "FAIL an installer with the four-argument --domain: rc=$rc, output: $(printf '%s' "$out" | tail -3)"
    fail=1
fi
[ $fail = 0 ] && echo "install-contract-probe: ok"
exit $fail
