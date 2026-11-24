// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
//
// domain-data.mjs — a domain document's codes items in the data form (data/*.json): code, text and args by title.
// The host domain (contract.d/host/host.json, reply.host.*) is a domain since V15, and its Catalan and the other
// languages stay in this tree's catalogs/; code-text-check.mjs reads its codes through this, and the language packs'
// gate (make catalog-gate) stages them beside data/ so `omx-contract translate --check --owner` reads every key the
// catalogs hold.
//
//   node tests/domain-data.mjs <domain.json> <out.json>   writes the domain's codes items as one data file
//
// Exit 0 written; 2 usage.
import { readFileSync, writeFileSync } from 'node:fs';

/** A domain document's codes items as the data form's: code, text and args by title. */
export function fromDomain(doc) {
  const out = {};
  for (const [name, it] of Object.entries(doc.components.schemas)) {
    if ((it['x-kind'] ?? 'codes') !== 'codes' || !it.oneOf) continue;
    out[name] = { kind: 'codes', codes: Object.fromEntries(it.oneOf.map((w) => [w.title, { code: w.const, text: { en: w['x-text'] }, args: w['x-args'] }])) };
  }
  return out;
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  const [src, out] = process.argv.slice(2);
  if (src === undefined || out === undefined || process.argv.length !== 4) {
    console.error('usage: node tests/domain-data.mjs <domain.json> <out.json>');
    process.exit(2);
  }
  writeFileSync(out, JSON.stringify(fromDomain(JSON.parse(readFileSync(src, 'utf8'))), null, 2) + '\n');
}
