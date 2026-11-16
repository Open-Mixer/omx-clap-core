# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# The test fixtures a consumer's tests load: the fault plugins (one .clap per mode of fault_clap.c) and the worker-gain
# LV2 bundle. This tree includes it, and omx-clap-core-devel ships it flat beside the sources under the fixturesdir of
# omx-clap-core.pc, so the one rule set builds both:
#
#   make -f $(pkg-config --variable=fixturesdir omx-clap-core)/fixtures.mk FIXTURES_OUT=<dir> \
#        CLAP_CFLAGS="$(pkg-config --cflags clap)" fixtures lv2-worker-gain
#
# builds tests/fault-<n>.clap and build/lv2/omx-worker-gain.lv2/ under FIXTURES_OUT (a directory the caller owns; the
# default, the current directory, is what the tree's own build uses). Nothing is written beside the sources.
FIXTURES_HERE := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
FAULT_C ?= $(FIXTURES_HERE)/fault_clap.c
LV2_FIXTURE_DIR ?= $(FIXTURES_HERE)
FIXTURES_OUT ?=
FIXTURES_PFX = $(if $(FIXTURES_OUT),$(FIXTURES_OUT)/)
FIXTURES_CFLAGS ?= -O2 -g -Wall -Wextra -std=gnu99 -fPIC -fvisibility=hidden -D_GNU_SOURCE -pthread
CLAP_CFLAGS ?= $(shell pkg-config --cflags clap 2>/dev/null)
LV2_CFLAGS ?= $(shell pkg-config --cflags lv2 lilv-0 2>/dev/null)
# -ffp-contract=off on the fixtures and the tests: an exact oracle (out == in * gain) holds only when neither side
# fuses a multiply into an add; aarch64's GCC fuses by default and the product's rounding then reads as an error
LV2_FIXTURE_CFLAGS = -O2 -g -Wall -Wextra -Werror -std=gnu99 -fPIC -shared -D_GNU_SOURCE -pthread -ffp-contract=off $(LV2_CFLAGS)

FAULT_MODES = 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
FIXTURES = $(foreach m,$(FAULT_MODES),$(FIXTURES_PFX)tests/fault-$(m).clap)
.PHONY: fixtures lv2-worker-gain
fixtures: $(FIXTURES)
lv2-worker-gain: $(FIXTURES_PFX)build/lv2/omx-worker-gain.lv2/omx-worker-gain.so

$(FIXTURES_PFX)tests/fault-%.clap: $(FAULT_C)
	@mkdir -p $(@D)
	$(CC) $(CLAP_CFLAGS) $(FIXTURES_CFLAGS) -Werror -shared -DOMX_FAULT_MODE=$* -o $@ $< -lm

$(FIXTURES_PFX)build/lv2/omx-worker-gain.lv2/omx-worker-gain.so: $(LV2_FIXTURE_DIR)/lv2_worker_gain.c $(LV2_FIXTURE_DIR)/lv2_worker_gain.h $(wildcard $(LV2_FIXTURE_DIR)/omx-worker-gain.lv2/*.ttl)
	@mkdir -p $(@D)
	cp $(LV2_FIXTURE_DIR)/omx-worker-gain.lv2/*.ttl $(@D)/
	$(CC) $(LV2_FIXTURE_CFLAGS) -DLV2_WORKER_GAIN_BUNDLE -o $@ $< -lm
