#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""clap_inventory.py: the inventory of the CLAP headers as installed, and the coverage of this tree's domain clap.

The inventory (inventory/clap.json) is every identifier the CLAP headers declare, with the version they were read from;
it is written by this tool and never edited by hand. The domain clap (contract.d/clap/clap.json) maps it header by
header: every installed CLAP identifier is mapped, with its status, and no identifier is mapped that the inventory
lacks. Moved from omx-contract's tools/format-inventory.mjs (its CLAP half) and tools/data-layout.mjs
(coverageProblems, CLAP half) with the terms themselves (sorting pass, V27b); the inventory is byte for byte the one
that tool writes.

  python3 tools/clap_inventory.py [--clap <include dir>] [--out <dir>] [--check]   write or check inventory/clap.json
  python3 tools/clap_inventory.py coverage [--inventory <dir>] [--domain <clap.json>]

--clap defaults to pkg-config's includedir for clap (else /usr/include). The headers are read as text. Exit 0 written,
equal or covered; 1 a difference or a coverage problem (each named) or a source that cannot be read; 2 usage."""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INVENTORY = os.path.join(ROOT, "inventory")
DOMAIN = os.path.join(ROOT, "contract.d", "clap", "clap.json")


def strip_comments(s):
    return re.sub(r"//[^\n]*", " ", re.sub(r"/\*[\s\S]*?\*/", " ", s))


def is_plumbing(name):
    """the plumbing macros of the CLAP headers: compiler and ABI spellings, include guards"""
    return bool(re.search(r"^(CLAP_(ABI|EXPORT|CONSTEXPR|NODISCARD|CPLUSPLUS|HAS_CXX\d*|VERSION_INIT))$|_H$", name))


RX = re.compile("|".join([
    r'const\s+(?:CLAP_CONSTEXPR\s+)?char\s+(CLAP_\w+)\s*\[\]\s*=\s*"([^"]*)"\s*;',
    r'#\s*define\s+(CLAP_\w+)[ \t]+"([^"]*)"',
    r"#\s*define\s+(CLAP_\w+)[ \t]+(\d+)\b",
    r"static\s+const\s+CLAP_CONSTEXPR\s+(?!char\b)\w+\s+(CLAP_\w+)\s*=\s*([^;]+);",
    r"\benum\s*(\w*)\s*\{([^}]*)\}",
]))


def read_header(text):
    """one CLAP header's identifiers: [{name, group, value}], in the order the header declares them. A string constant
    (an extension, factory, port-type or window-API id, a plugin feature) is group "string" with its text; a member of
    an enum is the enum's tag, or "enum" when it has none, with its value as written; a typed constant is "const" and a
    numeric #define "define", each with its value as written"""
    src = strip_comments(text)
    out, seen = [], set()

    def add(o):
        if o["name"] not in seen and not is_plumbing(o["name"]):
            seen.add(o["name"])
            out.append(o)

    for m in RX.finditer(src):
        if m.group(1):
            add({"name": m.group(1), "group": "string", "value": m.group(2)})
        elif m.group(3):
            add({"name": m.group(3), "group": "string", "value": m.group(4)})
        elif m.group(5):
            add({"name": m.group(5), "group": "define", "value": m.group(6)})
        elif m.group(7):
            add({"name": m.group(7), "group": "const", "value": re.sub(r"\s+", " ", m.group(8).strip())})
        else:
            group = m.group(9) or "enum"
            for part in m.group(10).split(","):
                e = re.match(r"^\s*(CLAP_\w+)\s*(?:=\s*([\s\S]+?))?\s*$", part)
                if e:
                    add({"name": e.group(1), "group": group,
                         "value": None if e.group(2) is None else re.sub(r"\s+", " ", e.group(2))})
    return out


def read_clap(include):
    """every header under <include>/clap, its private/ ones left out: {version, headers: {<path>: [...]}}"""
    root = os.path.join(include, "clap")
    if not os.path.exists(root):
        raise ValueError(f"no {root}")
    files = []
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "private")
        files += [os.path.join(base, n) for n in sorted(names) if n.endswith(".h")]
    headers = {}
    for p in sorted(files, key=lambda p: os.path.relpath(p, root)):
        ids = read_header(open(p, encoding="utf-8").read())
        if ids:
            headers[re.sub(r"\.h$", "", os.path.relpath(p, root))] = ids
    v = {i["name"]: i["value"] for i in headers.get("version", []) if i["group"] == "define"}
    if not v.get("CLAP_VERSION_MAJOR"):
        raise ValueError(f"{root}/version.h: no CLAP_VERSION_MAJOR")
    return {"version": f"{v['CLAP_VERSION_MAJOR']}.{v['CLAP_VERSION_MINOR']}.{v['CLAP_VERSION_REVISION']}", "headers": headers}


