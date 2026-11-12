#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# A package build's tests are the plain tier: the targets the spec's %check and debian/rules' dh_auto_test call build
# nothing with a sanitizer. The sanitizer tiers (thread, address) are jobs of this repository's CI, which has the
# environment they need; a package build has none of it (no libtsan in an rpm build root, a container whose address
# space ThreadSanitizer cannot map), and a tier there fails the release (omx-clap-core#32).
#
#   tests/package-check-plain.sh            the spec and debian/rules of this tree
#   tests/package-check-plain.sh --self-test a scratch copy whose %check calls a sanitizer tier is refused

set -u
cd "$(dirname "$0")/.." || exit 2

# the make targets a file's test step calls: the spec's lines after %check up to the next section, debian/rules'
# override_dh_auto_test recipe
targets() {
    case "$1" in
    *.spec) sed -n '/^%check/,/^%[a-z]/p' "$1" | sed -n 's/^make \([^#]*\)$/\1/p' ;;
    *) sed -n '/^override_dh_auto_test:/,/^$/p' "$1" | sed -n 's/^\t\$(MAKE) \(.*\)$/\1/p' ;;
    esac
}

check() {  # check <spec> <rules>: 0 when the test steps of both build no sanitizer
    bad=0
    for f in "$1" "$2"; do
        t=$(targets "$f" | tr '\n' ' ')
        [ -n "$t" ] || { echo "package-check-plain: $f calls no make target in its test step" >&2; bad=1; continue; }
        # shellcheck disable=SC2086
        s=$(make -n -B $t 2>/dev/null | grep -o -- '-fsanitize=[a-z]*' | sort -u | tr '\n' ' ')
        if [ -n "$s" ]; then
            echo "package-check-plain: $f's test step (make $t) builds with $s: a sanitizer tier is CI's, not a package build's" >&2
            bad=1
        fi
    done
    return $bad
}

if [ "${1:-}" = --self-test ]; then
    t=$(mktemp -d)
    trap 'rm -rf "$t"' EXIT
    sed 's/^make test-package$/make test-lv2/' packaging/omx-clap-host.spec > "$t/omx-clap-host.spec"
    if check "$t/omx-clap-host.spec" debian/rules 2>/dev/null; then
        echo "package-check-plain --self-test: a %check calling test-lv2 (its sanitizer tiers) was not refused" >&2
        exit 1
    fi
    echo "package-check-plain --self-test: ok (a %check calling test-lv2 is refused)"
    exit 0
fi
check packaging/omx-clap-host.spec debian/rules || exit 1
echo "package-check-plain: the package builds' test steps build no sanitizer"
