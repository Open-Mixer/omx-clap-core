#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The installed build dependencies meet the spec's BuildRequires ranges, BEFORE a suite runs: each `(<devel> >= <floor>
# with <devel> < <ceiling>)` of packaging/omx-clap-host.spec against the version its pkg-config file reports. A package
# below its floor or at its ceiling is refused BY NAME, with the floor and the installed version, instead of what it
# does later: the consumer link test (tests/core_link_test) gets nothing from `pkg-config --libs omx-clap-core`, whose
# Requires.private carry the same ranges, and reads as undefined references to every symbol (the staged verify of
# 0.32.5, 2026-11-15: staging served omx-contract-devel 3.17.1 above the channel's 3.18.1, below the spec's 3.18.0).
#
#   tests/build-floors.sh [<spec>]      the check; exit 0 met, 1 a package below its floor or at its ceiling, 2 unread
#   tests/build-floors.sh --self-test   a planted set below a floor, at a ceiling and within the range, through the check
#
# PKG_CONFIG names the tool. The pkg-config module of each devel package is the one the Makefile reads.
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
PKG_CONFIG=${PKG_CONFIG:-pkg-config}
# <devel package> <pkg-config module>
MODULES='omx-contract-devel omx-contract
omx-dsp-devel omxdsp
plugin-hostd-protocol-devel plugin-hostd-protocol
plugin-db-devel plugin-db'

# vercmp <a> <b>: -1, 0 or 1, by rpm when it is there, else by sort -V
vercmp() {
    if command -v rpm >/dev/null 2>&1; then rpm --eval "%{lua: print(rpm.vercmp([[$1]], [[$2]]))}"; return; fi
    [ "$1" = "$2" ] && { echo 0; return; }
    [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -1)" = "$1" ] && echo -1 || echo 1
}

check() { # check <spec>: one line per package, exit 1 on any refusal
    local spec=$1 devel mod floor ceiling have rc=0
    [ -r "$spec" ] || { echo "build-floors: no spec $spec" >&2; return 2; }
    while read -r devel mod; do
        [ -n "$devel" ] || continue
        floor=$(sed -n -E "s/^BuildRequires:[[:space:]]*\(${devel}[[:space:]]*>=[[:space:]]*([0-9.]+)[[:space:]]+with[[:space:]]+${devel}[[:space:]]*<[[:space:]]*([0-9.]+)\).*/\1/p" "$spec")
        ceiling=$(sed -n -E "s/^BuildRequires:[[:space:]]*\(${devel}[[:space:]]*>=[[:space:]]*([0-9.]+)[[:space:]]+with[[:space:]]+${devel}[[:space:]]*<[[:space:]]*([0-9.]+)\).*/\2/p" "$spec")
        [ -n "$floor" ] && [ -n "$ceiling" ] || { echo "build-floors: $spec states no (>= floor with < ceiling) range for $devel" >&2; return 2; }
        if ! have=$("$PKG_CONFIG" --modversion "$mod" 2>/dev/null); then
            echo "build-floors: $devel ($mod) is not installed: the spec needs >= $floor < $ceiling"; rc=1; continue
        fi
        if [ "$(vercmp "$have" "$floor")" -lt 0 ]; then
            echo "build-floors: REFUSED $devel $have installed is below the spec's floor $floor (a stale channel or staging set: the suites would read as link or render errors)"; rc=1
        elif [ "$(vercmp "$have" "$ceiling")" -ge 0 ]; then
            echo "build-floors: REFUSED $devel $have installed is at or past the spec's ceiling $ceiling"; rc=1
        else
            echo "ok   build-floors: $devel $have within >= $floor < $ceiling"
        fi
    done <<< "$MODULES"
    return $rc
}

self_test() {
    t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
    local fail=0; ok() { echo "ok   $*"; }; bad() { echo "FAIL $*"; fail=1; }
    cat > "$t/spec" <<'S'
BuildRequires: (omx-contract-devel >= 3.18.0 with omx-contract-devel < 4)
BuildRequires: (omx-dsp-devel >= 0.32.0 with omx-dsp-devel < 0.33)
BuildRequires: (plugin-hostd-protocol-devel >= 0.5.9 with plugin-hostd-protocol-devel < 0.6)
BuildRequires: (plugin-db-devel >= 0.4.2 with plugin-db-devel < 0.5)
S
    plant() { # plant <module> <version>
        printf 'Name: %s\nDescription: planted\nVersion: %s\nCflags:\n' "$1" "$2" > "$t/pc/$1.pc"
    }
    mkdir -p "$t/pc"; plant omx-contract 3.18.1; plant omxdsp 0.32.1; plant plugin-hostd-protocol 0.5.9; plant plugin-db 0.4.4
    out=$(PKG_CONFIG_LIBDIR=$t/pc PKG_CONFIG_PATH='' check "$t/spec" 2>&1) && ok "a set within every range is met" || bad "within the ranges: $out"
    plant omx-contract 3.17.1
    if out=$(PKG_CONFIG_LIBDIR=$t/pc PKG_CONFIG_PATH='' check "$t/spec" 2>&1); then bad "a package below its floor passed: $out"
    elif grep -q 'REFUSED omx-contract-devel 3.17.1 installed is below the spec.s floor 3.18.0' <<< "$out"; then ok "below the floor is refused by name, with the floor and the installed version"
    else bad "below the floor: refused, but not by name: $out"; fi
    plant omx-contract 3.18.1; plant omxdsp 0.33.0
    if out=$(PKG_CONFIG_LIBDIR=$t/pc PKG_CONFIG_PATH='' check "$t/spec" 2>&1); then bad "a package at its ceiling passed: $out"
    elif grep -q 'REFUSED omx-dsp-devel 0.33.0 installed is at or past the spec.s ceiling 0.33' <<< "$out"; then ok "at the ceiling is refused by name"
    else bad "at the ceiling: $out"; fi
    plant omxdsp 0.32.1; rm "$t/pc/plugin-db.pc"
    if out=$(PKG_CONFIG_LIBDIR=$t/pc PKG_CONFIG_PATH='' check "$t/spec" 2>&1); then bad "a missing package passed: $out"
    elif grep -q 'plugin-db-devel (plugin-db) is not installed' <<< "$out"; then ok "a missing package is named"
    else bad "missing: $out"; fi
    sed -i '/omx-contract-devel/d' "$t/spec"
    out=$(PKG_CONFIG_LIBDIR=$t/pc PKG_CONFIG_PATH='' check "$t/spec" 2>&1) && rc=0 || rc=$?
    [ $rc = 2 ] && grep -q 'states no (>= floor with < ceiling) range for omx-contract-devel' <<< "$out" && ok "a spec without a package's range is unread (2), named" || bad "no range: rc=$rc $out"
    [ $fail = 0 ] && echo "build-floors self-test ok"; return $fail
}

case "${1:-}" in
    --self-test) self_test ;;
    *) check "${1:-$here/packaging/omx-clap-host.spec}" ;;
esac
