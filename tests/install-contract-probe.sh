#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# make install-contract probes the omx-contract installer it found for the mode it uses, never a version (no floor): an
# install-contract-dir.sh without a --domain mode (one older than the contract tree, as a stale channel serves it) is
# refused by name before anything is installed, instead of printing its usage half-way through the domains (#214).
#   arm 1: a stub installer with no --domain mode -> install-contract exits non-zero, names the stub and "no --domain mode",
#          and the stub was never run;
#   arm 2: a stub installer with a --domain mode -> the probe passes (the stub records each call; every call succeeds).
# usage: tests/install-contract-probe.sh
set -u
root=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0

# an installer from before the --domain mode: its usage names the package mode alone
cat >"$tmp/old.sh" <<'EOF'
#!/bin/sh
echo "called $*" >>"${STUB_LOG:?}"
echo "usage: install-contract-dir.sh <package> <version> <schema major> <src> <contractdir> <name>" >&2
exit 2
EOF
# an installer with the mode: it answers every call
cat >"$tmp/new.sh" <<'EOF'
#!/bin/sh
# usage: install-contract-dir.sh <package> <version> <schema major> <src> <contractdir> <name>
#        install-contract-dir.sh --domain <domain dir> <contractdir> <package>
echo "called $*" >>"${STUB_LOG:?}"
exit 0
EOF

: >"$tmp/old.log"
out=$(STUB_LOG="$tmp/old.log" make -s -C "$root" install-contract INSTALL_CONTRACT_DIR="$tmp/old.sh" DESTDIR="$tmp/dest" 2>&1)
rc=$?
if [ $rc -ne 0 ] && printf '%s' "$out" | grep -qF "install-contract: $tmp/old.sh has no --domain mode: the omx-contract installer found is older than the contract tree" && [ ! -s "$tmp/old.log" ]; then
    echo "ok   an installer with no --domain mode is refused by name, before any call"
else
    echo "FAIL an installer with no --domain mode: rc=$rc, calls: $(wc -l <"$tmp/old.log"), output: $(printf '%s' "$out" | tail -3)"
    fail=1
fi

: >"$tmp/new.log"
out=$(STUB_LOG="$tmp/new.log" make -s -C "$root" install-contract INSTALL_CONTRACT_DIR="$tmp/new.sh" DESTDIR="$tmp/dest" 2>&1)
rc=$?
if ! printf '%s' "$out" | grep -qF 'has no --domain mode' && grep -q -- '--domain contract.d/scan' "$tmp/new.log"; then
    echo "ok   an installer with a --domain mode passes the probe and installs the domains (exit $rc)"
else
    echo "FAIL an installer with a --domain mode: rc=$rc, output: $(printf '%s' "$out" | tail -3)"
    fail=1
fi
[ $fail = 0 ] && echo "install-contract-probe: ok"
exit $fail
