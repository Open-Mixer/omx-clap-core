#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# No hand-kept version floor in this tree (owner ruling 2026-11-24). Each level builds and
# installs against the lower level's published packages and nothing else; a relation a package needs is generated
# (sonames, `= %{version}-%{release}`, `= ${binary:Version}`), never typed. Refused, by file and line:
#   - packaging/deps.txt (the floors file);
#   - a `>= X` on a requirement of a packaging/*.spec (above %changelog), and a `(>= X)` in debian/control;
#   - a version in a *.pc.in Requires line;
#   - a data file's `requires`, or a domain's `info.x-requires`, that is not a list of package/domain names: a floor map
#     (`{"omx-contract-schema": ">= 3.12.0"}`) is refused by name, and so is the `omx-contract-schema` entry.
# Breaks/Replaces/Obsoletes of a renamed package (packaging/renamed.txt) are an upgrade path, no floor, and are not read.
# THIRD-PARTY floors stay (the ruling covers our own levels): the CLAP headers (clap-devel, clap-headers 1.2.10), nodejs and
# debhelper-compat keep theirs; every other relation on a number is refused (>=, > or = in the spec, >=, >> or = in
# debian/control), and so is one on our own packages in a workflow or the Makefile.
#
#   no_floors_check.py <tree>       0 clean, 1 a floor found
#   no_floors_check.py --self-test  each kind planted in a scratch copy is found; the clean copy passes
import glob
import json
import os
import re
import shutil
import sys
import tempfile

NAME = re.compile(r"^[a-z][a-z0-9-]*(/[a-z][a-z0-9-]*)*$")
# third-party packages whose floor stays: the CLAP headers and node
THIRD_PARTY = ("clap-devel", "clap-headers", "nodejs", "debhelper-compat")
# a version relation on a number: >=, >, = (rpm) and >=, >>, = (deb); `= %{version}-%{release}` and `= ${binary:Version}`
# are generated, not numbers, and stay
SPEC_FLOOR = re.compile(r"([A-Za-z0-9_.+()-]+)\s*(?:>=|>|=)\s*[0-9]")
CTL_FLOOR = re.compile(r"([a-z0-9.+-]+)\s*\((?:>=|>>|=)\s*[0-9]")
# our own packages by name, wherever a workflow or the Makefile spells a relation on them (a dnf/apt/pkg-config line)
OWN = re.compile(r"(?<![A-Za-z0-9_.+-])((?:lib)?(?:omx|plugin-hostd|plugin-db|python3-plugin-hostd)[a-z0-9-]*)\s*(?:>=|>|=)\s*[0-9]")


def own(names):
    return [n for n in names if n not in THIRD_PARTY and not n.startswith("nodejs")]


def spec_floors(root):
    out = []
    for path in sorted(glob.glob(os.path.join(root, "packaging", "*.spec"))):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if line.startswith("%changelog"):
                    break
                if re.match(r"^(Build)?(Requires|Recommends|Suggests)(\([^)]*\))?:", line) and own(SPEC_FLOOR.findall(line)):
                    out.append("%s:%d: a version floor: %s" % (os.path.relpath(path, root), n, line.strip()))
    return out


def control_floors(root):
    out = []
    path = os.path.join(root, "debian", "control")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if not line.startswith("#") and own(CTL_FLOOR.findall(line)):
                    out.append("debian/control:%d: a version floor: %s" % (n, line.strip()[:160]))
    return out


def script_floors(root):
    """a relation on a number on one of our packages in a workflow or the Makefile (an install or pkg-config line)"""
    out = []
    paths = sorted(glob.glob(os.path.join(root, ".github", "workflows", "*.yml"))) + [os.path.join(root, "Makefile")]
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if line.lstrip().startswith("#"):
                    continue
                m = OWN.search(line)
                if m:
                    out.append("%s:%d: a version floor on %s: %s" % (os.path.relpath(path, root), n, m.group(1), line.strip()[:160]))
    return out


