#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Every number the host answers is named in the vocabulary (omx-clap-core#34): each ERR_* name src/ uses, resolved to
its number by plugin-hostd-protocol's host-errors.h, has a code with an English sentence in data/ (HOST_REPLY_CODES
or another group), so a table built from the vocabularies (plugin-hostd-protocol's reply_codes) names every refusal
and a controller asks for none by number. -2, the instance number already taken, is reply.host.instance-already-exists.

  tests/host-reply-codes-check.py --header <host-errors.h> [--self-test]
"""
import copy
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# a number whose code a controller names (zynthian-ui's engine branches on it): the code it must have
NAMED = {-2: "reply.host.instance-already-exists"}


def host_numbers(header):
    """{ERR_NAME: number} of host-errors.h's enum, an alias resolved to the number it names"""
    text = open(header).read()
    out = {}
    for name, value in re.findall(r"\b(ERR_[A-Z0-9_]+)\s*=\s*(-?\d+|ERR_[A-Z0-9_]+)", text):
        out[name] = int(value) if value.lstrip("-").isdigit() else out.get(value)
    return out


def answered(sources, numbers):
    """{number: [ERR names]} of every ERR_* name the sources use"""
    out = {}
    for text in sources:
        for name in re.findall(r"\b(ERR_[A-Z0-9_]+)\b", text):
            if numbers.get(name) is not None:
                out.setdefault(numbers[name], set()).add(name)
    return out


def coded(docs):
    """{resp: code entry} of every code of data/"""
    out = {}

    def walk(n):
        if isinstance(n, dict):
            if isinstance(n.get("resp"), int) and isinstance(n.get("code"), str):
                out.setdefault(n["resp"], n)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    for d in docs:
        walk(d)
    return out


def problems(sources, docs, numbers):
    have = coded(docs)
    out = []
    for resp, names in sorted(answered(sources, numbers).items(), reverse=True):
        c = have.get(resp)
        if c is None:
            out.append("resp %d (%s) is answered by src/ and has no code in data/" % (resp, ", ".join(sorted(names))))
        elif not ((c.get("text") or {}).get("en") or "").strip():
            out.append("%s (resp %d) has no English sentence" % (c["code"], resp))
    for resp, code in sorted(NAMED.items()):
        if have.get(resp, {}).get("code") != code:
            out.append("resp %d is %s, want %s" % (resp, have.get(resp, {}).get("code"), code))
    return out


def main():
    args = sys.argv[1:]
    if "--header" not in args:
        print("usage: host-reply-codes-check.py --header <host-errors.h> [--self-test]", file=sys.stderr)
        return 2
    numbers = host_numbers(args[args.index("--header") + 1])
    sources = [open(f).read() for f in sorted(glob.glob(os.path.join(ROOT, "src", "*.c")))]
    docs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "data", "*.json")))]
    if "--self-test" in args:
        arms = []
        dropped = copy.deepcopy(docs)
        for d in dropped:
            codes = (d.get("HOST_REPLY_CODES") or {}).get("codes")
            if codes:
                for k in [k for k, v in codes.items() if isinstance(v, dict) and v.get("resp") == -2]:
                    del codes[k]
        arms.append(("a vocabulary without -2", sources, dropped))
        unused = next((n for n, v in numbers.items() if v is not None and v not in coded(docs)), None)
        if unused:
            arms.append(("a source answering %s, which has no code" % unused, sources + ["return %s;" % unused], docs))
        for what, s, d in arms:
            if not problems(s, d, numbers):
                print("host-reply-codes-check --self-test: %s was not refused" % what, file=sys.stderr)
                return 1
        print("host-reply-codes-check --self-test: ok (%s refused)" % "; ".join(w for w, _, _ in arms))
        return 0
    bad = problems(sources, docs, numbers)
    for p in bad:
        print("host-reply-codes-check: " + p, file=sys.stderr)
    if not bad:
        print("host-reply-codes-check: every number src/ answers (%d) has a code and an English sentence"
              % len(answered(sources, numbers)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
