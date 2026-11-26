#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# fixtures-install-check.sh — the test fixtures a consumer's tests load are what the devel package ships: installed
# under a scratch prefix, omx-clap.pc names their directory (fixturesdir), and that directory alone builds the
# fault fixtures and the worker-gain LV2 bundle into a directory the caller owns, the installed tree read-only.
#
#   fixtures-install-check.sh <scratch dir>
#
# make install-fixtures puts the sources there; the checks read the variable, never a path of their own.
# Exit 0 held; 1 a failure; 2 usage.
set -eu

[ "$#" -eq 1 ] || { sed -n '9p' "$0" >&2; exit 2; }
work=$1
root=$work/root
out=$work/out
# a red run must not leave the installed tree read-only, or the next run cannot remove it
[ -d "$work" ] && chmod -R u+w "$work"
rm -rf "$work"
mkdir -p "$work"
trap 'chmod -R u+w "$work"' EXIT
make -s --no-print-directory install-fixtures install-pc PREFIX="$root/usr" LIBDIR="$root/usr/lib"
dir=$(PKG_CONFIG_PATH="$root/usr/lib/pkgconfig" pkg-config --variable=fixturesdir omx-clap 2>/dev/null) \
  || { echo "fixtures-install-check: omx-clap.pc declares no fixturesdir" >&2; exit 1; }
[ -n "$dir" ] || { echo "fixtures-install-check: omx-clap.pc declares no fixturesdir" >&2; exit 1; }
[ -f "$dir/fixtures.mk" ] || { echo "fixtures-install-check: $dir ships no fixtures.mk" >&2; exit 1; }
chmod -R a-w "$dir"
make -s -f "$dir/fixtures.mk" FIXTURES_OUT="$out" CLAP_CFLAGS="$(pkg-config --cflags clap 2>/dev/null)" fixtures lv2-worker-gain
n=0
for f in "$out"/tests/fault-*.clap; do [ -f "$f" ] && n=$((n + 1)); done
[ "$n" -ge 18 ] || { echo "fixtures-install-check: $n fault fixtures built, expected 18" >&2; exit 1; }
[ -f "$out/build/lv2/omx-worker-gain.lv2/omx-worker-gain.so" ] || { echo "fixtures-install-check: no worker-gain binary" >&2; exit 1; }
[ -f "$out/build/lv2/omx-worker-gain.lv2/manifest.ttl" ] || { echo "fixtures-install-check: no worker-gain manifest" >&2; exit 1; }
echo "fixtures-install-check: $n fault fixtures and the worker-gain bundle built from $dir"
