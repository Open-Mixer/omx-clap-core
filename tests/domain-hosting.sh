#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# omx-clap-core publishes its hosting codes as a domain the omx-contract loader opens: the installed tree holds
# contract.d/hosting/hosting.json, the loader (omx-domain, over omx_domain_open_at) opens it, and every HOSTING_* item
# lists exactly the codes data/hosting.json and data/hosting/*.json define. data/ stays the one source; the domain file is
# what tools/render-domain.py derives from it. `make check-domain` is red on a missing file, a hand edit and an
# un-rendered data change; the render refuses a word added or removed under an unchanged VERSION and an x-code that moved.
#   env: INSTALL_CONTRACT_DIR (install-contract-dir.sh, 3.20.0 or later), OMX_DOMAIN (the omx-domain command),
#        OMX_CONTRACT_DIR (an omx-contract checkout or install, for check-domain's fmt and validate)
set -eu
: "${MAKE:=make}"
: "${OMX_DOMAIN:=omx-domain}"
[ -n "${INSTALL_CONTRACT_DIR:-}" ] || { echo "FAIL domain-hosting: INSTALL_CONTRACT_DIR is not set: no install-contract-dir.sh" >&2; exit 1; }
command -v "$OMX_DOMAIN" >/dev/null || { echo "FAIL domain-hosting: no $OMX_DOMAIN command: install libomx-domain (3.20.0 or later)" >&2; exit 1; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fresh() { rm -rf "$tmp/t"; mkdir "$tmp/t"; cp -r Makefile VERSION data tools contract.d "$tmp/t/" 2>/dev/null || true; }
D=contract.d/hosting/hosting.json

# the installed tree holds the domain, and the loader opens it with exactly the codes of the data
mkdir -p "$tmp/dest/contractdir"
sh "$INSTALL_CONTRACT_DIR" --domain contract.d/hosting "$tmp/dest/contractdir"
test -f "$tmp/dest/contractdir/hosting/hosting.json" || { echo "FAIL the installed tree has no hosting/hosting.json"; exit 1; }
python3 - data > "$tmp/items" <<'P'
import glob, json, sys
for f in [sys.argv[1] + "/hosting.json"] + sorted(glob.glob(sys.argv[1] + "/hosting/*.json")):
    for item, body in json.load(open(f)).items():
        if item.startswith("HOSTING_") and body.get("kind") == "codes":
            print(item, " ".join(c["code"] for c in body["codes"].values()))
P
[ "$(wc -l < "$tmp/items")" -ge 19 ] || { echo "FAIL fewer than 19 HOSTING_ code items read from data/"; exit 1; }
while read -r item codes; do
  words=$(OMX_CONTRACT_PATH="$tmp/dest/contractdir" "$OMX_DOMAIN" hosting "" "$item") \
    || { echo "FAIL the loader does not open hosting $item"; exit 1; }
  got=$(printf '%s\n' "$words" | sed -n 's/^word=\([^ ]*\) .*/\1/p' | sort | tr '\n' ' ')
  want=$(printf '%s\n' $codes | sort | tr '\n' ' ')
  [ "$got" = "$want" ] || { echo "FAIL $item: the loader lists [$got], data/ defines [$want]"; exit 1; }
done < "$tmp/items"

# the gate: green on a clean tree, red on a missing file, a hand edit and an un-rendered data change
fresh
$MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null || { echo "FAIL check-domain is red on a clean tree"; exit 1; }
fresh
rm "$tmp/t/$D"
if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL a missing domain file stays green"; exit 1; fi
fresh
sed -i '0,/"const": "hosting\.latency\.resolved"/s//"const": "hosting.latency.resolvd"/' "$tmp/t/$D"
if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL a domain file changed by hand stays green"; exit 1; fi
fresh
sed -i 's/"hosting.latency.resolved"/"hosting.latency.resolvd"/' "$tmp/t/data/hosting/latency.json"
if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL data/ changed and not rendered again stays green"; exit 1; fi

# a word added or removed under the same VERSION is refused by name, an existing word keeps its x-code, a new word is appended
refused() { # <label> <expected text>: render-domain fails with that text, the file is untouched, check-domain stays red
  if out=$($MAKE --no-print-directory -C "$tmp/t" render-domain 2>&1); then echo "FAIL $1: render-domain wrote it"; exit 1; fi
  printf '%s\n' "$out" | grep -q "$2" || { echo "FAIL $1: refused without naming it ($2): $out"; exit 1; }
  cmp -s "$tmp/t/$D" "$D" || { echo "FAIL $1: the file was overwritten"; exit 1; }
  if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL $1: check-domain is green"; exit 1; fi
}
edit() { # <expression over the loaded latency item `w`, the codes dict>
  python3 - "$tmp/t/data/hosting/latency.json" "$1" <<'P'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
w = d["HOSTING_LATENCY_CODES"]["codes"]
exec(sys.argv[2])
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
P
}
ADD='w["latencyNew"] = {"code": "hosting.latency.new", "text": {"en": "A new word."}}'
fresh
edit "$ADD"
refused "a word added, the version unchanged" "words added or removed while the version is unchanged"
fresh
edit 'del w["latencyResolved"]'
refused "a word removed, the version unchanged" "words added or removed while the version is unchanged"
fresh
edit 'a = w.pop("latencyNonconforming"); w["latencyNonconforming"] = a'
refused "an x-code swap" "x-code moved"
# a new version with the word appended renders, and the codes of the earlier words stay put
fresh
edit "$ADD"
echo 9.9.9 > "$tmp/t/VERSION"
$MAKE --no-print-directory -C "$tmp/t" render-domain >/dev/null || { echo "FAIL a word appended under a new version is refused"; exit 1; }
$MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null || { echo "FAIL check-domain is red after a render under a new version"; exit 1; }
grep -q '"version": "9.9.9"' "$tmp/t/$D" || { echo "FAIL the domain's version is not VERSION"; exit 1; }
grep -q '"const": "hosting.latency.new"' "$tmp/t/$D" || { echo "FAIL the appended word is not in the domain file"; exit 1; }
echo "ok   domain hosting: installed, opened by the loader with every code of data/; check-domain red on missing, hand-edited and unrendered; a word added or removed or an x-code moved under the same version refused; an appended word under a new version renders"
