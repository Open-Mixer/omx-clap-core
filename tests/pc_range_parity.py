#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The library floors omx-clap-core builds against are declared once, in the rpm spec's BuildRequires, a floor and
# no ceiling (floors only; #66). The installed omx-clap-core.pc names the same floors in Requires.private, so a consumer that
# builds through pkg-config alone takes no omx-contract or omx-dsp the package itself refuses; debian/control states them
# again for the deb, and must state the same. None of the three carries a ceiling. The .pc checked is the one `make
# install-lib` writes, not its template.
#
#   pc_range_parity.py <tree>       0 when the installed .pc and debian/control carry the spec's floors and no ceiling
#   pc_range_parity.py --self-test  the spec's floor moved in a scratch copy: the installed .pc moves with it, and
#                                   debian/control, left behind, is found; a ceiling planted in either is found
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
    """Every (floor, ceiling, where) the spec's BuildRequires lines declare for <devel>: the ceiling is None when there is none."""
    pat = re.compile(r"^BuildRequires:\s*\(?%s\s*>=\s*([\d.]+)(?:\s+with\s+%s\s*<\s*([\d.]+))?" % (re.escape(devel), re.escape(devel)))
    found = []
    for path in sorted(glob.glob(os.path.join(root, "packaging", "*.spec"))):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                m = pat.search(line)
                if m:
                    found.append((m.group(1), m.group(2), "%s:%d" % (os.path.relpath(path, root), n)))
    return found


def control_ranges(root, dev):
    pat = re.compile(r"%s \(>=\s*([\d.]+)~\)(?:,\s*%s \(<<\s*([\d.]+)~\))?" % (re.escape(dev), re.escape(dev)))
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
        if ceiling is not None:
            found.append("%s: %s has a ceiling < %s (floors only)" % (where, devel, ceiling))
        got = pc_range(pc_text, name)
        if got != (floor, None):
            found.append("omx-clap-core.pc: %s >= %s%s; the spec (%s) declares >= %s and no ceiling" % (name, got[0], ", < " + got[1] if got[1] else "", where, floor))
        control = control_ranges(root, dev)
        if not control:
            found.append("debian/control: no %s floor" % dev)
        for f, c, at in control:
            if (f, c) != (floor, None):
                found.append("%s: %s >= %s%s; the spec (%s) declares >= %s and no ceiling" % (at, dev, f, ", << " + c if c else "", where, floor))
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
    print("ok   the tree's installed omx-clap-core.pc and debian/control carry the spec's floors and no ceiling")
    (floor, _, _), = spec_ranges(here, "omx-contract-devel")
    moved = floor + ".9"
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        shutil.copytree(here, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
        spec = glob.glob(os.path.join(tree, "packaging", "*.spec"))[0]
        with open(spec, encoding="utf-8") as f:
            text = f.read()
        before = "omx-contract-devel >= %s\n" % floor
        if before not in text:
            print("FAIL the arm no longer applies: the spec has no '%s'" % before.strip())
            return 1
        with open(spec, "w", encoding="utf-8") as f:
            f.write(text.replace(before, "omx-contract-devel >= %s\n" % moved, 1))
        with tempfile.TemporaryDirectory() as dest:
            pc = installed_pc(tree, dest)
        if pc_range(pc, "omx-contract") == (moved, None):
            print("ok   the spec's omx-contract floor moved to >= %s: the installed .pc moved with it" % moved)
        else:
            print("FAIL the spec's omx-contract floor moved to >= %s; the installed .pc has %s" % (moved, pc_range(pc, "omx-contract")))
            failed = 1
        if any(l.startswith("debian/control") for l in check(tree, pc)):
            print("ok   debian/control, left at >= %s, is found" % floor)
        else:
            print("FAIL debian/control, left behind, is not found")
            failed = 1
        # a ceiling planted in the .pc, and one in the spec, are each found by name
        if any("omx-clap-core.pc" in l for l in check(tree, pc.replace("omx-contract >=", "omx-contract < 99, omx-contract >="))):
            print("ok   a ceiling in the installed .pc is found")
        else:
            print("FAIL a ceiling in the installed .pc is not found")
            failed = 1
        with open(spec, "w", encoding="utf-8") as f:
            f.write(text.replace(before, "(omx-contract-devel >= %s with omx-contract-devel < 4)\n" % floor, 1))
        if any("has a ceiling" in l for l in check(tree, pc)):
            print("ok   a ceiling in the spec is found")
        else:
            print("FAIL a ceiling in the spec is not found")
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
    print("ok   the installed omx-clap-core.pc and debian/control carry the spec's omx-contract and omx-dsp floors, no ceiling")


if __name__ == "__main__":
    main()
