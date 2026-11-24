#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# no-upward-deps-check.sh — omx-clap is the lower layer: nothing in its build, tests, CI or packaging needs an
# omx-plugins header or devel package (#117). The panel-description layout is declared here (src/omx_clap_ext.h,
# tests/panel_abi_test.c) and omx-plugins holds its copy to this tree's installed header, never the other way round.
#
#   no-upward-deps-check.sh [--self-test] [--root <dir>]
#
# Scanned, the build's places: Makefile, src/, lv2/, tests/, fuzz/, .github/workflows/ and .github's scripts,
# packaging/ (a spec up to its %changelog), debian/control, debian/rules and the .install files, every *.pc.in and
# .gitmodules (the changelogs are history, docs/ and contract.d/ prose and provenance). A failure is a line that
#   includes <omx-plugins/...>,
#   asks pkg-config for omxplugins, or names it in a Requires (a .pc.in that pulls omx-plugins in),
#   passes an -I path into an omx-plugins tree (-I/usr/include/omx-plugins, -I../omx-plugins/include),
#   reads a sibling checkout (../omx-plugins),
#   clones omx-plugins (git clone ... omx-plugins, a checkout's repository: .../omx-plugins), or
#   names an omx-plugins package (omx-plugins-devel, -clap, -lv2, ...): nothing here installs one, plugins included.
# A tracked path with an omx-plugins component (a submodule's directory, a vendored copy) fails too.
# The runtime places, bench/ and tools/, are held to every form but the package name: they load and report the
# published omx-plugins plugins under test (bench.sh names their installed versions), which is not a build reading
# omx-plugins (#122). The tests that load a published omx-plugins plugin live in omx-plugins.
# --self-test runs the check on a scratch tree once clean and once per planted return, each of which must fail.
# Exit 0 held; 1 an upward dependency; 2 usage.
set -euo pipefail

# the forms a build reads omx-plugins by; PACKAGE, the package names, is held everywhere but the runtime places
BUILD='(#[[:space:]]*include[[:space:]]*[<"]omx-plugins/|omxplugins|^[[:space:]]*Requires(\.private)?:.*omx-?plugins|-I[[:space:]]*[^[:space:]]*omx-plugins|\.\./omx-plugins|git[^[:alnum:]#]{1,4}clone[^#]*omx-plugins|repository:[[:space:]]*[^[:space:]#]*/omx-plugins)'
PACKAGE='omx-plugins-[[:alnum:]]+'
PATTERN="($BUILD|$PACKAGE)"

