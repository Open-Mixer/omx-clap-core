<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- A bypassed plugin's dry path is delayed by the latency the plugin publishes: with none the input passes in the same
  block, as before; with some it comes out that many frames later, so a bypass does not move the lane against the
  latency the rest of the chain compensates for. The crossfades into and out of a bypass read the same delayed input,
  on a lane and in a chain alike. The blocks a sleeping plugin skips count as the silence they are: a bypass commanded
  right after it wakes never replays the input from before the sleep.
- The instance ABI is 21: `struct omx_clap_bypass_delay` added at the tail of `struct omx_clap_instance`. No field
  moves, the layout stays compatible under `libomx-clap-core.so.1`.
