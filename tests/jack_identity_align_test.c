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
/* The feeder of the identity tests (tests/jack_identity.c) records the same window it plays, whenever "go" lands in a
 * cycle. Its two process callbacks are driven here cycle by cycle with no server: the recorder's input is the source's
 * output of the same cycle (an identity effect), and the frame time is the cycle's. Each case runs in a child of its
 * own, from the feeder's initial state:
 *   - go before the cycle: the source and the recorder both start in it;
 *   - go between the source's callback and the recorder's in one cycle, as it landed in omx-clap-core#56's red CI run
 *     (the recordings one quantum early against the source, sample 0 of each arm being the source's sample -quantum);
 *   - go after both callbacks of a cycle: both start in the next.
 * In every case each recording equals the source sample for sample. The recorder's callback always runs after the
 * source's: it records the effects, which the graph runs after the source they are linked to. */
#define main jack_identity_main
#include "jack_identity.c"
#undef main

#include <sys/wait.h>

#define QUANTUM 8
#define PREROLL_BLOCKS 2
#define FRAMES 40
#define CYCLES 16

static float g_src_buf[QUANTUM], g_rec_buf[QUANTUM];
/* every sample the source played, in order, to tell where in its stream a recording starts */
static float g_stream[(CYCLES + 4) * QUANTUM];
static long g_nstream;
static jack_nframes_t g_now;
static int g_port_out, g_port_in;

void *jack_port_get_buffer(jack_port_t *port, jack_nframes_t nframes)
{
    (void)nframes;
    return port == (jack_port_t *)&g_port_out ? g_src_buf : g_rec_buf;
}

jack_nframes_t jack_last_frame_time(const jack_client_t *client)
{
    (void)client;
    return g_now;
}

enum order { GO_BEFORE, GO_BETWEEN, GO_AFTER };

static void stream_add(void)
{
    jack_nframes_t i;

    for (i = 0; i < QUANTUM; i++)
        if (g_src_buf[i] != 0.0f)
            g_stream[g_nstream++] = g_src_buf[i];
}

static void cycle(enum order order, int go_here)
{
    src_process(QUANTUM, NULL);
    memcpy(g_rec_buf, g_src_buf, sizeof(g_rec_buf));
    stream_add();
    if (go_here && order == GO_BETWEEN)
        atomic_store(&g_go, 1);
    rec_process(QUANTUM, NULL);
    if (go_here && order == GO_AFTER)
        atomic_store(&g_go, 1);
    g_now += QUANTUM;
}

/* one case, in the calling process: 0 when the recording is the source's window */
static int run_case(enum order order)
{
    int c;
    long i;

    g_recorders = 1;
    g_frames = FRAMES;
    g_preroll_frames = PREROLL_BLOCKS * QUANTUM;
    g_source = calloc(FRAMES, sizeof(float));
    g_rec[0] = calloc(FRAMES, sizeof(float));
    g_out = (jack_port_t *)&g_port_out;
    g_in[0] = (jack_port_t *)&g_port_in;
    g_now = 1000;
    for (c = 0; c < 3; c++)
        cycle(order, 0);
    if (order == GO_BEFORE)
        atomic_store(&g_go, 1);
    cycle(order, 1);
    for (c = 0; c < CYCLES; c++)
        cycle(order, 0);
    if (!atomic_load(&g_done))
    {
        printf("FAIL the recorder did not finish its %d frames\n", FRAMES);
        return 1;
    }
    for (i = 0; i < FRAMES; i++)
        if (g_rec[0][i] != g_source[i])
        {
            long k;

            for (k = 0; k < g_nstream && g_stream[k] != g_rec[0][i]; k++)
                ;
            printf("FAIL sample %ld recorded %g, the source played %g", i, (double)g_rec[0][i], (double)g_source[i]);
            if (k < g_nstream)
                printf(": the recording is the source's stream from frame %ld, its window from frame %ld (%ld frames early, "
                       "a quantum is %d)", k - i, g_preroll_frames, g_preroll_frames - (k - i), QUANTUM);
            printf("\n");
            return 1;
        }
    return 0;
}

int main(void)
{
    static const struct {
        enum order order;
        const char *what;
    } cases[] = {
        { GO_BEFORE, "go before the cycle" },
        { GO_BETWEEN, "go between the source's callback and the recorder's in one cycle" },
        { GO_AFTER, "go after both callbacks of a cycle" },
    };
    size_t n;
    int failed = 0;

    for (n = 0; n < sizeof(cases) / sizeof(cases[0]); n++)
    {
        pid_t pid;
        int status;

        fflush(stdout);
        pid = fork();
        if (pid == 0)
        {
            int rc = run_case(cases[n].order);

            fflush(stdout);
            _exit(rc);
        }
        if (pid < 0 || waitpid(pid, &status, 0) != pid || !WIFEXITED(status) || WEXITSTATUS(status) != 0)
        {
            printf("FAIL %s: the recording is not the window the source played\n", cases[n].what);
            failed++;
            continue;
        }
        printf("ok   %s: the recording is the source's window, sample for sample\n", cases[n].what);
    }
    return failed != 0;
}
