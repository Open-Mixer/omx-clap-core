#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Derive contract.d/hosting/hosting.json, omx-clap-core's hosting domain document, from data/hosting*.json.

data/hosting.json and data/hosting/*.json stay the source of the codes. The domain document carries one item per
HOSTING_* codes item of them (each item's doc is its description), each code as a oneOf entry: the code as const, its key
as title, its English text as description, its place in the item as x-code. Nothing here is typed twice.

The domain's version is VERSION. An item's x-since is the domain version that first carried the item: the version the
file already records for it, and the current version for an item the file does not yet have. The document is
append-only under one version, and the render refuses by name to replace the file with one that adds or removes a code
while the version is unchanged, or that moves the x-code of a code the file already has (a new code is appended, after
the existing ones). --check applies the same refusals before it compares.

    render-domain.py [--check] <data dir> <VERSION file> <out file>
"""
import glob
import json
import sys


def source_items(data_dir):
    items = {}
    for path in [f"{data_dir}/hosting.json"] + sorted(glob.glob(f"{data_dir}/hosting/*.json")):
        for name, body in json.load(open(path)).items():
            if name.startswith("HOSTING_") and isinstance(body, dict) and body.get("kind") == "codes":
                if name in items:
                    sys.exit(f"render-domain.py: {name} is declared twice (second in {path})")
                items[name] = body
    return items


def render(data_dir, version, old):
    since = {n: b.get("x-since") for n, b in (old or {}).get("components", {}).get("schemas", {}).items()}
    schemas = {}
    seen = {}
    for name, body in source_items(data_dir).items():
        one_of = []
        for code, (key, c) in enumerate(body["codes"].items()):
            word = c["code"]
            if word in seen:
                sys.exit(f"render-domain.py: {word} is in {seen[word]} and in {name}")
            seen[word] = name
            one_of.append({"const": word, "title": key, "description": c["text"]["en"], "x-code": code})
        schemas[name] = {"description": body["doc"], "x-since": since.get(name) or version, "oneOf": one_of}
    doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://openmixer.org/contract/hosting",
        "info": {
            "title": "The hosting codes of omx-clap-core",
            "version": version,
            "x-owner": "omx-clap-core",
            "x-stability": "experimental",
        },
        "components": {"schemas": schemas},
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def words_of(doc):
    return {i: {w["const"]: w["x-code"] for w in b["oneOf"]} for i, b in doc["components"]["schemas"].items()}


def refusals(old, new):
    """what a document that replaces `old` must not do, each by item and code"""
    out = []
    ow, nw = words_of(old), words_of(new)
    if old["info"]["version"] == new["info"]["version"]:
        for item in sorted(set(ow) | set(nw)):
            added = sorted(set(nw.get(item, {})) - set(ow.get(item, {})))
            removed = sorted(set(ow.get(item, {})) - set(nw.get(item, {})))
            if added or removed:
                out.append(f"{item}: words added or removed while the version is unchanged ({new['info']['version']}): "
                           f"added {added}, removed {removed}: bump VERSION")
    for item in sorted(set(ow) & set(nw)):
        for word in sorted(set(ow[item]) & set(nw[item])):
            if ow[item][word] != nw[item][word]:
                out.append(f"{item}: x-code moved: {word} was {ow[item][word]}, is {nw[item][word]}: "
                           "a new word is appended after the existing ones")
    return out


def main(argv):
    check = argv[:1] == ["--check"]
    args = argv[1:] if check else argv
    if len(args) != 3:
        sys.exit(__doc__)
    data_dir, version_file, out = args
    version = open(version_file).read().strip()
    old = None
    try:
        have = open(out).read()
    except OSError as e:
        if check:
            sys.exit(f"render-domain.py: {out}: {e.strerror}: run make render-domain")
        have = None
    if have is not None:
        try:
            old = json.loads(have)
            words_of(old)
        except (ValueError, KeyError, TypeError):
            old = None  # a file that is no document of this shape is only stale
    text = render(data_dir, version, old)
    if old is not None:
        problems = refusals(old, json.loads(text))
        if problems:
            sys.exit("".join(f"render-domain.py: {out}: {m}\n" for m in problems).rstrip("\n"))
    if check:
        if have != text:
            sys.exit(f"render-domain.py: {out} is not what data/hosting*.json and VERSION render: run make render-domain")
        return
    with open(out, "w") as f:
        f.write(text)


main(sys.argv[1:])
