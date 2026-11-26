<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
omx-clap-host
=============

omx-clap-host hosts CLAP and LV2 audio plugins without a screen. You drive it over a socket
with the same text commands as mod-host, and each plugin appears in your JACK or PipeWire
graph as a client of its own. It is for controllers, mixers and stage rigs on Linux that
already talk to mod-host and want CLAP plugins beside their LV2 ones.

An LV2 plugin runs natively, through lilv in the host's own process, mapped by the LV2 adapter
(`libomx-clap-lv2`). The CLAP hosting core is a library of its own, `libomx-clap`, for
programs that host CLAP plugins themselves. The host, the core and the adapter share one version.

Install
-------

Fedora 45 (x86_64):

    sudo dnf install https://www.openmixer.org/rpm/openmixer-release.noarch.rpm
    sudo dnf install omx-clap-host

Debian trixie and Raspberry Pi OS (arm64):

    cd /tmp && curl -fsSLO https://www.openmixer.org/deb/openmixer-release.deb && sudo apt install ./openmixer-release.deb
    sudo apt update && sudo apt install omx-clap-host

To build on the core: `omx-clap-devel` (`libomx-clap-dev`) and
`pkg-config --cflags --libs omx-clap`.

Start
-----

    omx-clap-scan /usr/lib64/clap/lsp-plugins.clap      # what a CLAP file holds
    omx-clap-host -n -p 5555                            # prints: omx-clap-host ready!

In another terminal (messages end in a NUL byte):

    send() { printf '%s\0' "$1" | nc -w3 127.0.0.1 5555 | tr '\0' '\n'; }
    send "add clap:/usr/lib64/clap/lsp-plugins.clap#in.lsp-plug.limiter_stereo 0"   # resp 0
    send "add lv2:urn:zamaudio:ZamComp 1"                                          # resp 1

Each plugin is now the JACK client `effect_<N>`, with ports `in_<k>` and `out_<k>`.

Documentation
-------------

<https://www.openmixer.org/projects/omx-clap-core>, the manual pages (`man omx-clap-host`,
`man omx-clap-scan`), and in this repository: the features, the packages, what CI tests and a
longer walk-through ([docs/overview.md](docs/overview.md)); every command
([doc/reference.md](doc/reference.md)); LV2 and CLAP support, row by row
([docs/lv2-compatibility.md](docs/lv2-compatibility.md),
[docs/clap-compatibility.md](docs/clap-compatibility.md)); building from source
([BUILDING.md](BUILDING.md)).

Release steps
-------------

The domain document `contract.d/hosting/hosting.json` is the one home of the hosting codes (`HOSTING_*_CODES`, read
by the omx-contract loader; data/ declares none of them, and the reader refuses a second copy). A code is added, changed or
documented there, by hand, in omx-contract's one formatting (`omx-contract fmt`). Its `info.version` is `VERSION`, and an
item added carries that version as its `x-since`. After the `VERSION` bump and before the release commit, raise
`info.version` and commit the file; `make check-domain`, which CI runs, holds it to the newest release tag that carries it
with omx-contract's `domain check`: a code added or removed under an unchanged version is refused by name, and so are two
codes reordered (a new code is appended after the existing ones). Every code carries its doc. `make test-contract`
renders `clap_host_limits.h`, the vocabulary and the TypeScript modules from it (`--with-domain`) and holds them to the
committed files, byte for byte.

Licence
-------

GPL-3.0-or-later. See [COPYING](COPYING).
