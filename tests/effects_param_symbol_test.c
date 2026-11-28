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

/* A CLAP parameter is named by the symbol its org.openmixer.param-contract/1 keeps, as well as by its id in decimal,
 * through the host's own effects.c (this file includes it): param_get, param_set and param_info, and the curve verbs,
 * which read each bound term through the backend's param_get. omx-panel's description serves a contracted CLAP
 * parameter by that symbol (describe's servedSymbolOf: "the name a host sets the parameter by"), and a panel binds its
 * curve with it: `curve_bind 1 0 transfer_curve dynamics threshold=thresholdDb:dB` was refused -103 by plugin-hostd 0.22.4
 * for omx-comp, whose threshold is parameter 0, so Zynthian drew no curve.
 *
 * tests/fake.clap's passthrough states a contract with FAKE_CONTRACT=good: latency (0, writable), activations,
 * process_calls and host_preset_load (1..3, read-only). Only JACK is replaced: the instance is opened and activated by the real core. */

#include "../src/effects.c"
#include "test_util.h"

#define PASSTHROUGH "org.omx-clap-host.test.passthrough"

static int g_dummy_client;

static int add_fake(int id, const char *path)
{
    effect_t *effect = &g_effects[id];
    char why[OMX_CLAP_WHY_MAX];

    memset(effect, 0, sizeof(*effect));
    effect->instance = id;
    effect->jack_client = (jack_client_t *)&g_dummy_client;
    atomic_store(&effect->rate, 48000.0);
    if (omx_clap_host_open(path, PASSTHROUGH, &effect->clap, why) != 0)
    {
        fprintf(stderr, "open %s: %s\n", path, why);
        return -1;
    }
    return omx_clap_host_activate(effect->clap, 48000.0, 64, why);
}

int main(int argc, char **argv)
{
    char by_id[256], by_symbol[256];
    float a = -1.0f, b = -2.0f;
    uint32_t version = 0;
    const char *why = NULL;
    const int fx = 0;

    if (argc != 2)
    {
        fprintf(stderr, "usage: %s <fake.clap>\n", argv[0]);
        return 2;
    }
    setenv("FAKE_CONTRACT", "good", 1);
    CHECK(add_fake(fx, argv[1]) == 0, "the passthrough opens and activates");
    CHECK(omx_clap_host_param_contract(g_effects[fx].clap, &version, &why) == 1, "it carries its contract (%s)", why ? why : "");

    /* read: the symbol and the id answer the same parameter */
    CHECK(effects_get_parameter(fx, "activations", &a) == SUCCESS && effects_get_parameter(fx, "1", &b) == SUCCESS && a == b,
          "param_get by the contract's symbol activations reads parameter 1 (%g, %g)", a, b);

    /* write: the symbol names the parameter the id names */
    CHECK(effects_set_parameter(fx, "latency", 7.0f) == SUCCESS, "param_set by the contract's symbol latency is taken");
    omx_clap_host_settle(g_effects[fx].clap, 200000);
    CHECK(effects_get_parameter(fx, "0", &a) == SUCCESS && a == 7.0f, "and parameter 0 holds it (%g)", a);
    CHECK(effects_get_parameter(fx, "latency", &b) == SUCCESS && b == 7.0f, "read back by the symbol (%g)", b);

    /* param_info: the same answer, whose last word is the symbol */
    CHECK(effects_param_info(fx, "0", by_id, sizeof(by_id)) == SUCCESS
          && effects_param_info(fx, "latency", by_symbol, sizeof(by_symbol)) == SUCCESS && strcmp(by_id, by_symbol) == 0,
          "param_info by the symbol is param_info by the id (%s | %s)", by_id, by_symbol);

    /* a symbol of no parameter, and a name that is no contract symbol, stay refused */
    CHECK(effects_get_parameter(fx, "thresholdDb", &a) == ERR_HOST_INVALID_PARAM_SYMBOL, "a symbol the contract does not hold: -103");
    CHECK(effects_set_parameter(fx, "process calls", 1.0f) == ERR_HOST_INVALID_PARAM_SYMBOL, "the parameter's name is no symbol: -103");
    CHECK(effects_get_parameter(fx, "4", &a) == ERR_HOST_INVALID_PARAM_SYMBOL, "an id clap.params does not list: -103");

    omx_clap_host_close(g_effects[fx].clap);
    printf("%d failure(s)\n", g_failures);
    return g_failures != 0;
}
