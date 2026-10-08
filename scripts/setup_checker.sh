#!/usr/bin/env bash
# Build the pinned Ethos checker separately from the frozen research objects.
# This script installs no system packages and never writes a proof or SMT input.
set -euo pipefail

PACKAGE_ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
ETHOS_COMMIT=08e4aa40c4f8a6e00833f10e8d8985777e424027
CVC5_COMMIT=2b2e84419f70817ec919a784a48806e79f677240
CVC5_VERSION=1.4.1
ETHOS_REPOSITORY=https://github.com/cvc5/ethos.git
CVC5_REPOSITORY=https://github.com/cvc5/cvc5.git

usage() {
    cat <<'USAGE'
Usage: bash scripts/setup_checker.sh --build [options]
       bash scripts/setup_checker.sh --check [--checker PATH]

  --build             Fetch the exact source commits, check signatures, and build.
  --check             Offline signature/hash and executable checks; no proof replay.
  --offline           With --build, require the pinned commits in the source cache.
  --jobs N            Compile workers (default: 2).
  --source-dir DIR    Source cache (default: PACKAGE/work/checker_sources).
  --output-dir DIR    Build directory (default: PACKAGE/work/checker_rebuilt).
  --checker PATH      Executable for --check; defaults to the rebuilt executable.
  --help              Show this message. No arguments also shows this message.

Environment:
  EVIDENCE_PYTHON      Python executable (default: python3).
  CXX                 C++17 compiler executable, without flags (default: c++).
  GMP_INCLUDE_DIR     Optional semicolon-separated GMP header directories.
  GMP_LIBRARIES       Optional semicolon-separated absolute GMP library files,
                      in link order (C++ GMP first, then C GMP).

Build prerequisites: Bash, Python 3.10+, Git, CMake 3.13+, Make or Ninja,
a C++17 compiler, and GMP C/C++ development headers and libraries.
The build obtains source code from GitHub unless --offline is supplied.
No package manager, sudo, system installation, or proof rewriting is performed.
USAGE
}

die() { printf 'setup_checker: %s\n' "$*" >&2; exit 2; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing executable: $1"; }

mode=
offline=false
jobs=2
source_dir="$PACKAGE_ROOT/work/checker_sources"
output_dir="$PACKAGE_ROOT/work/checker_rebuilt"
checker=
python_bin=${EVIDENCE_PYTHON:-python3}

if [[ $# -eq 0 ]]; then usage; exit 0; fi
while [[ $# -gt 0 ]]; do
    case "$1" in
        --build|--check)
            [[ -z "$mode" ]] || die 'choose exactly one of --build and --check'
            mode=$1; shift ;;
        --offline) offline=true; shift ;;
        --jobs|--source-dir|--output-dir|--checker)
            [[ $# -ge 2 && -n "$2" ]] || die "missing value for $1"
            case "$1" in
                --jobs) jobs=$2 ;;
                --source-dir) source_dir=$2 ;;
                --output-dir) output_dir=$2 ;;
                --checker) checker=$2 ;;
            esac
            shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) die "unknown option: $1" ;;
    esac
done
[[ -n "$mode" ]] || die 'supply --build or --check'
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || die '--jobs must be a positive integer'
if [[ "$mode" == --build && -n "$checker" ]]; then
    die '--checker is an option for --check only'
fi
if [[ "$mode" == --check && "$offline" == true ]]; then
    die '--check is already offline; --offline is an option for --build only'
fi
need "$python_bin"
"$python_bin" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else "Python 3.10 or newer is required")'

