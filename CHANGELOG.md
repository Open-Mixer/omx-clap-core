<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- No hand-kept version floor (owner ruling 2026-11-24): packaging/deps.txt is gone, the
  spec, debian/control and omx-clap.pc name every dependency without a version; what a package needs at run time is
  generated (sonames, ${shlibs:Depends}, = its own version). The data files state no `requires` (their only entry was the
  omx-contract-schema floor) and the omx-clap domain's info.x-requires is the list of names ["host"]. omx-clap-scan opens
  the scan domain with no floor (omx_domain_open without a version, omx-contract's wave). tests/build-floors.sh and the
  schema floor of code-text-check are gone; tests/no_floors_check.py (make test-no-floors) refuses a floor coming back.
- OMX_PARAM_CONTRACT_UNIT_IDS maps dbPerOct to dBPerOct and dbPerS to dBPerS, omx-contract's renamed PARAM_UNITS ids
  (a unit id is camelCase, "/" reads "Per"; omx-contract#198, ruling 2026-11-23), no alias. param_info answers the
  standard id through the new omx_clap_param_unit_id (plugin-hostd#215 D1).
- The parameter contract's unit codes are omx-clap's: the domain omx-param-contract (shipped in omx-clap-contract)
  holds OMX_PARAM_CONTRACT_UNITS, the 29 codes omx-contract released plus 260 dbPerOct, 261 dbPerS, 262 dbtp, 263 lu,
  and OMX_PARAM_CONTRACT_UNIT_IDS, each token's standard unit id (the PARAM_UNITS const: dB, Hz, deg, dB-oct). They
  render <omx-clap-host/omx_param_units.h> (guard OMX_CLAP_PARAM_UNITS_H, the defines and rows of omx-contract's header)
  and <omx-clap-host/omx_param_unit_ids.h> (OMX_PARAM_UNIT_IDS(X), X(code, token, id)); omx_clap_ext.h includes the
  first instead of <omxcontract/omx_param_units.h>. Floors: omx-contract 3.22.0 (the chain-3 release: PARAM_UNITS_CLAP_ENCODED, and its own copy of the sheet and header gone).
- The replies of note_input, idle_hold, note_drops and note_out_drops are typed and named (#49): OMX_CLAP_REPLIES of
  the omx-clap domain gives each as resp 0 and name:type per field, plugin-hostd-protocol's reply form, each type an
  arg_type of the protocol's table or one of OMX_CLAP_REPLY_TYPES (hold, microseconds); both items are read at run time
  and render nowhere. Each builder writes its reply with HOST_FIELDS_FMT(HOST_FIELDS_<VERB>) of src/host_verbs.h, the
  declared fields by name, and tests/host-replies-check.py holds the two together and to each verb's x-reply. The
  replies of param_info, remote_pages and remote_page_get are plugin-hostd-protocol's to type (host-dispatch.h writes
  them), and so is property_list's beside property_info and property_get; audio_ports' follows.
