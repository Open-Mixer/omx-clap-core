#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""F2, the code sheet's mapping to the standard units, held by two arms (the call-level test of the sorting row V23d).

    param-units-map-check.py <contract.d of this tree> <omx-contract.json>
    param-units-map-check.py --self-test <contract.d of this tree> <omx-contract.json>

The domain documents are contract.d/omx-param-contract/omx-param-contract.json, contract.d/omx-clap-scale/omx-clap-scale.json
and contract.d/clap/clap.json (CLAP's flag for the stepped scale); <omx-contract.json> is `omx-contract render --target json` of the contract directory (its items hold PARAM_UNITS and
PARAM_SCALES, the standard units and scales). The scale codes are held the same way: (a) the golden three, (c) each key a
word of PARAM_SCALES.

  (a) golden: the sheet holds the 29 tokens of omx-contract's sheet at 3.20.2 with their codes, and the four codes of
      260 to 263 (dB/oct, dB/s, dBTP, LU), and every token maps to a standard id;
  (c) every mapped id is a key of omx-contract's PARAM_UNITS, and no two codes map to one id. --self-test plants each
      failure (an id removed from a copy of PARAM_UNITS, two codes onto one id, a code moved) and each must be red.
"""
import copy
import json
import sys

GOLDEN_SCALES = {"linear": 0, "log": 1, "stepped": 2}
GOLDEN = {
    "none": 0, "s": 1, "ms": 2, "min": 3, "bar": 4, "beat": 5, "frame": 6, "m": 7, "cm": 8, "mm": 9, "km": 10, "inch": 11,
    "mile": 12, "db": 13, "pc": 14, "coef": 15, "hz": 16, "khz": 17, "mhz": 18, "bpm": 19, "oct": 20, "cent": 21,
    "semitone12TET": 22, "degree": 23, "midiNote": 24, "dbfs": 256, "dbu": 257, "ratio": 258, "lufs": 259,
    "dbPerOct": 260, "dbPerS": 261, "dbtp": 262, "lu": 263,
}


def check(domain, standard, old, scales, clap):
    bad = []
    items = domain["components"]["schemas"]
    sheet = items["OMX_PARAM_CONTRACT_UNITS"]["x-value"]
    ids = items["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]
    if sheet != GOLDEN:  # (a)
        bad.append("(a) the code sheet is not the golden 29 + 4: %s" % sorted(set(sheet.items()) ^ set(GOLDEN.items())))
    if list(ids) != list(sheet):
        bad.append("(a) a token has no standard id, or one too many: %s" % sorted(set(ids) ^ set(sheet)))
    units = set(standard["items"]["PARAM_UNITS"]["value"])  # (c)
    for t, i in ids.items():
        if i not in units:
            bad.append("(c) %s maps to %s, which omx-contract's PARAM_UNITS does not hold" % (t, i))
    seen = {}
    for t, i in ids.items():
        if i in seen:
            bad.append("(c) %s and %s map to one standard id, %s" % (seen[i], t, i))
        seen[i] = t
    sc = scales["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"]  # the scale codes, F2
    if sc != GOLDEN_SCALES:
        bad.append("(a) the scale codes are not the golden linear 0, log 1, stepped 2: %s" % sorted(set(sc.items()) ^ set(GOLDEN_SCALES.items())))
    for w in sc:
        if w not in standard["items"]["PARAM_SCALES"]["value"]:
            bad.append("(c) the scale %s is no word of omx-contract's PARAM_SCALES" % w)
    fl = clap["components"]["schemas"]["CLAP_PARAM_FLAG_SCALES"]["x-value"]  # the flags, F2
    if fl != {"CLAP_PARAM_IS_STEPPED": "stepped"}:
        bad.append("(a) the flag mapping is not the golden CLAP_PARAM_IS_STEPPED -> stepped: %s" % fl)
    for f, w in fl.items():
        if w not in standard["items"]["PARAM_SCALES"]["value"]:
            bad.append("(c) the flag %s maps to %s, no word of omx-contract's PARAM_SCALES" % (f, w))
    return bad


def main(argv):
    self_test = argv[:1] == ["--self-test"]
    argv = argv[1:] if self_test else argv
    if len(argv) != 2:
        sys.exit(__doc__)
    domain = json.load(open(argv[0] + "/omx-param-contract/omx-param-contract.json"))
    scales = json.load(open(argv[0] + "/omx-clap-scale/omx-clap-scale.json"))
    clap = json.load(open(argv[0] + "/clap/clap.json"))
    standard = json.load(open(argv[1]))
    old = None
    bad = check(domain, standard, old, scales, clap)
    if not self_test:
        for b in bad:
            print("param-units-map-check: " + b, file=sys.stderr)
        if bad:
            return 1
        print("param-units-map-check: %d unit codes, each mapped to a distinct standard unit, and %d scale codes, each a standard scale of omx-contract, and the CLAP flag for the stepped scale" % (len(domain["components"]["schemas"]["OMX_PARAM_CONTRACT_UNITS"]["x-value"]), len(scales["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"])))
        return 0
    if bad:
        print("FAIL self-test: the unsabotaged inputs are red: %s" % bad[:3])
        return 1
    failed = 0

    def must_be_red(what, d, s, o, arm, sc=None, cl=None):
        nonlocal failed
        b = check(d, s, o, sc if sc is not None else scales, cl if cl is not None else clap)
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
    sc2 = copy.deepcopy(scales)
    sc2["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"]["exp"] = 3
    must_be_red("a scale code that is no PARAM_SCALES word", domain, standard, old, "(c)", sc2)
    s3 = copy.deepcopy(standard)
    s3["items"]["PARAM_SCALES"]["value"].remove("log")
    must_be_red("a PARAM_SCALES without log", domain, s3, old, "(c)")
    sc3 = copy.deepcopy(scales)
    sc3["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"]["log"] = 5
    must_be_red("a scale code moved", domain, standard, old, "(a)", sc3)
    cl2 = copy.deepcopy(clap)
    cl2["components"]["schemas"]["CLAP_PARAM_FLAG_SCALES"]["x-value"]["CLAP_PARAM_IS_STEPPED"] = "step"
    must_be_red("a flag mapped to no standard scale", domain, standard, old, "(c)", None, cl2)
    d3 = copy.deepcopy(domain)
    d3["components"]["schemas"]["OMX_PARAM_CONTRACT_UNITS"]["x-value"]["dbu"] = 300
    must_be_red("a code moved", d3, standard, old, "(a)")
    d4 = copy.deepcopy(domain)
    del d4["components"]["schemas"]["OMX_PARAM_CONTRACT_UNIT_IDS"]["x-value"]["lu"]
    must_be_red("a token with no standard id", d4, standard, old, "(a)")
    return failed


sys.exit(main(sys.argv[1:]))
