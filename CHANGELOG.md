<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- The `scan` domain (contract.d/scan/scan.json and its six catalogs, owner omx-clap-core, `info.x-stability` experimental): SCAN_DOCUMENTS and
  SCAN_FIELD_SCOPES (the 13 scopes it came with and a `meter` scope, x-code 13), moved here from omx-contract's data/scan.json (omx-contract#81, move 1). omx-clap-scan --fields reads the scopes of
  its dump from the domain at start-up (through libomx-domain; OMX_CONTRACT_PATH, a ':' list, names the directories for a command
  line and a test) and refuses by name, exit 78, when the domain is absent, invalid or too old. src/scan_codes.h holds the one item C
  indexes by, SCAN_FIELD_SCOPES, as constants; there is no scan vocabulary header.
- omx-clap-host closes its JACK clients on SIGHUP as it does on SIGTERM and SIGINT: a host killed by the default action
  left its clients open, and a client that dies without jack_client_close strands nine of the fixed pool of mutexes
  of jackd's metadata store (tests/jack_close_e2e.sh).
- The floors move through packaging/deps.txt: omx-dsp 0.33.0 (published; the package carries no ceiling on it), omx-contract 3.20.0 (the first release with the domain loader and the installer's domain mode), and libomx-domain 3.20.0 for the scanner.
- org.openmixer.properties/1, a plugin's file and text properties: the host answers the event space, reads the
  table once at load (P1-P3), and offers omx_clap_host_property_count, _info, _get and _set (version node
  OMX_CLAP_CORE_0.33); a set reaches the plugin as one OMX_CLAP_EVENT_PROPERTY_SET at the next block, or through
  params.flush while no cycle runs. The LV2 adapter forges it into the plugin's patch:Set and sends one patch:Get
  after an activate (#15). ABI 22: the instance's layout grew at its tail (abi-check: compatible), so the release
  carrying it is a minor bump, 0.33.0.
