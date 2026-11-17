#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The scan domain (contract.d/scan/scan.json, docs/contract-dir.md "Domains") read back through omx-contract's reader:
# it is owned by this package, carries the 2 documents and the 13 field-dump scopes, and its render is the committed
# src/scan_vocabulary.h byte for byte (the words omx-contract held as data/scan.json, rendered unchanged).
# usage: tests/domain-scan-check.sh <omx-contract checkout or install root>
set -eu
oc=${1:?usage: domain-scan-check.sh <omx-contract root>}
tool="node $oc/bin/omx-contract.mjs"
work=$(mktemp -d "${TMPDIR:-/tmp}/domain-scan.XXXXXX")
trap 'rm -rf "$work"' EXIT
[ -f contract.d/scan/scan.json ] || { echo "domain-scan-check: contract.d/scan/scan.json is absent" >&2; exit 1; }
grep -q '"x-owner": "omx-clap-core"' contract.d/scan/scan.json || { echo "domain-scan-check: the scan domain is not owned by omx-clap-core" >&2; exit 1; }
$tool render --target c --package scan --contract-dir contract.d --out "$work"
cmp src/scan_vocabulary.h "$work/scan_vocabulary.h" || { echo "domain-scan-check: src/scan_vocabulary.h is not the render of contract.d/scan" >&2; exit 1; }
grep -qx '#define OMX_SCAN_DOCUMENTS_COUNT 2u' src/scan_vocabulary.h
grep -qx '#define OMX_SCAN_FIELD_SCOPES_COUNT 13u' src/scan_vocabulary.h
echo "domain-scan-check: ok"