def pc_floors(root):
    out = []
    for path in sorted(glob.glob(os.path.join(root, "*.pc.in"))):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if line.startswith("Requires") and re.search(r"[<>=]", line.split(":", 1)[-1]):
                    out.append("%s:%d: a version in a pkg-config requirement: %s" % (os.path.relpath(path, root), n, line.strip()))
    return out


def names_problem(value, key):
    if not isinstance(value, list):
        return "%s is not a list of names (a floor map is refused: no floors)" % key
    for v in value:
        if not isinstance(v, str) or not NAME.match(v):
            return "%s holds %s, which is no package or domain name" % (key, json.dumps(v))
        if v == "omx-contract-schema":
            return "%s names omx-contract-schema: the installed schema reads the file, no schema floor" % key
    if value != sorted(set(value)):
        return "%s is not sorted and unique" % key
    return None


def data_floors(root):
    out = []
    files = sorted(glob.glob(os.path.join(root, "data", "*.json")) + glob.glob(os.path.join(root, "data", "*", "*.json"))
                   + glob.glob(os.path.join(root, "fuzz", "corpus", "preset", "data-*")))
    for path in files:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        if "requires" in doc:
            # a file that names no package but omx-contract-schema states no requires at all (absent, never [])
            p = names_problem(doc["requires"], "requires") or ("requires is [] (a file that names nothing states no requires)" if doc["requires"] == [] else None)
            if p:
                out.append("%s: %s" % (os.path.relpath(path, root), p))
    for path in sorted(glob.glob(os.path.join(root, "contract.d", "*", "*.json"))):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        info = doc.get("info", {}) if isinstance(doc, dict) else {}
        if "x-requires" in info:
            p = names_problem(info["x-requires"], "info.x-requires") or ("info.x-requires is [] (a domain that names nothing states no x-requires)" if info["x-requires"] == [] else None)
            if p:
                out.append("%s: %s" % (os.path.relpath(path, root), p))
    return out


def check(root):
    out = []
    if os.path.exists(os.path.join(root, "packaging", "deps.txt")):
        out.append("packaging/deps.txt: the hand-kept floors file is back")
    return out + spec_floors(root) + control_floors(root) + script_floors(root) + pc_floors(root) + data_floors(root)


