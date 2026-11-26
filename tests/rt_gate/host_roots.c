/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/*
 * host_roots.c: the host side's roots as omx-clap-core binds them (make test-rt-gate-control): CLAP's try_push,
 * in_events.size and get, request_exec, tail.changed and request_flush, LV2's schedule_work and log.printf, audio;
 * the respond LV2 work is handed, worker. Clean it reads green; RT_GATE_PLANT=1 (malloc), 2 (a lock) or 3 (a sleep)
 * planted in try_push, and 4 (malloc) in respond, each reads red.
 */
#include <clap/clap.h>
#include <lv2/core/lv2.h>
#include <lv2/log/log.h>
#include <lv2/worker/worker.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef RT_GATE_PLANT
#define RT_GATE_PLANT 0
#endif

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static unsigned char store[64];

static bool try_push(const clap_output_events_t *list, const clap_event_header_t *event)
{
    (void)list;
#if RT_GATE_PLANT == 1
    void *p = malloc(event->size);
    free(p);
#elif RT_GATE_PLANT == 2
    pthread_mutex_lock(&lock);
    pthread_mutex_unlock(&lock);
#elif RT_GATE_PLANT == 3
    const struct timespec ts = { 0, 1000 };
    nanosleep(&ts, NULL);
#endif
    memcpy(store, event, event->size < sizeof store ? event->size : sizeof store);
    return true;
}

static uint32_t in_size(const clap_input_events_t *list) { (void)list; return 0; }
static const clap_event_header_t *in_get(const clap_input_events_t *list, uint32_t index) { (void)list; (void)index; return NULL; }
static bool request_exec(const clap_host_t *host, uint32_t num_tasks) { (void)host; return num_tasks == 0; }
static void tail_changed(const clap_host_t *host) { (void)host; }
static void request_flush(const clap_host_t *host) { (void)host; }

static LV2_Worker_Status schedule_work(LV2_Worker_Schedule_Handle handle, uint32_t size, const void *data)
{
    (void)handle;
    memcpy(store, data, size < sizeof store ? size : sizeof store);
    return LV2_WORKER_SUCCESS;
}

static int log_printf(LV2_Log_Handle handle, LV2_URID type, const char *fmt, ...)
{
    (void)handle; (void)type; (void)fmt;
    return 0;
}

static LV2_Worker_Status respond(LV2_Worker_Respond_Handle handle, uint32_t size, const void *data)
{
    (void)handle;
#if RT_GATE_PLANT == 4
    free(malloc(size));
#endif
    memcpy(store, data, size < sizeof store ? size : sizeof store);
    return LV2_WORKER_SUCCESS;
}

const clap_output_events_t rt_gate_out = { .ctx = NULL, .try_push = try_push };
const clap_input_events_t rt_gate_in = { .ctx = NULL, .size = in_size, .get = in_get };
const clap_host_thread_pool_t rt_gate_pool = { .request_exec = request_exec };
const clap_host_tail_t rt_gate_tail = { .changed = tail_changed };
const clap_host_params_t rt_gate_params = { .rescan = NULL, .clear = NULL, .request_flush = request_flush };
LV2_Worker_Schedule rt_gate_schedule = { .handle = NULL, .schedule_work = schedule_work };
LV2_Log_Log rt_gate_log = { .handle = NULL, .printf = log_printf, .vprintf = NULL };

/* the worker's turn, on the worker thread: the plugin's work gets the host's respond */
void rt_gate_work(const LV2_Worker_Interface *iface, LV2_Handle instance)
{
    static const unsigned char body[8];

    iface->work(instance, respond, NULL, sizeof body, body);
}
