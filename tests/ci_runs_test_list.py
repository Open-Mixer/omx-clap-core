#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas
#
# Every test target of the Makefile runs in CI. The workflow's steps used to be a hand-typed list of make targets beside
# the Makefile's own, and a target added to `test:` ran in no job until it failed unseen on main (test-effects-meter,
# 2026-11); the CI steps now run the groups the Makefile declares (print-test-plain, print-test-main-only,
# print-test-ns), and this check holds the workflow to them.
#
# In scope: every prerequisite of `test:` and every other test-* or check-* target of the Makefile, except those the
# Makefile lists in DESK_ONLY (print-desk-only), which it runs on a desk with the reason beside the list.
#
# A target runs in CI when a `make ...` invocation in the `run:` value of an enabled step of an enabled job names it, or
# names a target that has it as a prerequisite, directly or through other targets (the Makefile's own database,
# `make -pRrq`, answers that). The line is read as the shell reads it: a step name, a comment (whole line or trailing),
# a quoted string (a printf), the arguments of echo or printf, a step or job whose `if:` is false or `${{ false }}` are
# not runs.
#
#   ci_runs_test_list.py <tree>       0 when every in-scope target runs in CI, 1 naming each that does not
#   ci_runs_test_list.py --self-test  a target left out of a scratch workflow, and one only a name, comment, echo, printf
#                                     or disabled step or job spells, are found
import glob
import os
import re
import shlex
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


def disabled(value):
    """An `if:` value that is never true: false, 'false', ${{ false }}, with or without a trailing comment."""
    value = re.sub(r"\s+#.*$", "", value.strip()).strip()
    m = re.fullmatch(r"\$\{\{\s*(.*?)\s*\}\}", value)
    value = (m.group(1) if m else value).strip().strip("'\"").strip()
    return value == "false"


def run_lines(text):
    """The commands of every enabled step's `run:` value, in every enabled job: the inline one or the block scalar under
    it. A step name, a comment, a step or a job with a never-true `if:` are not runs."""
    out = []
    job_off = False
    step = None
    steps = []

    def flush():
        nonlocal step
        if step is not None and not job_off:
            steps.append(step)
        step = None

    def finish_job():
        nonlocal steps
        flush()
        for st in steps:
            out.extend(step_runs(st))
        steps = []

    for line in text.splitlines():
        if re.match(r"^\S", line) or re.match(r"^  [\w-]+:\s*(#.*)?$", line):
            finish_job()
            job_off = False
            continue
        m = re.match(r"^    if:\s*(.*)$", line)
        if m:
            job_off = job_off or disabled(m.group(1))
        if re.match(r"^\s*-\s", line):
            flush()
            step = []
        if step is not None:
            step.append(line)
    finish_job()
    return out


def step_runs(step):
    """The run commands of one step's lines, none when its own `if:` never holds."""
    if any((m := re.match(r"^\s*(?:-\s+)?if:\s*(.*)$", line)) and disabled(m.group(1)) for line in step):
        return []
    out = []
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
        elif value:
            out.append(value)
    return out


def make_words(line):
    """The words each `make` invocation of one shell line is given: the line is tokenised as the shell would, so a
    comment, a quoted string (a printf, an echo) and the arguments of echo or printf are text, not invocations."""
    # an expression `${{ cond && 'a' || 'b' }}` names what its quoted strings spell: either may run
    line = re.sub(r"\$\{\{(.*?)\}\}", lambda m: " ".join(re.findall(r"'([^']*)'", m.group(1))), line)
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        tokens = list(lexer)
    except ValueError:
        return set()
    words, start, i = set(), 0, 0
    while i < len(tokens):
        tok = tokens[i]
        if re.fullmatch(r"[;&|()<>]+", tok):
            start = i + 1
        elif tok == "make" and not {"echo", "printf"} & set(tokens[start:i]):
            j = i + 1
            while j < len(tokens) and not re.fullmatch(r"[;&|()<>]+", tokens[j]):
                words.update(re.findall(r"[A-Za-z][\w./-]*", tokens[j]))
                j += 1
        i += 1
    return words


def commands(lines):
    """The shell commands of run lines: a line ending in a backslash is joined to the next, and the body of a heredoc
    (up to its delimiter line) is text for the command it feeds, not commands."""
    out, pending, delimiter = [], "", None
    for line in lines:
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        if line.rstrip().endswith("\\"):
            pending += line.rstrip()[:-1] + " "
            continue
        line, pending = pending + line, ""
        out.append(line)
        m = re.search(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1", line)
        if m:
            delimiter = m.group(2)
    if pending:
        out.append(pending)
    return out


def named_in_workflow(text):
    """The words of every `make` invocation of an enabled run."""
    named = set()
    for line in commands(run_lines(text)):
        named |= make_words(line)
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
    no_runs = "".join(ln + "\n" for ln in steps.splitlines() if ln.lstrip().startswith(("steps:", "- name:")))
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
    plain = "        run: make $(make -s print-test-plain)"
    for what, line in (("a trailing comment that spells the make command", "        run: true  # make $(make -s print-test-plain)"),
                       ("a printf that prints the make command", "        run: printf '%s\\n' \"make $(make -s print-test-plain)\"")):
        if check(rule_map, steps.replace(plain, line), root):
            print("ok   %s is not a run" % what)
        else:
            print("FAIL %s counts as a run" % what)
            failed = 1
    for cond in ("false", "${{ false }}"):
        job = "jobs:\n  g:\n    if: %s\n%s" % (cond, steps)
        if check(rule_map, job, root):
            print("ok   a job with `if: %s` is not a run" % cond)
        else:
            print("FAIL a job with `if: %s` counts as a run" % cond)
            failed = 1
    heredoc = steps.replace(plain, "        run: |\n          cat <<EOF\n          make $(make -s print-test-plain)\n          EOF")
    if check(rule_map, heredoc, root):
        print("ok   a make command inside a heredoc body is not a run")
    else:
        print("FAIL a make command inside a heredoc body counts as a run")
        failed = 1
    joined = "      - run: |\n          make -C . \\\n" + " \\\n".join("            " + t for t in want) + "\n"
    if check(rule_map, joined, root):
        print("FAIL targets on the continuation lines of one make command were reported unreached")
        failed = 1
    else:
        print("ok   a make command continued over lines names every target on them")
    job = "jobs:\n  g:\n    if: github.event_name != 'pull_request'\n%s" % steps
    if check(rule_map, job, root):
        print("FAIL a job with a real condition was refused")
        failed = 1
    else:
        print("ok   a job with a real `if:` is a run")
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
    print("ok   every test target runs in CI (bar the desk-only ones)")


if __name__ == "__main__":
    main()
