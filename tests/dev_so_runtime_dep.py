#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#
# A development package's lib<name>.so is a symlink to the shared library lib<name>.so.<N>, which another package
# ships. Without a dependency on that package, a machine with the development package alone has a dangling symlink,
# and every consumer's -l<name> link fails (#96: libomx-clap-core-dev on Debian trixie). So:
#   deb  each package whose debian/<pkg>.install ships lib<name>.so depends on the package that ships lib<name>.so.*,
#        at (= ${binary:Version});
#   rpm  each subpackage whose %files holds lib<name>.so requires the subpackage holding lib<name>.so.*, at
#        %{version}-%{release} (%{?_isa} allowed).
#
#   dev_so_runtime_dep.py <tree>       0 when both packagings hold
#   dev_so_runtime_dep.py --self-test  each dependency removed in a scratch copy is found
import glob
import os
import re
import shutil
import sys
import tempfile

SO = re.compile(r"(?:^|/)(lib[^/]+)\.so$")
SO_N = re.compile(r"(?:^|/)(lib[^/]+)\.so\.[^/]*$")


def control_paragraphs(root):
    text = open(os.path.join(root, "debian", "control")).read()
    out = {}
    for para in re.split(r"\n\s*\n", text):
        m = re.search(r"^Package:\s*(\S+)", para, re.M)
        if m:
            dep = re.search(r"^Depends:(.*(?:\n[ \t].*)*)", para, re.M)
            out[m.group(1)] = " ".join(dep.group(1).split()) if dep else ""
    return out


def deb_problems(root):
    paras = control_paragraphs(root)
    dev_of, runtime_of = {}, {}
    for pkg in paras:
        path = os.path.join(root, "debian", pkg + ".install")
        if not os.path.exists(path):
            continue
        for line in open(path):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            m = SO.search(line)
            if m:
                dev_of.setdefault(m.group(1), []).append(pkg)
            m = SO_N.search(line)
            if m:
                runtime_of[m.group(1)] = pkg
    out = []
    for lib, devs in sorted(dev_of.items()):
        runtime = runtime_of.get(lib)
        for dev in devs:
            if runtime is None:
                out.append(f"deb: {dev} ships {lib}.so, and no package ships {lib}.so.*")
            elif not re.search(r"(?:^|[\s,])%s \(= \$\{binary:Version\}\)" % re.escape(runtime), paras[dev]):
                out.append(f"deb: {dev} ships {lib}.so but does not depend on {runtime} (= ${{binary:Version}}), which ships {lib}.so.*")
    return out


def spec_sections(spec_text, name):
    """{subpackage name: (requires, files)} of the spec, %package -n x and %package x both."""
    pkgs = {}
    current = None
    kind = None
    for line in spec_text.splitlines():
        m = re.match(r"^%(package|files)\s+(-n\s+)?(\S+)", line)
        if m:
            sub = m.group(3) if m.group(2) else f"{name}-{m.group(3)}"
            pkgs.setdefault(sub, ([], []))
            current, kind = sub, m.group(1)
            continue
        if re.match(r"^%(description|prep|build|install|check|changelog|post|pre|preun|postun)\b", line):
            current = None
            continue
        if current is None:
            continue
        if kind == "package" and line.startswith("Requires:"):
            pkgs[current][0].append(line.split(":", 1)[1].strip())
        elif kind == "files" and line.strip() and not line.startswith("%license") and not line.startswith("%doc"):
            pkgs[current][1].append(line.strip())
    return pkgs


def rpm_problems(root):
    spec_path = glob.glob(os.path.join(root, "packaging", "*.spec"))[0]
    text = open(spec_path).read()
    name = re.search(r"^Name:\s*(\S+)", text, re.M).group(1)
    pkgs = spec_sections(text, name)
    dev_of, runtime_of = {}, {}
    for pkg, (_, files) in pkgs.items():
        for f in files:
            m = SO.search(f)
            if m:
                dev_of.setdefault(m.group(1), []).append(pkg)
            m = SO_N.search(f)
            if m:
                runtime_of[m.group(1)] = pkg
    out = []
    for lib, devs in sorted(dev_of.items()):
        runtime = runtime_of.get(lib)
        for dev in devs:
            want = re.compile(r"^%s(%%\{\?_isa\})?\s*=\s*%%\{version\}-%%\{release\}$" % re.escape(runtime or ""))
            if runtime is None:
                out.append(f"rpm: {dev} holds {lib}.so, and no subpackage holds {lib}.so.*")
            elif not any(want.match(r) for r in pkgs[dev][0]):
                out.append(f"rpm: {dev} holds {lib}.so but does not require {runtime} = %{{version}}-%{{release}}, which holds {lib}.so.*")
    return out


def problems(root):
    return deb_problems(root) + rpm_problems(root)


def self_test(root):
    ok = True
    with tempfile.TemporaryDirectory() as t:
        for sub in ("debian", "packaging"):
            shutil.copytree(os.path.join(root, sub), os.path.join(t, sub))
        control = os.path.join(t, "debian", "control")
        text = open(control).read()
        bare = re.sub(r"\s*libomx-clap-core1 \(= \$\{binary:Version\}\),", "", text)
        held = re.sub(r"(Package: libomx-clap-core-dev\n(?:.*\n)*?Depends:)", r"\1 libomx-clap-core1 (= ${binary:Version}),", bare, count=1)
        want = "libomx-clap-core-dev ships libomx-clap-core.so but does not depend on libomx-clap-core1"
        open(control, "w").write(held)
        if any(want in p for p in deb_problems(t)):
            print("FAIL self-test: with the deb dependency stated it is still named")
            ok = False
        open(control, "w").write(bare)
        if not any(want in p for p in deb_problems(t)):
            print("FAIL self-test: the deb dependency removed is not found")
            ok = False
        open(control, "w").write(text)
        base = rpm_problems(t)
        spec = glob.glob(os.path.join(t, "packaging", "*.spec"))[0]
        stext = open(spec).read()
        devel = re.search(r"(%package -n omx-clap-core-devel\n(?:.*\n)*?)Requires: omx-clap-core%\{\?_isa\} = %\{version\}-%\{release\}\n", stext)
        if not devel:
            print("FAIL self-test: the spec's omx-clap-core-devel Requires line is not where the sabotage expects it")
            return False
        open(spec, "w").write(stext[: devel.start()] + devel.group(1) + stext[devel.end():])
        found = [p for p in rpm_problems(t) if p not in base]
        if not any("omx-clap-core-devel holds libomx-clap-core.so but does not require omx-clap-core" in p for p in found):
            print("FAIL self-test: the rpm requirement removed is not found:", found)
            ok = False
    print("ok   self-test: each dependency removed is found" if ok else "self-test FAILED")
    return ok


def main():
    if sys.argv[1:] == ["--self-test"]:
        return 0 if self_test(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) else 1
    found = problems(sys.argv[1] if len(sys.argv) > 1 else ".")
    for p in found:
        print("FAIL", p)
    if not found:
        print("ok   every development .so depends on the package that ships its shared library (deb and rpm)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
