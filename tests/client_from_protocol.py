#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The Python client of the plugin-hostd line protocol, plugin_hostd_client, is the protocol owner's: the package
# python3-plugin-hostd-client of plugin-hostd-protocol (plugin-hostd-protocol issue 45). plugin-hostd builds on this
# repository, so this repository's tests never read it from a plugin-hostd checkout or from plugin-hostd-tests: an
# inside-out build of this host, with the protocol installed and no plugin-hostd, runs its own tests. This holds it:
#   no Python test or bench puts a plugin-hostd path, or PLUGIN_HOSTD_TESTS_LIB, on sys.path for the client
#   (PLUGIN_HOSTD_TESTS_LIB still names plugin-hostd-tests' lib/protocol.sh, the shell client, which stays there);
#   the client imports here, from PLUGIN_HOSTD_CLIENT_DIR (a protocol checkout's clients/python, the developer's
#   override) or the installed package, with no plugin-hostd checkout beside this tree.
#
#   client_from_protocol.py <tree>       0 when the tree is clean and the client imports
#   client_from_protocol.py --self-test  every kind of return, planted in a scratch tree, must be found
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

# a sys.path entry built from a plugin-hostd path (not plugin-hostd-protocol's) or from the tests-lib variable, in code
# (a trailing comment is not read)
HOSTD_PATH = r"sys\.path\.insert\([^\n#]*(plugin-hostd(?!-protocol)|PLUGIN_HOSTD_TESTS_LIB)"


def uncommented(text):
    return [line for line in text.splitlines() if not line.lstrip().startswith("#")]


def path_returns(root):
    found = []
    for pattern in ("tests/**/*.py", "bench/**/*.py"):
        for path in glob.glob(os.path.join(root, pattern), recursive=True):
            if os.path.basename(path) == os.path.basename(__file__):
                continue  # this check plants the strings it looks for in its self-test
            with open(path, encoding="utf-8", errors="replace") as f:
                for n, line in enumerate(f, 1):
                    if re.search(HOSTD_PATH, line.split("#", 1)[0] if not line.lstrip().startswith("#") else ""):
                        found.append("%s:%d: %s" % (os.path.relpath(path, root), n, line.strip()))
    return found


def import_returns(root):
    """the client imports as the tests import it: from PLUGIN_HOSTD_CLIENT_DIR or the installed package, in a working
    directory with no plugin-hostd checkout beside it, PLUGIN_HOSTD_TESTS_LIB unset"""
    env = {k: v for k, v in os.environ.items() if k not in ("PLUGIN_HOSTD_TESTS_LIB", "PYTHONPATH")}
    code = ("import os, sys\n"
            "d = os.environ.get('PLUGIN_HOSTD_CLIENT_DIR')\n"
            "if d: sys.path.insert(0, d)\n"
            "import plugin_hostd_client\n"
            "print(plugin_hostd_client.__file__)\n")
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.run([sys.executable, "-c", code], cwd=cwd, env=env, capture_output=True, text=True)
    if p.returncode != 0:
        return ["plugin_hostd_client does not import from PLUGIN_HOSTD_CLIENT_DIR or an installed python3-plugin-hostd-client: "
                + p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "no import"]
    where = p.stdout.strip()
    if "plugin-hostd/" in where and "plugin-hostd-protocol" not in where:
        return ["plugin_hostd_client imported from a plugin-hostd tree: " + where]
    return []


def check(root):
    return path_returns(root) + import_returns(root)


def self_test():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    failed = 0
    found = path_returns(here)
    if found:
        print("FAIL the control: this tree puts a plugin-hostd path on sys.path for the client", *found, sep="\n  ")
        failed = 1
    arms = [
        ("tests/parity_harness.py", "import plugin_hostd_client",
         "sys.path.insert(0, os.path.join(here, '..', '..', 'plugin-hostd', 'tests', 'lib'))\nimport plugin_hostd_client",
         "a plugin-hostd checkout's tests/lib on sys.path"),
        ("tests/parity_harness.py", "import plugin_hostd_client",
         "sys.path.insert(0, os.environ.get('PLUGIN_HOSTD_TESTS_LIB'))\nimport plugin_hostd_client",
         "PLUGIN_HOSTD_TESTS_LIB on sys.path for the client"),
    ]
    for rel, before, after, what in arms:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "tests"))
            shutil.copy(os.path.join(here, rel), os.path.join(tmp, rel))
            path = os.path.join(tmp, rel)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            if before not in text:
                print("FAIL %s: the arm no longer applies" % what)
                failed = 1
                continue
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace(before, after, 1))
            if path_returns(tmp):
                print("ok   %s is found" % what)
            else:
                print("FAIL %s is not found" % what)
                failed = 1
    # the import arm: with no client reachable the check says so
    saved = os.environ.pop("PLUGIN_HOSTD_CLIENT_DIR", None)
    try:
        with tempfile.TemporaryDirectory() as empty:
            os.environ["PLUGIN_HOSTD_CLIENT_DIR"] = os.path.join(empty, "nothing")
            missing = import_returns(here)
    finally:
        if saved is None:
            os.environ.pop("PLUGIN_HOSTD_CLIENT_DIR", None)
        else:
            os.environ["PLUGIN_HOSTD_CLIENT_DIR"] = saved
    # an empty override still falls back to an installed package: only a tree with none installed can see this arm red
    if missing or not import_returns(here):
        print("ok   a client that does not import is named (or the installed package answers here)")
    else:
        print("FAIL the import check saw neither a client nor its absence")
        failed = 1
    print("client_from_protocol self-test: %s" % ("FAILED" if failed else "ok"))
    return failed


def main(argv):
    if argv[1:] == ["--self-test"]:
        return self_test()
    if len(argv) != 2:
        print("usage: client_from_protocol.py <tree> | --self-test")
        return 2
    found = check(os.path.abspath(argv[1]))
    if found:
        print("FAIL the client is not the protocol's here:", *found, sep="\n  ")
        return 1
    print("ok: the tests import plugin_hostd_client from PLUGIN_HOSTD_CLIENT_DIR or python3-plugin-hostd-client, never from plugin-hostd")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
