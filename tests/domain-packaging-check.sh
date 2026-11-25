#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
# The scan domain's install and requirements (omx-contract docs/consumer-move.md, step 6), read from the tree, no build:
#   - make install-contract installs the domain by the installer's domain mode, `install-contract-dir.sh --domain contract.d/scan`,
#     and writes no `install` line of its own for it;
#   - the data package omx-clap-contract lists it: the rpm as %{omx_contract_domain_dir}/scan/, the deb as
#     usr/share/omx-contract/contract.d/scan, and neither package lists the domain anywhere else;
#   - the reader, omx-clap-host (it ships omx-clap-scan), requires the loader (libomx-domain, libomx-domain0) and the data package, and
#     the source builds with the loader's headers (libomx-domain-devel, libomx-domain-dev), at the tree's omx-contract floor (the
#     spec's BuildRequires: omx-contract-devel), which is never below 3.20.0, the first release that ships the loader and the
#     installer's domain mode: the loader's floor is that floor in every place, and no omx-contract floor is below 3.20.0.
# usage: tests/domain-packaging-check.sh
set -eu
fail() { echo "domain-packaging-check: $1" >&2; exit 1; }
spec=packaging/omx-clap-host.spec
# the installer, in make install-contract
grep -Eq '(install-contract-dir\.sh|\$\(INSTALL_CONTRACT_DIR\)) +--domain +contract\.d/scan( |$)' Makefile || fail "Makefile: install-contract does not call the installer's --domain mode for contract.d/scan"
! grep -En '^[[:space:]]*install .*contract\.d/scan' Makefile || fail "Makefile: a hand-written install line for contract.d/scan (the installer's domain mode installs it)"
# the data package lists it
contract_files=$(awk '/^%files -n omx-clap-contract/{f=1;next} /^%files|^%package|^%changelog/{f=0} f' "$spec")
printf '%s\n' "$contract_files" | grep -qx '%{omx_contract_domain_dir}/scan/' || fail "$spec: omx-clap-contract does not list %{omx_contract_domain_dir}/scan/"
grep -qx 'usr/share/omx-contract/contract.d/scan' debian/omx-clap-contract.install || fail "debian/omx-clap-contract.install does not list usr/share/omx-contract/contract.d/scan"
# the code sheet's domains, omx-param-contract, omx-clap-scale, clap and omx-clap, the same way
for dom in omx-param-contract omx-clap-scale clap omx-clap; do
grep -Eq "(install-contract-dir\\.sh|\\\$\\(INSTALL_CONTRACT_DIR\\)) +--domain +contract\\.d/$dom( |\$)" Makefile || fail "Makefile: install-contract does not call the installer's --domain mode for contract.d/$dom"
! grep -En "^[[:space:]]*install .*contract\\.d/$dom" Makefile || fail "Makefile: a hand-written install line for contract.d/$dom"
printf '%s\n' "$contract_files" | grep -qx "%{omx_contract_domain_dir}/$dom/" || fail "$spec: omx-clap-contract does not list %{omx_contract_domain_dir}/$dom/"
grep -qx "usr/share/omx-contract/contract.d/$dom" debian/omx-clap-contract.install || fail "debian/omx-clap-contract.install does not list usr/share/omx-contract/contract.d/$dom"
done
# the domain host is plugin-hostd-protocol's (ruling R5): make install-contract does not install it, neither package lists
# it (two packages shipping contract.d/host/host.json refuse to install side by side), and the data package requires the one
# that ships it, by name
awk '/^install-contract:/{f=1;next} /^[^\t#]/{f=0} f' Makefile | grep -Eq -- '--domain +contract\.d/host( |$)' && fail "Makefile: install-contract installs contract.d/host, plugin-hostd-protocol's domain"
printf '%s\n' "$contract_files" | grep -q 'domain_dir}/host/' && fail "$spec: omx-clap-contract lists %{omx_contract_domain_dir}/host/, plugin-hostd-protocol's domain"
grep -q 'contract\.d/host' debian/omx-clap-contract.install && fail "debian/omx-clap-contract.install lists contract.d/host, plugin-hostd-protocol's domain"
awk '/^%package -n omx-clap-contract/{f=1;next} /^%description/{f=0} f' "$spec" | grep -qx 'Requires: plugin-hostd-protocol-contract' || fail "$spec: omx-clap-contract does not require plugin-hostd-protocol-contract"
awk '/^Package: omx-clap-contract$/{f=1;next} /^Package:/{f=0} f' debian/control | grep -Eq '^Depends:.*plugin-hostd-protocol-contract(,|$)' || fail "debian/control: omx-clap-contract does not depend on plugin-hostd-protocol-contract"
# the reader requires the loader and the data package
req() { grep -Eq "$1" "$spec" || fail "$spec: $2"; }
floor=$(sed -n 's/^BuildRequires: omx-contract-devel >= \([0-9][0-9.]*\)$/\1/p' "$spec")
[ -n "$floor" ] || fail "$spec: no BuildRequires: omx-contract-devel >= <floor>"
[ "$(printf '3.20.0\n%s\n' "$floor" | sort -V | head -1)" = 3.20.0 ] || fail "$spec: the omx-contract floor $floor is below 3.20.0"
fre=$(printf '%s' "$floor" | sed 's/\./\\./g')
req "^BuildRequires: libomx-domain-devel >= $fre\$" "no BuildRequires: libomx-domain-devel >= $floor"
host=$(awk '/^%description$/{exit} {print}' "$spec")
printf '%s\n' "$host" | grep -qx "Requires: libomx-domain >= $floor" || fail "$spec: omx-clap-host does not require libomx-domain >= $floor"
printf '%s\n' "$host" | grep -qx 'Requires: omx-clap-contract = %{version}-%{release}' || fail "$spec: omx-clap-host does not require omx-clap-contract at its own version"
grep -Eq "libomx-domain-dev \\(>= $fre~\\)" debian/control || fail "debian/control: no Build-Depends libomx-domain-dev (>= $floor~)"
awk '/^Package: omx-clap-host$/{f=1;next} /^Package:/{f=0} f' debian/control | grep -Eq "^Depends:.*libomx-domain0 \\(>= $fre~\\)" || fail "debian/control: omx-clap-host does not depend on libomx-domain0 (>= $floor~)"
awk '/^Package: omx-clap-host$/{f=1;next} /^Package:/{f=0} f' debian/control | grep -Eq '^Depends:.*omx-clap-contract \(= \$\{source:Version\}\)' || fail "debian/control: omx-clap-host does not depend on omx-clap-contract at its own version"
# omx-contract at 3.20.0 everywhere the tree names it
low=$( { awk '/^%changelog/{exit} {print FILENAME":"FNR":"$0}' "$spec"; awk '{print FILENAME":"FNR":"$0}' debian/control; } | grep -E '(omx-contract(-devel|-data)?|libomx-contract-dev) *(>=|\(>=) *3\.1[0-9]\.[0-9]+' || true)
[ -z "$low" ] || fail "an omx-contract floor below 3.20.0 is still declared: $(printf '%s' "$low" | head -3 | tr '\n' ' ')"
echo "domain-packaging-check: ok"
