<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- The host reads a plugin's meters at the rate omx-dsp declares for it (50 Hz, `hostReadHz`), taken from the installed
  omx-dsp definitions at build time; `IDLE_INTERVAL_MS` is no number of its own.
- A meter flagged `OMX_CLAP_METER_IS_HELD` is one the plugin holds until it is read; a burst of 10 ms between two reads
  reaches `output_set`. A meter that holds nothing is named unheld.
- A gain reduction is stepped by `omx_meter_gr_step` over the time elapsed between reads, on the deepest value since the last one.
- A level meter flagged `OMX_CLAP_METER_HAS_CLIP` carries a clip word after its channels; the host sends it as `<name> clip`,
  keeps it lit until it is cleared, and never reads it for a stopped monitor.
- `effects_monitor_output_off` stops reading an output. A monitor ends with the connection that set it. With nothing
  monitored the plugin is read zero times.
- docs/meters.md: the plugin holds, the reader recovers.
- The state root is made at 0700 (an existing, looser one is brought to it as well), a dead instance's
  `lv2-<pid>-<n>` directories and `.saved` copies are pruned at the next start, and the process's cwd moves into the
  root so a plugin that writes relative to its cwd (clap-protoplug) writes there and not wherever the host started.
- `MAX_PLUGIN_INSTANCES`/`MAX_TOOL_INSTANCES` are read from the rendered contract header
  (`OMX_HOSTED_STAGE_MAX_PLUGIN_INSTANCES`/`_MAX_TOOL_INSTANCES`), not restated as a local `#define`.
- `omx-clap-scan` frees every path its walk and its argument list built before it exits, on every path out of `main`.
- A bypassed plugin's dry path is delayed by the latency the plugin publishes: with none the input passes in the same
  block, as before; with some it comes out that many frames later, so a bypass does not move the lane against the
  latency the rest of the chain compensates for. The crossfades into and out of a bypass read the same delayed input,
  on a lane and in a chain alike. The blocks a sleeping plugin skips count as the silence they are: a bypass commanded
  right after it wakes never replays the input from before the sleep.
- The instance ABI is 21: `struct omx_clap_bypass_delay` added at the tail of `struct omx_clap_instance`. No field
  moves, the layout stays compatible under `libomx-clap-core.so.1`.
