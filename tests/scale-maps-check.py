#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""F2 for scales, the mapping of this level's codes and flags to omx-contract's standard scales, held by two arms (the
call-level test of the sorting rows V21 and V27b).

    scale-maps-check.py <contract.d of this tree> <omx-contract.json>
    scale-maps-check.py --self-test <contract.d of this tree> <omx-contract.json>

The domain documents are contract.d/omx-clap-scale/omx-clap-scale.json (the scale codes) and contract.d/clap/clap.json
(CLAP's flag for the stepped scale); <omx-contract.json> is `omx-contract render --target json` of the contract directory
(its items hold PARAM_SCALES, the standard scales).

  (a) golden: the scale codes are linear 0, log 1, stepped 2, and the flag mapping is CLAP_PARAM_IS_STEPPED to stepped;
  (c) every mapped word is a word of PARAM_SCALES. --self-test plants each failure (a scale that is no standard word, a
      PARAM_SCALES without log, a code moved, a flag mapped to no standard scale) and each must be red.
"""
import copy
import json
import sys

GOLDEN_SCALES = {"linear": 0, "log": 1, "stepped": 2}
GOLDEN_FLAGS = {"CLAP_PARAM_IS_STEPPED": "stepped"}


def check(standard, scales, clap):
    bad = []
    sc = scales["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"]
    if sc != GOLDEN_SCALES:
        bad.append("(a) the scale codes are not the golden linear 0, log 1, stepped 2: %s" % sorted(set(sc.items()) ^ set(GOLDEN_SCALES.items())))
    for w in sc:
        if w not in standard["items"]["PARAM_SCALES"]["value"]:
            bad.append("(c) the scale %s is no word of omx-contract's PARAM_SCALES" % w)
    fl = clap["components"]["schemas"]["CLAP_PARAM_FLAG_SCALES"]["x-value"]
    if fl != GOLDEN_FLAGS:
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
    scales = json.load(open(argv[0] + "/omx-clap-scale/omx-clap-scale.json"))
    clap = json.load(open(argv[0] + "/clap/clap.json"))
    standard = json.load(open(argv[1]))
    bad = check(standard, scales, clap)
    if not self_test:
        for b in bad:
            print("scale-maps-check: " + b, file=sys.stderr)
        if bad:
            return 1
        print("scale-maps-check: %d scale codes, each a standard scale of omx-contract, and the CLAP flag for the stepped scale"
              % len(scales["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"]))
        return 0
    if bad:
        print("FAIL self-test: the unsabotaged inputs are red: %s" % bad[:3])
        return 1
    failed = 0

    def must_be_red(what, s, sc, cl, arm):
        nonlocal failed
        if any(x.startswith(arm) for x in check(s, sc, cl)):
            print("ok   self-test: %s is red (%s)" % (what, arm))
        else:
            print("FAIL self-test: %s was not caught by arm %s" % (what, arm))
            failed = 1

    sc2 = copy.deepcopy(scales)
    sc2["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"]["exp"] = 3
    must_be_red("a scale code that is no PARAM_SCALES word", standard, sc2, clap, "(c)")
    s3 = copy.deepcopy(standard)
    s3["items"]["PARAM_SCALES"]["value"].remove("log")
    must_be_red("a PARAM_SCALES without log", s3, scales, clap, "(c)")
    sc3 = copy.deepcopy(scales)
    sc3["components"]["schemas"]["OMX_CLAP_SCALE_CODES"]["x-value"]["log"] = 5
    must_be_red("a scale code moved", standard, sc3, clap, "(a)")
    cl2 = copy.deepcopy(clap)
    cl2["components"]["schemas"]["CLAP_PARAM_FLAG_SCALES"]["x-value"]["CLAP_PARAM_IS_STEPPED"] = "step"
    must_be_red("a flag mapped to no standard scale", standard, scales, cl2, "(c)")
    return failed


sys.exit(main(sys.argv[1:]))
