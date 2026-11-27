<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Reading a plugin's panel description, for any host

A plugin that serves `org.openmixer.panel-description/1` says what its compact panel is. It names the sections, which
parameter is drawn as a knob, fader, switch or selector, which control hides while a mode is set, and which display sits
over which section. The host draws the panel itself, with its own widgets, at its own size and in its own look: in a
mixer strip, a device panel, a touch screen or a control surface. Nothing in it is a pixel, a coordinate, a font or a
colour. Range, default, value text and flags stay in `clap.params`.

This page is for a host other than ours that wants to read the extension. The layout is declared in
[`src/omx_clap_ext.h`](../src/omx_clap_ext.h) and pinned member by member by `tests/panel_abi_test.c`
(`make test-panel-abi`). omx-clap-scan's reader, [`src/scan_panel.c`](../src/scan_panel.c), is the reference for
the rules below, and `tests/clap_scan_test.c:panel_checks` holds it.

## The extension

```c
static const char OMX_CLAP_EXT_PANEL_DESCRIPTION[] = "org.openmixer.panel-description/1";

typedef struct omx_clap_plugin_panel_description_ext {
    const char *(CLAP_ABI *fingerprint)(const clap_plugin_t *plugin);              // [thread-safe]
    uint32_t    (CLAP_ABI *family)(const clap_plugin_t *plugin);                   // [main-thread]
    uint32_t    (CLAP_ABI *count)(const clap_plugin_t *plugin, uint32_t table);    // [main-thread]
    bool        (CLAP_ABI *get)(const clap_plugin_t *plugin, uint32_t table, uint32_t index, void *out); // [main-thread]
} omx_clap_plugin_panel_description_ext_t;
```

Ask for it with `clap_plugin->get_extension()` after `init()`, on the main thread, and read it whole there. Never read
it on the audio thread. A plugin's description is fixed for its build: the extension has no host callback that says it
changed, so a host may keep what it read for as long as it keeps the plugin.

## The five tables

Each table is walked by `count(table)` and then `get(table, i, &row)` for `i` from 0 to the count, in that order. The
order is the drawing order: sections in index order, controls in index order within their section.

| code | table | row type | what a row says |
|---|---|---|---|
| 0 | sections | `omx_clap_panel_description_section_t` | `key`, `label_key` (a translation key), `label` (the fallback text) |
| 1 | controls | `omx_clap_panel_description_control_t` | `param_id` (a `clap.params` id), `section` (an index into the sections), `widget`, `label_key`, `label`, `visible_param_id`, `visible_mask` |
| 2 | roles | `omx_clap_panel_description_role_t` | `role` (`threshold`, `ratio`, ...), `index` (0 unless the role repeats, as an EQ band does), `param_id` |
| 3 | displays | `omx_clap_panel_description_display_t` | `kind`, `section`, `source`, `meter_ids[2]`, `curve_index`, `floor_param_id`, `floor_db`, `label_key`, `label` |
| 4 | placement defaults | `omx_clap_panel_description_default_t` | `placement` (return, bus, master; never insert), `param_id`, `value` (its plain value there) |

The codes of families, widgets, display sources and placements are omx-panel's `panel` domain, installed as
`omxdomain/panel_codes.h`. The widgets are `auto` (0, the host chooses from the parameter's info), `knob`, `fader`,
`switch` and `selector`. We suggest that a host which does not know a code treats the widget as `auto` and leaves the
display out.

## The reader's rules

These are the rules `src/scan_panel.c` applies, and the ones we suggest to any host:

- **A table counted past 4096 entries is refused whole** (`OMX_CLAP_PANEL_DESCRIPTION_MAX_ENTRIES`). Nothing is
  reserved for it, none of its entries is read, and the other tables are still read. The count is the plugin's word, so
  it is checked before any allocation.
- **An entry the plugin's `get` refuses is left out.** The rest of the table is read.
- **A table the plugin cannot count** (no `count`, no `get`, or a count of 0) is empty.
- **Every text is cut at its field's end.** The host ends each string at its last byte, whatever the plugin wrote.
- **Unset ids are `CLAP_INVALID_ID`.** The reader blanks each row before `get`, and an id the plugin leaves unset
  (`visible_param_id`, `meter_ids`, `floor_param_id`) reads as none.
- **Nothing is filled in.** A family or fingerprint the plugin has no function for is unknown, not a default.

Our parameter contract (`org.openmixer.param-contract/1`) is stricter and is trusted whole or not at all. Whether a
panel description should also be whole-or-nothing is an open question. Today it is read entry by entry, as above.

## Visibility

A control with `visible_param_id` equal to `CLAP_INVALID_ID` is always shown. Otherwise it is shown while the value of
that parameter, a stepped one, rounds to `v` and bit `v` of `visible_mask` is set. `visible_param_id` 1 with mask `0x6`
means "shown while parameter 1 is 1 or 2". The host re-evaluates the rule when that parameter changes, from
`clap.params` values it already reads.

## Displays

A display is drawn over its section and reads its data by reference, never a copy:

| source | reads |
|---|---|
| `meters` | the `clap.meters/1` ids in `meter_ids` (one or two) |
| `gain_adjustment` | `clap.gain-adjustment-metering` |
| `curve` | the `clap.mini-curve-display/3` curve at `curve_index` |
| `family` | the family's own view of the section (our console's house views); a host without one leaves it out |

`floor_param_id`, or `floor_db` when no parameter sets it, is the display's floor. `kind` (gain-reduction bar,
transfer curve, EQ response, meter, time response) says what to draw. A host that cannot serve a source leaves the
display out and still draws the controls.

## Families and roles

`family` (gate, dynamics, limiter, de-esser, EQ, filter, drive, modulation, delay, reverb, pitch, utility, or none) says
which kind of view could draw the plugin. The roles name which parameter plays which part in it, such as the
threshold of a dynamics family. A host with its own compressor view can bind its controls through the roles. A host
without such views ignores both and draws the sections.

## What the host must never assume

- No geometry: no size, position, spacing or pixel density comes from the plugin. The host lays the panel out.
- No style: no colour, font or skin. The host's own look and its own accessible widgets apply.
- No second source of truth: range, default, unit and value text are `clap.params`', and a control adds nothing to
  them. A `param_id` that `clap.params` does not list is not drawn.
- No audio-thread read: the description is read on the main thread, before or while the plugin is active.

## The fallback

A host that cannot use a description draws its generic parameter list from `clap.params`, exactly as it would for a
plugin that serves none. That happens when the plugin serves none, a table it needs is refused, or the rows name nothing
it can draw. The plugin's own `clap.gui` window is unaffected: a plugin may offer its window, a description, or both.

## Seeing one

`omx-clap-scan --json <plugin.clap>` prints the description a plugin serves, as `panel` ([scan.md](scan.md)). `omx-clap-scan --fields clap:<path>#<id>` dumps it record by record. omx-plugins serves
the extension through its effects' shared CLAP face, and omx-panel generates descriptions for third-party LV2
and CLAP plugins from what they already declare.
