/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

/* The panel words of the extension are omx-panel's (omxdomain/panel_codes.h), read through omx_clap_ext.h's lists: the
 * scan's lookups of a code's word and enumerator, called, answer what omx-panel's domain says at its 1.1.0 (the golden
 * below, frozen from the lists omx_clap_ext.h spelled before): 13 families, 5 widgets, 4 display sources, 4 placements.
 * A header without a word is red (the sabotage arm of `make test-panel-words`). */

#include <stdio.h>
#include <string.h>

#include "../src/scan_panel.h"

static int g_failures;

#define CHECK(cond, ...) \
    do { \
        if (cond) { printf("ok   " __VA_ARGS__); printf("\n"); } \
        else { printf("FAIL " __VA_ARGS__); printf("\n"); g_failures++; } \
    } while (0)

_Static_assert(OMX_PANEL_FAMILIES_COUNT == 13, "13 families");
_Static_assert(OMX_PANEL_WIDGETS_COUNT == 5, "5 widgets");
_Static_assert(OMX_PANEL_DISPLAY_SOURCES_COUNT == 4, "4 display sources");
_Static_assert(OMX_PANEL_PLACEMENTS_COUNT == 4, "4 placements");

#define LOOKS(fn, prefix, golden) \
    do { \
        for (uint32_t c = 0; c < sizeof(golden) / sizeof(golden[0]); c++) { \
            char want[64]; \
            const char *word = scan_panel_##fn##_word(c), *en = scan_panel_##fn##_enum(c); \
            snprintf(want, sizeof(want), prefix "%s", golden[c][1]); \
            CHECK(word && strcmp(word, golden[c][0]) == 0 && en && strcmp(en, want) == 0, "%s %u is %s, %s", #fn, c, golden[c][0], want); \
        } \
        CHECK(scan_panel_##fn##_word((uint32_t)(sizeof(golden) / sizeof(golden[0]))) == NULL && scan_panel_##fn##_enum(99) == NULL, "%s: a code past the last is named by nothing", #fn); \
    } while (0)

int main(void)
{
    static const char *const family[][2] = { { "none", "NONE" }, { "gate", "GATE" }, { "dynamics", "DYNAMICS" }, { "limiter", "LIMITER" },
        { "deesser", "DEESSER" }, { "eq", "EQ" }, { "filter", "FILTER" }, { "drive", "DRIVE" }, { "modulation", "MODULATION" },
        { "delay", "DELAY" }, { "reverb", "REVERB" }, { "pitch", "PITCH" }, { "utility", "UTILITY" } };
    static const char *const widget[][2] = { { "auto", "AUTO" }, { "knob", "KNOB" }, { "fader", "FADER" }, { "switch", "SWITCH" }, { "selector", "SELECTOR" } };
    static const char *const display_source[][2] = { { "family", "FAMILY" }, { "meters", "METERS" }, { "gain_adjustment", "GAIN_ADJUSTMENT" }, { "curve", "CURVE" } };
    static const char *const placement[][2] = { { "insert", "INSERT" }, { "return", "RETURN" }, { "bus", "BUS" }, { "master", "MASTER" } };

    LOOKS(family, "OMX_CLAP_FAMILY_", family);
    LOOKS(widget, "OMX_CLAP_WIDGET_", widget);
    LOOKS(display_source, "OMX_CLAP_DISPLAY_FROM_", display_source);
    LOOKS(placement, "OMX_CLAP_PLACEMENT_", placement);
    printf("%s\n", g_failures ? "FAILED" : "scan_panel_words_test: all passed");
    return g_failures != 0;
}
