/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * omx-clap-host is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * omx-clap-host is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with omx-clap-host.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

/* The parameter contract's arithmetic on its own, against answers computed elsewhere: SHA-256 against FIPS 180-4's
 * examples, the canonical fingerprint against the contract's worked vector (time_ms, feedback, cutoff,
 * bypass: c248c4dc...), and the shortest decimal against node's String(n) for the same doubles. The fake plugin's fingerprint
 * (tests/fake_plugin.c) is node's SHA-256 of these lines, LF after each:
 *   org.openmixer.param-contract/1
 *   0 latency frame stepped 0 4096 64 1 1
 *   1 activations none stepped 0 1000000000 0 1 9
 *   2 process_calls none stepped 0 1000000000 0 1 9
 *   3 host_preset_load none stepped 0 1000000000 0 1 9
 * (fields TAB-separated). */

#include <stdio.h>

// the reading half (pc_read, pc_entry) is the host test's, through the library
#pragma GCC diagnostic ignored "-Wunused-function"
#include "../src/param_contract.h"
#include "../src/omx_param_unit_ids.h"

#include <omxcontract/omx_contract_limits.h>

// the scale codes are omx-contract's PARAM_SCALES positions: how many scales there are, here; which word stands at which
// ordinal, in main
#define PC_SCALE_COUNT(code, name) +1
_Static_assert(0 OMX_CLAP_PARAM_SCALES(PC_SCALE_COUNT) == OMX_PARAM_SCALES_COUNT, "OMX_CLAP_PARAM_SCALES names every scale of PARAM_SCALES");

#define PC_SCALE_ROW(code, name) { code, name },
static const struct { uint32_t code; const char *name; } g_scales[] = { OMX_CLAP_PARAM_SCALES(PC_SCALE_ROW) };

static long scale_code(const char *name)
{
    for (size_t i = 0; i < sizeof(g_scales) / sizeof(g_scales[0]); i++)
        if (strcmp(g_scales[i].name, name) == 0)
            return g_scales[i].code;
    return -1;
}

static int g_failures;

#define CHECK(cond, ...) \
    do { \
        if (cond) { printf("ok   " __VA_ARGS__); printf("\n"); } \
        else { printf("FAIL " __VA_ARGS__); printf("\n"); g_failures++; } \
    } while (0)

static void sha256_of(const char *text, char hex[65])
{
    struct pc_sha256 s;

    pc_sha256_init(&s);
    pc_sha256_update(&s, text, strlen(text));
    pc_sha256_hex(&s, hex);
}

static struct pc_param row(clap_id id, const char *symbol, uint32_t unit, uint32_t scale, double min, double max, double def,
                           double step, uint32_t flags)
{
    struct pc_param p;

    memset(&p, 0, sizeof(p));
    p.info.id = id;
    p.info.min_value = min;
    p.info.max_value = max;
    p.info.default_value = def;
    p.info.flags = flags;
    p.entry.param_id = id;
    snprintf(p.entry.symbol, sizeof(p.entry.symbol), "%s", symbol);
    p.entry.unit = unit;
    p.entry.scale = scale;
    p.entry.step = step;
    return p;
}

/* a symbol in a whole entry buffer, as a plugin hands it */
static int symbol_ok(const char *symbol)
{
    char buffer[OMX_CLAP_PARAM_CONTRACT_SYMBOL_SIZE] = { 0 };

    snprintf(buffer, sizeof(buffer), "%s", symbol);
    return pc_symbol_ok(buffer);
}

/* omx_param_unit_ids.h's rows as the lookup a C reader writes (docs/units.md of omx-contract, "The render shape") */
static const char *unit_id_of(unsigned code)
{
#define UNIT_ID_ROW(code_define, token, id) if (code == (code_define)) return id;
    OMX_PARAM_UNIT_IDS(UNIT_ID_ROW)
#undef UNIT_ID_ROW
    return NULL;
}

