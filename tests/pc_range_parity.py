#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The installed omx-clap.pc names the libraries whose headers omx-clap's take in Requires.private (omx-contract and
# omxdsp), by name and with no version: no hand-kept floor and no ceiling (owner ruling 2026-11-24). A consumer that builds through
# pkg-config takes whatever its build installed of the lower level. The .pc checked is the one `make install-lib`
# writes, not its template.
#
#   pc_range_parity.py <tree>       0 when the installed .pc names each library with no version
#   pc_range_parity.py --self-test  a floor and a ceiling planted in a scratch copy's template are each found
import os
import re
import shutil
import subprocess
import sys
import tempfile

# the pkg-config names the installed .pc must carry in Requires.private
LIBRARIES = ["omx-contract", "omxdsp"]


def requires_private(pc_text):
    req = next((l for l in pc_text.splitlines() if l.startswith("Requires.private:")), "")
    return [e.strip() for e in req.split(":", 1)[-1].split(",") if e.strip()]


def installed_pc(root, dest):
    """The omx-clap.pc `make install-lib` writes from <root> into <dest>."""
    r = subprocess.run(["make", "-s", "-C", root, "install-lib", "DESTDIR=" + dest, "PREFIX=/usr", "LIBDIR=/usr/lib64"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        raise RuntimeError("make install-lib failed:\n" + r.stdout[-2000:])
    with open(os.path.join(dest, "usr", "lib64", "pkgconfig", "omx-clap.pc"), encoding="utf-8") as f:
        return f.read()


def check(pc_text):
    found = []
    entries = requires_private(pc_text)
    for e in entries:
        if re.search(r"[<>=]", e):
            found.append("omx-clap.pc: Requires.private states a version: '%s' (no floor, no ceiling)" % e)
    for name in LIBRARIES:
        if name not in [re.split(r"\s", e)[0] for e in entries]:
            found.append("omx-clap.pc: Requires.private does not name %s" % name)
    return found


def run(root):
    with tempfile.TemporaryDirectory() as dest:
        return check(installed_pc(root, dest))


def self_test():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = run(here)
    if found:
        print("FAIL the control: this tree's installed .pc already states a version or misses a library")
        for line in found:
            print("     " + line)
        return 1
    print("ok   the tree's installed omx-clap.pc names omx-contract and omxdsp with no version")
    failed = 0
    for label, planted in (("a floor", "omx-contract >= 3.0.0"), ("a ceiling", "omx-contract < 4")):
        with tempfile.TemporaryDirectory() as tmp:
            tree = os.path.join(tmp, "tree")
            shutil.copytree(here, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
            tpl_path = os.path.join(tree, "omx-clap.pc.in")
            with open(tpl_path, encoding="utf-8") as f:
                tpl = f.read()
            if "Requires.private: omxdsp, omx-contract, " not in tpl:
                print("FAIL the arm no longer applies: the template's Requires.private changed")
                return 1
            with open(tpl_path, "w", encoding="utf-8") as f:
                f.write(tpl.replace("Requires.private: omxdsp, omx-contract, ", "Requires.private: omxdsp, %s, " % planted))
            with tempfile.TemporaryDirectory() as dest:
                pc = installed_pc(tree, dest)
            if check(pc):
                print("ok   %s planted in the template is found" % label)
            else:
                print("FAIL %s planted in the template is not found" % label)
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
    print("ok   the installed omx-clap.pc names omx-contract and omxdsp with no version")


if __name__ == "__main__":
    main()
