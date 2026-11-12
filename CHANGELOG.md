<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
<!-- Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> -->
# Unreleased

Lines for the next release; the release moves them into debian/changelog and the spec.

- `reply.host.instance-already-exists` (resp -2, mod-host's `ERR_INSTANCE_ALREADY_EXISTS`): `add` of an instance number
  the host already has is named in `HOST_REPLY_CODES`, with its English sentence and its Catalan (#34).
- Every number the host answers has its code in `HOST_REPLY_CODES` (#34): `reply.host.uri-invalid` (-101),
  `instantiation-failed` (-102), `preset-uri-invalid` (-104), `state-load-failed` (-105), the audio server's
  `jack-client-creation`, `jack-client-activation`, `jack-client-deactivation`, `jack-port-register`,
  `jack-port-connection`, `jack-port-disconnection` (-201 to -206), `value-out-of-range` (-207) and
  `external-ui-unavailable` (-404), each with its English sentence and its Catalan; tests/host-reply-codes-check.py holds
  every number src/ answers to a code.
