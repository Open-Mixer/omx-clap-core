#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""
The check proper of tests/host-verbs-check.sh, over C sources: no string literal types a verb omx-clap-host answers (the
verbs of ITEMS in plugin-hostd-protocol's domain plugin-hostd-protocol, ruling R5), and no source defines a reply number: a
HOST_REPLY_* or OMX_REPLY_*_RESP define is red, the number is OMX_REPLY_HOST_<NAME>_RESP of
<plugin-hostd/plugin_hostd_protocol_vocabulary.h>.

    host_verbs_source.py <plugin-hostd-protocol.json> <source>...

One line per failure on stderr; the count of declared verbs on stdout. Exit 0 held; 1 a failure; 2 no declaration.
"""
import json
import re
import sys

# token by token: a string literal, a character constant, a comment, a reply define, an identifier, anything else
TOKEN = re.compile(r'("(?:\\.|[^"\\\n])*")|(\'(?:\\.|[^\'\\\n])*\')|(/\*.*?\*/)|(//[^\n]*)'
                   r'|(#define[ \t]+(HOST_REPLY_[A-Z0-9_]+|OMX_REPLY_[A-Z0-9_]+_RESP)\b)|([A-Za-z_][A-Za-z0-9_]*)|(.)', re.S)


# the verbs omx-clap-host answers by its own handlers: the items of the domain plugin-hostd-protocol that ruling R5 moved
# there, word for word, from this tree's domain omx-clap
ITEMS = ('PLUGIN_HOSTD_PROTOCOL_SHARED_VERBS', 'PLUGIN_HOSTD_PROTOCOL_CLAP_HOST_VERBS')


def main():
    decl, files = sys.argv[1], sys.argv[2:]
    with open(decl) as f:
        data = json.load(f)['components']['schemas']
    verbs = set()
    for name in ITEMS:
        item = data.get(name)
        if item is None or item.get('x-kind') != 'verbs':
            print('host-verbs-check: %s declares no verbs item %s' % (decl, name), file=sys.stderr)
            return 2
        verbs |= {w['const'] for w in item['oneOf']}
    alt = '|'.join(re.escape(v) for v in sorted(verbs, key=len, reverse=True))
    # a literal that starts with a verb's word followed by a space or its end, or that holds a verb's word and a conversion
    starts = re.compile(r'^(%s)(?: |$)' % alt)
    inner = re.compile(r'(?<![A-Za-z0-9_])(%s) %%[isf]' % alt)
    bad = 0
    for path in files:
        with open(path, encoding='utf-8', errors='replace') as f:
            text = f.read()
        line = 1
        for m in TOKEN.finditer(text):
            lit, name = m.group(1), m.group(6)
            if lit is not None:
                hit = starts.search(lit[1:-1]) or inner.search(lit[1:-1])
                if hit:
                    print('host-verbs-check: %s:%d: %s types the verb %s by hand: write OMX_VERB_%s or its _FMT of '
                          '<plugin-hostd/plugin_hostd_protocol_host_verbs.h>' % (path, line, lit, hit.group(1), hit.group(1).upper()), file=sys.stderr)
                    bad = 1
            elif name is not None:
                print('host-verbs-check: %s:%d: %s is a reply number defined by hand: write OMX_REPLY_HOST_<NAME>_RESP of '
                      '<plugin-hostd/plugin_hostd_protocol_vocabulary.h>, the resp the domain host declares' % (path, line, name), file=sys.stderr)
                bad = 1
            line += m.group(0).count('\n')
    if bad:
        return 1
    print(len(verbs))
    return 0


if __name__ == '__main__':
    sys.exit(main())
