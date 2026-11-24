<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- OMX_PARAM_CONTRACT_UNIT_IDS maps dbPerOct to dBPerOct and dbPerS to dBPerS, omx-contract's renamed PARAM_UNITS ids
  (a unit id is camelCase, "/" reads "Per"; omx-contract#198, ruling 2026-11-23), no alias. param_info answers the
  standard id through the new omx_clap_param_unit_id (plugin-hostd#215 D1).
- The parameter contract's unit codes are omx-clap's: the domain omx-param-contract (shipped in omx-clap-contract)
  holds OMX_PARAM_CONTRACT_UNITS, the 29 codes omx-contract released plus 260 dbPerOct, 261 dbPerS, 262 dbtp, 263 lu,
  and OMX_PARAM_CONTRACT_UNIT_IDS, each token's standard unit id (the PARAM_UNITS const: dB, Hz, deg, dB-oct). They
  render <omx-clap-host/omx_param_units.h> (guard OMX_CLAP_PARAM_UNITS_H, the defines and rows of omx-contract's header)
  and <omx-clap-host/omx_param_unit_ids.h> (OMX_PARAM_UNIT_IDS(X), X(code, token, id)); omx_clap_ext.h includes the
  first instead of <omxcontract/omx_param_units.h>. Floors: omx-contract 3.22.0 (the chain-3 release: PARAM_UNITS_CLAP_ENCODED, and its own copy of the sheet and header gone).
- The real-time gate is omx-dsp's omx-rt-gate (spec 7.13): make test-rt-gate judges the core's and the LV2 adapter's
  units from the host roots they derive (eight audio fields, and respond handed to work() as the worker root), each
  declared root required among them; test-rt-gate-control and test-rt-gate-sabotage hold the gate's own arms; all three
  run in CI with make test's plain group. tests/rt_reach.py and the Makefile's four grep scans are gone. make install
  ships the core's call graphs in the -devel package ($(datadir)/omx-clap/rt-gate/graphs) for a plugin's run to join.
  Build floor: omx-rt-gate 0.34.0. Audio-path fixes the gate found: the LV2 log formats with its own printf (never
  vsnprintf), the URID lookup never allocates, the thread pool reads its thread id without a system call and no helper
  claims on the requesting thread's CPU.
