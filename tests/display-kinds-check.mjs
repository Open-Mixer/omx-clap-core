// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas
//
// display-kinds-check.mjs — OMX_CLAP_PANEL_DISPLAY_KINDS (src/omx_clap_ext.h) held to omx-panel's DISPLAY_KINDS, the
// vocabulary source: the same words in the same order, each word's code its position.
//
//   node display-kinds-check.mjs [--self-test] <src/omx_clap_ext.h>
//
// omx-panel's tree is OMX_PANEL_DIR (default /usr/share/omx-panel). A tree that is not there is a failure, never a skip.
// --self-test runs the check once clean and once per sabotage of the header as read (a kind dropped, two swapped, one
// renamed); each must be named. Exit 0 held; 1 a difference or no omx-panel; 2 usage.
import { readFileSync, existsSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const selfTest = args[0] === '--self-test';
if (selfTest) args.shift();
if (args.length !== 1) { console.error('usage: display-kinds-check.mjs [--self-test] <src/omx_clap_ext.h>'); process.exit(2); }

const dir = process.env.OMX_PANEL_DIR || '/usr/share/omx-panel';
const module = `${dir}/tools/panel-description.mjs`;
if (!existsSync(module)) {
  console.error(`display-kinds-check: no ${module}: install omx-panel (>= 0.13.8) or set OMX_PANEL_DIR to its tree`);
  process.exit(1);
}
const { DISPLAY_KINDS } = await import(pathToFileURL(module).href);
if (!Array.isArray(DISPLAY_KINDS)) { console.error(`display-kinds-check: ${module} exports no DISPLAY_KINDS`); process.exit(1); }

const text = readFileSync(args[0], 'utf8');
const start = text.indexOf('#define OMX_CLAP_PANEL_DISPLAY_KINDS(X)');
if (start < 0) { console.error('display-kinds-check: no OMX_CLAP_PANEL_DISPLAY_KINDS in ' + args[0]); process.exit(1); }
const body = text.slice(start).split(/\n\s*\n/)[0];
const read = () => [...body.matchAll(/X\((\d+),\s*"([^"]+)",\s*([A-Z_0-9]+)\)/g)].map(m => ({ code: Number(m[1]), word: m[2] }));

// the differences between a header's list and the vocabulary source
function differences(kinds) {
  const bad = [];
  const n = Math.max(kinds.length, DISPLAY_KINDS.length);
  for (let i = 0; i < n; i++) {
    const k = kinds[i], w = DISPLAY_KINDS[i];
    if (!k) bad.push(`omx-panel's DISPLAY_KINDS[${i}] "${w}" is missing from OMX_CLAP_PANEL_DISPLAY_KINDS`);
    else if (w === undefined) bad.push(`OMX_CLAP_PANEL_DISPLAY_KINDS code ${k.code} "${k.word}" is not in omx-panel's DISPLAY_KINDS`);
    else if (k.word !== w) bad.push(`position ${i}: OMX_CLAP_PANEL_DISPLAY_KINDS has "${k.word}", omx-panel's DISPLAY_KINDS "${w}"`);
    else if (k.code !== i) bad.push(`"${k.word}" is code ${k.code} in OMX_CLAP_PANEL_DISPLAY_KINDS, position ${i} in omx-panel's DISPLAY_KINDS`);
  }
  return bad;
}

const kinds = read();
const bad = differences(kinds);
for (const b of bad) console.error('FAIL ' + b);
if (selfTest) {
  const sabotage = {
    'a kind dropped': kinds.slice(0, -1),
    'two kinds swapped': kinds.map((k, i) => (i === 0 ? kinds[1] : i === 1 ? kinds[0] : k)),
    'a kind renamed': kinds.map((k, i) => (i === 0 ? { ...k, word: k.word + 'x' } : k)),
    'a kind added': [...kinds, { code: kinds.length, word: 'extra' }],
  };
  let missed = 0;
  for (const [name, list] of Object.entries(sabotage)) {
    if (differences(list).length === 0) { console.error(`FAIL the check passed with ${name}`); missed++; }
    else console.log(`ok   ${name}: named`);
  }
  if (missed || bad.length) process.exit(1);
}
if (bad.length) process.exit(1);
console.log(`ok   OMX_CLAP_PANEL_DISPLAY_KINDS is omx-panel's DISPLAY_KINDS (${kinds.length} kinds)`);
