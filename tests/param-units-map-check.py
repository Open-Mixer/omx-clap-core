#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""F2, the code sheet's mapping to the standard units, held by three arms (the call-level test of the sorting row V23d).

    param-units-map-check.py <omx-param-contract.json> <omx-contract.json> [<omx-contract's data/param-contract.json>]
    param-units-map-check.py --self-test <omx-param-contract.json> <omx-contract.json> [<param-contract.json>]

The domain document is contract.d/omx-param-contract/omx-param-contract.json; <omx-contract.json> is
`omx-contract render --target json` of the contract directory (its items hold PARAM_UNITS, the standard units).

  (a) golden: the sheet holds the 29 tokens of omx-contract's sheet at 3.20.2 with their codes, and the four codes of
      260 to 263 (dB/oct, dB/s, dBTP, LU), and every token maps to a standard id;
  (b) while omx-contract still holds its own sheet (the optional third file), the 29 tokens and codes are equal to it;
  (c) every mapped id is a key of omx-contract's PARAM_UNITS, and no two codes map to one id. --self-test plants each
      failure (an id removed from a copy of PARAM_UNITS, two codes onto one id, a code moved) and each must be red.
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


def check(domain, standard, old):
    bad = []
    items = domain["components"]["schemas"]
    sheet = items["OMX_PARAM_CONTRACT_UNITS"]["x-value"]
    ids = items["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]
    if sheet != GOLDEN:  # (a)
        bad.append("(a) the code sheet is not the golden 29 + 4: %s" % sorted(set(sheet.items()) ^ set(GOLDEN.items())))
    if list(ids) != list(sheet):
        bad.append("(a) a token has no standard id, or one too many: %s" % sorted(set(ids) ^ set(sheet)))
    if old is not None:  # (b)
        o = old["OMX_PARAM_CONTRACT_UNITS"]["value"]
        for t, c in o.items():
            if sheet.get(t) != c:
                bad.append("(b) %s is %s here and %s in omx-contract's sheet" % (t, sheet.get(t), c))
    units = set(standard["items"]["PARAM_UNITS"]["value"])  # (c)
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
    if len(argv) not in (2, 3):
        sys.exit(__doc__)
    domain = json.load(open(argv[0]))
    standard = json.load(open(argv[1]))
    old = json.load(open(argv[2])) if len(argv) == 3 else None
    bad = check(domain, standard, old)
    if not self_test:
        for b in bad:
            print("param-units-map-check: " + b, file=sys.stderr)
        if bad:
            return 1
        print("param-units-map-check: %d codes, each mapped to a distinct standard unit of omx-contract" % len(domain["components"]["schemas"]["OMX_PARAM_CONTRACT_UNITS"]["x-value"]))
        return 0
    if bad:
        print("FAIL self-test: the unsabotaged inputs are red: %s" % bad[:3])
        return 1
    failed = 0

    def must_be_red(what, d, s, o, arm):
        nonlocal failed
        b = check(d, s, o)
        if any(x.startswith(arm) for x in b):
            print("ok   self-test: %s is red (%s)" % (what, arm))
        else:
            print("FAIL self-test: %s was not caught by arm %s" % (what, arm))
            failed = 1

    s2 = copy.deepcopy(standard)
    del s2["items"]["PARAM_UNITS"]["value"]["dbu"]
    must_be_red("a PARAM_UNITS without dbu", domain, s2, old, "(c)")
    d2 = copy.deepcopy(domain)
    d2["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]["dbtp"] = "dbfs"
    must_be_red("two codes onto one id", d2, standard, old, "(c)")
    d3 = copy.deepcopy(domain)
    d3["components"]["schemas"]["OMX_PARAM_CONTRACT_UNITS"]["x-value"]["dbu"] = 300
    must_be_red("a code moved", d3, standard, old, "(a)")
    d4 = copy.deepcopy(domain)
    del d4["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]["lu"]
    must_be_red("a token with no standard id", d4, standard, old, "(a)")
    return failed


sys.exit(main(sys.argv[1:]))
