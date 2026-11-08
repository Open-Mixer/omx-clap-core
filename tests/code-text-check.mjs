// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
//
// code-text-check.mjs — every refusal and verdict code this tree declares (data/*.json, data/hosting/*.json: hosting.*
// and reply.host.*, the dimensions and the verbs this repo owns) carries a `text.en` and a `text.ca`, one sentence a
// person can read, with the same `{name}` placeholders in both, each one of `args` (omx-contract's schema, spec 7.11).
// Each file's `requires.omx-contract-schema` floor must be at least 3.11.0, the schema that carries `text` and `args`.
//
//   node tests/code-text-check.mjs              every code of every data file this tree owns
//   node tests/code-text-check.mjs --self-test  drops ca from one code in a scratch copy and requires red
//
// Exit 0 clean; 1 a problem found; 2 usage.
import { readFileSync, readdirSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const FLOOR = [3, 11, 0];

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

function checkFile(path) {
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
      if (!c.text.en) problems.push(`${where}: no text.en`);
      if (!c.text.ca) problems.push(`${where}: no text.ca`);
      if (!c.text.en || !c.text.ca) continue;
      const en = placeholders(c.text.en).sort();
      const ca = placeholders(c.text.ca).sort();
      if (en.join(',') !== ca.join(',')) problems.push(`${where}: text.en and text.ca use different placeholders`);
      const args = c.args || [];
      for (const p of new Set([...en, ...ca])) {
        if (!args.includes(p)) problems.push(`${where}: placeholder {${p}} is not in args`);
      }
    }
  }
  return problems;
}

function runCheck(root) {
  return dataFiles(root).flatMap(checkFile);
}

function selfTest(root) {
  const tmp = mkdtempSync(join(tmpdir(), 'code-text-check-'));
  try {
    const src = join(root, 'data', 'hosting', 'preset.json');
    const victim = join(tmp, 'preset.json');
    writeFileSync(join(tmp, 'placeholder'), '');
    const data = JSON.parse(readFileSync(src, 'utf8'));
    delete data.HOSTING_PRESET_CODES.codes.presetNotFound.text.ca;
    writeFileSync(victim, JSON.stringify(data, null, 2) + '\n');
    const problems = checkFile(victim);
    if (!problems.some((p) => p.includes('no text.ca'))) {
      console.error('code-text-check --self-test: dropping ca did not turn the check red');
      process.exit(1);
    }
    console.log('code-text-check --self-test: ok (dropping ca turned the check red)');
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
  console.log('code-text-check: every declared code carries text.en and text.ca, consistent args, floor >= 3.11.0');
} else {
  console.error('usage: node tests/code-text-check.mjs [--self-test]');
  process.exit(2);
}
