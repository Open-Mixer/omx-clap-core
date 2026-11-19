#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""Derive contract.d/hosting/hosting.json, omx-clap-core's hosting domain document, from data/hosting*.json.

data/hosting.json and data/hosting/*.json stay the source of the codes. The domain document carries one item per
HOSTING_* codes item of them (each item's doc is its description), each code as a oneOf entry: the code as const, its key
as title, its English text as description, its place in the item as x-code. Nothing here is typed twice.

The domain's version is VERSION. An item's x-since is the domain version that first carried the item: the version the
file already records for it, and the current version for an item the file does not yet have. The refusals (a word added
or removed under an unchanged version, an x-code moved, a version going down) are omx-contract's `domain check`, which the
Makefile runs on the new document against the committed one; this script only writes the new document.

    render-domain.py <data dir> <VERSION file> <committed file> <new file>
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


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    data_dir, version_file, committed, out = argv
    version = open(version_file).read().strip()
    old = None
    try:
        old = json.load(open(committed))
    except OSError:
        pass  # no committed document yet: every item is new
    except ValueError:
        old = None  # a file that is no document is only stale
    if old is not None and not isinstance(old.get("components", {}).get("schemas"), dict):
        old = None
    with open(out, "w") as f:
        f.write(render(data_dir, version, old))


main(sys.argv[1:])
