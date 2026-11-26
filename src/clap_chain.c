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
************************************************************************************************************************
*
* The chain (clap_chain.h, docs/chain.md): the members as the control thread keeps them, in order, and the walk a cycle
* reads, one of two plans. A change builds the spare plan, publishes it with one store and waits for the cycle that may
* still be reading the other to leave, so the cycle reads a plan no control thread writes and takes no lock.
*
************************************************************************************************************************
*/

/*
************************************************************************************************************************
*           INCLUDE FILES
************************************************************************************************************************
*/

#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "clap_chain.h"


/*
************************************************************************************************************************
*           LOCAL DATA TYPES
************************************************************************************************************************
*/

/* a member as the control thread keeps it */
struct chain_slot
{
    uint32_t id;
    struct omx_clap_instance *instance;
    omx_clap_chain_process_fn process;
    void *ctx;
    uint32_t in_channels, out_channels;
    uint32_t latency;
    uint32_t bypass;
};

/* one member of the walk: an instance or a stage */
struct chain_step
{
    struct omx_clap_instance *instance;
    omx_clap_chain_process_fn process;
    void *ctx;
    uint32_t in_channels, out_channels;     // its widths: what reaches it is matched to the first, it writes the second
};

/* the walk a cycle reads: the non-bypassed members in order, and a bypassed member whose widths are not the walk's
 * where it stands as its width change alone (no instance, no process), since a bypassed plugin routed alone still has
 * its ports: Zynthian sums both channels into a mono input and gives a mono output to both */
struct chain_plan
{
    uint32_t steps;
    struct chain_step step[OMX_CLAP_CHAIN_MEMBERS_MAX];
};

struct omx_clap_chain
{
    uint32_t channels;
    omx_clap_chain_latency_fn latency_changed;
    void *ctx;

    pthread_mutex_t lock;                   // every control-thread call; never the cycle
    struct chain_slot slot[OMX_CLAP_CHAIN_MEMBERS_MAX];
    uint32_t count;
    uint32_t next_id;
    uint32_t reported;                      // the latency latency_changed last said

    /* the two plans, the one the cycles read published in `live`, and the cycle's flag while it reads one */
    struct chain_plan plan[2];
    struct chain_plan *_Atomic live;
    _Atomic uint32_t in_cycle;

    /* what omx_clap_chain_report reads without the lock */
    _Atomic uint32_t members, running, latency, revision;
    _Atomic uint64_t passed;

    /* the two blocks between members and the block a member's input is matched to its width in, `channels` channels
     * of OMX_CLAP_CHAIN_FRAMES_MAX frames each, one allocation */
    float *block_mem;
    float *block[2][OMX_HOSTED_STAGE_PORT_CHANNELS];
    float *match[OMX_HOSTED_STAGE_PORT_CHANNELS];
};


/*
************************************************************************************************************************
*           LOCAL FUNCTIONS
************************************************************************************************************************
*/

/* a structure's `abi` and `size` are ones the library reads: this build's ABI at exactly this build's size */
static int abi_ok(uint32_t abi, uint32_t size, size_t size_abi1)
{
    return abi == OMX_CLAP_CHAIN_ABI && size == size_abi1;
}

/* the member with `id`, its index in slot[], or -1 */
static int slot_find(const struct omx_clap_chain *chain, uint32_t id)
{
    uint32_t i;

    for (i = 0; i < chain->count; i++)
        if (chain->slot[i].id == id)
            return (int)i;
    return -1;
}

/* the sum of the non-bypassed members' latencies */
static uint32_t latency_sum(const struct omx_clap_chain *chain)
{
    uint32_t i, sum = 0;

    for (i = 0; i < chain->count; i++)
        if (!chain->slot[i].bypass)
            sum += chain->slot[i].latency;
    return sum;
}

/* under the lock: the walk of the members as they now stand built into the spare plan, published, and the cycle that
 * may still read the old one waited for. The cycle's enter (store in_cycle, load live) and this (store live, load
 * in_cycle) are sequentially consistent: either that cycle loads the new plan, or this sees its flag and waits for its
 * leave. One audio thread per chain, so once the flag reads 0 no cycle reads the old plan, and the next change may
 * build into it. */
