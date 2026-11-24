<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- The hosting codes have one home, the domain hosting (contract.d/hosting/hosting.json, shipped in omx-clap-contract at
  <contractdir>/hosting/): the 19 HOSTING_*_CODES items left data/ (data/hosting.json keeps HOSTED_STAGE_LIMITS,
  data/hosting/ keeps HOSTING_VERB_HOSTS), and omx-contract's reader refuses a second copy (contract.item.duplicate). Each
  code carries its doc (the 54 that had none were written) and its English text, each item its impl links as x-source
  (omx-contract#215). clap_host_limits.h and omx_clap_vocabulary.h render from it through --with-domain; the idle and
  window codes' TypeScript module is the new omx-clap-hosting-codes.{js,d.ts}, and omx-clap-hosting.{js,d.ts} carries
  HOSTED_STAGE_LIMITS alone. tools/render-domain.py and make render-domain are gone: the domain is edited by hand, and
  make check-domain holds it to the newest release that carries it (omx-contract domain check). A reader of the codes
  from omx-clap's data (plugin-hostd's tests/verbs_declared.py) reads the domain instead (#156).
- OMX_PARAM_CONTRACT_UNIT_IDS maps dbPerOct to dBPerOct and dbPerS to dBPerS, omx-contract's renamed PARAM_UNITS ids
  (a unit id is camelCase, "/" reads "Per"; omx-contract#198, ruling 2026-11-23), no alias. param_info answers the
  standard id through the new omx_clap_param_unit_id (plugin-hostd#215 D1).
- The parameter contract's unit codes are omx-clap's: the domain omx-param-contract (shipped in omx-clap-contract)
  holds OMX_PARAM_CONTRACT_UNITS, the 29 codes omx-contract released plus 260 dbPerOct, 261 dbPerS, 262 dbtp, 263 lu,
  and OMX_PARAM_CONTRACT_UNIT_IDS, each token's standard unit id (the PARAM_UNITS const: dB, Hz, deg, dB-oct). They
  render <omx-clap-host/omx_param_units.h> (guard OMX_CLAP_PARAM_UNITS_H, the defines and rows of omx-contract's header)
  and <omx-clap-host/omx_param_unit_ids.h> (OMX_PARAM_UNIT_IDS(X), X(code, token, id)); omx_clap_ext.h includes the
  first instead of <omxcontract/omx_param_units.h>. Floors: omx-contract 3.22.0 (the chain-3 release: PARAM_UNITS_CLAP_ENCODED, and its own copy of the sheet and header gone).
