#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# No test or bench writes a NUL-ended command by hand: the line protocol's clients are plugin-hostd-tests' lib/protocol.sh
# and the protocol's plugin_hostd_client (python3-plugin-hostd-client; plugin-hostd#177, plugin-hostd-protocol#45), not a
# send() of a script's own. A copy of the shell form
# (printf '%s\0' ... >&<fd>) or of the Python form (sendall(<line>.encode() + b'\0')) is red; the check proves it can
# see one by running on a copy first.
# A script that imports plugin_hostd_client sets sys.dont_write_bytecode before the import: the client is read from
# plugin-hostd's tree (PLUGIN_HOSTD_TESTS_LIB), which a test reads and never writes (a __pycache__ left in it turned the
# stage chain's guard red, wave f45t 2026-11-23); `python3 -I` ignores PYTHONDONTWRITEBYTECODE, so the script says it.
#
#   protocol_client_check.sh [<dir>...]   (default: tests and bench)
set -u
here=$(cd "$(dirname "$0")" && pwd)
shell_copy="printf '%s\\\\0' .*>&"
py_copy="sendall\\(.*b.\\\\0"

scan() {
    grep -rEn --include='*.sh' --exclude=protocol_client_check.sh -e "$shell_copy" "$@" ; grep -rEn --include='*.py' -e "$py_copy" "$@"
}

# every .py that imports the client with no sys.dont_write_bytecode = True above the import, by file:line
bytecode() {
    grep -rlE --include='*.py' '^import plugin_hostd_client' "$@" | while IFS= read -r f; do
        awk -v f="$f" '/^sys\.dont_write_bytecode = True/ { ok = 1 } /^import plugin_hostd_client/ && !ok { print f ":" NR ": imports plugin_hostd_client with bytecode on"; exit }' "$f"
    done
}

# the check sees a copy of each form, so an empty result below means none, not a pattern that matches nothing
probe=$(mktemp -d)
trap 'rm -rf "$probe"' EXIT
printf '%s\n' "send() {" "    printf '%s\\0' \"\$1\" >&3" "}" >"$probe/copy.sh"
printf '%s\n' "    def send(self, line):" "        self.s.sendall(line.encode() + b'\\0')" >"$probe/copy.py"
[ "$(scan "$probe" | wc -l)" -eq 2 ] || { echo "protocol_client_check: cannot see a hand-written send in the probe" >&2; exit 2; }
printf '%s\n' "import sys" "import plugin_hostd_client" "sys.dont_write_bytecode = True" >"$probe/late.py"
printf '%s\n' "import sys" "sys.dont_write_bytecode = True" "import plugin_hostd_client" >"$probe/kept.py"
[ "$(bytecode "$probe")" = "$probe/late.py:2: imports plugin_hostd_client with bytecode on" ] \
    || { echo "protocol_client_check: cannot see an import of the client with bytecode on in the probe" >&2; exit 2; }

[ $# -gt 0 ] || set -- "$here" "$here/../bench"
found=$(scan "$@")
if [ -n "$found" ]; then
    echo "a hand-written NUL-framed send: source lib/protocol.sh or import plugin_hostd_client instead" >&2
    echo "$found" >&2
    exit 1
fi
written=$(bytecode "$@")
if [ -n "$written" ]; then
    echo "an import of plugin_hostd_client that may write __pycache__ into plugin-hostd's tree: set sys.dont_write_bytecode = True before it" >&2
    echo "$written" >&2
    exit 1
fi
echo "protocol_client_check: no test or bench writes its own send, and none writes bytecode into plugin-hostd's tree"
