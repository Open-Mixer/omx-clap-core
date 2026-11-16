// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas
/*
 * THE PANEL TABLES FOLLOW THE CONTRACT (Open-Mixer/omx-clap-core#104). omx_clap_ext.h's families, widgets and display
 * kinds are omx-contract's PANEL_FAMILIES, PANEL_WIDGETS and PANEL_DISPLAY_KINDS, never a copy kept here. Built with
 * tests/fixtures/contract-one-more-family first on the include path, a contract that declares one more of each: every
 * table must carry the fixture's rows, codes and names, in its order, with no edit in this tree. A hand table stays
 * at the words it was written with and is red.
 */
#include <stdio.h>
#include <string.h>

#include <omxcontract/omx_vocabulary.h>

#include "omx_clap_ext.h"

#define CODE(code, name, id) (unsigned)(code),
#define NAME(code, name, id) name,
#define ID(code, name, id) #id,

static int g_failures;

static void same(const char *what, const unsigned *oc, const char *const *on, const char *const *oi, size_t ours,
                 const unsigned *cc, const char *const *cn, const char *const *ci, size_t contract)
{
    if (ours != contract) {
        printf("FAIL %s: %zu rows here, %zu in the contract (last: %s)\n", what, ours, contract, cn[contract - 1]);
        g_failures++;
        return;
    }
    for (size_t i = 0; i < ours; i++) {
        if (oc[i] != cc[i] || strcmp(on[i], cn[i]) || strcmp(oi[i], ci[i])) {
            printf("FAIL %s row %zu: X(%u, \"%s\", %s) here, X(%u, \"%s\", %s) in the contract\n", what, i, oc[i], on[i],
                   oi[i], cc[i], cn[i], ci[i]);
            g_failures++;
            return;
        }
    }
    printf("ok   %s: the contract's %zu rows, last \"%s\"\n", what, ours, on[ours - 1]);
}

#define SAME(what, ours, contract)                                                                                     \
    do {                                                                                                               \
        static const unsigned oc[] = { ours(CODE) }, cc[] = { contract(CODE) };                                        \
        static const char *const on[] = { ours(NAME) }, *const cn[] = { contract(NAME) };                              \
        static const char *const oi[] = { ours(ID) }, *const ci[] = { contract(ID) };                                  \
        same(what, oc, on, oi, sizeof(oc) / sizeof(oc[0]), cc, cn, ci, sizeof(cc) / sizeof(cc[0]));                    \
    } while (0)

int main(void)
{
    SAME("families", OMX_CLAP_PANEL_FAMILIES, OMX_PANEL_FAMILIES);
    SAME("widgets", OMX_CLAP_PANEL_WIDGETS, OMX_PANEL_WIDGETS);
    SAME("display kinds", OMX_CLAP_PANEL_DISPLAY_KINDS, OMX_PANEL_DISPLAY_KINDS);
    return g_failures ? 1 : 0;
}
