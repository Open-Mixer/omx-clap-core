<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- CI: a pull request into devel, and a dispatch off main, fetches plugin-hostd's devel (PLUGIN_HOSTD_BRANCH) and builds
  against the staging channel in every job and the release dry run, the condition plugin-hostd's own ci.yml uses; the
  staging-provenance guard allows a staged package under it alone (#234).
- omx-clap-scan reads a plugin's `clap.mini-curve-display/3`: the curve count and each curve's axis names, in `--json` (`curves`) and `--fields`, a count past 4096 refused whole; a panel display of source curve whose `curve_index` names no curve the plugin draws carries `curve: {refused: "no-such-curve", count}` (#244).
- `org.openmixer.control-layout.draft/1`, the cut-down shape OpenMixer would propose to CLAP as `clap.control-layout/1`
  (sections, controls, displays; no family, roles, placement defaults, label keys or fingerprint), is declared in
  `src/omx_clap_ext.h` and pinned by `make test-panel-abi`. omx-clap-scan reads it against what the plugin offers
  (`clap.params`, `clap.meters/1`, `clap.mini-curve-display/3`, `clap.gain-adjustment-metering`), keeps what a host may
  draw and names every entry it leaves out with its reason (`controlLayout` in `--json`, a count line in the listing);
  `tests/clap_scan_test.c:layout_checks` holds one entry per rule (#249).
- The window tests hold that a floating window's plugin is never asked clap.gui `set_transient`: `tests/fake_gui.c` logs the call, and `make test-jack-window` (X11 floating) and `make test-jack-window-wl` (Wayland, and the build with no X11) require none (#247).
- The vocabulary pass: omx-clap 0.35.1 (#221) and V23d on devel (#223) merged into the wave, nothing of the 0.35 line
  dropped. Every domain stays at the package version, 0.M.m until 1.0 (owner 2026-11-25), so #221's return to 1.0.0
  and 2.18.0 is not taken. <omx-clap-host/omx_clap_host_verbs.h> left with the verbs (R5).
- What omx-clap-host shares with plugin-hostd-protocol is that package's (ruling R5, plugin-hostd-protocol#67): the domain
  host (HOST_REPLY_CODES, HOST_TRACK_KINDS, HOST_EVENTS, with their catalogs), HOSTING_VERB_HOSTS (now its domain
  hosting-verb) and the verbs this host answers (now PLUGIN_HOSTD_PROTOCOL_SHARED_VERBS and
  PLUGIN_HOSTD_PROTOCOL_CLAP_HOST_VERBS of its domain plugin-hostd-protocol) leave this tree word for word:
  contract.d/host, data/hosting/verb-hosts.json, the two verbs items of the omx-clap domain, the reply.host.* entries of
  catalogs/ and the render src/omx_clap_host_verbs.h are gone, and omx_clap_vocabulary.h and omx-clap-vocabulary.{js,d.ts}
  no longer carry the host words or the verb hosts. The omx-clap domain keeps OMX_CLAP_REPLIES and OMX_CLAP_REPLY_TYPES and
  states no x-requires. The sources include <plugin-hostd/plugin_hostd_protocol_host_verbs.h> and
  <plugin-hostd/plugin_hostd_protocol_vocabulary.h>, every macro as it was; the tests read the verbs and the host words
  from plugin-hostd-protocol's installed contract (PROTOCOL_DOMAINS: a checkout's contract.d, or omx-contract's contract
  directory), which the build requires by name (plugin-hostd-protocol-contract), as omx-clap-contract does. make
  host-verbs-contract reads both packages' contract directories as one, so a word declared by both is refused
  (contract.item.duplicate), and tests/no_protocol_copy.py refuses a verbs item, a rendered verb table or an item of the
  domains host and hosting-verb coming back. No alias, no second read.
- The replies of note_input, note_drops and note_out_drops are plugin-hostd-protocol's: its table's reply_forms types them,
  their one home, so OMX_CLAP_REPLIES drops them and types idle_hold alone. tests/host-replies-check.py holds
  HOST_FIELDS_NOTE_INPUT, HOST_FIELDS_NOTE_DROPS and HOST_FIELDS_NOTE_OUT_DROPS to the table's names and types, and
  refuses one of them typed here again (a reply with two homes).
- No hand-kept version floor (owner ruling 2026-11-24): packaging/deps.txt is gone, the
  spec, debian/control and omx-clap.pc name every dependency without a version; what a package needs at run time is
  generated (sonames, ${shlibs:Depends}, = its own version). The data files state no `requires` (their only entry was the
  omx-contract-schema floor) and the omx-clap domain's info.x-requires is the list of names ["host"]. omx-clap-scan opens
  the scan domain with no floor (omx_domain_open without a version, omx-contract's wave). tests/build-floors.sh and the
  schema floor of code-text-check are gone; tests/no_floors_check.py (make test-no-floors) refuses a floor coming back.
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
- The replies of note_input, idle_hold, note_drops and note_out_drops are typed and named (#49): OMX_CLAP_REPLIES of
  the omx-clap domain gives each as resp 0 and name:type per field, plugin-hostd-protocol's reply form, each type an
  arg_type of the protocol's table or one of OMX_CLAP_REPLY_TYPES (hold, microseconds); both items are read at run time
  and render nowhere. Each builder writes its reply with HOST_FIELDS_FMT(HOST_FIELDS_<VERB>) of src/host_verbs.h, the
  declared fields by name, and tests/host-replies-check.py holds the two together and to each verb's x-reply. The
  replies of param_info, remote_pages and remote_page_get are plugin-hostd-protocol's to type (host-dispatch.h writes
  them), and so is property_list's beside property_info and property_get; audio_ports' follows.
- The real-time gate is omx-dsp's omx-rt-gate (spec 7.13): make test-rt-gate judges the core's and the LV2 adapter's
  units from the host roots they derive (eight audio fields, and respond handed to work() as the worker root), each
  declared root required among them; test-rt-gate-control and test-rt-gate-sabotage hold the gate's own arms; all three
  run in CI with make test's plain group. tests/rt_reach.py and the Makefile's four grep scans are gone. make install
  ships the core's call graphs in the -devel package ($(datadir)/omx-clap/rt-gate/graphs) for a plugin's run to join.
  Audio-path fixes the gate found: the LV2 log formats with its own printf (never
  vsnprintf), the URID lookup never allocates, the thread pool reads its thread id without a system call and no helper
  claims on the requesting thread's CPU.
- omx-clap-host gives an embedded window's plugin its scale again (clap.gui `set_scale`) while the window exists, when the screen's `Xft.dpi` resource changes; never a floating window's (#229). `request_show` before the plugin has a window answers false, now held by `tests/window_test.c` (#230).
- A chain joins members of different widths (#232, zynthian-sys#42): a mono member feeds both channels of a stereo
  one, a stereo member is summed L+R into a mono one, as JACK links ports of two widths, and a width change between
  neighbours is never refused; a mono head takes stereo members, and its node carries the last member's outputs
  (`out_2`). `omx_clap_chain_process_ports` (version node OMX_CLAP_CORE_0.34) runs a chain between ports of the widths
  its ends have; `--capabilities` adds `mixed_width` (docs/chain.md, Widths).
