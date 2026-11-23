#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The x-since rule (omx-contract#123, omx-contract#127) as omx-clap-core reads it (#123, BUILDING.md): every domain under
# contract.d/ is versioned with the package, its info.version is VERSION, and an item's x-since is the omx-clap-core
# release that first shipped it, a version never above info.version. Every domain document is held, none skipped.
# usage: domain-x-since-check.py [--self-test] <package version> <contract.d of this tree>
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

def refusals(doc, package):
    top = doc['info']['version']
    out = []
    if top != package:
        out.append(f'info.version {top} is not the package version {package}')
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
if len(args) != 2 or not VERSION.match(args[0]):
    sys.exit('usage: domain-x-since-check.py [--self-test] <package version> <contract.d>')
package, real = args
bad = []
found = list(domains(real))
if not found:
    bad.append(f'no domain document under {real}')
for name, path in found:
    doc = json.load(open(path))
    bad += [f'{name}: {b}' for b in refusals(doc, package)]
    if self_test:  # the sabotage arms, planted in every domain: each must be refused
        text = json.dumps(doc)
        for arm, edit in (('info.version not the package version',
                           lambda d: d['info'].update(version='0.0.1' if package != '0.0.1' else '0.0.2')),
                          ('x-since above info.version',
                           lambda d: [t.update({'x-since': '999.0.0'}) for _, t in list(items(d))[:1]]),
                          ('x-since not a version',
                           lambda d: [t.update({'x-since': 'next'}) for _, t in list(items(d))[:1]])):
            d = json.loads(text)
            edit(d)
            if not refusals(d, package):
                bad.append(f'self-test: {name}: {arm} was not refused')
for b in bad:
    print('domain-x-since-check:', b, file=sys.stderr)
if bad:
    sys.exit(1)
print(f'domain-x-since-check: ok, {len(found)} domains at {package}' + (', every arm refused in each' if self_test else ''))
