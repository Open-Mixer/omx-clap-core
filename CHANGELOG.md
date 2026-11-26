<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- A chain joins members of different widths (#232, zynthian-sys#42): a mono member feeds both channels of a stereo
  one, a stereo member is summed L+R into a mono one, as JACK links ports of two widths, and a width change between
  neighbours is never refused; a mono head takes stereo members, and its node carries the last member's outputs
  (`out_2`). `omx_clap_chain_process_ports` (version node OMX_CLAP_CORE_0.34) runs a chain between ports of the widths
  its ends have; `--capabilities` adds `mixed_width` (docs/chain.md, Widths).
