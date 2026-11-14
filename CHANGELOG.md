<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- org.openmixer.properties/1, a plugin's file and text properties: the host answers the event space, reads the
  table once at load (P1-P3), and offers omx_clap_host_property_count, _info, _get and _set (version node
  OMX_CLAP_CORE_0.33); a set reaches the plugin as one OMX_CLAP_EVENT_PROPERTY_SET at the next block, or through
  params.flush while no cycle runs. The LV2 adapter forges it into the plugin's patch:Set and sends one patch:Get
  after an activate (#15). ABI 22: the instance's layout grew at its tail (abi-check: compatible), so the release
  carrying it is a minor bump, 0.33.0.
