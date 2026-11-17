#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The rpm spec's clap-devel and debian/control's clap-headers name the same CLAP headers, pinned from the same
# .github clap-headers source. A build from one packaging must not take headers the other refuses, so every floor
# the two files declare for them must be the one value. Floors only (owner rule): a ceiling on either is refused.
#
#   clap_floor_parity.py <tree>       0 when the spec and debian/control state the same floor and no ceiling
#   clap_floor_parity.py --self-test  a floor moved out of step, or a ceiling, planted in a scratch tree, is found
import glob
import os
import re
import shutil
import sys
import tempfile

SPEC_RE = re.compile(r"clap-devel\s*>=\s*([\d.]+)")
CONTROL_RE = re.compile(r"clap-headers\s*\(>=\s*([\d.]+)~?\)")
SPEC_CEIL_RE = re.compile(r"clap-devel\s*<")
CONTROL_CEIL_RE = re.compile(r"clap-headers\s*\(<")


def scan(path, root, floor_re, ceil_re):
    """(floor, where) for every line naming a floor; (None, where) for every line naming a ceiling."""
    found = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.lstrip().startswith(("#", "-", "*")):
                continue
            where = "%s:%d" % (os.path.relpath(path, root), n)
            m = floor_re.search(line)
            if m:
                found.append((m.group(1), where))
            if ceil_re.search(line):
                found.append((None, where))
    return found


def pins(root):
    found = []
    for path in glob.glob(os.path.join(root, "packaging", "*.spec")):
        found += scan(path, root, SPEC_RE, SPEC_CEIL_RE)
    return found + scan(os.path.join(root, "debian", "control"), root, CONTROL_RE, CONTROL_CEIL_RE)


def check(root):
    found_pins = pins(root)
    if not any(f for f, _ in found_pins):
        return ["no clap-devel/clap-headers floor found at all"]
    found = ["%s: a ceiling on the CLAP headers; floors only" % where for f, where in found_pins if f is None]
    floors = sorted(set(f for f, _ in found_pins if f))
    if len(floors) > 1:
        for floor, where in found_pins:
            if floor:
                found.append("%s: floor %s, the tree also has %s" % (where, floor, ", ".join(f for f in floors if f != floor)))
    return found


def self_test():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if check(here):
        print("FAIL the control: this tree's CLAP floors already disagree or carry a ceiling", check(here))
        return 1
    print("ok   the tree's spec and debian/control agree, floors only")
    arms = [
        ("packaging/omx-clap-host.spec", "BuildRequires: clap-devel >= 1.2.10", "BuildRequires: clap-devel >= 1.2.7",
         "one spec line back at the old floor"),
        ("debian/control", "clap-headers (>= 1.2.10~),", "clap-headers (>= 1.2.9~),",
         "a control line at a different floor"),
        ("packaging/omx-clap-host.spec", "BuildRequires: clap-devel >= 1.2.10", "BuildRequires: (clap-devel >= 1.2.10 with clap-devel < 2)",
         "a spec line with a ceiling"),
        ("debian/control", "clap-headers (>= 1.2.10~),", "clap-headers (>= 1.2.10~), clap-headers (<< 2~),",
         "a control line with a ceiling"),
    ]
    failed = 0
    for rel, before, after, what in arms:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "packaging"))
            os.makedirs(os.path.join(tmp, "debian"))
            for f in ("packaging/omx-clap-host.spec", "debian/control"):
                shutil.copy(os.path.join(here, f), os.path.join(tmp, f))
            path = os.path.join(tmp, rel)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            if before not in text:
                print("FAIL %s: the arm no longer applies" % what)
                failed = 1
                continue
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace(before, after, 1))
            if check(tmp):
                print("ok   %s is found" % what)
            else:
                print("FAIL %s is not found" % what)
                failed = 1
    return failed


def main():
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    if len(sys.argv) != 2:
        sys.exit(__doc__ or "usage: clap_floor_parity.py <tree> | --self-test")
    found = check(sys.argv[1])
    for line in found:
        print("FAIL the CLAP floor does not match across packagings, or a ceiling: " + line)
    if found:
        sys.exit(1)
    print("ok   the spec and debian/control state the same CLAP floor and no ceiling")


if __name__ == "__main__":
    main()