static void publish(struct omx_clap_chain *chain)
{
    struct chain_plan *old = atomic_load_explicit(&chain->live, memory_order_relaxed);
    struct chain_plan *next = old == &chain->plan[0] ? &chain->plan[1] : &chain->plan[0];
    uint32_t i, running;

    uint32_t width;

    next->steps = 0;
    running = 0;
    // the width that reaches the first member is its own input's: the caller's ports are matched to it
    width = chain->count ? chain->slot[0].in_channels : chain->channels;
    for (i = 0; i < chain->count; i++)
    {
        const struct chain_slot *slot = &chain->slot[i];
        const int runs = !slot->bypass;

        // a bypassed member as wide as the walk in and out is no step at all: no call, no copy
        if (!runs && slot->in_channels == width && slot->out_channels == width)
            continue;
        next->step[next->steps].instance = runs ? slot->instance : NULL;
        next->step[next->steps].process = runs ? slot->process : NULL;
        next->step[next->steps].ctx = runs ? slot->ctx : NULL;
        next->step[next->steps].in_channels = slot->in_channels;
        next->step[next->steps].out_channels = slot->out_channels;
        next->steps++;
        running += (uint32_t)runs;
        width = slot->out_channels;
    }
    atomic_store(&chain->live, next);
    while (atomic_load(&chain->in_cycle) != 0u)
        usleep(OMX_HOSTED_STAGE_UNPUBLISH_POLL_US);
    atomic_store_explicit(&chain->members, chain->count, memory_order_relaxed);
    atomic_store_explicit(&chain->running, running, memory_order_relaxed);
    atomic_fetch_add_explicit(&chain->revision, 1u, memory_order_relaxed);
}

/* under the lock: the latency summed again; nonzero when latency_changed is to be told, `*frames` the new sum */
static int latency_update(struct omx_clap_chain *chain, uint32_t *frames)
{
    const uint32_t sum = latency_sum(chain);

    atomic_store_explicit(&chain->latency, sum, memory_order_relaxed);
    *frames = sum;
    if (sum == chain->reported)
        return 0;
    chain->reported = sum;
    return chain->latency_changed != NULL;
}

/* the lock released: the latency told when it changed */
static void unlock_and_tell(struct omx_clap_chain *chain, int tell, uint32_t frames)
{
    pthread_mutex_unlock(&chain->lock);
    if (tell)
        chain->latency_changed(chain->ctx, frames);
}

/* RT: `from`, `n` channels, onto `to`, `m` channels, as a host routes one port to another of another width: the same
 * channel when the widths are equal (nothing copied onto itself), a mono channel to every output, every channel
 * summed into a mono one (L+R, as JACK sums two links into one port), and otherwise channel by channel, an output with
 * no input of its number silent. No allocation, no lock */
static void match_width(const float *const *from, uint32_t n, float *const *to, uint32_t m, uint32_t frames)
{
    const size_t bytes = (size_t)frames * sizeof(float);
    uint32_t c, k, i;

    if (n == 1u)
    {
        for (c = 0; c < m; c++)
            if (to[c] != from[0])
                memcpy(to[c], from[0], bytes);
        return;
    }
    if (m == 1u && n > 1u)
    {
        if (to[0] != from[0])
            memcpy(to[0], from[0], bytes);
        for (k = 1; k < n; k++)
            for (i = 0; i < frames; i++)
                to[0][i] += from[k][i];
        return;
    }
    for (c = 0; c < m; c++)
        if (c >= n)
            memset(to[c], 0, bytes);
        else if (to[c] != from[c])
            memcpy(to[c], from[c], bytes);
}

/* RT: `inputs` copied to `outputs`, the buffers that are not the same, matched in width */
static void pass_dry(const float *const *inputs, uint32_t n_in, float *const *outputs, uint32_t n_out, uint32_t frames)
{
    match_width(inputs, n_in, outputs, n_out, frames);
}