scan() {
    local root=$1 rc=0 f hits
    local files=()
    local runtime=()
    for f in "$root/Makefile" "$root/debian/control" "$root/debian/rules" "$root"/*.pc.in \
             "$root"/debian/*.install "$root"/.github/*.sh; do
        [ -f "$f" ] && files+=("$f")
    done
    while IFS= read -r f; do files+=("$f"); done < <(
        find "$root/src" "$root/lv2" "$root/tests" "$root/fuzz" "$root/.github/workflows" "$root/packaging" -type f \
            ! -name no-upward-deps-check.sh ! -name '*.spec' 2>/dev/null | sort)
    while IFS= read -r f; do runtime+=("$f"); done < <(find "$root/bench" "$root/tools" -type f 2>/dev/null | sort)
    for f in "${files[@]}"; do
        hits=$(grep -nE "$PATTERN" "$f" || true)
        [ -z "$hits" ] || { rc=1; printf '%s\n' "$hits" | sed "s|^|${f#"$root"/}:|"; }
    done
    for f in "${runtime[@]}"; do
        hits=$(grep -nE "$BUILD" "$f" || true)
        [ -z "$hits" ] || { rc=1; printf '%s\n' "$hits" | sed "s|^|${f#"$root"/}:|"; }
    done
    for f in "$root"/packaging/*.spec; do
        [ -f "$f" ] || continue
        hits=$(sed '/^%changelog/,$d' "$f" | grep -nE "$PATTERN" || true)
        [ -z "$hits" ] || { rc=1; printf '%s\n' "$hits" | sed "s|^|${f#"$root"/}:|"; }
    done
    # a submodule of omx-plugins, by whatever path it is checked out under
    if [ -f "$root/.gitmodules" ]; then
        hits=$(grep -n 'omx-plugins' "$root/.gitmodules" || true)
        [ -z "$hits" ] || { rc=1; printf '%s\n' "$hits" | sed 's|^|.gitmodules:|'; }
    fi
    # a submodule's directory or a vendored copy: a path of the tree with an omx-plugins component
    hits=$(cd "$root" && find . -path ./.git -prune -o -path '*omx-plugins*' -print 2>/dev/null | sed 's|^\./||' || true)
    [ -z "$hits" ] || { rc=1; printf '%s: an omx-plugins path in the tree\n' $hits; }
    return $rc
}

self_test() {
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/no-upward.XXXXXX")
    trap 'rm -rf "$tmp"' EXIT
    mkdir -p "$tmp/clean/src" "$tmp/clean/tests" "$tmp/clean/.github/workflows" "$tmp/clean/packaging" "$tmp/clean/debian" \
             "$tmp/clean/bench" "$tmp/clean/tools"
    printf 'test:\n\t$(CC) -Isrc -o t t.c\n' >"$tmp/clean/Makefile"
    printf '#include <clap/clap.h>\n' >"$tmp/clean/src/a.c"
    printf 'run: dnf install -y omx-dsp-devel cjson-devel\n' >"$tmp/clean/.github/workflows/ci.yml"
    printf 'BuildRequires: gcc\n\n%%changelog\n' >"$tmp/clean/packaging/x.spec"
    printf 'Source: x\nBuild-Depends: gcc\n' >"$tmp/clean/debian/control"
    printf '#!/usr/bin/make -f\n%%:\n\tdh $@\n' >"$tmp/clean/debian/rules"
    printf 'Name: x\nRequires: omxdsp >= 0.34.0\n' >"$tmp/clean/x.pc.in"
    printf 'plugin-hostd 0.20.0\n' >"$tmp/clean/packaging/deps.txt"
    printf '#!/bin/bash\ngit clone -q https://github.com/Open-Mixer/plugin-hostd "$1"\n' >"$tmp/clean/.github/fetch.sh"
    # the runtime places may name the plugin packages under test: bench reports their installed versions
    printf 'rpm -q omx-plugins-clap omx-plugins-lv2\n' >"$tmp/clean/bench/bench.sh"
    printf 'print(1)\n' >"$tmp/clean/tools/t.py"
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
        ".gitmodules|	url = https://github.com/Open-Mixer/omx-plugins|a submodule"
        "Makefile|PANEL_CFLAGS = -I/usr/include/omx-plugins|an -I path"
        "Makefile|	\$(CC) -I../omx-plugins/include -o t t.c|an -I path into a sibling checkout"
        "tests/run.sh|cp ../omx-plugins/include/omx_panel_description.h build/|a sibling checkout read by a test"
        "bench/lib.sh|. ../omx-plugins/tests/lib.sh|a sibling checkout read by the bench"
        ".github/workflows/ci.yml|          git clone --depth 1 https://github.com/Open-Mixer/omx-plugins /tmp/p|a git clone in CI"
        ".github/workflows/ci.yml|          repository: Open-Mixer/omx-plugins|a checkout of omx-plugins in CI"
        ".github/fetch.sh|git clone -q https://github.com/Open-Mixer/omx-plugins \"\$1\"|a git clone in .github's scripts"
        "x.pc.in|Requires: omxdsp >= 0.34.0, omxplugins|a .pc.in Requires"
        "x.pc.in|Requires.private: omx-plugins|a .pc.in Requires.private"
        "debian/rules|	dh_auto_build -- CFLAGS=-I/usr/include/omx-plugins|an -I path in debian/rules"
        "packaging/deps.txt|omx-plugins-devel  omx-plugins-dev  0.19.0|a deps.txt row"
        "tools/t.py|import subprocess; subprocess.run(['git', 'clone', 'https://github.com/Open-Mixer/omx-plugins'])|a git clone in tools/"
        "third_party/omx-plugins/include/omx_panel_description.h|/* vendored */|a vendored copy"
    )
    for arm in "${arms[@]}"; do
        IFS='|' read -r file line what <<<"$arm"
        rm -rf "$tmp/arm"; cp -r "$tmp/clean" "$tmp/arm"
        mkdir -p "$(dirname "$tmp/arm/$file")"
        if [ "$file" = packaging/x.spec ]; then sed -i "1i $line" "$tmp/arm/$file"; else printf '%s\n' "$line" >>"$tmp/arm/$file"; fi
        if "$0" --root "$tmp/arm" >/dev/null 2>&1; then echo "FAIL $what is not found"; return 1; fi
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
if scan "$root"; then echo "no upward dependency: omx-clap reads nothing of omx-plugins"; exit 0; fi
echo "no-upward-deps: the lines above need omx-plugins headers or packages; omx-clap owns the layout (#117)" >&2
exit 1
