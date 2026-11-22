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
  (c) every mapped id is a standard id of omx-contract's PARAM_UNITS, a word's const as released (dB, Hz, deg, dB-oct;
      never the lowercase key the word is filed under, which is this level's spelling), and no two codes map to one id. --self-test plants each
      failure (an id removed from a copy of PARAM_UNITS, two codes onto one id, a code moved, a token with no id) and
      each must be red.
"""
import copy
import json
import sys

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
    bad = check(domain, standard)
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
    return failed


sys.exit(main(sys.argv[1:]))
