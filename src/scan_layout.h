/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

#ifndef SCAN_LAYOUT_H
#define SCAN_LAYOUT_H

#include <stdbool.h>
#include <stdint.h>

#include <clap/plugin.h>

#include "omx_clap_ext.h"

/* The tables of org.openmixer.control-layout.draft/1, in the order a host reads them. */
enum scan_layout_table
{
    SCAN_LAYOUT_SECTIONS = 0,
    SCAN_LAYOUT_CONTROLS = 1,
    SCAN_LAYOUT_DISPLAYS = 2,
    SCAN_LAYOUT_TABLE_COUNT
};

/* What the plugin offers that the layout may name: its clap.params ids, which of them are stepped, its clap.meters/1
 * ids, how many curves it draws through clap.mini-curve-display/3 (0 for none, or a count past the maximum) and whether
 * it answers clap.gain-adjustment-metering. */
struct scan_layout_offer
{
    const clap_id *param_ids;
    const bool *param_stepped;
    uint32_t param_count;
    const clap_id *meter_ids;
    uint32_t meter_count;
    uint32_t curve_count;
    bool gain_adjustment;
};

/* One entry the reader left out: its table, its index in the plugin's table and why. */
struct scan_layout_left_out
{
    uint32_t table;  ///< a scan_layout_table
    uint32_t index;
    const char *reason;  ///< "get", "duplicate-id", "param", "section", "visibility", "source", "meter", "curve", "gain-adjustment"
};

/* The layout as a host may draw it: each table's kept entries in the plugin's order, the count of a table ignored whole
 * (past OMX_CLAP_CONTROL_LAYOUT_MAX_ENTRIES), and every entry left out with its reason. */
struct scan_layout
{
    omx_clap_control_layout_section_t *sections;
    omx_clap_control_layout_control_t *controls;
    omx_clap_control_layout_display_t *displays;
    uint32_t n[SCAN_LAYOUT_TABLE_COUNT];
    uint32_t refused[SCAN_LAYOUT_TABLE_COUNT];  ///< the count the plugin answered when past the maximum, else 0
    struct scan_layout_left_out *left_out;
    uint32_t n_left_out;
};

/* Reads the plugin's org.openmixer.control-layout.draft/1 against what it offers, on the main thread: 1 read (free it
 * with scan_layout_free), 0 the plugin does not serve it, -1 out of memory. */
int scan_layout_read(const clap_plugin_t *plugin, const struct scan_layout_offer *offer, struct scan_layout *layout);

void scan_layout_free(struct scan_layout *layout);

/* A code's word, lower case ("knob", "meter"), NULL for a code the extension does not name. */
const char *scan_layout_widget_word(uint32_t code);
const char *scan_layout_source_word(uint32_t code);

/* A table's name as the scan prints it: "sections", "controls", "displays". */
const char *scan_layout_table_name(uint32_t table);

#endif
