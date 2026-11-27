#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The x-since rule (omx-contract#123, omx-contract#127) as omx-clap-core reads it (BUILDING.md): a domain under contract.d/
# has a version of its own, like a protocol's (owner ruling 2026-11-25: 0.1.0, rising only when its own words change, never
# the package's VERSION), and an item's x-since is the domain version that first carried it, a version never above
# info.version. Every domain document is held, none skipped.
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
    if not isinstance(top, str) or not VERSION.match(top):
        out.append(f'info.version {top!r} is not a version')
    for path, since in walk(doc):
        if not isinstance(since, str) or not VERSION.match(since):
            out.append(f'{path}: x-since {since!r} is not a version')
        elif VERSION.match(top) and key(since) > key(top):
            out.append(f'{path}: x-since {since} is above info.version {top}')
    return out

def domains(root):
    for name in sorted(os.listdir(root)):
        doc = os.path.join(root, name, f'{name}.json')
        if os.path.isfile(doc):
            yield name, doc

args = sys.argv[1:]
self_test = bool(args) and args[0] == '--self-test'
if self_test:
    args = args[1:]
if len(args) != 1:
    sys.exit('usage: domain-x-since-check.py [--self-test] <contract.d>')
real, = args
bad = []
found = list(domains(real))
if not found:
    bad.append(f'no domain document under {real}')
for name, path in found:
    doc = json.load(open(path))
    bad += [f'{name}: {b}' for b in refusals(doc)]
    if self_test:  # the sabotage arms, planted in every domain: each must be refused
        text = json.dumps(doc)
        for arm, edit in (('info.version not a version',
                           lambda d: d['info'].update(version='next')),
                          ('x-since above info.version',
                           lambda d: [t.update({'x-since': '999.0.0'}) for _, t in list(items(d))[:1]]),
                          ('x-since not a version',
                           lambda d: [t.update({'x-since': 'next'}) for _, t in list(items(d))[:1]])):
            d = json.loads(text)
            edit(d)
            if not refusals(d):
                bad.append(f'self-test: {name}: {arm} was not refused')
for b in bad:
    print('domain-x-since-check:', b, file=sys.stderr)
if bad:
    sys.exit(1)
print(f'domain-x-since-check: ok, {len(found)} domains' + (', every arm refused in each' if self_test else ''))
