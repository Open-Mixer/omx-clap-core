// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
//
// code-text-check.mjs — every refusal and verdict code this tree declares (data/*.json, data/hosting/*.json: hosting.*
// and reply.host.*, the dimensions and the verbs this repo owns) carries `text.en`, its English source sentence and
// nothing else, and its Catalan in catalogs/ca.json under the code, with the same `{name}` placeholders, each one of
// `args` (omx-contract 3.12.0, spec 7.11, omx-contract#90). The catalog holds no key that is not a code of ours. Each
// file's `requires.omx-contract-schema` floor must be at least 3.12.0, the schema that has catalogs.
//
//   node tests/code-text-check.mjs              every code of every data file this tree owns
//   node tests/code-text-check.mjs --self-test  drops one code's Catalan from a scratch catalog and requires red
//
// Exit 0 clean; 1 a problem found; 2 usage.
import { readFileSync, readdirSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const FLOOR = [3, 12, 0];

function dataFiles(root) {
  const files = readdirSync(join(root, 'data')).filter((f) => f.endsWith('.json')).map((f) => join(root, 'data', f));
  for (const f of readdirSync(join(root, 'data', 'hosting'))) {
    if (f.endsWith('.json')) files.push(join(root, 'data', 'hosting', f));
  }
  return files;
}

function placeholders(s) {
  return [...s.matchAll(/\{([a-zA-Z0-9]+)\}/g)].map((m) => m[1]);
}

function floorOf(req) {
  const m = /^>=\s*([0-9]+)\.([0-9]+)\.([0-9]+)$/.exec(req || '');
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
}

function below(a, b) {
  for (let i = 0; i < 3; i++) { if (a[i] !== b[i]) return a[i] < b[i]; }
  return false;
}

function checkFile(path, messages, seen = new Set()) {
  const problems = [];
  const data = JSON.parse(readFileSync(path, 'utf8'));
  const floor = floorOf(data.requires && data.requires['omx-contract-schema']);
  if (!floor) problems.push(`${path}: requires.omx-contract-schema is not a plain ">= x.y.z" floor`);
  else if (below(floor, FLOOR)) problems.push(`${path}: requires.omx-contract-schema floor ${floor.join('.')} is below ${FLOOR.join('.')}`);
  for (const [itemName, item] of Object.entries(data)) {
    if (!item || item.kind !== 'codes') continue;
    for (const [name, c] of Object.entries(item.codes)) {
      const where = `${path} ${itemName}.${name} (${c.code})`;
      if (!c.text) { problems.push(`${where}: no text`); continue; }
      seen.add(c.code);
      if (!c.text.en) problems.push(`${where}: no text.en`);
      if (Object.keys(c.text).some((k) => k !== 'en')) problems.push(`${where}: text holds ${Object.keys(c.text).join(', ')}; the source sentence en alone, a translation is catalogs/<lang>.json`);
      // an entry is the sentence, or {text, by[, model, source]} with its provenance (omx-contract 3.16.0)
      const entry = messages[c.code];
      const caText = typeof entry === 'string' || entry === undefined ? entry : entry.text;
      if (caText === undefined) problems.push(`${where}: no Catalan in catalogs/ca.json`);
      if (!c.text.en || caText === undefined) continue;
      const en = placeholders(c.text.en).sort();
      const ca = placeholders(caText).sort();
      if (en.join(',') !== ca.join(',')) problems.push(`${where}: text.en and its Catalan use different placeholders`);
      const args = c.args || [];
      for (const p of new Set([...en, ...ca])) {
        if (!args.includes(p)) problems.push(`${where}: placeholder {${p}} is not in args`);
      }
    }
  }
  return problems;
}

function catalogOf(path) {
  const c = JSON.parse(readFileSync(path, 'utf8'));
  const problems = [];
  if (c.kind !== 'catalog' || c.lang !== 'ca' || c.owner !== 'omx-clap-core') problems.push(`${path}: not the Catalan catalog of omx-clap-core`);
  return { messages: c.messages ?? {}, problems };
}

function runCheck(root, catalogPath = join(root, 'catalogs', 'ca.json')) {
  const { messages, problems } = catalogOf(catalogPath);
  const seen = new Set();
  problems.push(...dataFiles(root).flatMap((f) => checkFile(f, messages, seen)));
  for (const key of Object.keys(messages)) if (!seen.has(key)) problems.push(`${catalogPath}: ${key} is no code of ours`);
  return problems;
}

function selfTest(root) {
  const tmp = mkdtempSync(join(tmpdir(), 'code-text-check-'));
  try {
    const cat = JSON.parse(readFileSync(join(root, 'catalogs', 'ca.json'), 'utf8'));
    const code = JSON.parse(readFileSync(join(root, 'data', 'hosting', 'preset.json'), 'utf8')).HOSTING_PRESET_CODES.codes.presetNotFound.code;
    const arms = [
      ['a code with no Catalan', (c) => { delete c.messages[code]; }, 'no Catalan'],
      ['a catalog key that is no code', (c) => { c.messages['hosting.zz.gone'] = 'Ja no hi és.'; }, 'no code of ours'],
    ];
    for (const [name, edit, want] of arms) {
      const c = structuredClone(cat);
      edit(c);
      const victim = join(tmp, 'ca.json');
      writeFileSync(victim, JSON.stringify(c, null, 2) + '\n');
      if (!runCheck(root, victim).some((p) => p.includes(want))) {
        console.error(`code-text-check --self-test: ${name} did not turn the check red`);
        process.exit(1);
      }
    }
    if (runCheck(root).length) {
      console.error('code-text-check --self-test: the tree as it is is red');
      process.exit(1);
    }
    console.log('code-text-check --self-test: ok (a code with no Catalan and a catalog key that is no code each turned the check red)');
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

const root = new URL('..', import.meta.url).pathname.replace(/\/$/, '');
if (process.argv[2] === '--self-test') {
  selfTest(root);
} else if (process.argv[2] === undefined) {
  const problems = runCheck(root);
  if (problems.length) {
    for (const p of problems) console.error(p);
    console.error(`code-text-check: ${problems.length} problem(s)`);
    process.exit(1);
  }
  console.log('code-text-check: every declared code carries its source sentence and its Catalan in catalogs/ca.json, consistent args, floor >= 3.12.0');
} else {
  console.error('usage: node tests/code-text-check.mjs [--self-test]');
  process.exit(2);
}
