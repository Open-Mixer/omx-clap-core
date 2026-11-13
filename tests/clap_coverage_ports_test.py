#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""tests/clap_coverage_ports_test.py: clap_coverage.py's self-test holds up beside other tests (make -j4).

Its fake host listens on a port and on the port after it (the feed). free_port() took a free port and never asked
about the next one, which another test running at the same time can hold: the host then cannot bind its feed, the
sabotaged run dies on a traceback with no FAIL line, and the loop printed that as "stayed green", a false red of the
whole check that is neither the rule nor the sabotage. Deterministic here, no load needed:
  - the port after the first one the system offers is held by this test: free_port() must not hand that one out;
  - a sabotaged run that ends non-zero with no FAIL line is broken, named so with its last line, never green.
"""
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clap_coverage  # noqa: E402

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def bindable(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


# the first port the system offers, with the one after it held, as a test running beside this one would hold it
while True:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    first = probe.getsockname()[1]
    probe.close()
    if first < 65000 and bindable(first + 1):
        break
held = socket.socket()
held.bind(("127.0.0.1", first + 1))
held.listen(1)

real_socket = socket.socket
offered = []


class FirstOffer(real_socket):
    """a socket whose first bind to port 0 lands on `first`, as the system's next offer would"""

    def bind(self, address):
        if address[1] == 0 and not offered:
            offered.append(first)
            return super().bind((address[0], first))
        return super().bind(address)


clap_coverage.socket.socket = FirstOffer
try:
    port = clap_coverage.free_port()
finally:
    clap_coverage.socket.socket = real_socket
    held.close()
check(port != first, "free_port does not hand out a port whose next port is held (%d offered first, %d answered)" % (first, port))
check(bindable(port) and bindable(port + 1), "the port it answers and the one after it are both free (%d)" % port)

verdict = getattr(clap_coverage, "sabotage_verdict", None)
check(verdict is not None, "the sabotage loop's verdict is a function a test can ask")
if verdict:
    red, text = verdict(1, "ok   a\nFAIL scan: the rows differ\n")
    check(red and "red" in text, "a run with a FAIL line and a non-zero exit is red: %s" % text)
    red, text = verdict(0, "ok   a\nok   b\n")
    check(not red and "stayed green" in text, "a run that passes is green, the sabotage unseen: %s" % text)
    red, text = verdict(1, "ok   a\nTraceback (most recent call last):\nOSError: [Errno 98] Address already in use\n")
    check(not red and "broken" in text and "Address already in use" in text and "stayed green" not in text,
          "a run that dies with no FAIL line is broken, named by its last line, never green: %s" % text)

print("clap coverage ports: %s" % ("ok" if not failures else "%d failed" % len(failures)))
sys.exit(1 if failures else 0)
