#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# contract-dir-check.sh — omx-clap's definitions read back through omx-contract's reader, and every file this
# tree commits as their render held to it.
#
#   contract-dir-check.sh <omx-contract checkout> <contract dir> <version>
#
# <contract dir> holds omx-clap's package as `make install-contract` wrote it. omx-contract's own data/ is
# installed beside it from the checkout (its npm ci done), the directory is validated with omx-clap required at
# <version>, and the package's own renders (`render --package omx-clap`: the headers and modules the `render` word of
# data/hosting.json and the hosting domain's x-render frame, the vocabulary of the hosting domain's data/hosting/ items, of
# data/hosting/ and of the host and omx-clap domains, and the verbs of the omx-clap domain) are compared with the files this
# tree commits, byte for byte: a header with src/<header>, a TypeScript module with ts/<module>.js and .d.ts. A committed render the output
# lacks, or an output this tree does not commit, is a failure too.
# Exit 0 equal; 1 a refusal or a difference; 2 usage.
set -eu

[ "$#" -eq 3 ] || { sed -n '8p' "$0" >&2; exit 2; }
oc=$1 dir=$2 version=$3
[ -f "$oc/bin/omx-contract.mjs" ] || { echo "contract-dir-check: no omx-contract checkout at $oc" >&2; exit 2; }
[ -f "$dir/3/omx-clap/MANIFEST.json" ] || { echo "contract-dir-check: no omx-clap package under $dir/3" >&2; exit 2; }
tool="node $oc/bin/omx-contract.mjs"
work=$(dirname "$dir")

# omx-contract's own package, less its reader's table (codes.json) and its golden vectors (scale-vectors.json), as omx-contract installs itself
ocv=$(sed -n 's/^  "version": "\([0-9.]*\)",$/\1/p' "$oc/package.json")
sh "${OMX_CONTRACT_SCRIPT:-$oc/tools/install-contract-dir.sh}" -x codes.json -x scale-vectors.json omx-contract "$ocv" 3 "$oc/data" "$dir" data
# omx-contract's own domains (the param domain: PARAM_UNITS and PARAM_SCALES, the standard words the mappings name)
for d in "$oc"/contract.d/*/; do
  [ -d "$d" ] && sh "${OMX_CONTRACT_SCRIPT:-$oc/tools/install-contract-dir.sh}" --domain "${d%/}" "$dir" omx-contract
done

# the domains of this owner that rebuild data files, in one read (--with-domain repeats): the code sheets, the host words,
# the verbs and the hosting codes (their one home, omx-contract#215: the codes header's render word, which spells
# CLAP_HOST_CODE_<NAME>, travels with them)
with="--with-domain $dir/omx-param-contract --with-domain $dir/omx-clap-scale --with-domain $dir/host --with-domain $dir/omx-clap --with-domain $dir/hosting"

# the read validates with omx-clap at <version> and its catalogs, every code they translate one omx-clap declares: the
# hosting codes are omx-clap's through --with-domain, as every render of them reads them
$tool validate --contract-dir "$dir" --needs "omx-clap@>= $version" --catalogs catalogs $with

# every impl link of the package's items names code that reads the item (contract.source.unread names the code and the
# link), found from this tree's root; the hosting codes' links among them, read through --with-domain
$tool links --check --root . --contract-dir "$dir" $with --package omx-clap

# the renders this tree commits, as <target>:<committed path>; the output's name is the committed file's
committed='c:src/clap_host_limits.h c:src/hosted_stage_limits.h c:src/omx_clap_vocabulary.h c:src/omx_clap_host_verbs.h c:src/omx_param_units.h c:src/omx_param_unit_ids.h c:src/omx_param_scales.h ts:ts/omx-clap-hosting.js ts:ts/omx-clap-hosting.d.ts ts:ts/omx-clap-hosting-codes.js ts:ts/omx-clap-hosting-codes.d.ts ts:ts/omx-clap-vocabulary.js ts:ts/omx-clap-vocabulary.d.ts'

bad=0
for target in c ts; do
  rm -rf "$work/$target"
  $tool render --target "$target" --package omx-clap --out "$work/$target" --contract-dir "$dir" $with
  for out in "$work/$target"/*; do
    name=$(basename "$out")
    path=
    for c in $committed; do
      [ "${c%%:*}" = "$target" ] && [ "$(basename "${c#*:}")" = "$name" ] && path=${c#*:}
    done
    [ -n "$path" ] || { echo "contract-dir-check: the $target render writes $name, which this tree does not commit" >&2; bad=1; continue; }
    if ! cmp -s "$path" "$out"; then
      diff -u "$path" "$out" >&2 || true
      echo "contract-dir-check: $path is not the render of data/" >&2
      bad=1
    fi
  done
done
for c in $committed; do
  [ -f "$work/${c%%:*}/$(basename "${c#*:}")" ] || { echo "contract-dir-check: the ${c%%:*} render has no $(basename "${c#*:}")" >&2; bad=1; }
done
[ "$bad" -eq 0 ] || exit 1
# the program hands the LV2 adapter the declared worker numbers, by name: every assignment of them in src/ reads
# hosted_stage_limits.h's define, which the render above holds to data/hosting.json
for f in worker_poll_us:WORKER_POLL_US worker_ring_bytes:WORKER_RING_BYTES; do
  set -- $(grep -rhE "\.${f%%:*} = " src/*.c | sed 's/^ *//' | sort -u)
  [ "$*" = "config.${f%%:*} = OMX_HOSTED_STAGE_${f#*:};" ] || {
    echo "contract-dir-check: src/ sets ${f%%:*} from \"$*\", not from the declared OMX_HOSTED_STAGE_${f#*:}" >&2; exit 1; }
