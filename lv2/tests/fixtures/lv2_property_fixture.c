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
 * lv2_property_fixture.c: the plugin of omx-property-fixture.lv2, a test fixture and never a shipped plugin
 * (lv2-as-clap-adapter spec §10.3, omx-clap-core#15).
 *
 *   urn:openmixer:test:property-fixture   out = in x gain. Its patch:writable, patch:readable atom:Path `gainfile`
 *                                         names a file holding a gain in dB: a patch:Set of it in run() is handed to
 *                                         the worker, work() reads the file, and work_response() is the one place the
 *                                         gain moves. Its atom:String `label` is kept as it is set. Each set is echoed
 *                                         as a patch:Set of the same property on patch_out, and a patch:Get answers
 *                                         both. Its state keeps the path (abstracted by state:mapPath when the host
 *                                         gives it; without it the path is not stored) and the label, and its restore
 *                                         reads the file again.
 *
 * Nothing is allocated or locked in run().
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <lv2/atom/atom.h>
#include <lv2/atom/forge.h>
#include <lv2/atom/util.h>
#include <lv2/core/lv2.h>
#include <lv2/patch/patch.h>
#include <lv2/state/state.h>
#include <lv2/urid/urid.h>
#include <lv2/worker/worker.h>

#define FX_URI "urn:openmixer:test:property-fixture"
#define FX_GAINFILE FX_URI "#gainfile"
#define FX_LABEL FX_URI "#label"
#define FX_TEXT_MAX 4096u

struct urids
{
    LV2_URID atom_path, atom_string, atom_float, atom_object, atom_sequence, atom_urid;
    LV2_URID patch_set, patch_get, patch_property, patch_value;
    LV2_URID gainfile, label;
};

struct fx
{
    const float *in;
    float *out;
    const LV2_Atom_Sequence *patch_in;
    LV2_Atom_Sequence *patch_out;
    LV2_URID_Map *map;
    LV2_Worker_Schedule *schedule;
    LV2_State_Map_Path *map_path;
    struct urids u;
    LV2_Atom_Forge forge;
    float gain;                     // linear, moved only by work_response() and restore
    char path[FX_TEXT_MAX];         // the gainfile path, as last set
    uint32_t path_len;
    char label[FX_TEXT_MAX];
    uint32_t label_len;
    int echo_path, echo_label;      // a set or a Get to answer on patch_out in this run
};

/* the dB a file holds, read on the worker's thread or at restore; 0 dB for a file that cannot be read */
static float db_of_file(const char *path)
{
    FILE *f = fopen(path, "r");
    float db = 0.0f;

    if (f)
    {
        if (fscanf(f, "%f", &db) != 1)
            db = 0.0f;
        fclose(f);
    }
    return db;
}

static LV2_Handle instantiate(const LV2_Descriptor *d, double rate, const char *bundle, const LV2_Feature *const *features)
{
    struct fx *p = calloc(1, sizeof(*p));
    uint32_t i;

    (void)d;
    (void)rate;
    (void)bundle;
    if (!p)
        return NULL;
    for (i = 0; features && features[i]; i++)
    {
        if (!strcmp(features[i]->URI, LV2_URID__map))
            p->map = features[i]->data;
        else if (!strcmp(features[i]->URI, LV2_WORKER__schedule))
            p->schedule = features[i]->data;
        else if (!strcmp(features[i]->URI, LV2_STATE__mapPath))
            p->map_path = features[i]->data;
    }
    if (!p->map || !p->schedule)
    {
        free(p);
        return NULL;
    }
    p->u.atom_path = p->map->map(p->map->handle, LV2_ATOM__Path);
    p->u.atom_string = p->map->map(p->map->handle, LV2_ATOM__String);
    p->u.atom_float = p->map->map(p->map->handle, LV2_ATOM__Float);
    p->u.atom_object = p->map->map(p->map->handle, LV2_ATOM__Object);
    p->u.atom_sequence = p->map->map(p->map->handle, LV2_ATOM__Sequence);
    p->u.atom_urid = p->map->map(p->map->handle, LV2_ATOM__URID);
    p->u.patch_set = p->map->map(p->map->handle, LV2_PATCH__Set);
    p->u.patch_get = p->map->map(p->map->handle, LV2_PATCH__Get);
    p->u.patch_property = p->map->map(p->map->handle, LV2_PATCH__property);
    p->u.patch_value = p->map->map(p->map->handle, LV2_PATCH__value);
    p->u.gainfile = p->map->map(p->map->handle, FX_GAINFILE);
    p->u.label = p->map->map(p->map->handle, FX_LABEL);
    lv2_atom_forge_init(&p->forge, p->map);
    p->gain = 1.0f;
    return p;
}

static void connect_port(LV2_Handle h, uint32_t port, void *data)
{
    struct fx *p = h;

    switch (port)
    {
    case 0: p->in = data; break;
    case 1: p->out = data; break;
    case 2: p->patch_in = data; break;
    case 3: p->patch_out = data; break;
    default: break;
    }
}

/* a text into `dst` when it fits with its NUL, else nothing: the length kept, or the old one */
static void keep_text(char *dst, uint32_t *len, const LV2_Atom *value)
{
    const char *text = LV2_ATOM_BODY_CONST(value);
    uint32_t n = value->size;

    if (n && text[n - 1] == '\0')
        n--;
    if (n + 1u > FX_TEXT_MAX)
        return;
    memcpy(dst, text, n);
    dst[n] = '\0';
    *len = n;
}

static void forge_set(struct fx *p, LV2_URID property, LV2_URID type, const char *text, uint32_t len)
{
    LV2_Atom_Forge_Frame frame;

    if (!lv2_atom_forge_frame_time(&p->forge, 0) || !lv2_atom_forge_object(&p->forge, &frame, 0, p->u.patch_set))
        return;
    lv2_atom_forge_key(&p->forge, p->u.patch_property);
    lv2_atom_forge_urid(&p->forge, property);
    lv2_atom_forge_key(&p->forge, p->u.patch_value);
    lv2_atom_forge_typed_string(&p->forge, type, text, len);
    lv2_atom_forge_pop(&p->forge, &frame);
}

static void run(LV2_Handle h, uint32_t frames)
{
    struct fx *p = h;
    LV2_Atom_Forge_Frame seq;
    uint32_t i;

    if (p->patch_out)
    {
        const uint32_t cap = p->patch_out->atom.size;

        lv2_atom_forge_set_buffer(&p->forge, (uint8_t *)p->patch_out, cap);
        lv2_atom_forge_sequence_head(&p->forge, &seq, 0);
    }
    if (p->patch_in)
        LV2_ATOM_SEQUENCE_FOREACH(p->patch_in, ev)
        {
            const LV2_Atom_Object *obj = (const LV2_Atom_Object *)&ev->body;
            const LV2_Atom *property = NULL, *value = NULL;

            if (ev->body.type != p->u.atom_object)
                continue;
            if (obj->body.otype == p->u.patch_get)
            {
                p->echo_path = p->echo_label = 1;
                continue;
            }
            if (obj->body.otype != p->u.patch_set)
                continue;
            lv2_atom_object_get(obj, p->u.patch_property, &property, p->u.patch_value, &value, 0);
            if (!property || property->type != p->u.atom_urid || !value)
                continue;
            if (((const LV2_Atom_URID *)property)->body == p->u.gainfile && value->type == p->u.atom_path)
            {
                keep_text(p->path, &p->path_len, value);
                // the path to the worker, which reads the file off the audio thread
                p->schedule->schedule_work(p->schedule->handle, p->path_len + 1u, p->path);
                p->echo_path = 1;
            }
            else if (((const LV2_Atom_URID *)property)->body == p->u.label && value->type == p->u.atom_string)
            {
                keep_text(p->label, &p->label_len, value);
                p->echo_label = 1;
            }
        }
    if (p->patch_out)
    {
        if (p->echo_path)
            forge_set(p, p->u.gainfile, p->u.atom_path, p->path, p->path_len);
        if (p->echo_label)
            forge_set(p, p->u.label, p->u.atom_string, p->label, p->label_len);
        lv2_atom_forge_pop(&p->forge, &seq);
    }
    p->echo_path = p->echo_label = 0;
    for (i = 0; i < frames; i++)
        p->out[i] = p->in[i] * p->gain;
}

static LV2_Worker_Status work(LV2_Handle h, LV2_Worker_Respond_Function respond, LV2_Worker_Respond_Handle rh, uint32_t size,
                              const void *data)
{
    float db;

    (void)h;
    if (!size || ((const char *)data)[size - 1] != '\0')
        return LV2_WORKER_ERR_UNKNOWN;
    db = db_of_file(data);
    return respond(rh, sizeof(db), &db);
}

static LV2_Worker_Status work_response(LV2_Handle h, uint32_t size, const void *data)
{
    struct fx *p = h;
    float db;

    if (size != sizeof(db))
        return LV2_WORKER_ERR_UNKNOWN;
    memcpy(&db, data, sizeof(db));
    p->gain = powf(10.0f, db / 20.0f);
    return LV2_WORKER_SUCCESS;
}

static LV2_State_Status save(LV2_Handle h, LV2_State_Store_Function store, LV2_State_Handle sh, uint32_t flags,
                             const LV2_Feature *const *features)
{
    struct fx *p = h;
    LV2_State_Map_Path *map_path = p->map_path;
    uint32_t i;

    (void)flags;
    for (i = 0; features && features[i]; i++)
        if (!strcmp(features[i]->URI, LV2_STATE__mapPath))
            map_path = features[i]->data;
    // a path is kept only through state:mapPath, as the extension asks of a plugin: without it the path is not stored
    if (p->path_len)
    {
        char *abstract = map_path ? map_path->abstract_path(map_path->handle, p->path) : NULL;

        if (abstract)
            store(sh, p->u.gainfile, abstract, strlen(abstract) + 1u, p->u.atom_path, LV2_STATE_IS_POD | LV2_STATE_IS_PORTABLE);
        free(abstract);
    }
    store(sh, p->u.label, p->label, p->label_len + 1u, p->u.atom_string, LV2_STATE_IS_POD | LV2_STATE_IS_PORTABLE);
    return LV2_STATE_SUCCESS;
}

static LV2_State_Status restore(LV2_Handle h, LV2_State_Retrieve_Function retrieve, LV2_State_Handle sh, uint32_t flags,
                                const LV2_Feature *const *features)
{
    struct fx *p = h;
    LV2_State_Map_Path *map_path = p->map_path;
    size_t size;
    uint32_t type, vflags, i;
    const char *v;

    (void)flags;
    for (i = 0; features && features[i]; i++)
        if (!strcmp(features[i]->URI, LV2_STATE__mapPath))
            map_path = features[i]->data;
    v = retrieve(sh, p->u.gainfile, &size, &type, &vflags);
    if (v && type == p->u.atom_path && size && v[size - 1] == '\0')
    {
        char *absolute = map_path ? map_path->absolute_path(map_path->handle, v) : NULL;
        const char *path = absolute ? absolute : v;
        const size_t n = strlen(path);

        if (n + 1u <= FX_TEXT_MAX)
        {
            memcpy(p->path, path, n + 1u);
            p->path_len = (uint32_t)n;
            p->gain = powf(10.0f, db_of_file(p->path) / 20.0f);
        }
        free(absolute);
    }
    v = retrieve(sh, p->u.label, &size, &type, &vflags);
    if (v && type == p->u.atom_string && size && size <= FX_TEXT_MAX && v[size - 1] == '\0')
    {
        memcpy(p->label, v, size);
        p->label_len = (uint32_t)(size - 1u);
    }
    return LV2_STATE_SUCCESS;
}

static const void *extension_data(const char *uri)
{
    static const LV2_Worker_Interface worker = { work, work_response, NULL };
    static const LV2_State_Interface state = { save, restore };

    if (!strcmp(uri, LV2_WORKER__interface))
        return &worker;
    if (!strcmp(uri, LV2_STATE__interface))
        return &state;
    return NULL;
}

static void cleanup(LV2_Handle h) { free(h); }

static const LV2_Descriptor g_descriptor = { FX_URI, instantiate, connect_port, NULL, run, NULL, cleanup, extension_data };

LV2_SYMBOL_EXPORT const LV2_Descriptor *lv2_descriptor(uint32_t index) { return index == 0 ? &g_descriptor : NULL; }
