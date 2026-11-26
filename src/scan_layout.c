/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

/* The control layout a plugin publishes (org.openmixer.control-layout.draft/1), read once for omx-clap-scan, with the
 * host's rules of src/omx_clap_ext.h applied: a table counted past OMX_CLAP_CONTROL_LAYOUT_MAX_ENTRIES is ignored whole
 * and the other tables are still read; an entry the plugin's get refuses or that breaks a rule is left out, named with
 * its reason, and the rest is kept in the plugin's order. Every text is cut at its field's end. */

#include <stdlib.h>
#include <string.h>

#include "scan_layout.h"
#include "abi_guard.h"

#define TERMINATE(field) ((field)[sizeof(field) - 1] = '\0')

static bool has_id(const clap_id *ids, uint32_t n, clap_id id)
{
    for (uint32_t i = 0; i < n; i++)
        if (ids[i] == id)
            return true;
    return false;
}

static bool has_section(const struct scan_layout *l, clap_id id)
{
    for (uint32_t i = 0; i < l->n[SCAN_LAYOUT_SECTIONS]; i++)
        if (l->sections[i].id == id)
            return true;
    return false;
}

static bool stepped(const struct scan_layout_offer *o, clap_id id)
{
    for (uint32_t i = 0; i < o->param_count; i++)
        if (o->param_ids[i] == id)
            return o->param_stepped[i];
    return false;
}

static int leave_out(struct scan_layout *l, uint32_t table, uint32_t index, const char *reason)
{
    struct scan_layout_left_out *grown = realloc(l->left_out, (size_t)(l->n_left_out + 1) * sizeof(*grown));

    if (!grown)
        return -1;
    l->left_out = grown;
    l->left_out[l->n_left_out++] = (struct scan_layout_left_out){ table, index, reason };
    return 0;
}

/* why a control is left out, NULL when it is kept */
static const char *control_fault(const struct scan_layout *l, const struct scan_layout_offer *o,
                                 const omx_clap_control_layout_control_t *c)
{
    if (!has_id(o->param_ids, o->param_count, c->param_id))
        return "param";
    if (!has_section(l, c->section_id))
        return "section";
    if (c->visible_if_param_id != CLAP_INVALID_ID && !stepped(o, c->visible_if_param_id))
        return "visibility";
    return NULL;
}

/* why a display is left out, NULL when it is kept */
static const char *display_fault(const struct scan_layout *l, const struct scan_layout_offer *o,
                                 const omx_clap_control_layout_display_t *d)
{
    if (!has_section(l, d->section_id))
        return "section";
    switch (d->source)
    {
    case OMX_CLAP_LAYOUT_DISPLAY_METER:
        if (d->ids[0] == CLAP_INVALID_ID || !has_id(o->meter_ids, o->meter_count, d->ids[0])
            || (d->ids[1] != CLAP_INVALID_ID && !has_id(o->meter_ids, o->meter_count, d->ids[1])))
            return "meter";
        return NULL;
    case OMX_CLAP_LAYOUT_DISPLAY_CURVE:
        return o->curves ? NULL : "curve";
    case OMX_CLAP_LAYOUT_DISPLAY_GAIN_ADJUSTMENT:
        return o->gain_adjustment ? NULL : "gain-adjustment";
    default:
        return "source";
    }
}

/* the count of one table, 0 with no function for it; past the maximum the table is refused before anything is reserved */
static uint32_t counted(struct scan_layout *l, uint32_t table, uint32_t count)
{
    if (count > OMX_CLAP_CONTROL_LAYOUT_MAX_ENTRIES)
    {
        l->refused[table] = count;
        return 0;
    }
    return count;
}

