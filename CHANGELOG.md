<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- The `scan` domain (contract.d/scan/scan.json, owner omx-clap-core): SCAN_DOCUMENTS and SCAN_FIELD_SCOPES, moved here from
  omx-contract's data/scan.json; src/scan_vocabulary.h is its render, the same `OMX_SCAN_*` macros byte for byte, installed
  beside omx_clap_core_vocabulary.h, and the document is installed to `<contractdir>/scan/scan.json` (omx-contract#81, move 1).
- org.openmixer.properties/1, a plugin's file and text properties: the host answers the event space, reads the
  table once at load (P1-P3), and offers omx_clap_host_property_count, _info, _get and _set (version node
  OMX_CLAP_CORE_0.33); a set reaches the plugin as one OMX_CLAP_EVENT_PROPERTY_SET at the next block, or through
  params.flush while no cycle runs. The LV2 adapter forges it into the plugin's patch:Set and sends one patch:Get
  after an activate (#15). ABI 22: the instance's layout grew at its tail (abi-check: compatible), so the release
  carrying it is a minor bump, 0.33.0.