check_signatures() {
    "$python_bin" - "$PACKAGE_ROOT" "$1" "$ETHOS_COMMIT" "$CVC5_COMMIT" "$CVC5_VERSION" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root, signature_root = map(Path, sys.argv[1:3])
pins = json.loads((root / "results/checker_build.json").read_text())
expected_pins = dict(zip(("ethos_commit", "cvc5_signature_commit", "cvc5_version"), sys.argv[3:]))
for key, value in expected_pins.items():
    if pins.get(key) != value:
        raise SystemExit(f"Version pin disagrees with results/checker_build.json: {key}")
receipt = json.loads((root / "results/root7_ethos.json").read_text())
expected = receipt["signature_sha256"]
actual = {str(p.relative_to(signature_root)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(signature_root.rglob("*.eo"))}
if actual != expected:
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(p for p in set(expected) & set(actual) if expected[p] != actual[p])
    raise SystemExit(f"Signature bytes differ from the archived receipt. Missing={missing}; extra={extra}; changed={changed}")
print(f"All {len(actual)} signature files match the archived hashes: {signature_root}")
PY
}

check_executable() {
    "$python_bin" - "$PACKAGE_ROOT" "$1" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root, checker = map(Path, sys.argv[1:])
if not checker.is_file():
    raise SystemExit(f"Checker not found: {checker}. Run this script with --build first.")
try:
    run = subprocess.run([str(checker.resolve()), "--help"], capture_output=True, text=True, timeout=20)
except (OSError, subprocess.TimeoutExpired) as error:
    raise SystemExit(f"Checker cannot run on this host: {error}. Check executable permissions and runtime libraries, or rebuild locally.")
if run.returncode != 0 or any(flag not in run.stdout for flag in ("--reference=", "--require-proof-of-false")):
    raise SystemExit(f"Checker startup/required-option check failed: {run.stdout}\n{run.stderr}")
digest = hashlib.sha256(checker.read_bytes()).hexdigest()
archived = json.loads((root / "results/checker_build.json").read_text())["ethos_binary_sha256"]
print(f"Checker starts successfully: {checker.resolve()}")
print(f"Executable SHA-256: {digest}")
print(f"Matches original build hash: {digest == archived}")
print("This is a setup check, not a checked mathematical proof. Run the proof replay commands in docs/REPRODUCTION.md.")
PY
}

check_signatures "$PACKAGE_ROOT/work/cvc5_signatures/proofs/eo/cpc"
if [[ "$mode" == --check ]]; then
    checker=${checker:-"$output_dir/ethos/build/src/ethos"}
    check_executable "$checker"
    exit 0
fi

need git
need cmake
compiler=${CXX:-c++}
need "$compiler"
compiler=$(command -v "$compiler")
"$python_bin" - <<'PY'
import re
import subprocess
version = subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0]
parts = re.search(r"(\d+)\.(\d+)", version)
if not parts or tuple(map(int, parts.groups())) < (3, 13):
    raise SystemExit("CMake 3.13 or newer is required by this setup script.")
PY
if command -v make >/dev/null 2>&1; then
    generator='Unix Makefiles'
    build_tool=$(command -v make)
elif command -v ninja >/dev/null 2>&1; then
    generator=Ninja
    build_tool=$(command -v ninja)
else
    die 'missing build tool: provide Make or Ninja'
fi

mkdir -p -- "$source_dir" "$output_dir/dependency_probe"
source_dir=$(CDPATH= cd -- "$source_dir" && pwd -P)
output_dir=$(CDPATH= cd -- "$output_dir" && pwd -P)
probe_dir="$output_dir/dependency_probe"
include_args=()
if [[ -n "${GMP_INCLUDE_DIR:-}" ]]; then
    IFS=';' read -r -a include_dirs <<< "$GMP_INCLUDE_DIR"
    for directory in "${include_dirs[@]}"; do
        [[ -d "$directory" ]] || die "GMP include directory not found: $directory"
        include_args+=("-I$directory")
    done
