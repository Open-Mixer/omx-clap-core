/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/*
 * clap_properties_test.c: org.openmixer.properties/1 end to end through this host and the LV2 adapter (lv2-as-clap-adapter
 * spec §10.3, omx-clap-core#15), on omx-property-fixture.lv2: its atom:Path `gainfile` names a file holding a gain in dB,
 * its atom:String `label` is free text.
 *
 *   count    the host answers the properties' event space, so the plugin presents both, with their kinds and flags
 *   level    the path set to a file holding -12 moves the output by -12.00 dB against the unset level (the level moved:
 *            the positive control), and get reads the path back
 *   text     the label round-trips byte for byte, multi-byte UTF-8 included
 *   state    a state saved and loaded into a fresh instance keeps the path and the level
 *
 * Usage: clap_properties_test <build/lv2 directory>
 */
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "clap_host.h"
#include "omx_clap_lv2.h"

#define BLOCK 64u
#define RATE 48000.0
#define FIXTURE_URI "urn:openmixer:test:property-fixture"
#define WAIT_BLOCKS 4000u

static int g_failures;
#define CHECK(cond, ...)                                                                                                    \
    do                                                                                                                      \
    {                                                                                                                       \
        if (cond)                                                                                                           \
        {                                                                                                                   \
            printf("ok   " __VA_ARGS__);                                                                                    \
            printf("\n");                                                                                                   \
        }                                                                                                                   \
        else                                                                                                                \
        {                                                                                                                   \
            printf("FAIL " __VA_ARGS__);                                                                                    \
            printf("\n");                                                                                                   \
            g_failures++;                                                                                                   \
        }                                                                                                                   \
    } while (0)

static float g_l[BLOCK], g_r[BLOCK];

/* one block of a constant 0.5 in, and the output's level: the first sample's magnitude (the gain is constant in a block) */
static float block(struct omx_clap_instance *in)
{
    for (uint32_t i = 0; i < BLOCK; i++)
        g_l[i] = g_r[i] = 0.5f;
    omx_clap_host_run(in, g_l, g_r, BLOCK);
    omx_clap_host_tick(in);
    return fabsf(g_l[BLOCK - 1]);
}

/* blocks until the level differs from `from` by more than `by`, or WAIT_BLOCKS ran: the level then */
static float level_after(struct omx_clap_instance *in, float from, float by)
{
    float l = block(in);

    for (uint32_t n = 0; n < WAIT_BLOCKS && fabsf(l - from) <= by; n++)
    {
        usleep(250);
        l = block(in);
    }
    return l;
}

/* blocks until get answers `want` for `id`, or WAIT_BLOCKS ran: 1 when it did */
static int reads_back(struct omx_clap_instance *in, clap_id id, const char *want)
{
    char got[OMX_CLAP_PROPERTY_VALUE_MAX];

    for (uint32_t n = 0; n < WAIT_BLOCKS; n++)
    {
        const int32_t len = omx_clap_host_property_get(in, id, got, sizeof(got));

        if (len == (int32_t)strlen(want) && strcmp(got, want) == 0)
            return 1;
        usleep(250);
        (void)block(in);
    }
    return 0;
}

static int find(struct omx_clap_instance *in, const char *symbol, omx_clap_property_info_t *info)
{
    const uint32_t n = omx_clap_host_property_count(in);

    for (uint32_t i = 0; i < n; i++)
        if (omx_clap_host_property_info(in, i, info) == 0 && strcmp(info->symbol, symbol) == 0)
            return 1;
    return 0;
}

static struct omx_clap_instance *open_one(const clap_plugin_entry_t *entry)
{
    char why[OMX_CLAP_WHY_MAX] = "";
    struct omx_clap_instance *in = NULL;

    CHECK(omx_clap_host_open_entry(entry, FIXTURE_URI, &in, why) == 0 && in, "%s opens through the adapter (%s)", FIXTURE_URI, why);
    if (!in)
        return NULL;
    CHECK(omx_clap_host_activate(in, RATE, BLOCK, why) == 0, "it activates (%s)", why);
    omx_clap_host_publish(in, pthread_self());
    return in;
}