/*
************************************************************************************************************************
*           GLOBAL FUNCTIONS
************************************************************************************************************************
*/

int omx_clap_chain_create(const struct omx_clap_chain_config *config, struct omx_clap_chain **out)
{
    struct omx_clap_chain *chain;
    void *mem = NULL;
    uint32_t b, c;

    if (!out)
        return OMX_CLAP_CHAIN_ERR_ARG;
    *out = NULL;
    if (!config)
        return OMX_CLAP_CHAIN_ERR_ARG;
    if (!abi_ok(config->abi, config->size, sizeof(*config)))
        return OMX_CLAP_CHAIN_ERR_ABI;
    if (config->channels == 0 || config->channels > OMX_HOSTED_STAGE_PORT_CHANNELS)
        return OMX_CLAP_CHAIN_ERR_WIDTH;
    chain = calloc(1, sizeof(*chain));
    if (!chain)
        return OMX_CLAP_CHAIN_ERR_MEMORY;
    // the two blocks between members, then the block a member's input is matched to its width in
    if (posix_memalign(&mem, OMX_CLAP_CHAIN_ALIGN, 3u * config->channels * OMX_CLAP_CHAIN_FRAMES_MAX * sizeof(float)) != 0)
    {
        free(chain);
        return OMX_CLAP_CHAIN_ERR_MEMORY;
    }
    memset(mem, 0, 3u * config->channels * OMX_CLAP_CHAIN_FRAMES_MAX * sizeof(float));
    chain->block_mem = mem;
    for (b = 0; b < 3; b++)
        for (c = 0; c < config->channels; c++)
        {
            float *const at = chain->block_mem + ((size_t)b * config->channels + c) * OMX_CLAP_CHAIN_FRAMES_MAX;

            if (b < 2)
                chain->block[b][c] = at;
            else
                chain->match[c] = at;
        }
    chain->channels = config->channels;
    chain->latency_changed = config->latency_changed;
    chain->ctx = config->ctx;
    chain->next_id = 1;
    pthread_mutex_init(&chain->lock, NULL);
    atomic_init(&chain->live, &chain->plan[0]);
    *out = chain;
    return OMX_CLAP_CHAIN_OK;
}

void omx_clap_chain_destroy(struct omx_clap_chain *chain)
{
    if (!chain)
        return;
    pthread_mutex_destroy(&chain->lock);
    free(chain->block_mem);
    free(chain);
}

int omx_clap_chain_add(struct omx_clap_chain *chain, const struct omx_clap_chain_member *member, uint32_t position, uint32_t *id)
{
    struct chain_slot slot;
    uint32_t frames;
    int tell;

    if (!chain || !member)
        return OMX_CLAP_CHAIN_ERR_ARG;
    if (!abi_ok(member->abi, member->size, sizeof(*member)))
        return OMX_CLAP_CHAIN_ERR_ABI;
    if ((member->instance == NULL) == (member->process == NULL))
        return OMX_CLAP_CHAIN_ERR_ARG;
    memset(&slot, 0, sizeof(slot));
    slot.instance = member->instance;
    slot.process = member->process;
    slot.ctx = member->instance ? NULL : member->ctx;
    slot.in_channels = member->instance ? member->instance->main_in.channels : member->in_channels;
    slot.out_channels = member->instance ? member->instance->main_out.channels : member->out_channels;
    slot.latency = member->instance ? omx_clap_host_latency(member->instance) : member->latency;
    slot.bypass = member->bypass != 0;
    // any width from one channel to the chain's joins: a width change between neighbours is matched as a host routes
    // one port to another (match_width), never refused. A member wider than the chain's blocks, or of no channel in or
    // out, is refused
    if (slot.in_channels == 0 || slot.in_channels > chain->channels || slot.out_channels == 0
        || slot.out_channels > chain->channels)
        return OMX_CLAP_CHAIN_ERR_WIDTH;

    pthread_mutex_lock(&chain->lock);
    if (position == OMX_CLAP_CHAIN_END)
        position = chain->count;
    if (position > chain->count)
    {
        pthread_mutex_unlock(&chain->lock);
        return OMX_CLAP_CHAIN_ERR_ARG;
    }
    if (chain->count == OMX_CLAP_CHAIN_MEMBERS_MAX)
    {
        pthread_mutex_unlock(&chain->lock);
        return OMX_CLAP_CHAIN_ERR_FULL;
    }
    slot.id = chain->next_id++;
    memmove(&chain->slot[position + 1], &chain->slot[position], (chain->count - position) * sizeof(chain->slot[0]));
    chain->slot[position] = slot;
    chain->count++;
    publish(chain);
    if (id)
        *id = slot.id;
    tell = latency_update(chain, &frames);
    unlock_and_tell(chain, tell, frames);
    return OMX_CLAP_CHAIN_OK;
}

