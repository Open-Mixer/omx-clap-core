# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The whole CLAP header vocabulary is mapped by this tree's domain clap: every identifier of inventory/clap.json has
its term in the domain, with its id and its status, and the domain maps no identifier the inventory lacks
(tools/clap_inventory.py, the CLAP half of omx-contract's format coverage check, moved with the terms; sorting pass
V27b). Not tests/clap_coverage.py, which covers the host.

(a) the call: `tools/clap_inventory.py coverage` over the committed domain and inventory exits 0, and the inventory
    holds the 58 headers and 297 identifiers it held in omx-contract;
(b) the inventory is the installed CLAP's, where the CLAP headers are installed (else skipped);
(c) sabotage, each through the same call on a scratch domain or inventory, refused by name: one identifier unmapped, a
    term without its status, a wrong id, a wrong version, an identifier the header does not declare, and a newer CLAP
    installed with one identifier more."""
import copy
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TOOL = os.path.join(ROOT, "tools", "clap_inventory.py")
DOMAIN = os.path.join(ROOT, "contract.d", "clap", "clap.json")
INVENTORY = os.path.join(ROOT, "inventory")

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def run(*args):
    r = subprocess.run([sys.executable, TOOL] + list(args), capture_output=True, text=True)
    return r.returncode, [ln[len("clap_inventory: "):] for ln in r.stderr.splitlines()]


def coverage(tmp, domain=None, inventory=None):
    """the call over the domain and inventory given (the committed ones when None): (exit code, problems)"""
    args = ["coverage"]
    if domain is not None:
        p = os.path.join(tmp, "clap.json")
        json.dump(domain, open(p, "w"))
        args += ["--domain", p]
    if inventory is not None:
        d = os.path.join(tmp, "inv")
        os.makedirs(d, exist_ok=True)
        json.dump(inventory, open(os.path.join(d, "clap.json"), "w"))
        args += ["--inventory", d]
    return run(*args)


def word(doc, item, key):
    return next(w for w in doc["components"]["schemas"][item]["oneOf"] if w["const"] == key)


def main():
    dom = json.load(open(DOMAIN))
    inv = json.load(open(os.path.join(INVENTORY, "clap.json")))
    with tempfile.TemporaryDirectory() as tmp:
        rc, problems = coverage(tmp)  # (a) the call
        check(rc == 0 and problems == [], f"every installed CLAP identifier is mapped by the domain clap ({rc}: {problems[:3]})")
        n = sum(len(v) for v in inv["headers"].values())
        check(len(inv["headers"]) == 58 and n == 297, f"the inventory holds 58 headers and 297 identifiers ({len(inv['headers'])}, {n})")

        if os.path.exists(os.path.join(sys.prefix, "include", "clap")) or os.path.exists("/usr/include/clap/version.h"):  # (b)
            rc, problems = run("--check")
            check(rc == 0, f"the committed inventory is the installed CLAP's ({problems})")
        else:
            print("skip no CLAP headers installed: the inventory is not read again here")

        # (c) sabotage
        item = next(k for k in dom["components"]["schemas"] if k == "CLAP_EXT_PARAMS_TERMS")
        first = dom["components"]["schemas"][item]["oneOf"][0]["const"]
        d = copy.deepcopy(dom)
        s = d["components"]["schemas"][item]
        s["oneOf"] = [w for w in s["oneOf"] if w["const"] != first]
        rc, problems = coverage(tmp, domain=d)
        check(rc == 1 and len(problems) == 1 and problems[0].startswith(f"{item}: CLAP_") and "is not mapped" in problems[0],
              f"sabotage: one identifier unmapped is refused by name ({problems})")
        d = copy.deepcopy(dom)
        del word(d, item, first)["x-term"]["status"]
        check(coverage(tmp, domain=d) == (1, [f"{item}: {first} has no status"]), "sabotage: a term without its status is refused by name")
        d = copy.deepcopy(dom)
        word(d, item, first)["x-term"]["id"] = "CLAP_PARAM_SOMETHING_ELSE"
        rc, problems = coverage(tmp, domain=d)
        check(rc == 1 and len(problems) == 1 and problems[0].startswith(f"{item}: {first} maps CLAP_PARAM_SOMETHING_ELSE"),
              f"sabotage: a wrong id is refused by name ({problems})")
        d = copy.deepcopy(dom)
        d["components"]["schemas"][item]["x-version"] = "0.1.0"
        rc, problems = coverage(tmp, domain=d)
        check(rc == 1 and len(problems) == 1 and problems[0].startswith(f"{item}: version 0.1.0, the installed CLAP is"),
              f"sabotage: a wrong version is refused by name ({problems})")
        d = copy.deepcopy(dom)
        s = d["components"]["schemas"][item]
        s["oneOf"].append(dict(copy.deepcopy(s["oneOf"][0]), const="invented", title="invented", **{"x-code": 999}))
        check(coverage(tmp, domain=d) == (1, [f"{item}: invented is no identifier of the installed clap/ext/params.h"]),
              "sabotage: an identifier the header does not declare is refused by name")
        i = copy.deepcopy(inv)
        i["headers"]["ext/params"].append({"name": "CLAP_PARAM_IS_INVENTED", "group": "clap_param_info_flags", "value": "1 << 30"})
        check(coverage(tmp, inventory=i) == (1, [f"{item}: CLAP_PARAM_IS_INVENTED is not mapped (as paramIsInvented)"]),
              "sabotage: a newer CLAP installed, one identifier more, is refused until it is mapped")

    print(f"{'FAIL' if failures else 'ok  '} clap_inventory_test: {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
