#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The numbers a controller branches on are named in HOST_REPLY_CODES (data/verbs.json), so a table built from the
vocabularies (plugin-hostd-protocol's reply_codes) names them: -2, the instance number already taken, answered by add
(omx-clap-core#34), is reply.host.instance-already-exists, with its English sentence and no args.

  tests/host-reply-codes-check.py [--self-test]
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# resp -> code: the numbers this check holds the vocabulary to
WANT = {-2: "reply.host.instance-already-exists"}


def problems(verbs):
    codes = verbs.get("HOST_REPLY_CODES", {}).get("codes", {})
    by_resp = {c.get("resp"): c for c in codes.values() if isinstance(c, dict)}
    out = []
    for resp, code in sorted(WANT.items()):
        c = by_resp.get(resp)
        if c is None:
            out.append("HOST_REPLY_CODES names no code for resp %d (want %s)" % (resp, code))
            continue
        if c.get("code") != code:
            out.append("resp %d is %s, want %s" % (resp, c.get("code"), code))
        if not ((c.get("text") or {}).get("en") or "").strip():
            out.append("%s has no English sentence" % code)
    return out


def main():
    with open(os.path.join(ROOT, "data", "verbs.json")) as f:
        verbs = json.load(f)
    if "--self-test" in sys.argv:
        broken = copy.deepcopy(verbs)
        broken["HOST_REPLY_CODES"]["codes"] = {k: v for k, v in broken["HOST_REPLY_CODES"]["codes"].items()
                                               if not (isinstance(v, dict) and v.get("resp") == -2)}
        if not problems(broken):
            print("host-reply-codes-check --self-test: a table without -2 was not refused", file=sys.stderr)
            return 1
        print("host-reply-codes-check --self-test: ok (a table without -2 is refused)")
        return 0
    bad = problems(verbs)
    for p in bad:
        print("host-reply-codes-check: " + p, file=sys.stderr)
    if not bad:
        print("host-reply-codes-check: %s" % ", ".join("%d is %s" % kv for kv in sorted(WANT.items())))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
