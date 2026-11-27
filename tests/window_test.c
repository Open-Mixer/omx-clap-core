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
 * window_test.c: what the host's clap.gui does with no display at all. src/window.c is compiled into the test, without
 * xcb, and its windows are made on window APIs this file owns: one embedded, whose output's scale the test sets, and
 * one floating. The plugin is a clap.gui of this file's that counts its calls.
 *
 *   ./tests/window_test
 *
 *  1. REQUEST_SHOW BEFORE A GUI EXISTS (#230): the plugin's request_show with no window of it answers false, and makes
 *     none: no create is called on the tick. With its window made it answers true and the tick shows it; after the
 *     remove it answers false again.
 *  2. THE SCALE IS GIVEN AGAIN (#229): an embedded window's plugin is given its output's scale at the create, and again
 *     on the tick after a display says the scale may have changed (scale_moved, what x_events calls on a new
 *     RESOURCE_MANAGER), only when it did change. The tick reads no scale unless a display said so. A floating
 *     window's plugin is never given one, even on an API that knows its output's scale; nor a removed window's.
 */

#include "../src/window.c"

static int g_failures;

#define CHECK(cond, ...) \
    do { \
        if (cond) { printf("ok   " __VA_ARGS__); printf("\n"); } \
        else { printf("FAIL " __VA_ARGS__); printf("\n"); g_failures++; } \
    } while (0)

/* the plugin's clap.gui calls, counted */
static unsigned g_creates, g_shows, g_hides, g_destroys, g_scales;
static double g_scale_given;

static bool gui_is_api_supported(const clap_plugin_t *p, const char *api, bool floating) { (void)p; (void)api; (void)floating; return true; }
static bool gui_create(const clap_plugin_t *p, const char *api, bool floating) { (void)p; (void)api; (void)floating; g_creates++; return true; }
static void gui_destroy(const clap_plugin_t *p) { (void)p; g_destroys++; }
static bool gui_set_scale(const clap_plugin_t *p, double scale) { (void)p; g_scales++; g_scale_given = scale; return true; }
static bool gui_set_parent(const clap_plugin_t *p, const clap_window_t *w) { (void)p; (void)w; return true; }
static bool gui_show(const clap_plugin_t *p) { (void)p; g_shows++; return true; }
static bool gui_hide(const clap_plugin_t *p) { (void)p; g_hides++; return true; }

static const clap_plugin_gui_t g_gui = {
    .is_api_supported = gui_is_api_supported, .create = gui_create, .destroy = gui_destroy, .set_scale = gui_set_scale,
    .set_parent = gui_set_parent, .show = gui_show, .hide = gui_hide,
};

static const void *plugin_get_extension(const clap_plugin_t *p, const char *id) { (void)p; return !strcmp(id, CLAP_EXT_GUI) ? &g_gui : NULL; }

static const clap_plugin_descriptor_t g_desc = { .clap_version = CLAP_VERSION_INIT, .id = "org.omx-clap-host.test.window" };
static const clap_plugin_t g_plugin = { .desc = &g_desc, .get_extension = plugin_get_extension };

/* the scale of the output the embedded window is on, as the test moves it */
static double g_output_scale = 1.0;
static unsigned g_scale_reads;

static int api_connect(void) { return 0; }
static void api_release(void) { }
static double api_scale(const struct window *w) { (void)w; g_scale_reads++; return g_output_scale; }

/* both count with the Wayland windows: the tick serves those with no X connection open, as it serves these */
static const struct window_api g_embedded = { CLAP_WINDOW_API_X11, 0, api_connect, api_release, &g_wl_open, api_scale };
static const struct window_api g_floating = { CLAP_WINDOW_API_WAYLAND, 1, api_connect, api_release, &g_wl_open, api_scale };

/* a plugin instance as the library hands one out: the host object's host_data is the instance */
static void instance(struct omx_clap_instance *in)
{
    memset(in, 0, sizeof(*in));
    in->desc = &g_desc;
    in->plugin = &g_plugin;
    in->host.host_data = in;
}

/* the plugin's window made on `api` as window_make makes it, with the scale an embedded one is given before its size */
static struct window *made(struct omx_clap_instance *in, const struct window_api *api)
{
    struct window *w = window_claim(in, &g_gui, api);

    if (!w || !g_gui.create(&g_plugin, api->name, api->floating))
        return NULL;
    w->created = 1;
    (*api->open)++;
    if (!api->floating)
        window_scale(w, NULL);
    return w;
}

static void request_show_before_a_gui(void)
{
    struct omx_clap_instance in;
    const char *code = NULL;
    struct window *w;

    instance(&in);
    g_creates = g_shows = 0;
    CHECK(!g_host_gui.request_show(&in.host), "request_show before the plugin has a window answers false");
    window_idle();
    CHECK(g_creates == 0 && g_shows == 0 && !window_of(&in), "and makes none: no create, no show, no window on the tick");
    CHECK(!g_host_gui.request_show(NULL), "request_show with no host answers false");

    w = made(&in, &g_embedded);
    CHECK(w && window_unhide(w, &code) == 0 && g_shows == 1, "the plugin's window made and shown");
    window_conceal(w);
    CHECK(g_host_gui.request_show(&in.host), "request_show with its window made answers true");
    window_idle();
    CHECK(g_shows == 2 && w->visible, "and the tick shows it (%u shows)", g_shows);
    window_close(&in);
    CHECK(!g_host_gui.request_show(&in.host), "request_show after the remove answers false again");
    window_idle();
    CHECK(g_creates == 1 && !window_of(&in), "and makes no window either");
}

static void scale_given_again(void)
{
    struct omx_clap_instance in, fl;
    struct window *w;
    unsigned reads;

    instance(&in);
    g_scales = 0;
    g_output_scale = 1.0;
    w = made(&in, &g_embedded);
    CHECK(w && g_scales == 1 && g_scale_given == 1.0, "the embedded window's plugin is given its output's scale, 1.0, at the create");

    g_output_scale = 2.0;
    reads = g_scale_reads;
    window_idle();
    CHECK(g_scales == 1 && g_scale_reads == reads, "no display said the scale moved: the tick reads none and gives none");

    scale_moved();
    window_idle();
    CHECK(g_scales == 2 && g_scale_given == 2.0, "the output's scale became 2.0 and a display said so: set_scale 2.0 on the tick (%u calls, %.1f)",
          g_scales, g_scale_given);
    window_idle();
    CHECK(g_scales == 2, "once: the next tick gives it no more");

    scale_moved();
    window_idle();
    CHECK(g_scales == 2, "a display said it moved and the scale is still 2.0: not given again");

    g_output_scale = 1.5;
    scale_moved();
    window_idle();
    CHECK(g_scales == 3 && g_scale_given == 1.5, "moved to an output of scale 1.5: set_scale 1.5 (%.1f)", g_scale_given);

    instance(&fl);
    w = made(&fl, &g_floating);
    g_output_scale = 3.0;
    scale_moved();
    window_idle();
    CHECK(w && g_scales == 4 && g_scale_given == 3.0, "the embedded one is given 3.0 beside a floating window (%u calls)", g_scales);
    window_close(&in);
    g_output_scale = 2.0;
    scale_moved();
    window_idle();
    CHECK(g_scales == 4, "a floating window's plugin is never given a scale, on an API that knows one; nor a removed window's");
    window_close(&fl);
}

int main(void)
{
    window_init();
    request_show_before_a_gui();
    scale_given_again();
    if (g_failures)
    {
        printf("window test FAILED (%d)\n", g_failures);
        return 1;
    }
    printf("window test ok\n");
    return 0;
}
