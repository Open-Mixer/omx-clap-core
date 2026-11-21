#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""
Where tests/host_verbs_check.py reads the verbs other packages declare for omx-clap-host: plugin-hostd-protocol's are
the words of its domain plugin-hostd (<contractdir>/plugin-hostd/plugin-hostd.json, plugin-hostd#214), and every domain
is read through omx-contract's own reader (domainDataFiles, the rebuild render --with-domain runs), never by a parse of
this tree's.

    host_verbs_domains.py --contract-path <dir>

<dir> is the contract directory make host-verbs-contract stages. Held:
  (a) it holds the domain plugin-hostd and plugin-hostd-protocol as an owner of domains, with no verbs file of its own;
  (b) the declarations of omx-clap-host hold chain of plugin-hostd-protocol, and each domain was read by the rebuild;
  (c) with the domain and its owner left out (the nopkg arm of tests/host_verbs_sabotage.sh), no verb of
      plugin-hostd-protocol is read, and the check's own step for the package is false.
  (d) a stale 3/plugin-hostd-protocol/verbs.json that the package's MANIFEST lists, with a verbs item the domain
      lacks, is never read: the check refuses it by name (the words of plugin-hostd-protocol are its domain's only).
Exit 0 held; 1 a failure.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import host_verbs_check as h  # noqa: E402

PACKAGE = 'plugin-hostd-protocol'
DOMAIN = 'plugin-hostd'
failures = 0


def check(ok, what):
    global failures
    print('%s %s' % ('ok  ' if ok else 'FAIL', what))
    failures += 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--contract-path', required=True)
    path = ap.parse_args().contract_path

    doc = os.path.join(path, DOMAIN, DOMAIN + '.json')
    owner = os.path.join(path, '3', PACKAGE)
    check(os.path.isfile(doc), '(a) the domain %s is staged at %s' % (DOMAIN, doc))
    manifest = {}
    if os.path.isfile(os.path.join(owner, 'MANIFEST.json')):
        with open(os.path.join(owner, 'MANIFEST.json')) as f:
            manifest = json.load(f)
    check(manifest.get('domains') == [DOMAIN] and manifest.get('files') == {},
          '(a) %s owns the domain %s and installs no data file: %s' % (PACKAGE, DOMAIN, manifest))
    check(not os.path.exists(os.path.join(owner, 'verbs.json')), '(a) no verbs.json of %s is staged' % PACKAGE)

    read = []
    rebuild = getattr(h, 'rebuild', None)
    check(rebuild is not None, '(b) host_verbs_check reads a domain through omx-contract\'s rebuild')
    if rebuild is not None:
        def spy(name, p):
            read.append(name)
            return rebuild(name, p)
        h.rebuild = spy
    verbs = h.declarations(path)
    theirs = {v['verb'] for v in verbs if v['package'] == PACKAGE}
    check('chain' in theirs, '(b) chain of %s is declared for %s: %s' % (PACKAGE, h.HOST, sorted(theirs)))
    domains = sorted(d for d in os.listdir(path) if os.path.isfile(os.path.join(path, d, d + '.json')))
    check(sorted(read) == domains, '(b) each domain was read by the rebuild: %s of %s' % (sorted(read), domains))

    work = tempfile.mkdtemp(prefix='host-verbs-domains.')
    try:
        nopkg = os.path.join(work, 'contract.d')
        shutil.copytree(path, nopkg)
        shutil.rmtree(os.path.join(nopkg, DOMAIN))
        shutil.rmtree(os.path.join(nopkg, '3', PACKAGE))
        left = {v['verb'] for v in h.declarations(nopkg) if v['package'] == PACKAGE}
        check(not left, '(c) without the domain no verb of %s is read: %s' % (PACKAGE, sorted(left)))
        check(not h.protocol_installed(nopkg) if hasattr(h, 'protocol_installed') else False,
              '(c) the check\'s step finds %s\'s domain missing' % PACKAGE)
        check(h.protocol_installed(path) if hasattr(h, 'protocol_installed') else False,
              '(c) the check\'s step finds %s\'s domain staged' % PACKAGE)
        stale = os.path.join(work, 'stale')
        shutil.copytree(path, stale)
        owner_dir = os.path.join(stale, '3', PACKAGE)
        with open(os.path.join(owner_dir, 'verbs.json'), 'w') as f:
            json.dump({'PLUGIN_HOSTD_STALE_VERBS': {'kind': 'verbs', 'verbs': {'staleVerb': {
                'verb': 'stale_verb', 'format': 'stale_verb %i', 'reply': 'resp 0', 'codes': [],
                'implementedBy': {h.HOST: 'required'}}}}}, f)
        with open(os.path.join(owner_dir, 'MANIFEST.json')) as f:
            m = json.load(f)
        m['files'] = {'verbs.json': '0' * 64}
        with open(os.path.join(owner_dir, 'MANIFEST.json'), 'w') as f:
            json.dump(m, f)
        refused, read = None, []
        try:
            read = [v['verb'] for v in h.declarations(stale)]
        except Exception as e:  # the refusal, whatever its class: its words name the file
            refused = str(e)
        check(refused is not None and os.path.join('3', PACKAGE, 'verbs.json') in refused,
              '(d) a stale verbs.json of %s is refused by name: %s' % (PACKAGE, refused))
        check('stale_verb' not in read, '(d) no verb of the stale verbs.json is read: %s' % sorted(read))
    finally:
        shutil.rmtree(work)

    print('host_verbs_domains: %s' % ('held' if failures == 0 else '%d failures' % failures))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
