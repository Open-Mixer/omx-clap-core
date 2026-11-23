/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

/* org.openmixer.panel-description/1 as omx_clap_ext.h declares it. omx-clap-core owns this layout: the structures are
 * pinned here, size and every member's offset, so a change to one is a change to this file, reviewed as the ABI change
 * it is. omx-plugins holds its omx_panel_*_row structures to this tree's installed header (its make panel-abi); this
 * tree reads nothing of omx-plugins. The extension's members are all pointers, pinned in units of sizeof(void *);
 * the table structures' numbers are the LP64 layout, a precondition stated below. */

#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "omx_clap_ext.h"

/* PRECONDITION: the pins below are the LP64 layout (x86_64, aarch64): 8-byte pointers and an 8-byte, 8-aligned double.
 * Every target this tree ships for is LP64; a 32-bit build fails here, by name, before any offset could mislead. */
_Static_assert(sizeof(void *) == 8, "precondition: LP64 (8-byte pointers); the panel layout pins below are LP64's");
_Static_assert(sizeof(double) == 8 && _Alignof(double) == 8, "precondition: LP64 (8-byte, 8-aligned double); the pins below rely on it");

#define SIZE(type, bytes) _Static_assert(sizeof(type) == (bytes), "the size of " #type " is " #bytes)
#define AT(type, member, bytes) \
    _Static_assert(offsetof(type, member) == (bytes), #type "." #member " is at " #bytes)

_Static_assert(OMX_CLAP_PANEL_DESCRIPTION_KEY_SIZE == 64, "a key's size");
_Static_assert(OMX_CLAP_PANEL_DESCRIPTION_NAME_SIZE == 256, "a label's size");

SIZE(omx_clap_panel_description_section_t, 384);
AT(omx_clap_panel_description_section_t, key, 0);
AT(omx_clap_panel_description_section_t, label_key, 64);
AT(omx_clap_panel_description_section_t, label, 128);

SIZE(omx_clap_panel_description_control_t, 344);
AT(omx_clap_panel_description_control_t, param_id, 0);
AT(omx_clap_panel_description_control_t, section, 4);
AT(omx_clap_panel_description_control_t, widget, 8);
AT(omx_clap_panel_description_control_t, label_key, 12);
AT(omx_clap_panel_description_control_t, label, 76);
AT(omx_clap_panel_description_control_t, visible_param_id, 332);
AT(omx_clap_panel_description_control_t, visible_mask, 336);

SIZE(omx_clap_panel_description_role_t, 72);
AT(omx_clap_panel_description_role_t, role, 0);
AT(omx_clap_panel_description_role_t, index, 64);
AT(omx_clap_panel_description_role_t, param_id, 68);

SIZE(omx_clap_panel_description_display_t, 360);
AT(omx_clap_panel_description_display_t, kind, 0);
AT(omx_clap_panel_description_display_t, section, 4);
AT(omx_clap_panel_description_display_t, source, 8);
AT(omx_clap_panel_description_display_t, meter_ids, 12);
AT(omx_clap_panel_description_display_t, curve_index, 20);
AT(omx_clap_panel_description_display_t, floor_param_id, 24);
AT(omx_clap_panel_description_display_t, floor_db, 32);
AT(omx_clap_panel_description_display_t, label_key, 40);
AT(omx_clap_panel_description_display_t, label, 104);

SIZE(omx_clap_panel_description_default_t, 16);
AT(omx_clap_panel_description_default_t, placement, 0);
AT(omx_clap_panel_description_default_t, param_id, 4);
AT(omx_clap_panel_description_default_t, value, 8);

SIZE(omx_clap_plugin_panel_description_ext_t, 4 * sizeof(void *));
AT(omx_clap_plugin_panel_description_ext_t, fingerprint, 0 * sizeof(void *));
AT(omx_clap_plugin_panel_description_ext_t, family, 1 * sizeof(void *));
AT(omx_clap_plugin_panel_description_ext_t, count, 2 * sizeof(void *));
AT(omx_clap_plugin_panel_description_ext_t, get, 3 * sizeof(void *));

static int g_failures;

#define CHECK(cond, ...) \
    do { \
        if (cond) { printf("ok   " __VA_ARGS__); printf("\n"); } \
        else { printf("FAIL " __VA_ARGS__); printf("\n"); g_failures++; } \
    } while (0)

int main(void)
{
    CHECK(strcmp(OMX_CLAP_EXT_PANEL_DESCRIPTION, "org.openmixer.panel-description/1") == 0, "the extension id: %s", OMX_CLAP_EXT_PANEL_DESCRIPTION);
    CHECK(CLAP_INVALID_ID == 0xffffffffu, "no parameter is CLAP_INVALID_ID");
    printf("%s\n", g_failures == 0 ? "panel abi test ok" : "panel abi test FAILED");
    return g_failures == 0 ? 0 : 1;
}
