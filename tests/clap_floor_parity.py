#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The rpm spec's clap-devel and debian/control's clap-headers name the same CLAP headers, pinned from the same
# .github clap-headers source. A build from one packaging must not take headers the other refuses, so every floor
# and every ceiling the two files declare for them must be the one value.
#
#   clap_floor_parity.py <tree>       0 when the spec and debian/control agree
#   clap_floor_parity.py --self-test  a floor or ceiling moved out of step, planted in a scratch tree, is found
import glob
import os
import re
import shutil
import sys
import tempfile

SPEC_RE = re.compile(r"clap-devel\s*>=\s*([\d.]+)\s+with\s+clap-devel\s*<\s*([\d.]+)")
CONTROL_RE = re.compile(r"clap-headers\s*\(>=\s*([\d.]+)~\),\s*clap-headers\s*\(<<\s*([\d.]+)~\)")


def spec_pins(root):
    found = []
    for path in glob.glob(os.path.join(root, "packaging", "*.spec")):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                m = SPEC_RE.search(line)
                if m:
                    found.append((m.group(1), m.group(2), "%s:%d" % (os.path.relpath(path, root), n)))
    return found


def control_pins(root):
    path = os.path.join(root, "debian", "control")
    found = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            m = CONTROL_RE.search(line)
            if m:
                found.append((m.group(1), m.group(2), "%s:%d" % (os.path.relpath(path, root), n)))
    return found


def check(root):
    pins = spec_pins(root) + control_pins(root)
    if not pins:
        return ["no clap-devel/clap-headers floor and ceiling found at all"]
    floors = sorted(set(p[0] for p in pins))
    ceilings = sorted(set(p[1] for p in pins))
    found = []
    if len(floors) > 1:
        for floor, ceiling, where in pins:
            found.append("%s: floor %s, the tree also has %s" % (where, floor, ", ".join(f for f in floors if f != floor)))
    if len(ceilings) > 1:
        for floor, ceiling, where in pins:
            found.append("%s: ceiling %s, the tree also has %s" % (where, ceiling, ", ".join(c for c in ceilings if c != ceiling)))
    return found


def self_test():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if check(here):
        print("FAIL the control: this tree's CLAP floor and ceiling already disagree", check(here))
        return 1
    print("ok   the tree's spec and debian/control agree")
    arms = [
        ("packaging/omx-clap-host.spec", "clap-devel >= 1.2.10 with clap-devel < 2", "clap-devel >= 1.2.7 with clap-devel < 2",
         "one spec line back at the old floor"),
        ("debian/control", "clap-headers (>= 1.2.10~), clap-headers (<< 2~)", "clap-headers (>= 1.2.9~), clap-headers (<< 2~)",
         "a control line at a different floor"),
        ("packaging/omx-clap-host.spec", "clap-devel >= 1.2.10 with clap-devel < 2", "clap-devel >= 1.2.10 with clap-devel < 3",
         "a spec line at a different ceiling"),
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
        print("FAIL the CLAP floor/ceiling does not match across packagings: " + line)
    if found:
        sys.exit(1)
    print("ok   the spec and debian/control state the same CLAP floor and ceiling")


if __name__ == "__main__":
    main()
