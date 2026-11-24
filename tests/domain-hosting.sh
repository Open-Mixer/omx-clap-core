#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# omx-clap's hosting codes have one home, the domain contract.d/hosting/hosting.json (omx-contract#215): the installed
# tree holds it, the loader (omx-domain, over omx_domain_open_at) opens every HOSTING_* item with exactly the codes the
# document declares, each code with its doc as its description, and data/ declares none of them. The read of the package
# and the domain together refuses a second home (contract.item.duplicate), and render --target md refuses a code with no
# doc. `make check-domain` is red on a missing file and on an undocumented code; its refusals against an earlier document
# (a word added or removed under an unchanged version, an x-code moved, a version going down) are omx-contract's
# `domain check`, and validate holds every item's x-since.
#   env: INSTALL_CONTRACT_DIR (install-contract-dir.sh, 3.22.0 or later: its --domain mode names the installing package), OMX_DOMAIN (the omx-domain command),
#        OMX_CONTRACT_DIR (an omx-contract checkout or install, for check-domain and the read)
set -eu
: "${MAKE:=make}"
: "${OMX_DOMAIN:=omx-domain}"
[ -n "${INSTALL_CONTRACT_DIR:-}" ] || { echo "FAIL domain-hosting: INSTALL_CONTRACT_DIR is not set: no install-contract-dir.sh" >&2; exit 1; }
command -v "$OMX_DOMAIN" >/dev/null || { echo "FAIL domain-hosting: no $OMX_DOMAIN command: install libomx-domain (3.20.0 or later)" >&2; exit 1; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fresh() { rm -rf "$tmp/t"; mkdir "$tmp/t"; cp -r Makefile VERSION data contract.d "$tmp/t/" 2>/dev/null || true; }
D=contract.d/hosting/hosting.json
tool="node $OMX_CONTRACT_DIR/bin/omx-contract.mjs"

# the installed tree holds the domain, and the loader opens it with exactly the codes the document declares, the doc as
# each code's description
mkdir -p "$tmp/dest/contractdir"
sh "$INSTALL_CONTRACT_DIR" --domain contract.d/hosting "$tmp/dest/contractdir" omx-clap
test -f "$tmp/dest/contractdir/hosting/hosting.json" || { echo "FAIL the installed tree has no hosting/hosting.json"; exit 1; }
python3 - "$D" > "$tmp/items" <<'P'
import json, sys
for item, body in json.load(open(sys.argv[1]))["components"]["schemas"].items():
    print(item, " ".join(w["const"] for w in body["oneOf"]))
P
[ "$(wc -l < "$tmp/items")" -ge 19 ] || { echo "FAIL fewer than 19 HOSTING_ code items in $D"; exit 1; }
while read -r item codes; do
  case $item in HOSTING_*_CODES) ;; *) echo "FAIL $item: the hosting domain holds only HOSTING_*_CODES items"; exit 1 ;; esac
  words=$(OMX_CONTRACT_PATH="$tmp/dest/contractdir" "$OMX_DOMAIN" hosting "" "$item") \
    || { echo "FAIL the loader does not open hosting $item"; exit 1; }
  got=$(printf '%s\n' "$words" | sed -n 's/^word=\([^ ]*\) .*/\1/p' | sort | tr '\n' ' ')
  want=$(printf '%s\n' $codes | sort | tr '\n' ' ')
  [ "$got" = "$want" ] || { echo "FAIL $item: the loader lists [$got], the domain declares [$want]"; exit 1; }
done < "$tmp/items"
OMX_CONTRACT_PATH="$tmp/dest/contractdir" "$OMX_DOMAIN" hosting "" HOSTING_IDLE_CODES hosting.idle.hold-refused \
  | grep -q 'description=the device could not be opened for writing' \
  || { echo "FAIL the loader does not serve hosting.idle.hold-refused's doc as its description"; exit 1; }

# one home: data/ declares no HOSTING_*_CODES item, every code carries its doc and its English text (never one for the
# other), and the items that name code keep their impl links as x-source
python3 - data "$D" <<'P' || exit 1
import glob, json, sys
bad = []
for f in [sys.argv[1] + "/hosting.json"] + sorted(glob.glob(sys.argv[1] + "/hosting/*.json")):
    for name, body in json.load(open(f)).items():
        if name.startswith("HOSTING_") and isinstance(body, dict) and body.get("kind") == "codes":
            bad.append(f"{f} declares {name}: its home is the hosting domain")
items = json.load(open(sys.argv[2]))["components"]["schemas"]
for name, it in items.items():
    for w in it["oneOf"]:
        if not w.get("description"): bad.append(f"{name}.{w['title']}: no doc (description)")
        if not w.get("x-text"): bad.append(f"{name}.{w['title']}: no English text (x-text)")
        if w.get("description") == w.get("x-text"): bad.append(f"{name}.{w['title']}: the doc is the English text")
        if w.get("x-name") != w["title"]: bad.append(f"{name}.{w['title']}: x-name {w.get('x-name')!r} is not its key")
    if not it.get("x-file"): bad.append(f"{name}: no x-file, the data path it rebuilds into")
for name in ("HOSTING_IDLE_CODES", "HOSTING_WINDOW_CODES"):
    if not items.get(name, {}).get("x-source", {}).get("impl"): bad.append(f"{name}: no x-source impl links")
if bad:
    sys.exit("FAIL the hosting domain is not the codes' one home:\n  " + "\n  ".join(bad[:8]))
P

