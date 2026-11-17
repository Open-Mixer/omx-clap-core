#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# no-upward-deps-check.sh — omx-clap-core is the lower layer: nothing in its build, tests, CI or packaging needs an
# omx-plugins header or devel package (#117). The panel-description layout is declared here (src/omx_clap_ext.h,
# tests/panel_abi_test.c) and omx-plugins holds its copy to this tree's installed header, never the other way round.
#
#   no-upward-deps-check.sh [--self-test] [--root <dir>]
#
# Scanned: Makefile, src/, lv2/, tests/, fuzz/, .github/workflows/, packaging/*.spec up to its %changelog and
# debian/control (the changelogs are history, docs/ prose). A failure is a line that
#   includes <omx-plugins/...>,
#   asks pkg-config for omxplugins, or
#   names an omx-plugins package (omx-plugins-devel, -clap, -lv2, ...): nothing here installs one, plugins included.
# The tests that load a published omx-plugins plugin live in omx-plugins.
# --self-test runs the check on a scratch tree once clean and once per planted return, each of which must fail.
# Exit 0 held; 1 an upward dependency; 2 usage.
set -euo pipefail

PATTERN='(#[[:space:]]*include[[:space:]]*[<"]omx-plugins/|omxplugins|omx-plugins-[[:alnum:]]+)'

scan() {
    local root=$1 rc=0 f hits
    local files=()
    for f in "$root/Makefile" "$root/debian/control"; do [ -f "$f" ] && files+=("$f"); done
    while IFS= read -r f; do files+=("$f"); done < <(
        find "$root/src" "$root/lv2" "$root/tests" "$root/fuzz" "$root/.github/workflows" -type f 2>/dev/null \
            ! -name no-upward-deps-check.sh | sort)
    for f in "${files[@]}"; do
        hits=$(grep -nE "$PATTERN" "$f" || true)
        [ -z "$hits" ] || { rc=1; printf '%s\n' "$hits" | sed "s|^|${f#"$root"/}:|"; }
    done
    for f in "$root"/packaging/*.spec; do
        [ -f "$f" ] || continue
        hits=$(sed '/^%changelog/,$d' "$f" | grep -nE "$PATTERN" || true)
        [ -z "$hits" ] || { rc=1; printf '%s\n' "$hits" | sed "s|^|${f#"$root"/}:|"; }
    done
    return $rc
}

self_test() {
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/no-upward.XXXXXX")
    trap 'rm -rf "$tmp"' EXIT
    mkdir -p "$tmp/clean/src" "$tmp/clean/tests" "$tmp/clean/.github/workflows" "$tmp/clean/packaging" "$tmp/clean/debian"
    printf 'test:\n\t$(CC) -Isrc -o t t.c\n' >"$tmp/clean/Makefile"
    printf '#include <clap/clap.h>\n' >"$tmp/clean/src/a.c"
    printf 'run: dnf install -y omx-dsp-devel cjson-devel\n' >"$tmp/clean/.github/workflows/ci.yml"
    printf 'BuildRequires: gcc\n\n%%changelog\n' >"$tmp/clean/packaging/x.spec"
    printf 'Source: x\nBuild-Depends: gcc\n' >"$tmp/clean/debian/control"
    if ! "$0" --root "$tmp/clean" >/dev/null; then echo "FAIL the clean tree is refused"; return 1; fi
    local arm n=0 file line what
    local arms=(
        "src/planted.c|#include <omx-plugins/omx_panel_description.h>|an include"
        "Makefile|	@pkg-config --exists omxplugins|a pkg-config ask"
        ".github/workflows/ci.yml|          dnf install -y omx-plugins-devel|a CI install"
        ".github/workflows/ci.yml|          dnf install -y omx-dsp-devel omx-plugins-clap|a CI install of the CLAP plugin package"
        ".github/workflows/ci.yml|          dnf install -y omx-plugins-lv2|a CI install of the LV2 plugin package"
        "packaging/x.spec|BuildRequires: omx-plugins-devel|a spec BuildRequires"
        "debian/control|Build-Depends: omx-plugins-dev|a debian Build-Depends"
    )
    for arm in "${arms[@]}"; do
        IFS='|' read -r file line what <<<"$arm"
        rm -rf "$tmp/arm"; cp -r "$tmp/clean" "$tmp/arm"
        if [ "$file" = packaging/x.spec ]; then sed -i "1i $line" "$tmp/arm/$file"; else printf '%s\n' "$line" >>"$tmp/arm/$file"; fi
        if "$0" --root "$tmp/arm" >/dev/null; then echo "FAIL $what is not found"; return 1; fi
        n=$((n + 1))
    done
    rm -rf "$tmp/arm"; cp -r "$tmp/clean" "$tmp/arm"
    printf '%s\n' '- the omx-plugins-devel headers (history)' >>"$tmp/arm/packaging/x.spec"
    "$0" --root "$tmp/arm" >/dev/null && n=$((n + 1)) || { echo "FAIL a line after %changelog is refused"; return 1; }
    echo "no-upward-deps self-test ok: $n arms"
}

root=$(cd "$(dirname "$0")/.." && pwd)
mode=check
while [ $# -gt 0 ]; do
    case $1 in
        --self-test) mode=self ;;
        --root) root=$2; shift ;;
        *) echo "usage: $0 [--self-test] [--root <dir>]" >&2; exit 2 ;;
    esac
    shift
done
if [ "$mode" = self ]; then self_test; exit $?; fi
if scan "$root"; then echo "no upward dependency: omx-clap-core reads nothing of omx-plugins"; exit 0; fi
echo "no-upward-deps: the lines above need omx-plugins headers or packages; omx-clap-core owns the layout (#117)" >&2
exit 1
