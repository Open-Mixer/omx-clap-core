#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The x-since rule (omx-contract#123, omx-contract#127): an item's x-since is the info.version of its DOMAIN document that
# first carried it, never a release of omx-contract or of a package, never above info.version. Held here for the scan domain
# until omx-contract's `domain check` (3.20.1, validate rule domain-x-since) is the one place that says it.
# usage: domain-x-since-check.py [--self-test] <contract.d of this tree>
import json, os, re, sys

VERSION = re.compile(r'^\d+\.\d+\.\d+$')

def key(v):
    return tuple(int(p) for p in v.split('.'))

def walk(node, path=''):
    if isinstance(node, dict):
        if 'x-since' in node:
            yield path, node['x-since']
        for k, v in node.items():
            yield from walk(v, f'{path}/{k}')
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f'{path}/{i}')

def items(node):  # the nodes that carry an x-since
    if isinstance(node, dict):
        if 'x-since' in node:
            yield '', node
        for v in node.values():
            yield from items(v)
    elif isinstance(node, list):
        for v in node:
            yield from items(v)

def refusals(doc):
    top = doc['info']['version']
    out = []
    for path, since in walk(doc):
        if not isinstance(since, str) or not VERSION.match(since):
            out.append(f'{path}: x-since {since!r} is not a version')
        elif key(since) > key(top):
            out.append(f'{path}: x-since {since} is above info.version {top}')
    return out

args = sys.argv[1:]
self_test = args and args[0] == '--self-test'
real = args[-1]
doc = json.load(open(os.path.join(real, 'scan', 'scan.json')))
bad = refusals(doc)
if self_test:  # the sabotage arms: each must be refused
    text = json.dumps(doc)
    for name, edit in (('x-since above info.version', lambda d: d['info'].update(version='0.0.1')),
                       ('x-since not a version', lambda d: [t.update({'x-since': 'next'}) for _, t in
                                                            list(items(d))[:1]])):
        d = json.loads(text)
        edit(d)
        if not refusals(d):
            bad.append(f'self-test: {name} was not refused')
for b in bad:
    print('domain-x-since-check:', b, file=sys.stderr)
if bad:
    sys.exit(1)
print('domain-x-since-check: ok')