int main(void)
{
    CHECK(scale_code("linear") == OMX_PARAM_SCALES_LINEAR, "linear stands at omx-contract's PARAM_SCALES position %d (%ld)", OMX_PARAM_SCALES_LINEAR, scale_code("linear"));
    CHECK(scale_code("log") == OMX_PARAM_SCALES_LOG, "log stands at omx-contract's PARAM_SCALES position %d (%ld)", OMX_PARAM_SCALES_LOG, scale_code("log"));
    CHECK(scale_code("stepped") == OMX_PARAM_SCALES_STEPPED, "stepped stands at omx-contract's PARAM_SCALES position %d (%ld)", OMX_PARAM_SCALES_STEPPED, scale_code("stepped"));

    /* the unit codes are this tree's (omx_param_units.h, the render of the omx-param-contract domain): the vendor block's
     * four codes of 260 to 263 and the first of it answer by their token */
    /* the code -> standard id lookup a reader builds from omx_param_unit_ids.h, joined to the code by its define */
    {
        struct { unsigned code; const char *id; } want[] = { { 260u, "dBPerOct" }, { 13u, "dB" }, { 14u, "percent" }, { 23u, "deg" }, { 264u, NULL } };
        for (size_t i = 0; i < sizeof want / sizeof want[0]; i++) {
            const char *got = unit_id_of(want[i].code);
            CHECK(want[i].id ? (got && strcmp(got, want[i].id) == 0) : got == NULL, "code %u stands for %s (%s)", want[i].code,
                  want[i].id ? want[i].id : "no id", got ? got : "none");
        }
    }

    CHECK(pc_unit_name(OMX_CLAP_UNIT_DBU) != NULL && strcmp(pc_unit_name(OMX_CLAP_UNIT_DBU), "dbu") == 0 && OMX_CLAP_UNIT_DBU == 257u,
          "257 is dbu");
    CHECK(OMX_CLAP_UNIT_DB_PER_OCT == 260u && strcmp(pc_unit_name(260), "dbPerOct") == 0, "260 is dbPerOct");
    CHECK(OMX_CLAP_UNIT_DB_PER_S == 261u && strcmp(pc_unit_name(261), "dbPerS") == 0, "261 is dbPerS");
    CHECK(OMX_CLAP_UNIT_DBTP == 262u && strcmp(pc_unit_name(262), "dbtp") == 0, "262 is dbtp");
    CHECK(OMX_CLAP_UNIT_LU == 263u && strcmp(pc_unit_name(263), "lu") == 0, "263 is lu");
    CHECK(pc_unit_name(264) == NULL && pc_unit_name(25) == NULL, "264 and 25 are no unit");

    /* node: for (const x of [...]) String(x) */
    static const struct { double value; const char *text; } numbers[] = {
        { 0.1, "0.1" }, { 0.10000000149011612, "0.10000000149011612" }, { 1e21, "1e+21" }, { 1e-7, "1e-7" },
        { 1.23e-18, "1.23e-18" }, { 1.5e300, "1.5e+300" }, { -2.5, "-2.5" }, { 100, "100" },
        { 1e20, "100000000000000000000" }, { 0.000001, "0.000001" }, { 5e-324, "5e-324" },
        { 1.7976931348623157e308, "1.7976931348623157e+308" }, { 20000.5, "20000.5" }, { 12345.678, "12345.678" },
        { -0.0001234, "-0.0001234" }, { 9007199254740994.0, "9007199254740994" }, { 0.0, "0" }, { -0.0, "0" },
        { 1e9, "1000000000" }, { 4096, "4096" },
    };
    struct pc_param vector[4];
    char hex[65], text[48];
    size_t i;

    sha256_of("", hex);
    CHECK(strcmp(hex, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") == 0, "SHA-256 of nothing");
    sha256_of("abc", hex);
    CHECK(strcmp(hex, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") == 0, "SHA-256 of abc");
    sha256_of("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", hex);
    CHECK(strcmp(hex, "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1") == 0, "SHA-256 of two blocks");

    for (i = 0; i < sizeof(numbers) / sizeof(numbers[0]); i++)
    {
        const int n = pc_number(numbers[i].value, text, sizeof(text));

        CHECK(n == (int)strlen(numbers[i].text) && strcmp(text, numbers[i].text) == 0, "%.17g is written %s (%s)",
              numbers[i].value, numbers[i].text, n < 0 ? "none" : text);
    }
    CHECK(pc_number(INFINITY, text, sizeof(text)) == -1 && pc_number(NAN, text, sizeof(text)) == -1, "no form for inf and NaN");

    vector[0] = row(0, "time_ms", 2, 0, 1, 2000, 350, 1, 0);
    vector[1] = row(1, "feedback", 14, 0, 0, 95, 35, 1, 0);
    vector[2] = row(2, "cutoff", 16, 1, 20, 20000, 8000, 0, 0);
    vector[3] = row(3, "bypass", 0, 2, 0, 1, 0, 1, CLAP_PARAM_IS_STEPPED | CLAP_PARAM_IS_BYPASS | CLAP_PARAM_IS_HIDDEN);
    CHECK(pc_fingerprint(vector, 4, hex) == 0
          && strcmp(hex, "c248c4dca4d98f4829bc7aae75e8e8f5f28cfe177c01a686ff4c16838438d6a5") == 0,
          "the worked vector (%s); IS_HIDDEN is not in the flags it serialises", hex);
    vector[1].info.min_value = 0.5;
    CHECK(pc_fingerprint(vector, 4, hex) == 0
          && strcmp(hex, "c248c4dca4d98f4829bc7aae75e8e8f5f28cfe177c01a686ff4c16838438d6a5") != 0, "one bound moved: another fingerprint");

    vector[0] = row(0, "latency", 6, 2, 0, 4096, 64, 1, CLAP_PARAM_IS_STEPPED);
    vector[1] = row(1, "activations", 0, 2, 0, 1e9, 0, 1, CLAP_PARAM_IS_STEPPED | CLAP_PARAM_IS_READONLY);
    vector[2] = row(2, "process_calls", 0, 2, 0, 1e9, 0, 1, CLAP_PARAM_IS_STEPPED | CLAP_PARAM_IS_READONLY);
    vector[3] = row(3, "host_preset_load", 0, 2, 0, 1e9, 0, 1, CLAP_PARAM_IS_STEPPED | CLAP_PARAM_IS_READONLY);
    CHECK(pc_fingerprint(vector, 4, hex) == 0
          && strcmp(hex, "e89aa4a2d94c1b011532ca7f054c182a34b8b13004e017fed2c231b3167a0dc5") == 0,
          "the fake plugin's fingerprint is node's (%s)", hex);

    CHECK(symbol_ok("time_ms") && symbol_ok("_x9") && !symbol_ok("9x") && !symbol_ok("a-b") && !symbol_ok(""),
          "the symbol grammar");

    printf("%s\n", g_failures == 0 ? "param contract test ok" : "FAILED");
    return g_failures == 0 ? 0 : 1;
}
