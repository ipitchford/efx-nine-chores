#!/usr/bin/env python3
"""Check a CPC refutation with Ethos, bound to its original SMT-LIB assertions.

Success requires all three conditions: Ethos exits successfully; its verdict is
`correct` (never `incomplete`); and --require-proof-of-false enforces a final
refutation at assumption level zero. The --reference option checks every global
proof assumption against the original SMT2 assertions. The proof is streamed
through stdin: the pinned Ethos release clears reference state when a proof
file is instead opened through its positional-file include path. No rules are
skipped. Initial proof declarations are matched exactly to the original Real
constants and omitted, so the proof uses those existing constants instead of
fresh redeclarations. Every proof step is retained. Boundary controls in
check_ethos_controls.py exercise these distinctions.

Ethos checks derivations against a supplied calculus; it does not prove that
calculus sound. This runner records the signature files and binary hashes so
that this trust boundary is explicit and the run can be reproduced.

See https://github.com/cvc5/ethos/blob/main/user_manual.md .
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def prepare_proof_stream(reference: Path, proof: Path):
    """Reuse original QF_LRA constants and preserve reference-checking state.

    Ethos constants are fresh on redeclaration. This adapter removes only the
    CPC prefix's exact, attribute-free Real declarations already present in
    the original reference. It rejects unknown or later declarations and any
    include/reference command that could clear the pinned checker's state.
    """
    text = reference.read_text(encoding="utf-8")
    declarations = re.findall(r"(?m)^\s*\(declare-fun\s+([^\s()]+)\s+\(\s*\)\s+Real\s*\)\s*$", text)
    declarations += re.findall(r"(?m)^\s*\(declare-const\s+([^\s()]+)\s+Real\s*\)\s*$", text)
    if len(declarations) != len(set(declarations)):
        raise ValueError("duplicate original declarations are unsupported")
    declared = set(declarations)
    removed = []
    at_prefix = True
    stream = tempfile.TemporaryFile(mode="w+b")
    hasher = hashlib.sha256()
    count = 0
    try:
        with proof.open("rb") as source:
            for line in source:
                stripped = line.strip()
                if not stripped or stripped.startswith(b";"):
                    stream.write(line)
                    hasher.update(line)
                    count += len(line)
                    continue
                if any(character in stripped for character in (b'"', b'|', b';')):
                    raise ValueError("quoted symbols, strings, and inline comments are outside this QF_LRA adapter")
                depth = 0
                for bracket in re.finditer(rb"[()]", stripped):
                    depth += 1 if bracket.group() == b"(" else -1
                    if depth < 0 or (depth == 0 and bracket.end() != len(stripped)):
                        raise ValueError("expected exactly one complete CPC command per line")
                if depth != 0:
                    raise ValueError("multiline CPC commands are outside this adapter")
                match = re.fullmatch(rb"\(declare-const\s+([^\s()]+)\s+Real\s*\)", stripped)
                if match:
                    name = match.group(1).decode("utf-8")
                    if not at_prefix or name not in declared or name in removed:
                        raise ValueError(f"unsupported proof declaration: {name}")
                    removed.append(name)
                    continue
                at_prefix = False
                command = re.match(rb"\(\s*([^\s()]+)", stripped)
                if command is None or command.group(1) not in {b"define", b"assume", b"assume-push", b"step", b"step-pop"}:
                    raise ValueError("unsupported proof command or multiline command start")
                stream.write(line)
                hasher.update(line)
                count += len(line)
        stream.seek(0)
        return stream, {
            "adaptation": "Drop exact original Real declarations from CPC prefix; reuse reference constants; retain all proof steps.",
            "removed_duplicate_declarations": removed,
            "stream_sha256": hasher.hexdigest(),
            "stream_bytes": count,
            "embedded_include_reference_commands_allowed": False,
        }
    except BaseException:
        stream.close()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("proof", type=Path)
    parser.add_argument("--checker", type=Path, default=ROOT / "work/ethos/build/src/ethos")
    parser.add_argument("--signatures", type=Path, default=ROOT / "work/cvc5_signatures/proofs/eo/cpc")
    parser.add_argument("--include-expert", action="store_true")
    parser.add_argument("--timeout", type=float, default=1200)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    for path in (args.input, args.proof, args.checker, args.signatures / "Cpc.eo"):
        if not path.is_file():
            parser.error(f"required file does not exist: {path}")
    signatures = {
        str(path.relative_to(args.signatures)): digest(path)
        for path in sorted(args.signatures.rglob("*.eo"))
    }
    command = [
        str(args.checker.resolve()),
        "--require-proof-of-false",
        f"--include={(args.signatures / 'Cpc.eo').resolve()}",
    ]
    if args.include_expert:
        command.append(f"--include={(args.signatures / 'expert/CpcExpert.eo').resolve()}")
    command += [f"--reference={args.input.resolve()}"]
    started = time.perf_counter()
    timed_out = False
    proof_stream, adaptation = prepare_proof_stream(args.input, args.proof)
    try:
        with proof_stream:
            completed = subprocess.run(command, stdin=proof_stream, capture_output=True, text=True, timeout=args.timeout)
        stdout, stderr, status = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        stdout = stdout.decode("utf-8", errors="replace") if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode("utf-8", errors="replace") if isinstance(stderr, bytes) else stderr
        status = None
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    verdict = lines[-1] if lines else None
    accepted = status == 0 and verdict == "correct" and not timed_out
    report = {
        "result": "verified" if accepted else "not_verified",
        "checker": "Ethos",
        "checker_binary": str(args.checker.resolve()),
        "checker_sha256": digest(args.checker),
        "input": str(args.input.resolve()),
        "input_sha256": digest(args.input),
        "proof": str(args.proof.resolve()),
        "proof_sha256": digest(args.proof),
        "command": command,
        "proof_input_mode": "stdin_preserves_reference_state_in_pinned_ethos",
        "proof_stream_adaptation": adaptation,
        "reference_binding": True,
        "requires_final_false_at_global_scope": True,
        "expert_signature_enabled": args.include_expert,
        "signature_sha256": signatures,
        "signature_trust_boundary": "Ethos checks rule applications; the supplied CPC calculus is a premise.",
        "returncode": status,
        "verdict": verdict,
        "timed_out": timed_out,
        "check_s": round(time.perf_counter() - started, 6),
        "stdout": stdout,
        "stderr": stderr,
    }
    serialized = json.dumps(report, indent=2) + "\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding="utf-8")
    sys.stdout.write(serialized)
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
