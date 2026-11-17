#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas
#
# Every prerequisite of the Makefile's `test:` runs in CI. The workflow's steps used to be a hand-typed list of make
# targets beside the Makefile's own, and a target added to `test:` ran in no job until it failed unseen on main
# (test-effects-meter, 2026-11); the CI steps now run the groups the Makefile declares (print-test-plain,
# print-test-main-only, print-test-ns), and this check holds the workflow to them.
#
# The targets in scope: every prerequisite of `test:` and every other test-* or check-* target of the Makefile, except
# those it lists in DESK_ONLY (run on a desk, with the reason beside the list).
#
# A target runs in CI when a `make ...` line of an enabled step's `run:` value names it, or names a target that has it as a prerequisite,
# directly or through other targets (the Makefile's own database, `make -pRrq`, answers that). A comment or an echo
# that spells a target is not a run.
#
#   ci_runs_test_list.py <tree>       0 when every phony prerequisite of `test:` runs in CI, 1 naming each that does not
#   ci_runs_test_list.py --self-test  a target left out of a scratch workflow, and one a comment only mentions, are found
import glob
import os
import re
import subprocess
import sys



def rules(root):
    """target -> set of prerequisites, from make's own database (every `test:` line, included files, pattern rules out)."""
    db = subprocess.run(["make", "-pRrq", "-C", root], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout
    found = {}
    for m in re.finditer(r"^([^\s#:=%.][^:=\n]*?):(?!=)[ \t]*([^\n=]*)$", db, re.M):
        for target in m.group(1).split():
            found.setdefault(target, set()).update(m.group(2).split("|")[0].split())
    return found


def run_lines(text):
    """The commands of every enabled step's `run:` value: the inline one or the block scalar under it. A step's name, a
    comment, a step with `if: false` and an echo are not runs."""
    steps, cur = [], None
    for line in text.splitlines():
        if re.match(r"^\s*-\s", line):
            cur = []
            steps.append(cur)
        if cur is not None:
            cur.append(line)
    out = []
    for step in steps:
        if any(re.match(r"^\s*(-\s+)?if:\s*['\"]?false['\"]?\s*(#.*)?$", l) for l in step):
            continue
        i = 0
        while i < len(step):
            m = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", step[i])
            i += 1
            if not m:
                continue
            key_indent, value = len(m.group(1)), m.group(2).strip()
            if re.match(r"^[|>][+-]?\d*\s*(#.*)?$", value):
                while i < len(step) and (not step[i].strip() or len(step[i]) - len(step[i].lstrip()) > key_indent):
                    out.append(step[i])
                    i += 1
            elif value and not value.startswith("#"):
                out.append(value)
    return out


def named_in_workflow(text):
    """The words of every `make` command line of an enabled run: not a comment, not an echo."""
    named = set()
    for line in run_lines(text):
        stripped = line.strip()
        if stripped.startswith("#") or re.search(r"\becho\b", stripped) or not re.search(r"\bmake\b", stripped):
            continue
        for word in re.findall(r"[A-Za-z][\w./-]*", stripped.split("make", 1)[1]):
            named.add(word)
    return named


def expand_groups(root, named):
    """`make $(make -s print-test-plain)` names what the Makefile's print target answers."""
    out = set(named)
    for word in named:
        if word.startswith("print-test-"):
            r = subprocess.run(["make", "-s", "-C", root, word], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            out.update(r.stdout.split())
    return out


def reached(rule_map, named):
    seen = set()
    todo = list(named)
    while todo:
        t = todo.pop()
        if t in seen:
            continue
        seen.add(t)
        todo.extend(rule_map.get(t, ()))
    return seen


def desk_only(root):
    """The targets the Makefile names as run on a desk only (print-desk-only), each with its reason beside the list."""
    r = subprocess.run(["make", "-s", "-C", root, "print-desk-only"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return set(r.stdout.split())


def wanted(rule_map, root="."):
    """Every prerequisite of `test:` and every other test-* or check-* target, bar the desk-only ones."""
    desk = desk_only(root)
    own = {t for t in rule_map if re.match(r"^(test|check)-[\w-]+$", t)}
    return sorted(t for t in own | set(rule_map.get("test", ())) if "/" not in t and t not in desk)


def check(rule_map, workflow_text, root="."):
    want = wanted(rule_map, root)
    ran = reached(rule_map, expand_groups(root, named_in_workflow(workflow_text)))
    return ["%s is a test target and runs in no CI step" % t for t in want if t not in ran]


def workflow_text(root):
    text = ""
    for path in sorted(glob.glob(os.path.join(root, ".github", "workflows", "*.yml"))):
        with open(path, encoding="utf-8") as f:
            text += f.read() + "\n"
    return text


def self_test(root):
    rule_map = rules(root)
    if not rule_map.get("test"):
        print("FAIL the control: make's database has no prerequisites for `test`")
        return 1
    failed = 0
    want = wanted(rule_map, root)
    full = "".join("      - run: make %s\n" % t for t in want)
    others = "".join("      - run: make %s\n" % t for t in want if t not in rule_map["test"])
    if check(rule_map, full, root):
        print("FAIL a workflow naming every prerequisite of `test` was refused")
        failed = 1
    else:
        print("ok   a workflow naming every prerequisite of `test` is met")
    if check(rule_map, "      - run: make test\n" + others, root):
        print("FAIL `make test` and the targets outside it were not taken as running them")
        failed = 1
    else:
        print("ok   `make test` runs its prerequisites")
    groups = "      - run: make test-fake\n" + others + "".join("      - run: make $(make -s print-test-%s)\n" % g for g in ("plain", "main-only", "ns"))
    if check(rule_map, groups, root):
        print("FAIL the three print-test groups do not reach every prerequisite of `test`")
        failed = 1
    else:
        print("ok   the three print-test groups reach every prerequisite of `test`")
    if check(rule_map, groups.replace("main-only", "plain"), root):
        print("ok   a group left out (main-only) is found")
    else:
        print("FAIL a workflow without print-test-main-only was accepted")
        failed = 1
    outside = [t for t in want if t not in rule_map["test"]]
    if not outside:
        print("FAIL the control: every test-* target is a prerequisite of `test`")
        return 1
    # the first target that only its own run line reaches (test-package, say, is reached through test-fake)
    victim = outside[0]
    for t in outside:
        text = "".join("      - run: make %s\n" % u for u in want if u != t)
        if any(t in line for line in check(rule_map, text, root)):
            victim = t
            break
    left_out = "".join("      - run: make %s\n" % t for t in want if t != victim)
    if any(victim in line for line in check(rule_map, left_out, root)):
        print("ok   %s left out of the workflow is found" % victim)
    else:
        print("FAIL %s left out of the workflow is not found" % victim)
        failed = 1
    only_said = left_out + "      # make %s\n      - run: echo make %s\n" % (victim, victim)
    if any(victim in line for line in check(rule_map, only_said, root)):
        print("ok   %s only in a comment and an echo is found" % victim)
    else:
        print("FAIL %s only in a comment and an echo counts as run" % victim)
        failed = 1
    # a real workflow: the step NAMES spell make test, the groups' run lines are what runs
    steps = (
        "    steps:\n"
        "      - name: The checks and sabotage arms make test lists\n"
        "        run: make $(make -s print-test-plain)\n"
        "      - name: The sabotage arms make test-main-only runs\n"
        "        run: make $(make -s print-test-main-only)\n"
        "      - run: make test-fake\n"
        + others.replace("      - run:", "      - name: others\n        run:") +
        "      - name: The namespace checks of make test\n"
        "        run: |\n"
        "          if unshare true; then\n"
        "            make $(make -s print-test-ns)\n"
        "          fi\n"
    )
    if check(rule_map, steps, root):
        print("FAIL a workflow with the three group run lines was refused")
        failed = 1
    else:
        print("ok   a workflow with the three group run lines is met")
    no_runs = "".join(l + "\n" for l in steps.splitlines() if l.lstrip().startswith(("steps:", "- name:")))
    if check(rule_map, no_runs, root):
        print("ok   the group run lines deleted, the step names left, is found")
    else:
        print("FAIL step names that spell `make test` count as a run: the three group run lines deleted stays green")
        failed = 1
    disabled = steps.replace("        run: make $(make -s print-test-plain)", "        if: false\n        run: make $(make -s print-test-plain)")
    if check(rule_map, disabled, root):
        print("ok   a step with `if: false` is not a run")
    else:
        print("FAIL a step with `if: false` counts as a run")
        failed = 1
    return failed


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        sys.exit(self_test(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if len(sys.argv) != 2:
        sys.exit("usage: ci_runs_test_list.py <tree> | --self-test")
    found = check(rules(sys.argv[1]), workflow_text(sys.argv[1]), sys.argv[1])
    for line in found:
        print("FAIL " + line)
    if found:
        sys.exit(1)
    print("ok   every prerequisite of `make test` runs in CI")


if __name__ == "__main__":
    main()