# the gate: green on a clean tree, red on a missing file and on a code without its doc
fresh
$MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null || { echo "FAIL check-domain is red on a clean tree"; exit 1; }
fresh
rm "$tmp/t/$D"
if $MAKE --no-print-directory -C "$tmp/t" check-domain >/dev/null 2>&1; then echo "FAIL a missing domain file stays green"; exit 1; fi
edit() { # <expression over the loaded document `d` and the latency item's words `w`>
  python3 - "$tmp/t/$D" "$1" <<'P'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
w = d["components"]["schemas"]["HOSTING_LATENCY_CODES"]["oneOf"]
exec(sys.argv[2])
open(p, "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
P
}
fresh
edit 'del w[0]["description"]'
if out=$($MAKE --no-print-directory -C "$tmp/t" check-domain 2>&1); then echo "FAIL a code without its doc stays green"; exit 1; fi
printf '%s\n' "$out" | grep -q "hosting.latency.nonconforming: the word has no doc" || { echo "FAIL a code without its doc is refused without naming it: $out"; exit 1; }

# a second home is refused: an item copied back into data/ makes the read of the package and the domain red by name
fresh
python3 - "$tmp/t/data/hosting.json" "$tmp/t/$D" <<'P'
import json, sys
d = json.load(open(sys.argv[1]))
it = json.load(open(sys.argv[2]))["components"]["schemas"]["HOSTING_IDLE_CODES"]
d["HOSTING_IDLE_CODES"] = {"kind": "codes", "since": "2.20.0", "doc": it["description"],
                           "codes": {w["title"]: {"code": w["const"], "doc": w["description"], "text": {"en": w["x-text"]}} for w in it["oneOf"]}}
open(sys.argv[1], "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
P
mkdir -p "$tmp/dup"
sh "$INSTALL_CONTRACT_DIR" omx-clap "$(cat VERSION)" 3 "$tmp/t/data" "$tmp/dup" data >/dev/null
sh "$INSTALL_CONTRACT_DIR" --domain "$tmp/t/contract.d/hosting" "$tmp/dup" omx-clap >/dev/null
if out=$($tool validate --contract-dir "$tmp/dup" 2>&1); then echo "FAIL HOSTING_IDLE_CODES in data/ and in the domain validates"; exit 1; fi
printf '%s\n' "$out" | grep -q "contract.item.duplicate.*HOSTING_IDLE_CODES" || { echo "FAIL a second home is refused without naming it: $out"; exit 1; }

# a word added or removed under the same version is refused by name, an existing word keeps its x-code, a version going
# down is refused: omx-contract's `domain check`, held to the committed document (DOMAIN_BASE)
cp "$D" "$tmp/base.json"
refused() { # <label> <expected text>: check-domain fails against the committed document with that text
  if out=$($MAKE --no-print-directory -C "$tmp/t" check-domain DOMAIN_BASE="$tmp/base.json" 2>&1); then echo "FAIL $1: check-domain is green"; exit 1; fi
  printf '%s\n' "$out" | grep -q "$2" || { echo "FAIL $1: refused without naming it ($2): $out"; exit 1; }
}
ADD='w.append({"const": "hosting.latency.new", "title": "latencyNew", "description": "a new word", "x-code": len(w), "x-text": "A new word.", "x-name": "latencyNew"})'
fresh
edit "$ADD"
refused "a word added, the version unchanged" "word added while info.version stays"
fresh
edit 'w.pop()'
refused "a word removed, the version unchanged" "word removed while info.version stays"
fresh
edit 'w[0], w[1] = w[1], w[0]; w[0]["x-code"], w[1]["x-code"] = 0, 1'
refused "two words reordered" "the words were reordered"
fresh
edit 'd["info"]["version"] = "0.1.0"'
refused "a version going down" "is below"
# a word appended under a new version passes, and the earlier words keep their codes
fresh
edit "$ADD"'; d["info"]["version"] = "9.9.9"'
$MAKE --no-print-directory -C "$tmp/t" check-domain DOMAIN_BASE="$tmp/base.json" >/dev/null || { echo "FAIL a word appended under a new version is refused"; exit 1; }
# every item carries an x-since, never above the document's info.version: validate (omx-contract's rule domain-x-since) is red
since_red() { # <label> <sed script over the domain file>
  fresh
  sed -i "$2" "$tmp/t/$D"
  rm -rf "$tmp/only"; mkdir -p "$tmp/only"; cp -r "$tmp/t/contract.d/hosting" "$tmp/only/"
  if out=$($tool validate --contract-dir "$tmp/only" 2>&1); then echo "FAIL $1: validate is green"; exit 1; fi
  printf '%s\n' "$out" | grep -q "domain-x-since" || { echo "FAIL $1: validate is red without naming domain-x-since: $out"; exit 1; }
}
since_red "an item without x-since" '0,/"x-since": "[0-9.]*",/{/"x-since": "[0-9.]*",/d}'
since_red "an x-since above info.version" '0,/"x-since": "[0-9.]*"/s//"x-since": "99.0.0"/'
# every item of the document says the version that first carried it: 0.35.0, the first release that ships the domain, or
# a later one; never an earlier one (a version that shipped without the domain cannot have carried an item)
FIRST=0.35.0
python3 - "$D" "$FIRST" <<'P' || exit 1
import json, sys
items = json.load(open(sys.argv[1]))["components"]["schemas"]
key = lambda v: tuple(int(p) for p in v.split("."))
early = [n for n, b in items.items() if key(b.get("x-since", "0.0.0")) < key(sys.argv[2])]
if len(items) < 19 or early:
    sys.exit(f"FAIL {len(items)} items, and these carry no x-since or one before {sys.argv[2]}: {early}")
P
echo "ok   domain hosting: the one home of the HOSTING_*_CODES, installed and opened by the loader with every code and its doc; data/ declares none; a second home refused (contract.item.duplicate); check-domain red on a missing file and an undocumented code; a word added or removed, two words reordered or a version going down refused against the committed document; an appended word under a new version passes"
