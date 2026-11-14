#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The library ranges omx-clap-core builds against are declared once, in the rpm spec's BuildRequires, floor and
# ceiling (#66). The installed omx-clap-core.pc names the same ranges in Requires.private, so a consumer that builds
# through pkg-config alone takes no omx-contract or omx-dsp the package itself refuses; debian/control states them
# again for the deb, and must state the same. The .pc checked is the one `make install-lib` writes, not its template.
#
#   pc_range_parity.py <tree>       0 when the installed .pc and debian/control carry the spec's ranges
#   pc_range_parity.py --self-test  the spec's floor and ceiling moved in a scratch copy: the installed .pc moves with
#                                   them, and debian/control, left behind, is found
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

# (the spec's devel package, the pkg-config name, the deb's -dev package)
LIBRARIES = [
    ("omx-contract-devel", "omx-contract", "libomx-contract-dev"),
    ("omx-dsp-devel", "omxdsp", "libomxdsp-dev"),
]


def spec_ranges(root, devel):
    """Every (floor, ceiling, where) the spec's BuildRequires lines declare for <devel>."""
    pat = re.compile(r"^BuildRequires:\s*\(%s\s*>=\s*([\d.]+)\s+with\s+%s\s*<\s*([\d.]+)\)" % (re.escape(devel), re.escape(devel)))
    found = []
    for path in sorted(glob.glob(os.path.join(root, "packaging", "*.spec"))):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                m = pat.search(line)
                if m:
                    found.append((m.group(1), m.group(2), "%s:%d" % (os.path.relpath(path, root), n)))
    return found


def control_ranges(root, dev):
    pat = re.compile(r"%s \(>=\s*([\d.]+)~\),\s*%s \(<<\s*([\d.]+)~\)" % (re.escape(dev), re.escape(dev)))
    found = []
    with open(os.path.join(root, "debian", "control"), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            for m in pat.finditer(line):
                found.append((m.group(1), m.group(2), "debian/control:%d" % n))
    return found


def pc_range(pc_text, name):
    req = next((l for l in pc_text.splitlines() if l.startswith("Requires.private:")), "")
    floor = re.search(r"(?:^|[ ,])%s\s*>=\s*([\d.]+)" % re.escape(name), req.split(":", 1)[-1])
    ceiling = re.search(r"(?:^|[ ,])%s\s*<\s*([\d.]+)" % re.escape(name), req.split(":", 1)[-1])
    return (floor.group(1) if floor else None, ceiling.group(1) if ceiling else None)


def installed_pc(root, dest):
    """The omx-clap-core.pc `make install-lib` writes from <root> into <dest>."""
    r = subprocess.run(["make", "-s", "-C", root, "install-lib", "DESTDIR=" + dest, "PREFIX=/usr", "LIBDIR=/usr/lib64"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        raise RuntimeError("make install-lib failed:\n" + r.stdout[-2000:])
    with open(os.path.join(dest, "usr", "lib64", "pkgconfig", "omx-clap-core.pc"), encoding="utf-8") as f:
        return f.read()


def check(root, pc_text):
    found = []
    for devel, name, dev in LIBRARIES:
        spec = spec_ranges(root, devel)
        if len(spec) != 1:
            found.append("%s: the spec declares %d BuildRequires ranges, want exactly one" % (devel, len(spec)))
            continue
        floor, ceiling, where = spec[0]
        got = pc_range(pc_text, name)
        if got != (floor, ceiling):
            found.append("omx-clap-core.pc: %s >= %s, < %s; the spec (%s) declares >= %s, < %s" % (name, got[0], got[1], where, floor, ceiling))
        control = control_ranges(root, dev)
        if not control:
            found.append("debian/control: no %s floor and ceiling" % dev)
        for f, c, at in control:
            if (f, c) != (floor, ceiling):
                found.append("%s: %s >= %s, << %s; the spec (%s) declares >= %s, < %s" % (at, dev, f, c, where, floor, ceiling))
    return found


def run(root):
    with tempfile.TemporaryDirectory() as dest:
        return check(root, installed_pc(root, dest))


def self_test():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = run(here)
    if found:
        print("FAIL the control: this tree's installed .pc or debian/control already differs from the spec")
        for line in found:
            print("     " + line)
        return 1
    print("ok   the tree's installed omx-clap-core.pc and debian/control carry the spec's ranges")
    (floor, ceiling, _), = spec_ranges(here, "omx-contract-devel")
    moved = (floor + ".9", str(int(ceiling.split(".")[0]) + 1))
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        shutil.copytree(here, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
        spec = glob.glob(os.path.join(tree, "packaging", "*.spec"))[0]
        with open(spec, encoding="utf-8") as f:
            text = f.read()
        before = "omx-contract-devel >= %s with omx-contract-devel < %s" % (floor, ceiling)
        if before not in text:
            print("FAIL the arm no longer applies: the spec has no '%s'" % before)
            return 1
        with open(spec, "w", encoding="utf-8") as f:
            f.write(text.replace(before, "omx-contract-devel >= %s with omx-contract-devel < %s" % moved))
        with tempfile.TemporaryDirectory() as dest:
            pc = installed_pc(tree, dest)
        failed = 0
        if pc_range(pc, "omx-contract") == moved:
            print("ok   the spec's omx-contract range moved to >= %s, < %s: the installed .pc moved with it" % moved)
        else:
            print("FAIL the spec's omx-contract range moved to >= %s, < %s; the installed .pc stayed at >= %s, < %s" % (moved + pc_range(pc, "omx-contract")))
            failed = 1
        if any(l.startswith("debian/control") for l in check(tree, pc)):
            print("ok   debian/control, left at >= %s, < %s, is found" % (floor, ceiling))
        else:
            print("FAIL debian/control, left behind, is not found")
            failed = 1
        return failed


def main():
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    if len(sys.argv) != 2:
        sys.exit("usage: pc_range_parity.py <tree> | --self-test")
    found = run(sys.argv[1])
    for line in found:
        print("FAIL " + line)
    if found:
        sys.exit(1)
    print("ok   the installed omx-clap-core.pc and debian/control carry the spec's omx-contract and omx-dsp ranges")


if __name__ == "__main__":
    main()
