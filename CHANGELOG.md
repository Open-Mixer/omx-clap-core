<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- FIXED (#220): the installed omx-clap domain and data/ are read by omx-contract 3.22.0: `info.x-requires` is the name
  list `["host"]`, no data file carries a `requires` floor map, and `HOSTING_VERB_HOSTS` (data/hosting/verb-hosts.json,
  translated) holds the hosts a verb names. tests/requires-names-check.py refuses a floor map. 0.34.2.
