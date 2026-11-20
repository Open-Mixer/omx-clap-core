#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# plugin-hostd at the release tag PLUGIN_HOSTD_REF names, or at the tip of the branch PLUGIN_HOSTD_BRANCH names (the chain
# passes plugin-hostd's chain head through that variable for omx-clap's tests), fetched into a directory: its protocol and pin headers are what
# this host builds against, and its daemon is what the pin test runs behind.
#
#   plugin-hostd.sh <dir>
set -eu

dir=${1:?usage: plugin-hostd.sh <dir>}
if [ -n "${PLUGIN_HOSTD_BRANCH:-}" ]; then
  # a branch by name: fetched, FETCH_HEAD checked out (no sha pinned, no ref: on a checkout); the sha it resolved to is
  # printed, and a branch that does not resolve is refused by name
  git init -q "$dir"
  git -C "$dir" fetch -q --depth 1 https://github.com/Open-Mixer/plugin-hostd "refs/heads/$PLUGIN_HOSTD_BRANCH" \
    || { echo "plugin-hostd.sh: the branch $PLUGIN_HOSTD_BRANCH of plugin-hostd does not resolve" >&2; exit 1; }
  git -C "$dir" checkout -q FETCH_HEAD
  echo "plugin-hostd at $PLUGIN_HOSTD_BRANCH: $(git -C "$dir" rev-parse HEAD)"
  git config --global --add safe.directory "$(readlink -f "$dir")"
  exit 0
fi
ref=${PLUGIN_HOSTD_REF:?PLUGIN_HOSTD_REF (a release tag, vX.Y.Z) or PLUGIN_HOSTD_BRANCH (a branch name)}
# A release tag (vX.Y.Z) or a branch by name (PLUGIN_HOSTD_BRANCH above), never a commit: a sha is a pin, and a pin is
# the stopgap that was dropped
case $ref in
  v[0-9]*.[0-9]*.[0-9]*) want=refs/tags/$ref ;;
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]*) echo "PLUGIN_HOSTD_REF is $ref, which is a commit: take a release tag (vX.Y.Z), or a branch through PLUGIN_HOSTD_BRANCH" >&2; exit 1 ;;
  *) echo "PLUGIN_HOSTD_REF is $ref, which is not a release tag (vX.Y.Z): a branch goes through PLUGIN_HOSTD_BRANCH" >&2; exit 1 ;;
esac
git init -q "$dir"
git -C "$dir" fetch -q --depth 1 https://github.com/Open-Mixer/plugin-hostd "$want"
git -C "$dir" checkout -q FETCH_HEAD
git config --global --add safe.directory "$(readlink -f "$dir")"
