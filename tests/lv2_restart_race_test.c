// SPDX-License-Identifier: GPL-3.0-or-later
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
 * lv2_restart_race_test: the LV2 adapter's own restart bookkeeping (lv2/clap/lv2_clap.c: latency_active,
 * latency_pending, latency_held_frames, restart_requested), written by latency_watch on the cycle that calls
 * process() and read and written by plugin_activate/plugin_deactivate on the control thread that restarts it, against
 * the same cycle gate omx-clap-host runs its own restart through (cycle_gate_test.c's rig, an LV2 instance in place of
 * the fake CLAP one): the fixture's declared latency (7 frames, taken only once run() has read it) asks this adapter
 * for the one kind of restart test-identity-lv2 exercises and no other e2e test does. Built with -fsanitize=thread
 * (make test-lv2-restart-race-tsan): a cycle reading or writing the shim's restart fields while the control thread's
 * restart does too is a report, and the run halts on it.
 *
 * usage: lv2_restart_race_test <build/lv2 directory>
 */

#include <limits.h>
#include <math.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "clap_host.h"
#include "cycle_gate.h"
#include "omx_clap_lv2.h"

#define BLOCK       64u
#define SAMPLE_RATE 48000.0
#define ROUNDS      200u
#define HOLD_MS     1u
#define FIXTURE_URI "urn:openmixer:test:host-fixture"

static int g_failures;

#define CHECK(cond, ...)                         \
    do                                           \
    {                                            \
        if (cond)                                \
            printf("ok   ");                     \
        else                                     \
        {                                        \
            printf("FAIL ");                     \
            g_failures++;                        \
        }                                        \
        printf(__VA_ARGS__);                     \
        printf("\n");                            \
    } while (0)

struct rig {
    struct omx_clap_instance *in;
    struct omx_cycle_gate gate;
    _Atomic int stop;
    _Atomic uint32_t cycles;
    _Atomic uint32_t nonfinite;
};

/* effects.c process(), the fixture's one in and one out leg: the gate entered, the stage run or the lane dry */
static void *cycles_run(void *arg)
{
    struct rig *r = arg;
    float in[BLOCK], out[BLOCK];
    const float *ins[1] = { in };
    float *outs[1] = { out };
    uint32_t i;

    for (i = 0; i < BLOCK; i++)
        in[i] = 0.25f;
    while (!atomic_load(&r->stop))
    {
        if (omx_cycle_gate_enter(&r->gate) && __atomic_load_n(&r->in->active, __ATOMIC_ACQUIRE) && !omx_cycle_gate_resizing(&r->gate))
            omx_clap_host_run_ports(r->in, ins, outs, BLOCK);
        else
            memcpy(out, in, sizeof(out));
        omx_cycle_gate_leave(&r->gate);
        for (i = 0; i < BLOCK; i++)
            if (!isfinite(out[i]))
            {
                atomic_fetch_add(&r->nonfinite, 1u);
                break;
            }
        atomic_fetch_add(&r->cycles, 1u);
        usleep(20);
    }
    return NULL;
}

/* wait until the cycle thread ran `n` more cycles */
static void cycles_wait(struct rig *r, uint32_t n)
{
    const uint32_t from = atomic_load(&r->cycles);
    unsigned waited = 0;

    while (atomic_load(&r->cycles) - from < n && waited < 2000000u)
    {
        usleep(100);
        waited += 100;
    }
}

int main(int argc, char **argv)
{
    char why[OMX_CLAP_WHY_MAX] = "";
    char lv2_why[OMX_CLAP_LV2_WHY_MAX] = "";
    char bundle[PATH_MAX];
    omx_clap_lv2_config_t config = { omx_clap_lv2_provided, 1000u, 4096u, 0u, HOLD_MS, NULL, NULL };
    const clap_plugin_entry_t *entry;
    struct rig r;
    pthread_t t;
    uint32_t i, restarted = 0, rescanned = 0, failed = 0;

    if (argc < 2)
    {
        fprintf(stderr, "usage: %s <build/lv2 directory>\n", argv[0]);
        return 2;
    }
    if (omx_clap_lv2_configure(&config, lv2_why) != 0)
    {
        fprintf(stderr, "configure: %s\n", lv2_why);
        return 1;
    }
    snprintf(bundle, sizeof(bundle), "%s/omx-host-fixture.lv2", argv[1]);
    entry = omx_clap_lv2_entry(bundle, lv2_why);
    CHECK(entry != NULL, "the fixture bundle's entry opens (%s)", lv2_why);
    if (!entry)
        return 1;

    memset(&r, 0, sizeof(r));
    CHECK(omx_clap_host_open_entry(entry, FIXTURE_URI, &r.in, why) == 0 && r.in, "%s opens through the entry (%s)", FIXTURE_URI, why);
    if (!r.in)
    {
        omx_clap_lv2_entry_release(entry);
        return 1;
    }
    CHECK(omx_clap_host_activate(r.in, SAMPLE_RATE, BLOCK, why) == 0, "it activates (%s)", why);
    (void)omx_clap_host_ports_rescanned(r.in);
    if (pthread_create(&t, NULL, cycles_run, &r) != 0)
    {
        CHECK(0, "the cycle thread starts");
        omx_clap_host_close(r.in);
        return 1;
    }
    omx_clap_host_publish(r.in, t);
    cycles_wait(&r, 8);
    for (i = 0; i < ROUNDS; i++)
    {
        const int ret = omx_cycle_gate_restart(&r.gate, r.in, OMX_HOSTED_STAGE_ROLE_POLL_US, OMX_HOSTED_STAGE_ROLE_TIMEOUT_US);

        if (ret == 0)
            restarted++;
        else if (ret == OMX_CLAP_RESTART_RESCANNED)
            rescanned++;
        else
            failed++;
        cycles_wait(&r, 2);
    }
    cycles_wait(&r, 8);
    CHECK(failed == 0 && restarted + rescanned == ROUNDS,
          "%u restarts under running cycles: %u restarted, %u stopped by a rescan, %u failed", ROUNDS, restarted, rescanned, failed);
    CHECK(atomic_load(&r.nonfinite) == 0, "no cycle wrote a non-finite sample (%u cycles)", atomic_load(&r.cycles));
    atomic_store(&r.stop, 1);
    pthread_join(t, NULL);
    omx_clap_host_stop(r.in);
    omx_clap_host_close(r.in);
    omx_clap_lv2_entry_release(entry);
    return g_failures ? 1 : 0;
}