int omx_clap_chain_remove(struct omx_clap_chain *chain, uint32_t id)
{
    uint32_t frames;
    int i, tell;

    if (!chain)
        return OMX_CLAP_CHAIN_ERR_ARG;
    pthread_mutex_lock(&chain->lock);
    i = slot_find(chain, id);
    if (i < 0)
    {
        pthread_mutex_unlock(&chain->lock);
        return OMX_CLAP_CHAIN_ERR_NO_MEMBER;
    }
    // the member before it now hands its output to the one after it: the walk is built from the members left
    memmove(&chain->slot[i], &chain->slot[i + 1], (chain->count - (uint32_t)i - 1u) * sizeof(chain->slot[0]));
    chain->count--;
    publish(chain);
    tell = latency_update(chain, &frames);
    unlock_and_tell(chain, tell, frames);
    return OMX_CLAP_CHAIN_OK;
}

int omx_clap_chain_order(struct omx_clap_chain *chain, const uint32_t *ids, uint32_t n)
{
    struct chain_slot slot[OMX_CLAP_CHAIN_MEMBERS_MAX];
    uint32_t taken[OMX_CLAP_CHAIN_MEMBERS_MAX];
    uint32_t i, frames;
    int k, tell;

    if (!chain || (!ids && n))
        return OMX_CLAP_CHAIN_ERR_ARG;
    pthread_mutex_lock(&chain->lock);
    if (n != chain->count)
    {
        pthread_mutex_unlock(&chain->lock);
        return OMX_CLAP_CHAIN_ERR_ARG;
    }
    // the new order built aside, every id one member's and none twice, before the members change at all
    memset(taken, 0, sizeof(taken));
    for (i = 0; i < n; i++)
    {
        k = slot_find(chain, ids[i]);
        if (k < 0 || taken[k])
        {
            pthread_mutex_unlock(&chain->lock);
            return k < 0 ? OMX_CLAP_CHAIN_ERR_NO_MEMBER : OMX_CLAP_CHAIN_ERR_ARG;
        }
        taken[k] = 1;
        slot[i] = chain->slot[k];
    }
    memcpy(chain->slot, slot, n * sizeof(slot[0]));
    publish(chain);
    tell = latency_update(chain, &frames);
    unlock_and_tell(chain, tell, frames);
    return OMX_CLAP_CHAIN_OK;
}

int omx_clap_chain_bypass(struct omx_clap_chain *chain, uint32_t id, int bypass)
{
    uint32_t frames;
    int i, tell;

    if (!chain)
        return OMX_CLAP_CHAIN_ERR_ARG;
    pthread_mutex_lock(&chain->lock);
    i = slot_find(chain, id);
    if (i < 0)
    {
        pthread_mutex_unlock(&chain->lock);
        return OMX_CLAP_CHAIN_ERR_NO_MEMBER;
    }
    if (chain->slot[i].bypass != (uint32_t)(bypass != 0))
    {
        chain->slot[i].bypass = bypass != 0;
        publish(chain);
    }
    tell = latency_update(chain, &frames);
    unlock_and_tell(chain, tell, frames);
    return OMX_CLAP_CHAIN_OK;
}

