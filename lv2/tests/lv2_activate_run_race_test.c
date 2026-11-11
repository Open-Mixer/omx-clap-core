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

/*
 * lv2_activate_run_race_test.c — omx-clap-core#3: activate is serialised against the first run.
 *
 * One instance of the host fixture, activated once to prime it, then raced for ROUNDS iterations: one thread calls
 * lv2_instance_activate at an alternating rate (48000/96000), which drops and remakes the instance every time (a
 * real rate change, not a no-op through options:interface), while the other calls lv2_instance_run in a tight loop.
 * Built with -fsanitize=thread (the Makefile's test-lv2-tsan): a run that observes in->handle, in->audio or the
 * worker rings mid-rebuild is a data race TSan reports, which fails the build (TSAN_OPTIONS halt_on_error=1); this
 * binary links no lilv itself, as lv2_host_test does not, so only lv2/core is under the sanitizer.
 *
 *   lv2_activate_run_race_test <build/lv2 directory>
 */
#include <dlfcn.h>
#include <limits.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lv2_core.h"

#define FIXTURE_URI "urn:openmixer:test:host-fixture"
#define ROUNDS 200u
#define BLOCK 64u

static struct lv2_instance *g_in;
static atomic_int g_stop;

static void *activate_thread(void *arg)
{
    char why[LV2_CORE_WHY_MAX] = "";
    uint32_t i;
    (void)arg;

    for (i = 0; i < ROUNDS; i++)
        lv2_instance_activate(g_in, (i & 1u) ? 96000.0 : 48000.0, 1, BLOCK, why);
    g_stop = 1;
    return NULL;
}

static void *run_thread(void *arg)
{
    (void)arg;

    while (!g_stop)
        lv2_instance_run(g_in, BLOCK);
    return NULL;
}

int main(int argc, char **argv)
{
    static const struct lv2_core_config config = { lv2_core_provided, 1000u, 4096u, 0u, NULL, NULL };
    char build[PATH_MAX], dir[PATH_MAX + 32], why[LV2_CORE_WHY_MAX] = "";
    struct lv2_bundle *bundle;
    struct lv2_plugin *p;
    pthread_t act, run;

    if (argc < 2 || !realpath(argv[1], build))
    {
        printf("FAIL usage: lv2_activate_run_race_test <build/lv2>\n");
        return 1;
    }
    if (lv2_core_configure(&config, why) != 0)
    {
        printf("FAIL configure (%s)\n", why);
        return 1;
    }
    snprintf(dir, sizeof(dir), "%s/omx-host-fixture.lv2", build);
    bundle = lv2_bundle_ref(dir, why);
    p = bundle ? lv2_plugin_open(bundle, FIXTURE_URI, why) : NULL;
    lv2_bundle_unref(bundle);
    if (!p || lv2_plugin_load(p, why) != 0)
    {
        printf("FAIL open/load the fixture (%s)\n", why);
        return 1;
    }
    g_in = lv2_instance_new(p);
    if (!g_in || lv2_instance_activate(g_in, 48000.0, 1, BLOCK, why) != 0)
    {
        printf("FAIL prime activate (%s)\n", why);
        return 1;
    }
    if (pthread_create(&act, NULL, activate_thread, NULL) != 0 || pthread_create(&run, NULL, run_thread, NULL) != 0)
    {
        printf("FAIL could not start both threads\n");
        return 1;
    }
    pthread_join(act, NULL);
    pthread_join(run, NULL);
    lv2_instance_free(g_in);
    lv2_plugin_close(p);
    printf("ok   activate and the first run raced from two threads, %u rounds, no report under the thread sanitizer\n", ROUNDS);
    printf("lv2 activate/run race test ok\n");
    return 0;
}