int main(int argc, char **argv)
{
    char why[OMX_CLAP_WHY_MAX] = "", lv2_why[OMX_CLAP_LV2_WHY_MAX] = "";
    char bundle[PATH_MAX], dir[] = "/var/tmp/clap-properties.XXXXXX", root[PATH_MAX], file[PATH_MAX];
    static const char label[] = "Sala gran \xc3\xa0 la llum \xe2\x9c\x93";   // multi-byte UTF-8
    omx_clap_lv2_config_t config = { omx_clap_lv2_provided, 1000u, 4096u, 0u, 1u, NULL, NULL };
    const clap_plugin_entry_t *entry;
    struct omx_clap_instance *a, *b;
    omx_clap_property_info_t path, text;
    unsigned char state[65536];
    size_t state_len = 0;
    float unset, set, restored;
    FILE *f;

    if (argc < 2)
    {
        fprintf(stderr, "usage: %s <build/lv2 directory>\n", argv[0]);
        return 2;
    }
    if (!mkdtemp(dir))
        return 2;
    snprintf(root, sizeof(root), "%s/state", dir);
    config.state_root = root;
    snprintf(file, sizeof(file), "%s/gain.txt", dir);
    f = fopen(file, "w");
    if (!f)
        return 2;
    fprintf(f, "-12\n");
    fclose(f);
    if (omx_clap_lv2_configure(&config, lv2_why) != 0)
    {
        fprintf(stderr, "configure: %s\n", lv2_why);
        return 1;
    }
    snprintf(bundle, sizeof(bundle), "%s/omx-property-fixture.lv2", argv[1]);
    entry = omx_clap_lv2_entry(bundle, lv2_why);
    CHECK(entry != NULL, "the fixture bundle's entry opens (%s)", lv2_why);
    if (!entry || !(a = open_one(entry)))
        return 1;

    /* count: the host answers the event space, so both properties are presented */
    CHECK(omx_clap_host_property_count(a) == 2, "the plugin presents its two properties (%u)", omx_clap_host_property_count(a));
    CHECK(find(a, "gainfile", &path) && path.kind == OMX_CLAP_PROPERTY_PATH &&
              path.flags == (OMX_CLAP_PROPERTY_IS_WRITABLE | OMX_CLAP_PROPERTY_IS_READABLE),
          "gainfile: a path, writable and readable");
    CHECK(find(a, "label", &text) && text.kind == OMX_CLAP_PROPERTY_STRING &&
              text.flags == (OMX_CLAP_PROPERTY_IS_WRITABLE | OMX_CLAP_PROPERTY_IS_READABLE),
          "label: a string, writable and readable");

    /* level: the file's -12 dB reaches the audio through the path */
    unset = level_after(a, 0.0f, 0.0f);
    CHECK(fabsf(unset - 0.5f) < 1e-6f, "unset, the fixture passes its input (%g)", (double)unset);
    CHECK(omx_clap_host_property_set(a, path.id, file, why) == 0, "the path is set (%s)", why);
    set = level_after(a, unset, 1e-6f);
    CHECK(fabsf(set - unset) > 1e-3f, "positive control: the level moved (%g -> %g)", (double)unset, (double)set);
    CHECK(fabs(20.0 * log10((double)set / (double)unset) + 12.0) < 0.01, "the path to a file holding -12 moves the output by -12.00 dB (%.3f)",
          20.0 * log10((double)set / (double)unset));
    CHECK(reads_back(a, path.id, file), "get reads the path back");

    /* text: byte for byte */
    CHECK(omx_clap_host_property_set(a, text.id, label, why) == 0, "the label is set (%s)", why);
    CHECK(reads_back(a, text.id, label), "the label round-trips byte for byte, multi-byte UTF-8 included");

    /* state: a fresh instance keeps both */
    CHECK(omx_clap_host_state_save(a, state, sizeof(state), &state_len) == 0 && state_len > 0, "the state saves (%zu bytes)", state_len);
    omx_clap_host_unpublish(a, 10, 1000000);
    omx_clap_host_close(a);
    if (!(b = open_one(entry)))
        return 1;
    CHECK(omx_clap_host_state_load(b, state, state_len) >= 0, "a fresh instance loads it");
    restored = level_after(b, 0.5f, 1e-6f);
    CHECK(fabs(20.0 * log10((double)restored / 0.5) + 12.0) < 0.01, "the fresh instance plays at -12.00 dB (%.3f)",
          20.0 * log10((double)restored / 0.5));
    CHECK(find(b, "gainfile", &path) && reads_back(b, path.id, file), "and reads the path back");
    CHECK(find(b, "label", &text) && reads_back(b, text.id, label), "and the label");
    omx_clap_host_unpublish(b, 10, 1000000);
    omx_clap_host_close(b);
    omx_clap_lv2_entry_release(entry);
    printf("clap properties test: %s\n", g_failures ? "FAILED" : "ok");
    return g_failures ? 1 : 0;
}