int omx_clap_chain_member_latency_set(struct omx_clap_chain *chain, uint32_t id, uint32_t frames)
{
    uint32_t sum;
    int i, tell;

    if (!chain)
        return OMX_CLAP_CHAIN_ERR_ARG;
    pthread_mutex_lock(&chain->lock);
    i = slot_find(chain, id);
    if (i < 0 || chain->slot[i].instance)
    {
        pthread_mutex_unlock(&chain->lock);
        return i < 0 ? OMX_CLAP_CHAIN_ERR_NO_MEMBER : OMX_CLAP_CHAIN_ERR_ARG;
    }
    chain->slot[i].latency = frames;
    tell = latency_update(chain, &sum);
    unlock_and_tell(chain, tell, sum);
    return OMX_CLAP_CHAIN_OK;
}

int omx_clap_chain_refresh(struct omx_clap_chain *chain)
{
    uint32_t i, frames;
    int tell;

    if (!chain)
        return OMX_CLAP_CHAIN_ERR_ARG;
    pthread_mutex_lock(&chain->lock);
    for (i = 0; i < chain->count; i++)
        if (chain->slot[i].instance)
            chain->slot[i].latency = omx_clap_host_latency(chain->slot[i].instance);
    tell = latency_update(chain, &frames);
    unlock_and_tell(chain, tell, frames);
    return OMX_CLAP_CHAIN_OK;
}

int omx_clap_chain_report(const struct omx_clap_chain *chain, struct omx_clap_chain_report *out)
{
    if (!chain || !out)
        return OMX_CLAP_CHAIN_ERR_ARG;
    if (!abi_ok(out->abi, out->size, sizeof(*out)))
        return OMX_CLAP_CHAIN_ERR_ABI;
    out->channels = chain->channels;
    out->members = atomic_load_explicit(&chain->members, memory_order_relaxed);
    out->running = atomic_load_explicit(&chain->running, memory_order_relaxed);
    out->latency = atomic_load_explicit(&chain->latency, memory_order_relaxed);
    out->revision = atomic_load_explicit(&chain->revision, memory_order_relaxed);
    out->passed = atomic_load_explicit(&chain->passed, memory_order_relaxed);
    return OMX_CLAP_CHAIN_OK;
}

int omx_clap_chain_member_info(struct omx_clap_chain *chain, uint32_t position, struct omx_clap_chain_member_info *out)
{
    const struct chain_slot *slot;

    if (!chain || !out)
        return OMX_CLAP_CHAIN_ERR_ARG;
    if (!abi_ok(out->abi, out->size, sizeof(*out)))
        return OMX_CLAP_CHAIN_ERR_ABI;
    pthread_mutex_lock(&chain->lock);
    if (position >= chain->count)
    {
        pthread_mutex_unlock(&chain->lock);
        return OMX_CLAP_CHAIN_ERR_NO_MEMBER;
    }
    slot = &chain->slot[position];
    out->id = slot->id;
    out->position = position;
    out->in_channels = slot->in_channels;
    out->out_channels = slot->out_channels;
    out->latency = slot->latency;
    out->bypass = slot->bypass;
    out->instance = slot->instance;
    out->ctx = slot->ctx;
    pthread_mutex_unlock(&chain->lock);
    return OMX_CLAP_CHAIN_OK;
}

/* an instance member run by the direct body on the audio thread, its clamp left to the chain's output: `*owed` becomes
 * the instance when its plugin's output was delivered unclamped, so the chain clamps once, at its output, and counts
 * what that moved on the last such member. Its scan for non-finite output is its own and is never left: a NaN or an
 * infinity it makes is discarded there, its input passed, and no member after it, a stateful one least, is handed it.
 * A member that clamps and does not scan keeps its own clamp, which holds a NaN or an infinity at the ceiling before
 * the next member is handed it (omx_clap_direct_defers) */
static void run_direct(struct omx_clap_instance *in, const float *const *from, float *const *to, uint32_t frames,
                       struct omx_clap_instance **owed)
{
    if (omx_clap_host_run_direct(in, from, to, frames, 1u) && omx_clap_direct_defers(&in->stage))
        *owed = in;
}

