#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The scan domain (contract.d/scan/scan.json) held to the consumer-move recipe (omx-contract docs/consumer-move.md, steps 1 to 4):
#   1. the document conforms: $schema, the exact $id, info.x-owner omx-clap-core, info.x-stability experimental, every item prefixed
#      SCAN_, and it validates with its six catalogs by omx-contract's reader;
#   2. no scan_vocabulary.h exists or is included, anywhere in the tree;
#   3. the codes header src/scan_codes.h is the render (--check), and holds only the items marked x-c-codes (SCAN_FIELD_SCOPES,
#      the scopes the field dump indexes by), never SCAN_DOCUMENTS.
# usage: tests/domain-scan-check.sh <omx-contract checkout or install root>
set -eu
oc=${1:?usage: domain-scan-check.sh <omx-contract root>}
tool="node $oc/bin/omx-contract.mjs"
work=$(mktemp -d "${TMPDIR:-/tmp}/domain-scan.XXXXXX")
trap 'rm -rf "$work"' EXIT
doc=contract.d/scan/scan.json
fail() { echo "domain-scan-check: $1" >&2; exit 1; }
[ -f "$doc" ] || fail "$doc is absent"
node -e '
  const d = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
  const bad = [];
  if (d.$schema !== "https://json-schema.org/draft/2020-12/schema") bad.push("$schema is " + d.$schema);
  if (d.$id !== "https://openmixer.org/contract/scan") bad.push("$id is " + d.$id);
  if (d.info?.["x-owner"] !== "omx-clap-core") bad.push("info.x-owner is " + d.info?.["x-owner"]);
  if (d.info?.["x-stability"] !== "experimental") bad.push("info.x-stability is " + d.info?.["x-stability"]);
  for (const n of Object.keys(d.components.schemas)) if (!n.startsWith("SCAN_")) bad.push("item " + n + " is not prefixed SCAN_");
  if (d.components.schemas.SCAN_FIELD_SCOPES?.["x-c-codes"] !== true) bad.push("SCAN_FIELD_SCOPES is not marked x-c-codes");
  if ("x-c-codes" in (d.components.schemas.SCAN_DOCUMENTS ?? {})) bad.push("SCAN_DOCUMENTS is marked x-c-codes, and no C switches on it");
  if (bad.length) { console.error(bad.join("\n")); process.exit(1); }
' "$doc" || fail "the scan document breaks the recipe (step 1)"
$tool validate --contract-dir contract.d | grep -q ", valid, 6 catalogs" || fail "the scan domain and its 6 catalogs do not validate"
if [ -e src/scan_vocabulary.h ] || git grep -n 'scan_vocabulary' -- . ':!tests/domain-scan-check.sh' | grep -q .; then
  fail "scan_vocabulary.h exists or is still named (step 3): $(git grep -n 'scan_vocabulary' -- . ':!tests/domain-scan-check.sh' | head -3 | tr '\n' ' ')"
fi
[ -f src/scan_codes.h ] || fail "src/scan_codes.h is absent (step 2)"
$tool render --target c --package scan --contract-dir contract.d --out "$work"
cmp src/scan_codes.h "$work/scan_codes.h" || fail "src/scan_codes.h is not the render of contract.d/scan"
grep -q 'OMX_SCAN_FIELD_SCOPES_PLACEMENT_DEFAULT' src/scan_codes.h || fail "the codes header lacks the SCAN_FIELD_SCOPES words"
! grep -q 'OMX_SCAN_DOCUMENTS' src/scan_codes.h || fail "the codes header holds SCAN_DOCUMENTS, which no C switches on"
echo "domain-scan-check: ok"
