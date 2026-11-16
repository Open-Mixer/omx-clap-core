#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# OMX_CLAP_PANEL_FAMILIES (src/omx_clap_ext.h) is a hand-written append-only table, and the panel families are
# omx-contract's (data/panel.json, PANEL_FAMILIES): the words and their order are the contract, a word's code is its place.
# This table must EQUAL the contract's, word and code, in order: a family the contract has and this table lacks is a plugin
# whose panel description a host here cannot name.
#
#   python3 tests/panel_families_match_contract.py <contract dir>   (a checkout or the installed one: <dir>/data/panel.json)
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def table():
    text = open(os.path.join(ROOT, "src", "omx_clap_ext.h"), encoding="utf-8").read()
    body = re.search(r"#define\s+OMX_CLAP_PANEL_FAMILIES\(X\)((?:[^\n]*\\\n)*[^\n]*)", text).group(1)
    return [(int(c), w) for c, w in re.findall(r'X\(\s*(\d+)\s*,\s*"([^"]+)"', body)]


def contract(directory):
    words = json.load(open(os.path.join(directory, "data", "panel.json"), encoding="utf-8"))["PANEL_FAMILIES"]["words"]
    return list(enumerate(words))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: panel_families_match_contract.py <contract dir>")
    ours, theirs = table(), contract(sys.argv[1])
    if ours != theirs:
        print("panel families differ from omx-contract's PANEL_FAMILIES (code, word):")
        print("  omx_clap_ext.h:", ours)
        print("  omx-contract:  ", theirs)
        missing = [r for r in theirs if r not in ours]
        extra = [r for r in ours if r not in theirs]
        print("  contract has, this table lacks:", missing)
        print("  this table has, contract lacks:", extra)
        return 1
    print("panel families match omx-contract: %d rows" % len(ours))
    return 0


sys.exit(main())
