#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The library floors omx-clap-core builds against are declared once, in packaging/deps.txt, and generated from it into
# the rpm spec's BuildRequires and debian/control (Open-Mixer/.github deps-render). Floors only: our own packages carry no
# ceiling. The installed omx-clap-core.pc names the same floors in Requires.private, so a consumer that builds through
# pkg-config alone takes no omx-contract or omx-dsp the package itself refuses. The .pc checked is the one
# `make install-lib` writes, not its template; it must carry the spec's floor and no upper bound.
#
#   pc_range_parity.py <tree>       0 when the installed .pc carries the spec's floors and no ceiling
#   pc_range_parity.py --self-test  the spec's floor moved in a scratch copy: the installed .pc moves with it, and a
#                                   ceiling planted in the template is found
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

# (the spec's devel package, the pkg-config name)
LIBRARIES = [
    ("omx-contract-devel", "omx-contract"),
    ("omx-dsp-devel", "omxdsp"),
]


def spec_floors(root, devel):
    """Every (floor, where) the spec's BuildRequires lines declare for <devel>."""
    pat = re.compile(r"^BuildRequires:\s*%s\s*>=\s*([\d.]+)\s*$" % re.escape(devel))
    found = []
    for path in sorted(glob.glob(os.path.join(root, "packaging", "*.spec"))):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                m = pat.search(line)
                if m:
                    found.append((m.group(1), "%s:%d" % (os.path.relpath(path, root), n)))
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
    for devel, name in LIBRARIES:
        spec = spec_floors(root, devel)
        if len(spec) != 1:
            found.append("%s: the spec declares %d BuildRequires floors, want exactly one" % (devel, len(spec)))
            continue
        floor, where = spec[0]
        got = pc_range(pc_text, name)
        if got != (floor, None):
            found.append("omx-clap-core.pc: %s >= %s, < %s; the spec (%s) declares >= %s and no ceiling" % (name, got[0], got[1], where, floor))
    return found


def run(root):
    with tempfile.TemporaryDirectory() as dest:
        return check(root, installed_pc(root, dest))


def self_test():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = run(here)
    if found:
        print("FAIL the control: this tree's installed .pc already differs from the spec")
        for line in found:
            print("     " + line)
        return 1
    print("ok   the tree's installed omx-clap-core.pc carries the spec's floors and no ceiling")
    (floor, _), = spec_floors(here, "omx-contract-devel")
    moved = floor + ".9"
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        shutil.copytree(here, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
        spec = glob.glob(os.path.join(tree, "packaging", "*.spec"))[0]
        with open(spec, encoding="utf-8") as f:
            text = f.read()
        before = "BuildRequires: omx-contract-devel >= %s\n" % floor
        if before not in text:
            print("FAIL the arm no longer applies: the spec has no '%s'" % before.strip())
            return 1
        with open(spec, "w", encoding="utf-8") as f:
            f.write(text.replace(before, "BuildRequires: omx-contract-devel >= %s\n" % moved))
        with tempfile.TemporaryDirectory() as dest:
            pc = installed_pc(tree, dest)
        if pc_range(pc, "omx-contract") == (moved, None):
            print("ok   the spec's omx-contract floor moved to >= %s: the installed .pc moved with it" % moved)
        else:
            print("FAIL the spec's omx-contract floor moved to >= %s; the installed .pc has %s" % (moved, pc_range(pc, "omx-contract")))
            failed = 1
        with open(os.path.join(tree, "omx-clap-core.pc.in"), encoding="utf-8") as f:
            tpl = f.read()
        with open(os.path.join(tree, "omx-clap-core.pc.in"), "w", encoding="utf-8") as f:
            f.write(tpl.replace("Requires.private: ", "Requires.private: omx-contract < 4, "))
        with tempfile.TemporaryDirectory() as dest:
            pc = installed_pc(tree, dest)
        if check(tree, pc):
            print("ok   a ceiling planted in the template is found")
        else:
            print("FAIL a ceiling planted in the template is not found")
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
    print("ok   the installed omx-clap-core.pc carries the spec's omx-contract and omx-dsp floors and no ceiling")


if __name__ == "__main__":
    main()
