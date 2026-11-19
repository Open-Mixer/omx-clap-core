#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# An item's x-since is the info.version of its domain document that first carried it (omx-contract's contract
# directory rule, omx-contract#127): never a release number of a package or of omx-contract, and never above the
# document's own info.version, which omx-contract's validate refuses (omx-contract#128). Every x-since in
# contract.d, at any depth, must be a x.y.z and at most the info.version of the document that holds it.
#
#   domain_x_since.py [<contract.d>]   red on an x-since above its document's info.version (default: this tree's)
#   domain_x_since.py --self-test      a 3.7.0 in a 1.0.0 document, a malformed x-since and a missing info.version,
#                                      each planted in a scratch copy, must be red; the tree's own must be green
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEMVER = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)$")


def ver(v):
    return tuple(int(x) for x in SEMVER.match(v).groups())


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "x-since":
                yield path or "/", v
            else:
                yield from walk(v, path + "/" + k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, path + "/" + str(i))


def check(contract_dir):
    fails, seen = [], 0
    for dirpath, _, names in sorted(os.walk(contract_dir)):
        for name in sorted(names):
            if not name.endswith(".json"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            if not isinstance(doc, dict) or "info" not in doc:
                continue
            own = (doc.get("info") or {}).get("version")
            if not isinstance(own, str) or not SEMVER.match(own):
                fails.append("%s: info.version %r is not x.y.z" % (path, own))
                continue
            for where, since in walk(doc):
                seen += 1
                if not isinstance(since, str) or not SEMVER.match(since):
                    fails.append("%s %s: x-since %r is not x.y.z" % (path, where, since))
                elif ver(since) > ver(own):
                    fails.append("%s %s: x-since %s is above the document's info.version %s" % (path, where, since, own))
    if seen == 0:
        fails.append("%s: no x-since found: the check reads nothing" % contract_dir)
    return fails


def self_test():
    failed = []
    if check(os.path.join(ROOT, "contract.d")):
        failed.append("the tree's own contract.d is not green")
    plants = {
        "an x-since above the document's version": lambda t: t.replace('"x-since": "1.0.0"', '"x-since": "3.7.0"', 1),
        "a malformed x-since": lambda t: t.replace('"x-since": "1.0.0"', '"x-since": "v1"', 1),
        "a document with no info.version": lambda t: t.replace('"version": "1.0.0"', '"vers": "1.0.0"', 1),
    }
    for label, plant in plants.items():
        with tempfile.TemporaryDirectory() as d:
            copy = os.path.join(d, "contract.d")
            shutil.copytree(os.path.join(ROOT, "contract.d"), copy)
            target = os.path.join(copy, "scan", "scan.json")
            with open(target, encoding="utf-8") as f:
                text = f.read()
            planted = plant(text)
            if planted == text:
                failed.append(label + ": the plant changed nothing")
                continue
            with open(target, "w", encoding="utf-8") as f:
                f.write(planted)
            if not check(copy):
                failed.append(label + ": not found")
    for label in failed:
        print("FAIL domain x-since self-test: " + label)
    if failed:
        return 1
    print("ok   domain x-since self-test: %d planted documents, every one found" % len(plants))
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "--self-test":
        return self_test()
    d = argv[1] if len(argv) == 2 else os.path.join(ROOT, "contract.d")
    found = check(d)
    for p in found:
        print("FAIL domain x-since: " + p)
    if found:
        return 1
    print("ok   domain x-since: every x-since is at most its document's info.version")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
