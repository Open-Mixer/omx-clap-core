#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The scan domain's install and requirements (omx-contract docs/consumer-move.md, step 6), read from the tree, no build:
#   - make install-contract installs the domain by the installer's domain mode, `install-contract-dir.sh --domain contract.d/scan`,
#     and writes no `install` line of its own for it;
#   - the data package omx-clap-core-contract lists it: the rpm as %{omx_contract_domain_dir}/scan/, the deb as
#     usr/share/omx-contract/contract.d/scan, and neither package lists the domain anywhere else;
#   - the reader, omx-clap-host (it ships omx-clap-scan), requires the loader (libomx-domain, libomx-domain0) and the data package, and
#     the source builds with the loader's headers (libomx-domain-devel, libomx-domain-dev), omx-contract at 3.20.0, the first release
#     that ships the loader and the installer's domain mode: a floor in every place that names omx-contract, none below it.
# usage: tests/domain-packaging-check.sh
set -eu
fail() { echo "domain-packaging-check: $1" >&2; exit 1; }
spec=packaging/omx-clap-host.spec
# the installer, in make install-contract
grep -Eq '(install-contract-dir\.sh|\$\(INSTALL_CONTRACT_DIR\)) +--domain +contract\.d/scan( |$)' Makefile || fail "Makefile: install-contract does not call the installer's --domain mode for contract.d/scan"
! grep -En '^[[:space:]]*install .*contract\.d/scan' Makefile || fail "Makefile: a hand-written install line for contract.d/scan (the installer's domain mode installs it)"
# the data package lists it
contract_files=$(awk '/^%files -n omx-clap-core-contract/{f=1;next} /^%files|^%package|^%changelog/{f=0} f' "$spec")
printf '%s\n' "$contract_files" | grep -qx '%{omx_contract_domain_dir}/scan/' || fail "$spec: omx-clap-core-contract does not list %{omx_contract_domain_dir}/scan/"
grep -qx 'usr/share/omx-contract/contract.d/scan' debian/omx-clap-core-contract.install || fail "debian/omx-clap-core-contract.install does not list usr/share/omx-contract/contract.d/scan"
# the reader requires the loader and the data package
req() { grep -Eq "$1" "$spec" || fail "$spec: $2"; }
req '^BuildRequires: libomx-domain-devel >= 3\.20\.0$' "no BuildRequires: libomx-domain-devel >= 3.20.0"
host=$(awk '/^%description$/{exit} {print}' "$spec")
printf '%s\n' "$host" | grep -qx 'Requires: libomx-domain >= 3.20.0' || fail "$spec: omx-clap-host does not require libomx-domain >= 3.20.0"
printf '%s\n' "$host" | grep -qx 'Requires: omx-clap-core-contract = %{version}-%{release}' || fail "$spec: omx-clap-host does not require omx-clap-core-contract at its own version"
grep -Eq '^Build-Depends:|^ +libomx-domain-dev \(>= 3\.20\.0~\)' debian/control && grep -Eq 'libomx-domain-dev \(>= 3\.20\.0~\)' debian/control || fail "debian/control: no Build-Depends libomx-domain-dev (>= 3.20.0~)"
awk '/^Package: omx-clap-host$/{f=1;next} /^Package:/{f=0} f' debian/control | grep -Eq '^Depends:.*libomx-domain0 \(>= 3\.20\.0~\)' || fail "debian/control: omx-clap-host does not depend on libomx-domain0 (>= 3.20.0~)"
awk '/^Package: omx-clap-host$/{f=1;next} /^Package:/{f=0} f' debian/control | grep -Eq '^Depends:.*omx-clap-core-contract \(= \$\{source:Version\}\)' || fail "debian/control: omx-clap-host does not depend on omx-clap-core-contract at its own version"
# omx-contract at 3.20.0 everywhere the tree names it
low=$( { awk '/^%changelog/{exit} {print FILENAME":"FNR":"$0}' "$spec"; awk '{print FILENAME":"FNR":"$0}' debian/control; } | grep -E '(omx-contract(-devel|-data)?|libomx-contract-dev) *(>=|\(>=) *3\.1[0-9]\.[0-9]+' || true)
[ -z "$low" ] || fail "an omx-contract floor below 3.20.0 is still declared: $(printf '%s' "$low" | head -3 | tr '\n' ' ')"
# a floor and no ceiling: omx-contract's packages are named by their floor only (the rule: floors only), in the spec above its
# changelog, in debian/control and in the workflow's installs
ceil=$( { awk '/^%changelog/{exit} {print FILENAME":"FNR":"$0}' "$spec"; awk '{print FILENAME":"FNR":"$0}' debian/control; awk '{print FILENAME":"FNR":"$0}' .github/workflows/ci.yml; } \
  | grep -E "(omx-contract(-devel|-data)?|libomx-contract-dev)[ ']*(<|<<|\(<<|\(<) *[0-9]|(omx-contract(-devel|-data)?|libomx-contract-dev)[^;]*(with|and) +(omx-contract(-devel|-data)?|libomx-contract-dev) *< *[0-9]" || true)
[ -z "$ceil" ] || fail "omx-contract is bounded above (floors only, no ceiling): $(printf '%s' "$ceil" | head -3 | cut -c1-150 | tr '\n' ' ')"
# omx-dsp the same: floor 0.33.0 (the release the scanner and the host are built on) in every place, and no ceiling
dsp=$( { awk '/^%changelog/{exit} {print FILENAME":"FNR":"$0}' "$spec"; awk '{print FILENAME":"FNR":"$0}' debian/control; awk '{print FILENAME":"FNR":"$0}' .github/workflows/ci.yml; } \
  | grep -E "(omx-dsp(-devel)?|libomxdsp-dev)[ ']*(<|<<|\(<<|\(<) *0\.[0-9]|(omx-dsp(-devel)?|libomxdsp-dev)[ ']*(>=|\(>=) *0\.(2[0-9]|3[0-2])\.|with +omx-dsp-devel *<|atleast-version=0\.3[0-2]\.[0-9]+ omxdsp" || true)
[ -z "$dsp" ] || fail "omx-dsp is bounded above or has a floor below 0.33.0 (floors only, >= 0.33.0): $(printf '%s' "$dsp" | head -3 | cut -c1-150 | tr '\n' ' ')"
echo "domain-packaging-check: ok"
