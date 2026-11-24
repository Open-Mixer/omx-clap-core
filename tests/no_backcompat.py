#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas
#
# omx-clap carries no backward-compatibility machinery: the library accepts its current ABI only, there is no
# recorded-baseline ABI gate, no package Breaks/Replaces/Conflicts lists, no ignored release input, and the meters
# declaration is ours alone. Each check below fails while the old mechanism is in the tree. The one package relation
# allowed is a rename's, exactly as packaging/renamed.txt declares it: the new RPM package obsoletes the old name and
# the new DEB package Breaks and Replaces it, below the release that renamed it, and nothing provides an old name.
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


def renamed(root):
    rows = []
    for line in text(root, "packaging/renamed.txt").splitlines():
        f = line.split("#", 1)[0].split()
        if f:
            rows.append(f)
    return rows


def stanzas(body, start):
    # {package: [lines]} of a spec (%package -n <name>) or debian/control (Package: <name>)
    out, cur = {}, None
    for line in body.splitlines():
        m = re.match(start, line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return out


def relations(root):
    """row 8: the spec and debian/control carry a rename's relations exactly as packaging/renamed.txt states them"""
    bad = []
    rows = renamed(root)
    spec = text(root, "packaging/omx-clap-host.spec")
    control = text(root, "debian/control")
    want_rpm, want_deb = set(), set()
    for f in rows:
        if len(f) != 5:
            bad.append("row 8 packaging/renamed.txt: %s is not <old rpm> <new rpm> <old deb> <new deb> <since>" % " ".join(f))
            continue
        old_rpm, new_rpm, old_deb, new_deb, since = f
        want_rpm.add((new_rpm, "Obsoletes: %s < %s" % (old_rpm, since)))
        want_deb.add((new_deb, "Breaks: %s (<< %s~)" % (old_deb, since)))
        want_deb.add((new_deb, "Replaces: %s (<< %s~)" % (old_deb, since)))
        if re.search(r"^(%%package -n|Name:)\s*%s\s*$" % re.escape(old_rpm), spec, re.M):
            bad.append("row 8 spec: %s is renamed and still built" % old_rpm)
        if re.search(r"^Package:\s*%s\s*$" % re.escape(old_deb), control, re.M):
            bad.append("row 8 debian/control: %s is renamed and still built" % old_deb)
        if re.search(r"^Provides:.*\b%s\b" % re.escape(old_rpm), spec, re.M):
            bad.append("row 8 spec: Provides %s, an old name" % old_rpm)
        if re.search(r"^Provides:.*\b%s\b" % re.escape(old_deb), control, re.M):
            bad.append("row 8 debian/control: Provides %s, an old name" % old_deb)
    have_rpm = set()
    for pkg, lines in stanzas(spec, r"^%package\s+(?:-n\s+)?(\S+)").items():
        for line in lines:
            if re.match(r"^(Obsoletes|Conflicts):", line):
                have_rpm.add((pkg, " ".join(line.split())))
    have_deb = set()
    for pkg, lines in stanzas(control, r"^Package:\s*(\S+)").items():
        for line in lines:
            if re.match(r"^(Breaks|Replaces|Conflicts):", line):
                have_deb.add((pkg, " ".join(line.split())))
    # a relation before the first %package is the main package's: none is declared for it
    head = spec.split("%package", 1)[0]
    for n, line in enumerate(head.splitlines(), 1):
        if re.match(r"^(Obsoletes|Conflicts):", line):
            bad.append("row 8 spec: packaging/omx-clap-host.spec:%d: %s is no rename of packaging/renamed.txt" % (n, line.strip()))
    for pkg, rel in sorted(have_rpm - want_rpm):
        bad.append("row 8 spec: %s carries %s, no rename of packaging/renamed.txt" % (pkg, rel))
    for pkg, rel in sorted(want_rpm - have_rpm):
        bad.append("row 8 spec: %s lacks %s (packaging/renamed.txt)" % (pkg, rel))
    for pkg, rel in sorted(have_deb - want_deb):
        bad.append("row 8 debian/control: %s carries %s, no rename of packaging/renamed.txt" % (pkg, rel))
    for pkg, rel in sorted(want_deb - have_deb):
        bad.append("row 8 debian/control: %s lacks %s (packaging/renamed.txt)" % (pkg, rel))
    return bad


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
    # 8: no Breaks/Replaces/Conflicts/Obsoletes but a rename's, as packaging/renamed.txt declares it
    bad += relations(root)
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
        ("packaging/omx-clap-host.spec", "Obsoletes: foo < 1\n"),
        ("packaging/omx-clap-host.spec", "Provides: omx-clap-core-contract = 0.34.1\n"),
        ("debian/control", "Provides: libomx-clap-core1\n"),
        ("packaging/renamed.txt", "omx-clap-x omx-clap-y libomx-clap-x libomx-clap-y 0.34.0\n"),
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
    # a rename's relation taken away is found: each line naming an old name dropped from a scratch copy
    for rel, line in (("packaging/omx-clap-host.spec", "Obsoletes: omx-clap-core-contract < 0.34.0\n"),
                      ("debian/control", "Breaks: libomx-clap-core-dev (<< 0.34.0~)\n"),
                      ("debian/control", "Replaces: libomx-clap-core1 (<< 0.34.0~)\n")):
        with tempfile.TemporaryDirectory() as tmp:
            scratch = os.path.join(tmp, "t")
            shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(".git", "build", "node_modules"))
            path = os.path.join(scratch, rel)
            body = text(scratch, rel)
            if line not in body:
                print("FAIL self-test: %s is not in %s to take away" % (line.strip(), rel))
                failed += 1
                continue
            with open(path, "w", encoding="utf-8") as f:
                f.write(body.replace(line, "", 1))
            if not check(scratch):
                print("FAIL self-test: %s taken from %s and not missed" % (line.strip(), rel))
                failed += 1
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
    print("ok   no_backcompat self-test: each of %d old things planted is found, and each of 3 rename relations taken away" % len(cases))
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