fi
gmp_libraries=${GMP_LIBRARIES:-'gmpxx;gmp'}
link_args=(-lgmpxx -lgmp)
if [[ -n "${GMP_LIBRARIES:-}" ]]; then
    IFS=';' read -r -a link_args <<< "$GMP_LIBRARIES"
    for library in "${link_args[@]}"; do
        [[ "$library" == /* && -f "$library" ]] || die "GMP_LIBRARIES entries must be existing absolute files: $library"
    done
fi
cat > "$probe_dir/gmp.cpp" <<'CPP'
#include <gmp.h>
#include <gmpxx.h>
#include <iostream>
int main() {
    mpq_class x(1, 3), y(2, 3);
    if (x + y != 1) return 1;
    std::cout << gmp_version << '\n';
    return 0;
}
CPP
if ! "$compiler" -std=c++17 "${include_args[@]}" "$probe_dir/gmp.cpp" \
        "${link_args[@]}" -o "$probe_dir/gmp_probe" > "$probe_dir/compiler.log" 2>&1; then
    cat "$probe_dir/compiler.log" >&2
    die 'C++17/GMP compile check failed. Provide gmp.h, gmpxx.h and the C/C++ GMP libraries; nonstandard paths can be supplied through GMP_INCLUDE_DIR and GMP_LIBRARIES. No package has been installed.'
fi
if ! "$probe_dir/gmp_probe" > "$probe_dir/gmp_version.txt" 2> "$probe_dir/runtime.log"; then
    cat "$probe_dir/runtime.log" >&2
    die 'GMP runtime probe failed; check the host runtime library search path'
fi

fetch_pinned() {
    local repository=$1 commit=$2 directory=$3
    if [[ ! -d "$directory/.git" ]]; then
        [[ ! -e "$directory" ]] || die "source destination exists but is not a Git checkout: $directory"
        [[ "$offline" != true ]] || die "offline source checkout is missing: $directory"
        git init --quiet "$directory"
        git -C "$directory" remote add origin "$repository"
    fi
    [[ "$(git -C "$directory" remote get-url origin)" == "$repository" ]] || die "unexpected source remote in $directory"
    [[ -z "$(git -C "$directory" status --porcelain --untracked-files=all)" ]] || die "source checkout has local changes: $directory"
    if ! git -C "$directory" cat-file -e "$commit^{commit}" 2>/dev/null; then
        [[ "$offline" != true ]] || die "pinned commit is absent from offline source cache: $commit"
        git -C "$directory" fetch --depth=1 origin "$commit"
    fi
    git -C "$directory" checkout --quiet --detach "$commit"
    [[ "$(git -C "$directory" rev-parse HEAD)" == "$commit" ]] || die "source commit check failed: $directory"
}

fetch_pinned "$ETHOS_REPOSITORY" "$ETHOS_COMMIT" "$source_dir/ethos"
fetch_pinned "$CVC5_REPOSITORY" "$CVC5_COMMIT" "$source_dir/cvc5"
check_signatures "$source_dir/cvc5/proofs/eo/cpc"

cmake_args=(-S "$source_dir/ethos" -B "$output_dir/ethos/build"
    -G "$generator" "-DCMAKE_MAKE_PROGRAM=$build_tool"
    -DCMAKE_BUILD_TYPE=Release -DBUILD_STATIC=OFF "-DCMAKE_CXX_COMPILER=$compiler"
    "-DGMP_LIBRARIES=$gmp_libraries")
if [[ -n "${GMP_INCLUDE_DIR:-}" ]]; then
    cmake_args+=("-DGMP_INCLUDE_DIR=$GMP_INCLUDE_DIR")
fi
if ! cmake "${cmake_args[@]}"; then
    die 'CMake configuration failed; check compiler and GMP paths in the diagnostic above'
fi
if ! cmake --build "$output_dir/ethos/build" --target ethos --parallel "$jobs"; then
    die 'Ethos build failed; no proof was changed or checked'
fi
mkdir -p -- "$output_dir/ethos/licenses"
cp -- "$source_dir/ethos/COPYING" "$source_dir/ethos/AUTHORS" "$output_dir/ethos/"
cp -- "$source_dir/ethos/licenses/lgpl-3.0.txt" "$output_dir/ethos/licenses/"
checker="$output_dir/ethos/build/src/ethos"
check_executable "$checker"
"$python_bin" - "$output_dir" "$source_dir" "$compiler" "$jobs" "$ETHOS_COMMIT" "$CVC5_COMMIT" "$gmp_libraries" "${GMP_INCLUDE_DIR:-automatic}" <<'PY'
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

out, source = map(Path, sys.argv[1:3])
checker = out / "ethos/build/src/ethos"
receipt = {
    "scope": "Local pinned-source build and setup checks; no mathematical proof replay",
    "ethos_commit": sys.argv[5], "cvc5_signature_commit": sys.argv[6],
    "source_directory": str(source), "checker": str(checker),
    "checker_sha256": hashlib.sha256(checker.read_bytes()).hexdigest(),
    "platform": platform.platform(), "python": sys.version,
    "compiler": subprocess.check_output([sys.argv[3], "--version"], text=True).splitlines()[0],
    "cmake": subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0],
    "build_parallelism": int(sys.argv[4]),
    "gmp_runtime_version": (out / "dependency_probe/gmp_version.txt").read_text().strip(),
    "gmp_libraries": sys.argv[7], "gmp_include_directories": sys.argv[8],
    "proofs_rewritten": False,
}
path = out / "build_receipt.json"
path.write_text(json.dumps(receipt, indent=2) + "\n")
print(f"Local build receipt: {path}")
PY
printf '\nUse --checker %q with src/check_ethos.py.\n' "$checker"
