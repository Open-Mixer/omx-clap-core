<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- The parameter contract's unit codes are omx-clap's: the domain omx-param-contract (shipped in omx-clap-contract)
  holds OMX_PARAM_CONTRACT_UNITS, the 29 codes omx-contract released plus 260 dbPerOct, 261 dbPerS, 262 dbtp, 263 lu,
  and OMX_PARAM_CONTRACT_UNIT_IDS, each token's standard unit id (the PARAM_UNITS const: dB, Hz, deg, dB-oct). They
  render <omx-clap-host/omx_param_units.h> (guard OMX_CLAP_PARAM_UNITS_H, the defines and rows of omx-contract's header)
  and <omx-clap-host/omx_param_unit_ids.h> (OMX_PARAM_UNIT_IDS(X), X(code, token, id)); omx_clap_ext.h includes the
  first instead of <omxcontract/omx_param_units.h>. Floors: omx-contract 3.23.0 (the chain-3 release: PARAM_UNITS_CLAP_ENCODED, and its own copy of the sheet and header gone).