/* the clamp the members left, once over the chain's output, counted in the clamped samples of the last member that left
 * it */
static void clamp_out(float *const *outputs, uint32_t n_out, uint32_t frames, struct omx_clap_instance *owed)
{
    uint32_t c, moved = 0;

    for (c = 0; c < n_out; c++)
        moved += omx_hosted_clamp(outputs[c], frames);
    if (moved)
        omx_hosted_count(&owed->stage.h.clamped_samples, moved);
}

/* a member's step, on the audio thread: what reaches it, `width` channels of `from`, matched to its input's width in the
 * match block when the two differ, then the member run from there onto `to` (or, bypassed, its input matched to its
 * output's width). No allocation, no lock */
static void run_step(struct omx_clap_chain *chain, const struct chain_step *step, const float *const *from, uint32_t width,
                     float *const *to, uint32_t frames, struct omx_clap_instance **owed)
{
    if (width != step->in_channels)
    {
        match_width(from, width, chain->match, step->in_channels, frames);
        from = (const float *const *)chain->match;
    }
    if (step->instance && omx_clap_direct_fits(&step->instance->stage, from, to))
        run_direct(step->instance, from, to, frames, owed);    // reads `from`, writes `to`: no copy between members
    else if (step->instance)
        omx_clap_host_run_ports(step->instance, from, to, frames);
    else if (step->process)
        step->process(step->ctx, from, to, frames);
    else
        match_width(from, step->in_channels, to, step->out_channels, frames);
}

int omx_clap_chain_process(struct omx_clap_chain *chain, const float *const *inputs, float *const *outputs, uint32_t frames)
{
    if (!chain)
        return OMX_CLAP_CHAIN_ERR_ARG;
    return omx_clap_chain_process_ports(chain, inputs, chain->channels, outputs, chain->channels, frames);
}

int omx_clap_chain_process_ports(struct omx_clap_chain *chain, const float *const *inputs, uint32_t n_in, float *const *outputs,
                                 uint32_t n_out, uint32_t frames)
{
    const struct chain_plan *plan;
    const float *const *from;
    float *const *to = outputs;
    struct omx_clap_instance *owed = NULL;
    uint32_t s, width;

    if (!chain || !inputs || !outputs || n_in == 0 || n_in > chain->channels || n_out == 0 || n_out > chain->channels)
        return OMX_CLAP_CHAIN_ERR_ARG;
    // a cycle longer than the blocks: the chain's input to its output, no member run
    if (frames > OMX_CLAP_CHAIN_FRAMES_MAX)
    {
        pass_dry(inputs, n_in, outputs, n_out, frames);
        atomic_fetch_add_explicit(&chain->passed, 1u, memory_order_relaxed);
        return OMX_CLAP_CHAIN_PASSED;
    }
    atomic_store(&chain->in_cycle, 1u);
    plan = atomic_load(&chain->live);
    if (plan->steps == 0)
        pass_dry(inputs, n_in, outputs, n_out, frames);
    // the first member reads the chain's input, the last writes its output, each between them the block the member
    // before it wrote, the two blocks taken in turn so none is handed its input as its output; what reaches a member
    // is matched to its input's width, and the last member's output to the caller's
    for (s = 0, from = inputs, width = n_in; s < plan->steps; s++, from = (const float *const *)to)
    {
        const struct chain_step *step = &plan->step[s];

        to = s + 1 == plan->steps && step->out_channels == n_out ? outputs : chain->block[s & 1u];
        run_step(chain, step, from, width, to, frames, &owed);
        width = step->out_channels;
    }
    if (plan->steps && (float *const *)from != outputs)
        match_width(from, width, outputs, n_out, frames);
    // one clamp for the chain, at its output, where every member's own would have been
    if (owed)
        clamp_out(outputs, n_out, frames, owed);
    atomic_store_explicit(&chain->in_cycle, 0u, memory_order_release);
    return OMX_CLAP_CHAIN_OK;
}
