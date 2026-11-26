<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- omx-clap-host gives an embedded window's plugin its scale again (clap.gui `set_scale`) while the window exists, when the screen's `Xft.dpi` resource changes; never a floating window's (#229). `request_show` before the plugin has a window answers false, now held by `tests/window_test.c` (#230).