done
# each module loads as an ES module and exports its files' items, nothing else: the hosting module data/hosting.json's,
# the hosting codes module the hosting domain's root x-file's (the idle and window codes), the vocabulary module every
# item of data/hosting/, the hosting domain's items of data/hosting/ and the codes and words of the host and omx-clap
# domains, a words item with its _WORDS; a domain item with no x-file (OMX_CLAP_REPLIES) is read at run time only: it
# rebuilds no data file, so no module exports it
for m in omx-clap-hosting:HOSTED_STAGE_LIMITS omx-clap-hosting-codes:HOSTING_IDLE_CODES,HOSTING_WINDOW_CODES; do
  node --input-type=module -e "import('$(pwd)/ts/${m%%:*}.js').then((m) => { const k = Object.keys(m).sort().join(','); if (k !== '${m#*:}') { console.error('contract-dir-check: ts/${m%%:*}.js exports ' + k + ', not ${m#*:}'); process.exit(1); } })"
done
node --input-type=module -e "
import { readdirSync, readFileSync } from 'node:fs';
const own = (f, only = (v) => f.startsWith('data/') || v['x-file'] !== undefined) => { const d = JSON.parse(readFileSync(f, 'utf8')); const items = f.startsWith('data/') ? d : d.components.schemas; return Object.entries(items).filter(([k, v]) => !k.startsWith('\$') && k !== 'requires' && (v.kind ?? v['x-kind']) !== 'verbs' && only(v)).flatMap(([k, v]) => ((v.kind ?? v['x-kind']) === 'words' ? [k, k + '_WORDS'] : [k])); };
const items = [...readdirSync('data/hosting').flatMap((f) => own('data/hosting/' + f)), ...own('contract.d/hosting/hosting.json', (v) => (v['x-file'] ?? '').startsWith('hosting/')), ...own('contract.d/host/host.json'), ...own('contract.d/omx-clap/omx-clap.json')].sort().join(' ');
import('$(pwd)/ts/omx-clap-vocabulary.js').then((m) => { const k = Object.keys(m).sort().join(' '); if (k !== items) { console.error('contract-dir-check: ts/omx-clap-vocabulary.js exports ' + k + ', data/ declares ' + items); process.exit(1); } })"
echo "contract-dir-check: omx-clap $version read back; $(echo "$committed" | sed 's/[a-z]*://g') the render of data/ and the domains, byte for byte"
