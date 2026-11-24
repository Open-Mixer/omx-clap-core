#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# omx-clap publishes its hosting codes as a domain the omx-contract loader opens: the installed tree holds
# contract.d/hosting/hosting.json, the loader (omx-domain, over omx_domain_open_at) opens it, and every HOSTING_* item
# lists exactly the codes data/hosting.json and data/hosting/*.json define. data/ stays the one source; the domain file is
# what tools/render-domain.py derives from it. `make check-domain` is red on a missing file, a hand edit and an
# un-rendered data change; the refusals (a word added or removed under an unchanged VERSION, an x-code that moved, a version going down) are omx-contract's `domain check`, and validate holds every item's x-since.
#   env: INSTALL_CONTRACT_DIR (install-contract-dir.sh, 3.22.0 or later: its --domain mode names the installing package), OMX_DOMAIN (the omx-domain command),
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
sh "$INSTALL_CONTRACT_DIR" --domain contract.d/hosting "$tmp/dest/contractdir" omx-clap
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
refused "a word added, the version unchanged" "word added while info.version stays"
fresh
edit 'del w["latencyResolved"]'
refused "a word removed, the version unchanged" "word removed while info.version stays"
fresh
edit 'a = w.pop("latencyNonconforming"); w["latencyNonconforming"] = a'
refused "an x-code swap" "x-code moved from"
# the refusals are omx-contract's `domain check`: a version going down is refused too, and the document is untouched
fresh
echo 0.1.0 > "$tmp/t/VERSION"
refused "a version going down" "is below"
# every item carries an x-since, never above the document's info.version: validate (omx-contract's rule domain-x-since) is red
since_red() { # <label> <sed script over the domain file>
  fresh
  sed -i "$2" "$tmp/t/$D"
  rm -rf "$tmp/only"; mkdir -p "$tmp/only"; cp -r "$tmp/t/contract.d/hosting" "$tmp/only/"
  if out=$(node "$OMX_CONTRACT_DIR/bin/omx-contract.mjs" validate --contract-dir "$tmp/only" 2>&1); then echo "FAIL $1: validate is green"; exit 1; fi
  printf '%s\n' "$out" | grep -q "domain-x-since" || { echo "FAIL $1: validate is red without naming domain-x-since: $out"; exit 1; }
}
since_red "an item without x-since" '0,/"x-since": "[0-9.]*",/{/"x-since": "[0-9.]*",/d}'
since_red "an x-since above info.version" '0,/"x-since": "[0-9.]*"/s//"x-since": "99.0.0"/'
# every item of the rendered file says the version that first carried it: 0.35.0, the first release that ships the
# domain, or a later one; never an earlier one (a version that shipped without the domain cannot have carried an item)
FIRST=0.35.0
python3 - "$D" "$FIRST" <<'P' || exit 1
import json, sys
items = json.load(open(sys.argv[1]))["components"]["schemas"]
key = lambda v: tuple(int(p) for p in v.split("."))
early = [n for n, b in items.items() if key(b.get("x-since", "0.0.0")) < key(sys.argv[2])]
if len(items) < 19 or early:
    sys.exit(f"FAIL {len(items)} items, and these carry no x-since or one before {sys.argv[2]}: {early}")
P
# a new version with the word appended renders, and the codes of the earlier words stay put
fresh
edit "$ADD"
echo 9.9.9 > "$tmp/t/VERSION"
$MAKE --no-print-directory -C "$tmp/t" render-domain >/dev/null || { echo "FAIL a word appended under a new version is refused"; exit 1; }
$MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null || { echo "FAIL check-domain is red after a render under a new version"; exit 1; }
[ "$(grep -c '"x-since": "9.9.9"' "$tmp/t/$D")" = 0 ] || { echo "FAIL an item that was there got the new version as its x-since"; exit 1; }
grep -q '"version": "9.9.9"' "$tmp/t/$D" || { echo "FAIL the domain's version is not VERSION"; exit 1; }
grep -q '"const": "hosting.latency.new"' "$tmp/t/$D" || { echo "FAIL the appended word is not in the domain file"; exit 1; }
echo "ok   domain hosting: installed, opened by the loader with every code of data/; check-domain red on missing, hand-edited and unrendered; a word added or removed or an x-code moved under the same version refused; an appended word under a new version renders"
