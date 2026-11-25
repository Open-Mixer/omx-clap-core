#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# A data file's `requires` and a domain's `info.x-requires` are lists of package and domain names, no version floors
# (owner ruling 2026-11-24): omx-contract 3.22.0 refuses a floor map ({"omx-contract-schema": ">= 3.12.0"},
# {"host": ">= 1.0.0"}) by name, so a package that still installs one cannot be read by the contract it serves.
# Refused here, by file: a map, an empty list, a name that is no package or domain name, a list out of ascending order.
#
#   requires-names-check.py <tree>        0 clean, 1 a floor map or a bad list found
#   requires-names-check.py --self-test   each fault planted in a scratch copy is found; the clean copy passes
import glob
import json
import os
import re
import shutil
import sys
import tempfile

NAME = re.compile(r"^[a-z][a-z0-9-]*(/[a-z][a-z0-9-]*)*$")


def bad(v):
    if v is None:
        return None
    if isinstance(v, dict):
        return "is a map of version floors %s" % json.dumps(v)
    if not isinstance(v, list):
        return "%s is not a list of names" % json.dumps(v)
    if not v:
        return "is an empty list"
    for i, k in enumerate(v):
        if not isinstance(k, str) or not NAME.match(k):
            return "names %s, which is no package or domain name" % json.dumps(k)
        if i and not v[i - 1] < k:
            return "is not in ascending order, each name once"
    return None


def findings(root):
    out = []
    for path in sorted(glob.glob(os.path.join(root, "data", "**", "*.json"), recursive=True)):
        why = bad(json.load(open(path)).get("requires"))
        if why:
            out.append("%s: requires %s" % (os.path.relpath(path, root), why))
    for path in sorted(glob.glob(os.path.join(root, "contract.d", "*", "*.json"))):
        doc = json.load(open(path))
        why = bad((doc.get("info") or {}).get("x-requires"))
        if why:
            out.append("%s: info.x-requires %s" % (os.path.relpath(path, root), why))
    return out


def self_test(root):
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "clean")
        os.makedirs(base)
        for d in ("data", "contract.d"):
            shutil.copytree(os.path.join(root, d), os.path.join(base, d))
        clean = findings(base)
        print("%s  the clean copy passes" % ("ok  " if not clean else "FAIL"))
        ok &= not clean
        data = sorted(glob.glob(os.path.join(base, "data", "**", "*.json"), recursive=True))[0]
        dom = sorted(glob.glob(os.path.join(base, "contract.d", "*", "*.json")))[0]
        arms = [
            ("a data file's floor map", data, lambda d: d.__setitem__("requires", {"omx-contract-schema": ">= 3.12.0"})),
            ("an empty requires", data, lambda d: d.__setitem__("requires", [])),
            ("a domain's floor map", dom, lambda d: d["info"].__setitem__("x-requires", {"host": ">= 1.0.0"})),
            ("a list out of order", dom, lambda d: d["info"].__setitem__("x-requires", ["omx-clap", "host"])),
            ("a version as a name", dom, lambda d: d["info"].__setitem__("x-requires", [">= 1.0.0"])),
        ]
        for name, path, plant in arms:
            keep = open(path).read()
            doc = json.loads(keep)
            plant(doc)
            open(path, "w").write(json.dumps(doc))
            found = findings(base)
            open(path, "w").write(keep)
            print("%s  sabotage: %s is refused" % ("ok  " if found else "FAIL", name))
            ok &= bool(found)
    return ok


def main(argv):
    if argv[:1] == ["--self-test"]:
        return 0 if self_test(argv[1] if len(argv) > 1 else ".") else 1
    root = argv[0] if argv else "."
    out = findings(root)
    for line in out:
        print("requires-names-check: %s" % line)
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
