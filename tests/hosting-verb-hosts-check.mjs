// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
//
// hosting-verb-hosts-check.mjs: the hosts a verb's implementedBy names (V29), declared in data/hosting/verb-hosts.json
// as HOSTING_VERB_HOSTS, the item omx-contract's verbs validator reads (contract.verb.host-unknown).
//
//   node hosting-verb-hosts-check.mjs [<hosting dir>]
//   node hosting-verb-hosts-check.mjs --self-test [<hosting dir>]
//
// The item is a words item of exactly the three golden hosts, each with its text; a missing word, an extra one, a
// changed spelling or an empty text is a failure. The self test applies each of those to a copy and each must fail.
// Exit 0 held; 1 a difference.
import { readFileSync } from 'node:fs';

const args = process.argv.slice(2);
const selfTest = args[0] === '--self-test';
const dir = args.find((a) => !a.startsWith('--')) ?? new URL('../data/hosting', import.meta.url).pathname;
const GOLDEN = { pluginHostd: 'plugin-hostd', omxClapHost: 'omx-clap-host', modHost: 'mod-host' };

function problems(doc) {
  const out = [];
  const item = doc.HOSTING_VERB_HOSTS;
  if (!item) return ['HOSTING_VERB_HOSTS is not declared'];
  if (item.kind !== 'words') out.push('kind is not words');
  const words = item.words ?? {};
  for (const [name, word] of Object.entries(GOLDEN)) {
    if (!words[name]) out.push(`word ${name} is missing`);
    else {
      if (words[name].word !== word) out.push(`word ${name} is not ${word}`);
      if (!words[name].text?.en) out.push(`word ${name} has no en text`);
    }
  }
  for (const name of Object.keys(words)) if (!(name in GOLDEN)) out.push(`word ${name} is not a golden host`);
  return out;
}

let doc;
try {
  doc = JSON.parse(readFileSync(`${dir}/verb-hosts.json`, 'utf8'));
} catch (e) {
  console.log(`FAIL ${dir}/verb-hosts.json: ${e.message}`);
  process.exit(1);
}
const bad = problems(doc);
for (const b of bad) console.log(`FAIL ${b}`);
if (bad.length) process.exit(1);
console.log('ok   HOSTING_VERB_HOSTS holds the three golden hosts');

if (selfTest) {
  const arms = {
    'a word dropped': (d) => delete d.HOSTING_VERB_HOSTS.words.modHost,
    'a word added': (d) => { d.HOSTING_VERB_HOSTS.words.jalv = { word: 'jalv', text: { en: 'jalv' } }; },
    'a spelling changed': (d) => { d.HOSTING_VERB_HOSTS.words.pluginHostd.word = 'plugin_hostd'; },
    'a text emptied': (d) => { d.HOSTING_VERB_HOSTS.words.omxClapHost.text = {}; },
    'the item dropped': (d) => delete d.HOSTING_VERB_HOSTS,
  };
  let failed = 0;
  for (const [arm, apply] of Object.entries(arms)) {
    const copy = structuredClone(doc);
    apply(copy);
    const red = problems(copy).length > 0;
    console.log(`${red ? 'ok  ' : 'FAIL'} sabotage: ${arm} is refused`);
    if (!red) failed++;
  }
  process.exit(failed ? 1 : 0);
}
