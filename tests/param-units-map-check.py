#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""F2 for units, the code sheet's mapping to the standard units, held by two arms (the call-level test of the sorting
row V23d).

    param-units-map-check.py <contract.d of this tree> <omx-contract.json>
    param-units-map-check.py --self-test <contract.d of this tree> <omx-contract.json>

The domain document is contract.d/omx-param-contract/omx-param-contract.json (items OMX_PARAM_CONTRACT_UNITS, the code
sheet, and OMX_PARAM_CONTRACT_UNIT_IDS, each token's standard unit id); <omx-contract.json> is `omx-contract render
--target json` of the contract directory (its items hold PARAM_UNITS, the standard units). The scale codes are held by
scale-maps-check.py.

  (a) golden: the sheet holds the 29 tokens of omx-contract's sheet at 3.20.2 with their codes, and the four codes of
      260 to 263 (dB/oct, dB/s, dBTP, LU), and every token maps to its golden standard id;
  (c) the mapped ids are exactly omx-contract's PARAM_UNITS_CLAP_ENCODED (the ids the extension encodes, param domain;
      a words item whose words copy PARAM_UNITS by x-from, each id its word's const; any other kind is refused), and every mapped id is a standard id of omx-contract's PARAM_UNITS, a word's const as released (dB, Hz, deg, dB-oct;
      never the lowercase key the word is filed under, which is this level's spelling), and no two codes map to one id;
  (r) the renders are omx-clap's (project omx-clap, guards OMX_CLAP_*), the ids item has its own x-file and renders
      src/omx_param_unit_ids.h (OMX_PARAM_UNIT_IDS(X), X(OMX_CLAP_UNIT_<TOKEN>, "<token>", "<id>")), and the committed
      header holds the item's rows in its order. --self-test plants each
      failure (an id removed from a copy of PARAM_UNITS, two codes onto one id, a code moved, a token with no id) and
      each must be red.
"""
import copy
import json
import os
import re
import shutil
import sys
import tempfile

GOLDEN = {
    "none": 0, "s": 1, "ms": 2, "min": 3, "bar": 4, "beat": 5, "frame": 6, "m": 7, "cm": 8, "mm": 9, "km": 10, "inch": 11,
    "mile": 12, "db": 13, "pc": 14, "coef": 15, "hz": 16, "khz": 17, "mhz": 18, "bpm": 19, "oct": 20, "cent": 21,
    "semitone12TET": 22, "degree": 23, "midiNote": 24, "dbfs": 256, "dbu": 257, "ratio": 258, "lufs": 259,
    "dbPerOct": 260, "dbPerS": 261, "dbtp": 262, "lu": 263,
}
# each token's standard id: the const of its PARAM_UNITS word (the coordinator's ruling on #158, Q-a)
GOLDEN_IDS = {
    "none": "none", "s": "s", "ms": "ms", "min": "min", "bar": "bar", "beat": "beat", "frame": "frames", "m": "m", "cm": "cm",
    "mm": "mm", "km": "km", "inch": "inch", "mile": "mile", "db": "dB", "pc": "percent", "coef": "coef", "hz": "Hz",
    "khz": "kHz", "mhz": "MHz", "bpm": "bpm", "oct": "oct", "cent": "cents", "semitone12TET": "st", "degree": "deg",
    "midiNote": "midiNote", "dbfs": "dBFS", "dbu": "dBu", "ratio": "ratio", "lufs": "LUFS", "dbPerOct": "dB-oct",
    "dbPerS": "dB-s", "dbtp": "dBTP", "lu": "LU",
}


def const_case(s):
    """omx-contract's constCase (render/vocabulary.mjs): dbPerOct -> DB_PER_OCT, the name of a code's define."""
    return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)).upper()


IDS_HEADER = "src/omx_param_unit_ids.h"
UNITS_HEADER = "src/omx_param_units.h"


def is_string_sheet(value):
    return isinstance(value, dict) and bool(value) and all(isinstance(v, str) for v in value.values())


def package_string_sheets(contract_d, data_dir):
    """Every sheet of strings the omx-clap package holds, by item name, sorted: the items of every domain under
    contract.d (x-kind sheet, x-value) and of every data file under data/ (kind sheet, value). The root entry of
    omx_param_unit_ids.h reads the package (scope package), so each one that reaches the render would join
    OMX_PARAM_UNIT_IDS(X)."""
    names = []
    for base, _, files in os.walk(contract_d):
        for f in files:
            if not f.endswith(".json"):
                continue
            try:
                doc = json.load(open(os.path.join(base, f)))
            except (OSError, ValueError):
                continue
            for n, i in ((doc.get("components") or {}).get("schemas") or {}).items() if isinstance(doc, dict) else []:
                # a domain sheet reaches the render only with an x-file (docs/render.md of omx-contract): one without is
                # read at run time only (clap's CLAP_PARAM_FLAG_SCALES), and joins no header
                if isinstance(i, dict) and i.get("x-kind") == "sheet" and "x-file" in i and is_string_sheet(i.get("x-value")):
                    names.append(n)
    for base, _, files in os.walk(data_dir):
        for f in files:
            if not f.endswith(".json"):
                continue
            try:
                doc = json.load(open(os.path.join(base, f)))
            except (OSError, ValueError):
                continue
            for n, i in doc.items() if isinstance(doc, dict) else []:
                if isinstance(i, dict) and i.get("kind") == "sheet" and is_string_sheet(i.get("value")):
                    names.append(n)
    return sorted(names)


def id_rows(text):
    """The rows of OMX_PARAM_UNIT_IDS(X) in a header text: [(define, token, id)] in their order."""
    return re.findall(r'X\((OMX_CLAP_UNIT_\w+), "([^"]*)", "([^"]*)"\)', text)


def check_render(domain, ids_header, package_strings, units_header):
    """(r) the renders are omx-clap's and all of them are the domain's ROOT x-render (no item carries one: a pass changes
    no format): every entry names project omx-clap and a guard of its own (OMX_CLAP_*, never omx-contract's
    OMX_PARAM_UNITS_H); the ids item has an x-file of its own and is the one sheet of strings of the domain (the root
    entry of omx_param_unit_ids.h reads the whole package, scope package, so a second sheet of strings would join its
    macro); one root entry renders omx_param_unit_ids.h with scope package and the strings section {prefix
    OMX_CLAP_UNIT_, table OMX_PARAM_UNIT_IDS}; and the committed header holds one row X(OMX_CLAP_UNIT_<TOKEN>,
    "<token>", "<id>") per token, in the sheet's order."""
    bad = []
    items = domain["components"]["schemas"]
    entries = list(domain.get("x-render", {}).get("c", []))
    ids_item = items["OMX_PARAM_CONTRACT_UNIT_IDS"]
    for name, item in items.items():
        if "x-render" in item:
            bad.append("(r) the item %s carries an x-render; a render is the domain root's x-render" % name)
    if package_strings != ["OMX_PARAM_CONTRACT_UNIT_IDS"]:
        bad.append("(r) the sheets of strings of the omx-clap package are %s, not OMX_PARAM_CONTRACT_UNIT_IDS alone: a second one joins OMX_PARAM_UNIT_IDS(X)" % package_strings)
    if units_header is None:
        bad.append("(r) %s is not committed" % UNITS_HEADER)
    elif "OMX_PARAM_UNIT_IDS" in units_header or re.search(r'X\(OMX_CLAP_UNIT_\w+, "', units_header):
        bad.append("(r) %s holds rows of the ids table; it renders the numbers of OMX_PARAM_CONTRACT_UNITS only" % UNITS_HEADER)
    for e in entries:
        if e.get("project") != "omx-clap":
            bad.append("(r) the render of %s names project %s, not omx-clap" % (e.get("header"), e.get("project")))
        if not str(e.get("guard", "")).startswith("OMX_CLAP_"):
            bad.append("(r) the render of %s has the guard %s, not one of its own (OMX_CLAP_*)" % (e.get("header"), e.get("guard")))
    if ids_item.get("x-file") in (None, domain.get("x-file"), items["OMX_PARAM_CONTRACT_UNITS"].get("x-file")):
        bad.append("(r) OMX_PARAM_CONTRACT_UNIT_IDS has no x-file of its own (%s)" % ids_item.get("x-file"))
    strings = [e for e in entries if e.get("header") == "omx_param_unit_ids.h" and "strings" in e]
    if len(strings) != 1 or strings[0].get("scope") != "package" or strings[0]["strings"].get("prefix") != "OMX_CLAP_UNIT_" or strings[0]["strings"].get("table") != "OMX_PARAM_UNIT_IDS":
        bad.append("(r) the root x-render has no omx_param_unit_ids.h entry with scope package and strings {prefix OMX_CLAP_UNIT_, table OMX_PARAM_UNIT_IDS}")
    want = [("OMX_CLAP_UNIT_" + const_case(t), t, i) for t, i in ids_item["x-value"].items()]
    if ids_header is None:
        bad.append("(r) %s is not committed" % IDS_HEADER)
    elif id_rows(ids_header) != want:
        bad.append("(r) %s does not hold the rows of the ids item in its order: %s" % (IDS_HEADER, sorted(set(id_rows(ids_header)) ^ set(want))[:4]))
    return bad


GROUP = "PARAM_UNITS_CLAP_ENCODED"


def group_ids(standard):
    """The ids of omx-contract's PARAM_UNITS_CLAP_ENCODED, a words item (the coordinator's ruling on #158, option A): its
    words copy PARAM_UNITS by x-from, keyed by title, each id the word's const (value.<title>.word). Returns (ids, why):
    ids None and why the refusal when the render holds no such item or one of another kind."""
    item = standard["items"].get(GROUP)
    if item is None:
        return None, "omx-contract's render holds no %s (the ids the extension encodes)" % GROUP
    if item.get("kind") != "words" or not isinstance(item.get("value"), dict):
        return None, "%s must be a words item (it renders as %s)" % (GROUP, item.get("kind"))
    return [w["word"] for w in item["value"].values()], None


def with_group(standard, ids):
    """A copy of `standard` whose PARAM_UNITS_CLAP_ENCODED is a words item holding `ids`, each word copied from
    PARAM_UNITS, as x-from copies it (an id PARAM_UNITS lacks is filed under itself), for the self test."""
    s = copy.deepcopy(standard)
    by_word = {w["word"]: (t, w) for t, w in standard["items"]["PARAM_UNITS"]["value"].items()}
    s["items"][GROUP] = {"kind": "words", "value": {by_word[i][0] if i in by_word else i: dict(by_word.get(i, (i, {}))[1], word=i) for i in ids}}
    return s


def check(domain, standard):
    bad = []
    items = domain["components"]["schemas"]
    sheet = items["OMX_PARAM_CONTRACT_UNITS"]["x-value"]
    ids = items["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]
    if sheet != GOLDEN:  # (a)
        bad.append("(a) the code sheet is not the golden 29 + 4: %s" % sorted(set(sheet.items()) ^ set(GOLDEN.items())))
    if list(ids) != list(sheet):
        bad.append("(a) a token has no standard id, or one too many: %s" % sorted(set(ids) ^ set(sheet)))
    if ids != GOLDEN_IDS:
        bad.append("(a) a token does not map to its golden standard id: %s" % sorted(set(ids.items()) ^ set(GOLDEN_IDS.items())))
    units = {w["word"] for w in standard["items"]["PARAM_UNITS"]["value"].values()}  # (c) the ids are the words' consts
    for t, i in ids.items():
        if i not in units:
            bad.append("(c) %s maps to %s, which omx-contract's PARAM_UNITS does not hold" % (t, i))
    group, why = group_ids(standard)  # (c) the served set, omx-contract's words item
    if group is None:
        bad.append("(c) " + why)
    else:
        for i in sorted(set(ids.values()) - set(group)):
            bad.append("(c) %s is mapped, and PARAM_UNITS_CLAP_ENCODED does not hold it" % i)
        for i in sorted(set(group) - set(ids.values())):
            bad.append("(c) PARAM_UNITS_CLAP_ENCODED holds %s, which no token maps to" % i)
    seen = {}
    for t, i in ids.items():
        if i in seen:
            bad.append("(c) %s and %s map to one standard id, %s" % (seen[i], t, i))
        seen[i] = t
    return bad


def main(argv):
    self_test = argv[:1] == ["--self-test"]
    argv = argv[1:] if self_test else argv
    if len(argv) != 2:
        sys.exit(__doc__)
    domain = json.load(open(argv[0] + "/omx-param-contract/omx-param-contract.json"))
    standard = json.load(open(argv[1]))
    root = os.path.join(argv[0], "..")
    at = os.path.join(root, IDS_HEADER)
    ids_header = open(at).read() if os.path.exists(at) else None
    at = os.path.join(root, UNITS_HEADER)
    units_header = open(at).read() if os.path.exists(at) else None
    package_strings = package_string_sheets(argv[0], os.path.join(root, "data"))
    bad = check(domain, standard) + check_render(domain, ids_header, package_strings, units_header)
    if not self_test:
        for b in bad:
            print("param-units-map-check: " + b, file=sys.stderr)
        if bad:
            return 1
        print("param-units-map-check: %d unit codes, each mapped to a distinct standard unit of omx-contract"
              % len(domain["components"]["schemas"]["OMX_PARAM_CONTRACT_UNITS"]["x-value"]))
        return 0
    if bad:
        print("FAIL self-test: the unsabotaged inputs are red: %s" % bad[:3])
        return 1
    failed = 0

    def must_be_red(what, d, s, arm):
        nonlocal failed
        if any(x.startswith(arm) for x in check(d, s)):
            print("ok   self-test: %s is red (%s)" % (what, arm))
        else:
            print("FAIL self-test: %s was not caught by arm %s" % (what, arm))
            failed = 1

    mapped = list(domain["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"].values())
    exact = with_group(standard, mapped)
    if check(domain, exact):
        print("FAIL self-test: PARAM_UNITS_CLAP_ENCODED holding exactly the mapped ids is red: %s" % check(domain, exact)[:2])
        failed = 1
    else:
        print("ok   self-test: PARAM_UNITS_CLAP_ENCODED holding exactly the mapped ids is green")
    must_be_red("a mapped id (dBu) missing from PARAM_UNITS_CLAP_ENCODED", domain, with_group(standard, [i for i in mapped if i != "dBu"]), "(c)")
    must_be_red("an id (us) in PARAM_UNITS_CLAP_ENCODED that no token maps to", domain, with_group(standard, mapped + ["us"]), "(c)")
    as_set = copy.deepcopy(standard)
    as_set["items"][GROUP] = {"kind": "set", "value": list(mapped)}
    if any("must be a words item" in x for x in check(domain, as_set)):
        print("ok   self-test: PARAM_UNITS_CLAP_ENCODED rendered as a set is refused by name ((c))")
    else:
        print("FAIL self-test: PARAM_UNITS_CLAP_ENCODED rendered as a set was not refused by name: %s" % check(domain, as_set)[:2])
        failed = 1
    s2 = copy.deepcopy(standard)
    del s2["items"]["PARAM_UNITS"]["value"]["dbu"]  # the word dBu, filed under the key dbu
    must_be_red("a PARAM_UNITS without dbu", domain, s2, "(c)")
    d2 = copy.deepcopy(domain)
    d2["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]["dbtp"] = "dBFS"
    must_be_red("two codes onto one id", d2, standard, "(c)")
    d3 = copy.deepcopy(domain)
    d3["components"]["schemas"]["OMX_PARAM_CONTRACT_UNITS"]["x-value"]["dbu"] = 300
    must_be_red("a code moved", d3, standard, "(a)")
    d4 = copy.deepcopy(domain)
    del d4["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]["lu"]
    must_be_red("a token with no standard id", d4, standard, "(a)")
    d5 = copy.deepcopy(domain)
    d5["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]["db"] = "db"
    must_be_red("a token mapped to a lowercase key, not the standard id", d5, standard, "(c)")
    d6 = copy.deepcopy(domain)
    v6 = d6["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]
    v6["cent"], v6["semitone12TET"] = v6["semitone12TET"], v6["cent"]
    if check(d6, standard) and all(x.startswith("(a)") for x in check(d6, standard)):
        print("ok   self-test: cent and semitone12TET with their ids swapped (both valid consts) is red ((a) only)")
    else:
        print("FAIL self-test: the cent/semitone12TET swap was not caught by (a) alone: %s" % check(d6, standard))
        failed = 1

    def must_be_red_render(what, d, h, strings=None, units=None):
        nonlocal failed
        if check_render(d, h, package_strings if strings is None else strings, units_header if units is None else units):
            print("ok   self-test: %s is red ((r))" % what)
        else:
            print("FAIL self-test: %s was not caught by arm (r)" % what)
            failed = 1

    r1 = copy.deepcopy(domain)
    r1["x-render"]["c"][0]["project"] = "omx-contract"
    must_be_red_render("the units header rendered as omx-contract's", r1, ids_header)
    r2 = copy.deepcopy(domain)
    r2["x-render"]["c"][0]["guard"] = "OMX_PARAM_UNITS_H"
    must_be_red_render("the units header under omx-contract's guard", r2, ids_header)
    must_be_red_render("an ids header whose dB-oct row says dbPerOct", domain, (ids_header or "").replace('"dbPerOct", "dB-oct"', '"dbPerOct", "dbPerOct"'))
    r3 = copy.deepcopy(domain)
    r3["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-file"] = domain.get("x-file")
    must_be_red_render("the ids item in the units sheet's x-file", r3, ids_header)
    r4 = copy.deepcopy(domain)
    moved = [e for e in r4["x-render"]["c"] if e.get("header") == "omx_param_unit_ids.h"]
    r4["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-render"] = {"c": moved}
    r4["x-render"]["c"] = [e for e in r4["x-render"]["c"] if e.get("header") != "omx_param_unit_ids.h"]
    must_be_red_render("the ids header rendered by an item-level x-render", r4, ids_header)
    work = tempfile.mkdtemp(prefix="param-units-map.")
    try:
        planted = os.path.join(work, "contract.d")
        shutil.copytree(argv[0], planted)
        with open(os.path.join(planted, "omx-clap", "planted-words.json"), "w") as f:
            json.dump({"components": {"schemas": {"OMX_CLAP_PLANTED_WORDS": {"x-kind": "sheet", "x-file": "planted-words.json", "x-value": {"db": "decibel"}}}}}, f)
        must_be_red_render("a second sheet of strings planted in the omx-clap package", domain, ids_header,
                           package_string_sheets(planted, os.path.join(root, "data")))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    must_be_red_render("the units header carrying the ids table", domain, ids_header, None,
                       (units_header or "") + "\n#define OMX_PARAM_UNIT_IDS(X) X(OMX_CLAP_UNIT_DB, \"db\", \"dB\")\n")
    return failed


sys.exit(main(sys.argv[1:]))
