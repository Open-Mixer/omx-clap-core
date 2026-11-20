#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas
#
# omx-clap carries no backward-compatibility machinery: the library accepts its current ABI only, there is no
# recorded-baseline ABI gate, no package Breaks/Replaces/Conflicts lists, no ignored release input, and the meters
# declaration is ours alone. Each check below fails while the old mechanism is in the tree.
#
#   no_backcompat.py <tree>       0 when none of it is left
#   no_backcompat.py --self-test  each old thing planted in a scratch copy of the tree: every one is found
import os
import re
import shutil
import sys
import tempfile

SCAN_DIRS = ["src", "tools", "tests", "docs", "doc", "lv2", "bench"]
SCAN_FILES = ["README.md", "BUILDING.md", "Makefile"]
SELF = "tests/no_backcompat.py"
ROOT = ""


def text(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def walk(root):
    for d in SCAN_DIRS:
        for dp, _, names in os.walk(os.path.join(root, d)):
            for n in names:
                yield os.path.relpath(os.path.join(dp, n), root)
    for n in SCAN_FILES:
        if os.path.exists(os.path.join(root, n)):
            yield n


def workflows(root):
    d = os.path.join(root, ".github", "workflows")
    return [".github/workflows/" + n for n in sorted(os.listdir(d))] if os.path.isdir(d) else []


def grep(root, files, pat, where):
    rx = re.compile(pat)
    out = []
    for rel in files:
        if rel == SELF:
            continue
        for n, line in enumerate(text(root, rel).splitlines(), 1):
            if rx.search(line):
                out.append("%s: %s:%d: %s" % (where, rel, n, line.strip()[:100]))
    return out


def check(root):
    bad = []
    files = list(walk(root))
    wf = workflows(root)
    # 1: only the current ABI is accepted
    bad += grep(root, files, r"ABI_OLDEST|_default_sized", "row 1 an old ABI range or a sized default")
    # 2: no recorded-baseline ABI gate
    if os.path.isdir(os.path.join(root, "abi")):
        bad.append("row 2: abi/ baselines are still there")
    for n in ("abi-check.sh", "abi-check-sabotage.sh", "abi-format-test.sh", "abi-layout.sh"):
        if os.path.exists(os.path.join(root, "tests", n)):
            bad.append("row 2: tests/%s is still there" % n)
    if os.path.exists(os.path.join(root, ".github/workflows/abi.yml")):
        bad.append("row 2: .github/workflows/abi.yml is still there")
    bad += grep(root, ["Makefile"], r"abi-(stage|baseline|check|sabotage|format|layout)|^ABI_|abi/", "row 2 Makefile ABI gate")
    bad += grep(root, wf, r"abi\.yml|abi-check|test-abi-|\.so\.1\.abi|^  abi:|needs:.*\babi\b", "row 2 workflow ABI gate")
    bad += grep(root, ["packaging/omx-clap-host.spec", "debian/libomx-clap-dev.install"], r"\.abi\b", "row 2 installed baseline")
    # 7: the meters declaration is ours alone
    bad += grep(root, ["src/clap_meters.h"], r"__has_include|OMX_CLAP_METERS_FROM_SDK", "row 7 either/or SDK branch")
    # 8: no Breaks/Replaces/Conflicts
    bad += grep(root, ["debian/control"], r"^(Breaks|Replaces):", "row 8 debian Breaks/Replaces")
    bad += grep(root, ["packaging/omx-clap-host.spec"], r"^Conflicts:", "row 8 spec Conflicts")
    bad += grep(root, wf, r"\^ (Breaks|Replaces):|^\s*moved:", "row 8 CI grep or langpacks moved")
    # 9: the xrun sentence has no older-host case
    bad += grep(root, ["doc/reference.md"], r"older omx-clap-host", "row 9 older host")
    # 10: no ignored input
    bad += grep(root, wf, r"staged-deps", "row 10 staged-deps")
    return bad


def self_test():
    cases = [
        ("src/clap_host.h", "#define OMX_CLAP_CORE_ABI_OLDEST 18u\n"),
        ("src/clap_host.c", "void omx_clap_host_config_default_sized(void);\n"),
        ("abi/libomx-clap.so.1.abi", "x\n"),
        ("tests/abi-check.sh", "x\n"),
        (".github/workflows/abi.yml", "x\n"),
        ("Makefile", "abi-check: abi-stage\n"),
        (".github/workflows/ci.yml", "    needs: [abi]\n"),
        ("packaging/omx-clap-host.spec", "%{_datadir}/omx-clap/libomx-clap.so.*.abi\n"),
        ("src/clap_meters.h", "#if __has_include(<clap/ext/draft/meters.h>)\n"),
        ("debian/control", "Breaks: foo (<< 1~)\n"),
        ("packaging/omx-clap-host.spec", "Conflicts: foo < 1\n"),
        (".github/workflows/ci.yml", "          moved: ca:0.32.1\n"),
        (".github/workflows/ci.yml", "dpkg -I x | grep -E '^ Breaks: foo'\n"),
        ("doc/reference.md", "such as an older omx-clap-host\n"),
        (".github/workflows/release.yml", "      staged-deps:\n"),
    ]
    start = check(ROOT)
    if start:
        print("FAIL self-test: the tree is not clean to start with (%d findings)" % len(start))
        return 1
    failed = 0
    for rel, plant in cases:
        with tempfile.TemporaryDirectory() as tmp:
            scratch = os.path.join(tmp, "t")
            shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(".git", "build", "node_modules"))
            path = os.path.join(scratch, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(plant)
            if not check(scratch):
                print("FAIL self-test: %s planted in %s and not found" % (plant.strip(), rel))
                failed += 1
    if failed:
        return 1
    print("ok   no_backcompat self-test: each of %d old things planted is found" % len(cases))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        sys.exit(self_test())
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    ROOT = sys.argv[1]
    problems = check(ROOT)
    for p in problems:
        print("FAIL " + p)
    if problems:
        sys.exit(1)
    print("ok   no backward-compatibility machinery is left")
