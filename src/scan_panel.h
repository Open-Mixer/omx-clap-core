/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

#ifndef SCAN_PANEL_H
#define SCAN_PANEL_H

#include <stdbool.h>
#include <stdint.h>

#include <clap/plugin.h>

#include "omx_clap_ext.h"

/* The tables of org.openmixer.panel-description/1, SCAN_PANEL_SECTIONS and on, by their OMX_CLAP_PANEL_TABLES code. */
#define SCAN_PANEL_TABLE_CODE(code, name, id) SCAN_PANEL_##id = code,
enum scan_panel_table
{
    OMX_CLAP_PANEL_TABLES(SCAN_PANEL_TABLE_CODE)
    SCAN_PANEL_TABLE_COUNT
};
#undef SCAN_PANEL_TABLE_CODE

/* One table as the plugin answered it: the entries its get filled, each with its index in the table. An entry the get
 * refuses is left out; a table the plugin has no count or get for is empty; a table whose count is past
 * OMX_CLAP_PANEL_DESCRIPTION_MAX_ENTRIES is refused, `refused` its count, and none of its entries is read. */
struct scan_panel_rows
{
    void *rows;  ///< `n` structures of the table's type
    uint32_t *index;  ///< each row's index in the plugin's table
    uint32_t n;
    uint32_t refused;  ///< the count the plugin answered when it is past the maximum, 0 when the table is read
};

/* The panel description a plugin publishes, as omx-clap-scan prints it: nothing is filled in that the plugin did not
 * answer. */
struct scan_panel
{
    bool has_fingerprint;
    char fingerprint[257];  ///< as the plugin gives it, up to 256 bytes
    bool has_family;
    uint32_t family;  ///< an OMX_CLAP_PANEL_FAMILIES code, as the plugin answers it
    struct scan_panel_rows table[SCAN_PANEL_TABLE_COUNT];
};

/* Reads the plugin's org.openmixer.panel-description/1 into `*panel`, on the main thread: 1 read (free it with
 * scan_panel_free), 0 the plugin does not serve it, -1 out of memory. */
int scan_panel_read(const clap_plugin_t *plugin, struct scan_panel *panel);

void scan_panel_free(struct scan_panel *panel);

/* The curves a plugin draws through clap.mini-curve-display/3, which a panel display of source CURVE reads by index: the
 * count and each curve's axis names, asked on the main thread (no render: that needs the curve observed). A count past
 * OMX_CLAP_PANEL_DESCRIPTION_MAX_ENTRIES is refused whole, `refused` its count, and no name is read. */
struct scan_curve
{
    bool named;  ///< get_axis_name answered true
    char x_name[64];
    char y_name[64];
};

struct scan_curves
{
    bool served;  ///< the plugin answers the extension
    uint32_t n;  ///< the curves read, 0 when refused
    uint32_t refused;  ///< the count the plugin answered when it is past the maximum, 0 when read
    struct scan_curve *curve;
};

/* Reads the plugin's curves into `*curves`: 1 read (free it with scan_curves_free), 0 the plugin does not serve the
 * extension, -1 out of memory. */
int scan_curves_read(const clap_plugin_t *plugin, struct scan_curves *curves);

void scan_curves_free(struct scan_curves *curves);

/* Whether a display of the panel reads a curve the plugin does not draw: its source is CURVE and its curve_index is not
 * one of the curves read. */
bool scan_panel_curve_missing(const omx_clap_panel_description_display_t *display, const struct scan_curves *curves);

/* The rows of a table, typed. */
#define SCAN_PANEL_ROW(panel, t, type, i) (&((const type *)(panel)->table[t].rows)[i])

/* A code's word (omx-plugins' name for it, "fader") and enumerator (as omx_panel_description.h names it,
 * "OMX_CLAP_WIDGET_FADER"), NULL for a code the extension does not name. */
const char *scan_panel_family_word(uint32_t code);
const char *scan_panel_family_enum(uint32_t code);
const char *scan_panel_widget_word(uint32_t code);
const char *scan_panel_widget_enum(uint32_t code);
const char *scan_panel_display_source_word(uint32_t code);
const char *scan_panel_display_source_enum(uint32_t code);
const char *scan_panel_placement_word(uint32_t code);
const char *scan_panel_placement_enum(uint32_t code);

#endif