def self_test():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    failed = 0

    def copy(tmp):
        tree = os.path.join(tmp, "tree")
        for sub in ("packaging", "debian", "data", "contract.d", os.path.join("fuzz", "corpus", "preset")):
            shutil.copytree(os.path.join(here, sub), os.path.join(tree, sub))
        for pc in glob.glob(os.path.join(here, "*.pc.in")) + [os.path.join(here, "Makefile")]:
            shutil.copy(pc, tree)
        shutil.copytree(os.path.join(here, ".github", "workflows"), os.path.join(tree, ".github", "workflows"))
        return tree

    def edit(path, old, new):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if old not in text:
            raise SystemExit("FAIL the arm no longer applies: %s has no %r" % (path, old))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))

    arms = [
        ("deps.txt back", lambda t: open(os.path.join(t, "packaging", "deps.txt"), "w").write("omx-dsp-devel libomxdsp-dev 0.34.0\n"), "packaging/deps.txt"),
        ("a spec floor", lambda t: edit(glob.glob(os.path.join(t, "packaging", "*.spec"))[0], "BuildRequires: omx-dsp-devel\n", "BuildRequires: omx-dsp-devel >= 0.34.0\n"), "a version floor"),
        ("a control floor", lambda t: edit(os.path.join(t, "debian", "control"), "libomxdsp-dev,", "libomxdsp-dev (>= 0.34.0~),"), "debian/control"),
        ("a third-party floor is no finding, an own one is", lambda t: edit(glob.glob(os.path.join(t, "packaging", "*.spec"))[0], "BuildRequires: plugin-db-devel\n", "BuildRequires: plugin-db-devel >= 0.5.0\n"), "plugin-db-devel >= 0.5.0"),
        ("a spec > floor", lambda t: edit(glob.glob(os.path.join(t, "packaging", "*.spec"))[0], "BuildRequires: omx-dsp-devel\n", "BuildRequires: omx-dsp-devel > 0.33\n"), "omx-dsp-devel > 0.33"),
        ("a spec = pin", lambda t: edit(glob.glob(os.path.join(t, "packaging", "*.spec"))[0], "BuildRequires: omx-dsp-devel\n", "BuildRequires: omx-dsp-devel = 0.34.0\n"), "omx-dsp-devel = 0.34.0"),
        ("a control = pin", lambda t: edit(os.path.join(t, "debian", "control"), "libomxdsp-dev,", "libomxdsp-dev (= 0.34.0~),"), "debian/control"),
        ("a workflow floor", lambda t: edit(os.path.join(t, ".github", "workflows", "ci.yml"), "plugin-hostd-protocol-contract omx-contract", "plugin-hostd-protocol-contract 'omx-contract >= 3.22.0'"), "ci.yml"),
        ("a Makefile floor", lambda t: open(os.path.join(t, "Makefile"), "a").write("\nOMXDSP_CFLAGS := $(shell pkg-config --cflags 'omxdsp >= 0.34.0')\n"), "Makefile"),
        ("an empty x-requires", lambda t: edit(os.path.join(t, "contract.d", "omx-clap", "omx-clap.json"), '"x-requires": [\n      "host"\n    ]', '"x-requires": []'), "info.x-requires is []"),
        ("an unsorted requires", lambda t: edit(os.path.join(t, "contract.d", "omx-clap", "omx-clap.json"), '"x-requires": [\n      "host"\n    ]', '"x-requires": ["omx-clap", "host"]'), "not sorted and unique"),
        ("a repeated requires", lambda t: edit(os.path.join(t, "contract.d", "omx-clap", "omx-clap.json"), '"x-requires": [\n      "host"\n    ]', '"x-requires": ["host", "host"]'), "not sorted and unique"),
        ("a requires that is no name", lambda t: edit(os.path.join(t, "contract.d", "omx-clap", "omx-clap.json"), '"x-requires": [\n      "host"\n    ]', '"x-requires": ["Host Words"]'), "no package or domain name"),
        ("a .pc floor", lambda t: edit(os.path.join(t, "omx-clap.pc.in"), "omx-contract, ", "omx-contract >= 3.22.0, "), "pkg-config"),
        ("a data floor map", lambda t: edit(os.path.join(t, "data", "hosting.json"), "{\n", '{\n  "requires": {\n    "omx-contract-schema": ">= 3.12.0"\n  },\n'), "floor map"),
        ("a schema name", lambda t: edit(os.path.join(t, "data", "hosting.json"), "{\n", '{\n  "requires": ["omx-contract-schema"],\n'), "omx-contract-schema"),
        ("an empty requires", lambda t: edit(os.path.join(t, "data", "hosting.json"), "{\n", '{\n  "requires": [],\n'), "requires is []"),
        ("an x-requires floor", lambda t: edit(os.path.join(t, "contract.d", "omx-clap", "omx-clap.json"), '"x-requires": [\n      "host"\n    ]', '"x-requires": {\n      "host": ">= 1.0.0"\n    }'), "info.x-requires"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        found = check(copy(tmp))
        if found:
            print("FAIL the control: the clean copy is refused: " + "; ".join(found))
            return 1
        print("ok   the clean copy passes")
    for label, plant, want in arms:
        with tempfile.TemporaryDirectory() as tmp:
            tree = copy(tmp)
            plant(tree)
            found = check(tree)
            if any(want in f for f in found):
                print("ok   %s is refused: %s" % (label, found[0]))
            else:
                print("FAIL %s is not refused (%s)" % (label, found))
                failed = 1
    return failed


def main():
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    if len(sys.argv) != 2:
        sys.exit("usage: no_floors_check.py <tree> | --self-test")
    found = check(sys.argv[1])
    for line in found:
        print("FAIL " + line)
    if found:
        sys.exit(1)
    print("ok   no hand-kept version floor: no deps.txt, no relation on a number in the spec, debian/control, .pc templates, workflows or Makefile (third-party CLAP, node and debhelper aside), requires are names")


if __name__ == "__main__":
    main()
