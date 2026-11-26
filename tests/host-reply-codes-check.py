#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Every number the host answers is named in the vocabulary (omx-clap-core#34): each ERR_* name src/ uses, resolved to
its number by plugin-hostd-protocol's host-errors.h, has a code with an English sentence in data/, in a domain of
contract.d/ or in a domain document named by --domain (HOST_REPLY_CODES is plugin-hostd-protocol's domain host since ruling
R5: its installed host/host.json, or a checkout's contract.d/host/host.json), so a table built from the vocabularies
(plugin-hostd-protocol's reply_codes) names every refusal and a controller asks for none by number. -2, the instance
number already taken, is reply.host.instance-already-exists.

  tests/host-reply-codes-check.py --header <host-errors.h> [--domain <domain.json>]... [--self-test]
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


def from_domain(doc):
    """a domain document's codes items in the data form: {item: {"codes": {title: {code, resp, text}}}}"""
    out = {}
    for name, it in (doc.get("components") or {}).get("schemas", {}).items():
        if it.get("x-kind", "codes") != "codes" or not isinstance(it.get("oneOf"), list):
            continue
        out[name] = {"kind": "codes", "codes": {w.get("title"): {"code": w.get("const"), "resp": w.get("x-resp"),
                                                                 "text": {"en": w.get("x-text")}}
                                                for w in it["oneOf"]}}
    return out


def load_docs(root, domains=()):
    """data/*.json as written, and every contract.d/<domain>/<domain>.json and every named domain document in the data form"""
    docs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(root, "data", "*.json")))]
    for f in sorted(glob.glob(os.path.join(root, "contract.d", "*", "*.json"))):
        if os.path.basename(f) == os.path.basename(os.path.dirname(f)) + ".json":
            docs.append(from_domain(json.load(open(f))))
    for f in domains:
        docs.append(from_domain(json.load(open(f))))
    return docs


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
            out.append("resp %d (%s) is answered by src/ and has no code in data/ or contract.d/" % (resp, ", ".join(sorted(names))))
        elif not ((c.get("text") or {}).get("en") or "").strip():
            out.append("%s (resp %d) has no English sentence" % (c["code"], resp))
    for resp, code in sorted(NAMED.items()):
        if have.get(resp, {}).get("code") != code:
            out.append("resp %d is %s, want %s" % (resp, have.get(resp, {}).get("code"), code))
    return out


def main():
    args = sys.argv[1:]
    if "--header" not in args:
        print("usage: host-reply-codes-check.py --header <host-errors.h> [--domain <domain.json>]... [--self-test]", file=sys.stderr)
        return 2
    numbers = host_numbers(args[args.index("--header") + 1])
    sources = [open(f).read() for f in sorted(glob.glob(os.path.join(ROOT, "src", "*.c")))]
    domains = [args[i + 1] for i, a in enumerate(args) if a == "--domain" and i + 1 < len(args)]
    for f in domains:
        if not os.path.isfile(f):
            print("host-reply-codes-check: no domain document at %s" % f, file=sys.stderr)
            return 2
    docs = load_docs(ROOT, domains)
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