int scan_layout_read(const clap_plugin_t *plugin, const struct scan_layout_offer *offer, struct scan_layout *l)
{
    const omx_clap_plugin_control_layout_t *ext = OMX_ABI_CALL(NULL, "get_extension", plugin->get_extension, plugin, OMX_CLAP_EXT_CONTROL_LAYOUT);
    uint32_t count, i;

    memset(l, 0, sizeof(*l));
    if (!ext)
        return 0;

    count = ext->section_count && ext->get_section
        ? counted(l, SCAN_LAYOUT_SECTIONS, OMX_ABI_CALL(NULL, "ext.section_count", ext->section_count, plugin)) : 0;
    if (count && !(l->sections = malloc((size_t)count * sizeof(*l->sections))))
        goto oom;
    for (i = 0; i < count; i++)
    {
        omx_clap_control_layout_section_t s = { CLAP_INVALID_ID, "" };
        const char *why = NULL;

        if (!OMX_ABI_CALL(NULL, "ext.get_section", ext->get_section, plugin, i, &s))
            why = "get";
        else if (has_section(l, s.id))
            why = "duplicate-id";
        if (why)
        {
            if (leave_out(l, SCAN_LAYOUT_SECTIONS, i, why) != 0)
                goto oom;
            continue;
        }
        TERMINATE(s.name);
        l->sections[l->n[SCAN_LAYOUT_SECTIONS]++] = s;
    }

    count = ext->control_count && ext->get_control
        ? counted(l, SCAN_LAYOUT_CONTROLS, OMX_ABI_CALL(NULL, "ext.control_count", ext->control_count, plugin)) : 0;
    if (count && !(l->controls = malloc((size_t)count * sizeof(*l->controls))))
        goto oom;
    for (i = 0; i < count; i++)
    {
        omx_clap_control_layout_control_t c;
        const char *why;

        memset(&c, 0, sizeof(c));
        c.visible_if_param_id = CLAP_INVALID_ID;
        why = OMX_ABI_CALL(NULL, "ext.get_control", ext->get_control, plugin, i, &c) ? control_fault(l, offer, &c) : "get";
        if (why)
        {
            if (leave_out(l, SCAN_LAYOUT_CONTROLS, i, why) != 0)
                goto oom;
            continue;
        }
        TERMINATE(c.label);
        if (!scan_layout_widget_word(c.widget))
            c.widget = OMX_PANEL_WIDGETS_AUTO;  // an unknown widget is AUTO
        l->controls[l->n[SCAN_LAYOUT_CONTROLS]++] = c;
    }

    count = ext->display_count && ext->get_display
        ? counted(l, SCAN_LAYOUT_DISPLAYS, OMX_ABI_CALL(NULL, "ext.display_count", ext->display_count, plugin)) : 0;
    if (count && !(l->displays = malloc((size_t)count * sizeof(*l->displays))))
        goto oom;
    for (i = 0; i < count; i++)
    {
        omx_clap_control_layout_display_t d;
        const char *why;

        memset(&d, 0, sizeof(d));
        d.ids[0] = d.ids[1] = CLAP_INVALID_ID;
        why = OMX_ABI_CALL(NULL, "ext.get_display", ext->get_display, plugin, i, &d) ? display_fault(l, offer, &d) : "get";
        if (why)
        {
            if (leave_out(l, SCAN_LAYOUT_DISPLAYS, i, why) != 0)
                goto oom;
            continue;
        }
        TERMINATE(d.label);
        l->displays[l->n[SCAN_LAYOUT_DISPLAYS]++] = d;
    }
    return 1;

oom:
    scan_layout_free(l);
    return -1;
}

void scan_layout_free(struct scan_layout *l)
{
    free(l->sections);
    free(l->controls);
    free(l->displays);
    free(l->left_out);
    memset(l, 0, sizeof(*l));
}

#define LAYOUT_WORD(code, id) [code] = #id,
static const char *const g_widget_tokens[] = { OMX_CLAP_CONTROL_LAYOUT_WIDGETS(LAYOUT_WORD) };
static const char *const g_source_tokens[] = { OMX_CLAP_CONTROL_LAYOUT_DISPLAY_SOURCES(LAYOUT_WORD) };
static char g_widget_words[sizeof(g_widget_tokens) / sizeof(g_widget_tokens[0])][32];
static char g_source_words[sizeof(g_source_tokens) / sizeof(g_source_tokens[0])][32];

/* the token in lower case, '_' written '-', made once per code on first use (the scan is one thread) */
static const char *word(const char *const *tokens, char (*words)[32], size_t n, uint32_t code)
{
    if (code >= n || !tokens[code])
        return NULL;
    if (!words[code][0])
        for (size_t i = 0; i < 31 && tokens[code][i]; i++)
        {
            const char ch = tokens[code][i];
            words[code][i] = ch == '_' ? '-' : (char)(ch >= 'A' && ch <= 'Z' ? ch - 'A' + 'a' : ch);
        }
    return words[code];
}

const char *scan_layout_widget_word(uint32_t code)
{
    return word(g_widget_tokens, g_widget_words, sizeof(g_widget_tokens) / sizeof(g_widget_tokens[0]), code);
}

const char *scan_layout_source_word(uint32_t code)
{
    return word(g_source_tokens, g_source_words, sizeof(g_source_tokens) / sizeof(g_source_tokens[0]), code);
}

const char *scan_layout_table_name(uint32_t table)
{
    static const char *const names[SCAN_LAYOUT_TABLE_COUNT] = { "sections", "controls", "displays" };
    return table < SCAN_LAYOUT_TABLE_COUNT ? names[table] : NULL;
}
