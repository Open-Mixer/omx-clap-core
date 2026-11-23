#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# .github/plugin-hostd.sh takes plugin-hostd at a release tag (PLUGIN_HOSTD_REF, vX.Y.Z) or at a branch by name
# (PLUGIN_HOSTD_BRANCH), never at a commit: a sha is the dropped pin mechanism. Each arm runs the script and judges its
# refusal by name; none reaches the network (a refusal comes before the fetch).
set -u
here=$(cd "$(dirname "$0")" && pwd)
script=$here/../.github/plugin-hostd.sh
failed=0
tmp=$(mktemp -d) || exit 2
trap 'rm -rf "$tmp"' EXIT

refused() {  # refused <what> <text the refusal names> <env assignment>...
  what=$1 want=$2; shift 2
  if env -u PLUGIN_HOSTD_REF -u PLUGIN_HOSTD_BRANCH "$@" sh "$script" "$tmp/h" >"$tmp/out" 2>&1; then
    echo "FAIL $what: the script took it"; failed=1
  elif grep -q -- "$want" "$tmp/out"; then
    echo "ok   $what: refused by name ($(head -n 1 "$tmp/out"))"
  else
    echo "FAIL $what: refused, but not naming \"$want\": $(head -n 1 "$tmp/out")"; failed=1
  fi
  rm -rf "$tmp/h"
}

refused "a full commit as PLUGIN_HOSTD_REF" "is a commit" PLUGIN_HOSTD_REF=54eee2956b1af815d2e1fd2fb8218a77bb6679db
refused "a branch name as PLUGIN_HOSTD_REF" "is not a release tag" PLUGIN_HOSTD_REF=main
refused "no ref and no branch" "PLUGIN_HOSTD_REF" UNRELATED=1
exit $failed
