#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# published-comp-scan.py: omx-clap-scan states what a published plugin exports through clap.meters/1 and
# org.openmixer.param-contract/1, held by value on omx-plugins' omx-comp.clap as its package installs it.
#
#   published-comp-scan.py <omx-clap-scan> <omx-comp.clap>
#
# omx-comp declares four meters, in this order (its declaration's `meters`, the CLAP meter id the index): compGr, a
# linked gain reduction; compIn and compOut, stereo levels; compKey, the key's level. Its contract states each
# parameter's symbol, unit, scale and step. The scan must print both, as text and as JSON, with these values; a scan
# that reads neither (every omx-clap-scan up to 0.31.1) fails here, on the first missing word.
# Exit 0 held; 1 a value missing or different; 2 usage or the scan failed.
import json
import re
import subprocess
import sys

PLUGIN_ID = 'org.openmixer.comp'
# id, name, kind, channels: the meters as omx-comp declares them
METERS = [(0, 'compGr', 'gain-reduction', 1), (1, 'compIn', 'level', 2), (2, 'compOut', 'level', 2),
          (3, 'compKey', 'level', 1)]
# parameter name, contract symbol, unit, scale: the parameters the panel's dynamics roles read
CONTRACT = [('Threshold', 'thresholdDb', 'db', 'stepped'), ('Ratio', 'ratio', 'none', 'linear'),
            ('Attack', 'attackMs', 'ms', 'linear'), ('Release', 'releaseMs', 'ms', 'stepped')]

failures = []


def expect(ok, what):
    if not ok:
        failures.append(what)


def scan(prog, path, *args):
    out = subprocess.run([prog, *args, path], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f'published-comp-scan: {prog} {" ".join(args)} {path} exited {out.returncode}: {out.stderr.strip()[:300]}')
    return out.stdout


def main(argv):
    if len(argv) != 3:
        print('usage: published-comp-scan.py <omx-clap-scan> <omx-comp.clap>', file=sys.stderr)
        return 2
    prog, path = argv[1], argv[2]
    doc = json.loads(scan(prog, path, '--json'))
    plugins = [p for f in doc.get('files', []) for p in f.get('plugins', []) if p.get('id') == PLUGIN_ID]
    if len(plugins) != 1:
        sys.exit(f'published-comp-scan: {path} holds no single {PLUGIN_ID}')
    p = plugins[0]

    # JSON: the meters, by value
    meters = p.get('meters')
    expect(isinstance(meters, list), 'json: the plugin has no "meters" list')
    meters = meters if isinstance(meters, list) else []
    got = [(m.get('id'), m.get('name'), m.get('kind'), m.get('channels')) for m in meters]
    expect(got == METERS, f'json: meters {got}, expected {METERS}')
    for m in meters:
        lo, hi = m.get('min'), m.get('max')
        expect(isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo < hi,
               f'json: meter {m.get("name")} has no display range min < max ({lo}, {hi})')

    # JSON: the contract, whole and per parameter
    pc = p.get('param_contract')
    expect(isinstance(pc, dict), 'json: the plugin has no "param_contract"')
    pc = pc if isinstance(pc, dict) else {}
    expect(isinstance(pc.get('version'), int) and pc.get('version') >= 1, f'json: contract version {pc.get("version")}')
    expect(isinstance(pc.get('fingerprint'), str) and re.fullmatch(r'[0-9a-f]{64}', pc.get('fingerprint') or ''),
           f'json: contract fingerprint {pc.get("fingerprint")!r} is not 64 lowercase hex')
    by_name = {q.get('name'): q for q in p.get('params', [])}
    for name, symbol, unit, scale in CONTRACT:
        c = (by_name.get(name) or {}).get('contract')
        expect(isinstance(c, dict), f'json: parameter {name} has no "contract"')
        c = c if isinstance(c, dict) else {}
        expect((c.get('symbol'), c.get('unit'), c.get('scale')) == (symbol, unit, scale),
               f'json: parameter {name} contract {(c.get("symbol"), c.get("unit"), c.get("scale"))}, '
               f'expected {(symbol, unit, scale)}')
    expect(all(isinstance(q.get('contract'), dict) for q in p.get('params', [])),
           'json: a parameter clap.params lists has no contract entry (the contract is whole or absent)')

    # text: the same words, one line per meter and per parameter's contract
    text = scan(prog, path)
    for mid, name, kind, ch in METERS:
        expect(re.search(rf'^\s+meter {mid} "{name}" {kind} {ch} channels? \[', text, re.M),
               f'text: no line "meter {mid} "{name}" {kind} {ch} channel(s) [min .. max]"')
    expect(re.search(r'^\s+contract version \d+ fingerprint [0-9a-f]{64}$', text, re.M),
           'text: no line "contract version <n> fingerprint <sha256>"')
    for name, symbol, unit, scale in CONTRACT:
        expect(re.search(rf'^\s+param \d+ {name} .*\n\s+contract {symbol} {unit} {scale} step ', text, re.M),
               f'text: parameter {name} is not followed by "contract {symbol} {unit} {scale} step <s>"')

    for f in failures:
        print(f'FAIL {f}')
    print(f'published-comp-scan: {len(failures)} failure(s) on {path}' if failures
          else f'published-comp-scan: held on {path} ({len(METERS)} meters, {len(CONTRACT)} contract rows by value)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
