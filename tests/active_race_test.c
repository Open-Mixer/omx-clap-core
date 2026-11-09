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

/* active_race_test: the instance's `active` flag is written by the control thread (activate, deactivate) and read by
 * threads that hold no lock: effects.c's process() and idle read it as the flag the cycle gate leaves open to them. Two
 * threads, the control thread toggling the flag through omx_clap_host_activate and omx_clap_host_deactivate and a reader
 * loading it, once with the atomic load effects.c uses and once as cycle_gate.h reads it. Built with
 * -fsanitize=thread (make test-active-race-tsan): a plain write racing either read is a report, and the run halts on it.
 *
 * usage: active_race_test <fake.clap> */

#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>

#include "clap_host.h"

#define BLOCK       64u
#define SAMPLE_RATE 48000.0
#define ROUNDS      200u
#define STEREO_MONO "org.omx-clap-host.test.stereo-mono"

static _Atomic int g_stop;

static void *reader(void *arg)
{
    struct omx_clap_instance *in = arg;
    unsigned seen = 0;

    while (!atomic_load(&g_stop))
        seen += (__atomic_load_n(&in->active, __ATOMIC_ACQUIRE) != 0) + (in->active != 0);
    return (void *)(size_t)seen;
}

int main(int argc, char **argv)
{
    struct omx_clap_host_config config;
    struct omx_clap_instance *in = NULL;
    char why[OMX_CLAP_WHY_MAX] = "";
    pthread_t t;
    unsigned i, bad = 0;

    if (argc < 2)
    {
        fprintf(stderr, "usage: %s <fake.clap>\n", argv[0]);
        return 2;
    }
    omx_clap_host_config_default(&config);
    config.lane_channels = 0;
    if (omx_clap_host_configure(&config) != 0 || omx_clap_host_open(argv[1], STEREO_MONO, &in, why) != 0 || !in)
    {
        fprintf(stderr, "cannot open %s: %s\n", STEREO_MONO, why);
        return 1;
    }
    if (pthread_create(&t, NULL, reader, in) != 0)
        return 1;
    for (i = 0; i < ROUNDS; i++)
    {
        if (omx_clap_host_activate(in, SAMPLE_RATE, BLOCK, why) != 0)
            bad++;
        omx_clap_host_deactivate(in);
    }
    atomic_store(&g_stop, 1);
    pthread_join(t, NULL);
    omx_clap_host_close(in);
    printf("%s active race test: %u rounds, %u refused activations\n", bad ? "FAIL" : "ok", ROUNDS, bad);
    return bad ? 1 : 0;
}