def default_include():
    try:
        r = subprocess.run(["pkg-config", "--variable=includedir", "clap"], capture_output=True, text=True)
    except OSError:
        return "/usr/include"
    return (r.stdout.strip() or "/usr/include") if r.returncode == 0 else "/usr/include"


def inventory_text(include=None):
    """inventory/clap.json as the tool writes it, from the CLAP headers installed under include"""
    doc = {"format": "clap", "from": "the CLAP headers (clap package), private/ left out", **read_clap(include or default_include())}
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def path_name(p):
    return re.sub(r"[^A-Za-z0-9]+", "_", p).upper()


def clap_name(ident, group, value):
    """a CLAP identifier's name in its item: a string constant's text less clap., any other in lowerCamel less CLAP_"""
    if group == "string":
        return value[5:] if value.startswith("clap.") else value
    parts = ident[5:].lower().split("_")
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def coverage_problems(schemas, inventory):
    """the coverage problems of the domain clap's items (its components.schemas) against the inventory: [message]"""
    out, mapped = [], set()
    for h, ids in inventory["headers"].items():
        want_item = f"CLAP_{path_name(h)}_TERMS"
        it = schemas.get(want_item)
        if not it or it.get("x-kind") != "terms":
            out.append(f"{want_item}: the CLAP header clap/{h}.h is not mapped")
            continue
        mapped.add(want_item)
        if it.get("x-version") != inventory["version"]:
            out.append(f"{want_item}: version {it.get('x-version')}, the installed CLAP is {inventory['version']}")
        terms = {w["const"]: w.get("x-term", {}) for w in it["oneOf"]}
        want = {clap_name(i["name"], i["group"], i["value"]): i for i in ids}
        for n, i in want.items():
            m = terms.get(n)
            if m is None:
                out.append(f"{want_item}: {i['name']} is not mapped (as {n})")
            elif m.get("id") != i["name"] or (i["group"] == "string" and m.get("value") != i["value"]):
                out.append(f"{want_item}: {n} maps {m.get('id')} {m.get('value', '')}, the identifier is {i['name']} "
                           f"{i['value'] if i['group'] == 'string' else ''}")
            elif not m.get("status"):
                out.append(f"{want_item}: {n} has no status")
        for n in terms:
            if n not in want:
                out.append(f"{want_item}: {n} is no identifier of the installed clap/{h}.h")
    for n, it in schemas.items():
        if it.get("x-kind") == "terms" and n not in mapped:
            out.append(f"{n}: maps no installed header")
    return out


def main(argv):
    if argv[:1] == ["coverage"]:
        inv_dir, dom = INVENTORY, DOMAIN
        args = argv[1:]
        while args:
            a = args.pop(0)
            if a == "--inventory" and args:
                inv_dir = args.pop(0)
            elif a == "--domain" and args:
                dom = args.pop(0)
            else:
                print(f"clap_inventory: unknown argument {a}", file=sys.stderr)
                return 2
        problems = coverage_problems(json.load(open(dom))["components"]["schemas"],
                                     json.load(open(os.path.join(inv_dir, "clap.json"))))
        for p in problems:
            print(f"clap_inventory: {p}", file=sys.stderr)
        if not problems:
            print("clap_inventory: every installed CLAP identifier is mapped by the domain clap, with its status, and nothing more")
        return 1 if problems else 0
    include, out, check = None, INVENTORY, False
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--check":
            check = True
        elif a in ("--clap", "--out") and args:
            v = args.pop(0)
            if a == "--out":
                out = v
            else:
                include = v
        else:
            print(f"clap_inventory: unknown argument {a}", file=sys.stderr)
            return 2
    try:
        text = inventory_text(include)
    except (OSError, ValueError) as e:
        print(f"clap_inventory: {e}", file=sys.stderr)
        return 1
    p = os.path.join(out, "clap.json")
    if not check:
        os.makedirs(out, exist_ok=True)
        with open(p, "w") as f:
            f.write(text)
        print(f"clap_inventory: wrote {p}")
        return 0
    have = open(p).read() if os.path.exists(p) else ""
    if have != text:
        print(f"clap_inventory: {p} is not the inventory of the installed CLAP: run python3 tools/clap_inventory.py and map "
              "what changed", file=sys.stderr)
        return 1
    print("clap_inventory: the committed inventory is the installed CLAP's")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
