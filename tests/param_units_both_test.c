/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/*
 * param_units_both_test.c: this tree's unit codes (src/omx_param_units.h, the render of the domain omx-param-contract)
 * and omx-contract's old copy (<omxcontract/omx_param_units.h>, shipped until its removal goes last) in ONE unit.
 *
 * Each header has its own guard, so neither is skipped when a unit includes both: an identical redefinition of a macro
 * is legal C, and a row that differs (a code moved, a token appended on one side only) is a redefinition with another
 * body, which -Werror turns into a failed build (make test-param-units-both, with its sabotage arm).
 */
#include <omxcontract/omx_param_units.h>
#include "omx_param_units.h"
#include "omx_param_unit_ids.h"

#ifndef OMX_CLAP_PARAM_UNITS_H
#error "src/omx_param_units.h has no guard of its own (OMX_CLAP_PARAM_UNITS_H): a unit including omx-contract's header first skips it"
#endif

#include <stdio.h>
#include <string.h>

#define COUNT_ROW(code, name) + 1
static const int rows = 0 OMX_PARAM_UNITS(COUNT_ROW);

/* the code -> standard id lookup a reader builds from omx_param_unit_ids.h, joined to the code by its define */
#define ID_ROW(code, token, id) { code, token, id },
static const struct { unsigned code; const char *token, *id; } ids[] = { OMX_PARAM_UNIT_IDS(ID_ROW) };

static const char *id_of(unsigned code)
{
    for (size_t i = 0; i < sizeof ids / sizeof ids[0]; i++)
        if (ids[i].code == code)
            return ids[i].id;
    return NULL;
}

int main(void)
{
    if (OMX_CLAP_UNIT_DBU != 257u || OMX_CLAP_UNIT_LU != 263u) {
        fprintf(stderr, "param_units_both_test: dbu or lu is not at its code\n");
        return 1;
    }
    if ((int)(sizeof ids / sizeof ids[0]) != rows || strcmp(id_of(260u), "dB-oct") != 0 || strcmp(id_of(13u), "dB") != 0 ||
        strcmp(id_of(14u), "percent") != 0 || strcmp(id_of(23u), "deg") != 0 || id_of(264u) != NULL) {
        fprintf(stderr, "param_units_both_test: the ids table does not answer 260 dB-oct, 13 dB, 14 percent, 23 deg\n");
        return 1;
    }
    printf("param_units_both_test: both headers in one unit, %d rows, no row differs\n", rows);
    return 0;
}
