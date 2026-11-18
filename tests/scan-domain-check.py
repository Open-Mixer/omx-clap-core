#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# omx-clap-scan reads the scan domain at start-up (omx-contract docs/consumer-move.md, steps 4 and 5, the tests 3, 5 and 6):
# the scopes of its field dump are the words of SCAN_FIELD_SCOPES, read through the loader, never literals of its own.
#   3. a fixture directory with one word changed (param -> parameter) through OMX_CONTRACT_PATH: the dump writes the new word;
#   5. OMX_CONTRACT_PATH is a ':' list standing where the contract directory stands, the first directory holding the domain wins;
#      only a command line reads it (this scanner is one), the library never does;
#   6. a missing, invalid or too-old domain is refused by name at start-up: exit 78, naming the domain and the code.
# usage: scan-domain-check.py <omx-clap-scan> <fake.clap> <contract.d of this tree>
import json, os, re, shutil, subprocess, sys, tempfile

scan, fake, real = sys.argv[1:4]
bad = []
work = tempfile.mkdtemp(prefix='scan-domain.')

def ids(path):
    return [p['id'] for p in json.loads(subprocess.run([scan, '--json', path], check=True, capture_output=True, text=True).stdout)['files'][0]['plugins']]

target = f'clap:{os.path.abspath(fake)}#{ids(fake)[0]}'

def dump(path_var):
    env = {k: v for k, v in os.environ.items() if k != 'OMX_CONTRACT_PATH'}
    if path_var is not None: env['OMX_CONTRACT_PATH'] = path_var
    return subprocess.run([scan, '--fields', target], capture_output=True, text=True, env=env)

def scopes(r):
    return {l.split('\t')[0].split(':')[0] for l in r.stdout.splitlines()[1:] if l and not l.startswith('#')}

def fixture(name, edit):
    d = os.path.join(work, name)
    shutil.copytree(os.path.join(real, 'scan'), os.path.join(d, 'scan'))
    f = os.path.join(d, 'scan', 'scan.json')
    doc = json.load(open(f))
    edit(doc)
    json.dump(doc, open(f, 'w'), indent=2)
    return d

def rename_param(doc):
    for w in doc['components']['schemas']['SCAN_FIELD_SCOPES']['oneOf']:
        if w['const'] == 'param': w['const'] = 'parameter'

# the real domain: the dump writes the declared words
r = dump(real)
if r.returncode != 0: bad.append(f'the real domain: --fields exits {r.returncode}: {r.stderr.strip()}')
elif not {'plugin', 'param', 'audio_out'} <= scopes(r): bad.append(f'the real domain: the dump has scopes {sorted(scopes(r))}')

# 3. one word changed, the dump follows
changed = fixture('changed', rename_param)
r = dump(changed)
if r.returncode != 0: bad.append(f'a changed word: --fields exits {r.returncode}: {r.stderr.strip()}')
else:
    s = scopes(r)
    if 'parameter' not in s: bad.append(f'a changed word: the dump has no "parameter" scope (it has {sorted(s)}): the scopes are literals, not the domain\'s words')
    if 'param' in s: bad.append('a changed word: the dump still writes "param"')

# 5. a ':' list: the first directory that holds the domain wins; a directory without it is passed over
r = dump(f'{os.path.join(work, "nowhere")}:{changed}:{real}')
if r.returncode != 0 or 'parameter' not in scopes(r): bad.append(f'a path list: the first directory holding the domain must win (exit {r.returncode}, scopes {sorted(scopes(r))})')

# 6. refused by name, exit 78
def refused(label, var, code):
    r = dump(var)
    if r.returncode != 78: bad.append(f'{label}: exit {r.returncode}, want 78 ({r.stderr.strip()[:120]})')
    elif not (re.search(r'\bscan\b', r.stderr) and code in r.stderr): bad.append(f'{label}: the refusal does not name the domain "scan" and {code}: {r.stderr.strip()[:200]}')
    elif r.stdout.strip(): bad.append(f'{label}: wrote a dump before refusing')

refused('an absent domain', os.path.join(work, 'nowhere'), 'contract.dir.absent')
def notjson(doc): pass
d = fixture('notjson', notjson)
open(os.path.join(d, 'scan', 'scan.json'), 'w').write('{ not json')
refused('an invalid document', d, 'contract.file.not-json')
d = fixture('wrongid', lambda doc: doc.update({'$id': 'https://openmixer.org/contract/elsewhere'}))
refused('a document of another id', d, 'contract.manifest.invalid')
d = fixture('old', lambda doc: doc['info'].update({'version': '0.0.1'}))
refused('a too-old domain', d, 'contract.package.too-old')
def drop_scope(doc):
    doc['components']['schemas']['SCAN_FIELD_SCOPES']['oneOf'] = [w for w in doc['components']['schemas']['SCAN_FIELD_SCOPES']['oneOf'] if w['const'] != 'role']
d = fixture('missingword', drop_scope)
refused('a domain without a scope the scanner writes', d, 'contract.word.unknown')

shutil.rmtree(work, ignore_errors=True)
if bad:
    print('\n'.join('scan-domain-check: ' + b for b in bad), file=sys.stderr)
    sys.exit(1)
print('scan-domain-check: ok')
