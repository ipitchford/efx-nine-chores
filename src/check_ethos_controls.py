#!/usr/bin/env python3
"""Small controls for the two required external-checker boundary conditions.

These controls test enforcement of reference assumptions and final global false.
They do not establish soundness of Ethos or of the supplied CPC calculus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from check_ethos import prepare_proof_stream


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checker', type=Path,
                        default=ROOT / 'work/ethos/build/src/ethos')
    parser.add_argument('--report', type=Path,
                        default=ROOT / 'results/checker_controls.json')
    parser.add_argument('--work-dir', type=Path,
                        default=ROOT / 'work/checker_controls')
    args = parser.parse_args()
    checker = args.checker.resolve()
    if not checker.is_file():
        parser.error(f'checker executable does not exist: {checker}')
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    full = work / 'contradiction.smt2'
    missing = work / 'missing_assumptions.smt2'
    sat = work / 'satisfiable.smt2'
    full.write_text('(set-logic QF_LRA)\n(declare-fun x () Real)\n(assert (> x 0.0))\n(assert (< x 0.0))\n(check-sat)\n')
    missing.write_text('(set-logic QF_LRA)\n(declare-fun x () Real)\n(assert (> x 0.0))\n(check-sat)\n')
    sat.write_text('(set-logic QF_LRA)\n(declare-fun x () Real)\n(assert (> x 0.0))\n(check-sat)\n')
    nonfalse = work / 'nonfalse.cpc'
    nonfalse.write_text('(declare-const x Real)\n(assume a (> x 0/1))\n')
    generated = subprocess.run([
        sys.executable, str(ROOT / 'src/check_cvc5.py'), str(full),
        '--format', 'cpc', '--output', str(work / 'contradiction'),
        '--report', str(work / 'generation.json'), '--timeout', '30',
    ], capture_output=True, text=True, timeout=60)
    if generated.returncode:
        raise RuntimeError(f'control proof generation failed: {generated.stdout} {generated.stderr}')
    signature = ROOT / 'work/cvc5_signatures/proofs/eo/cpc/Cpc.eo'
    cases = [
        ('valid_refutation', full, work / 'contradiction.cpc', True, True),
        ('missing_reference_assumptions', missing, work / 'contradiction.cpc', True, False),
        ('valid_nonrefuting_prefix_without_false_requirement', sat, nonfalse, False, True),
        ('same_nonrefuting_prefix_with_false_requirement', sat, nonfalse, True, False),
    ]
    receipts = []
    for name, reference, proof, require_false, expected in cases:
        command = [str(checker), f'--include={signature}', f'--reference={reference}']
        if require_false:
            command.append('--require-proof-of-false')
        stream, adaptation = prepare_proof_stream(reference, proof)
        with stream:
            result = subprocess.run(command, stdin=stream, capture_output=True, text=True, timeout=30)
        lines = [s.strip() for s in result.stdout.splitlines() if s.strip()]
        accepted = result.returncode == 0 and bool(lines) and lines[-1] == 'correct'
        receipts.append({
            'case': name, 'expected_accepted': expected, 'accepted': accepted,
            'passed': accepted == expected, 'command': command,
            'proof_input_mode': 'stdin',
            'proof_stream_adaptation': adaptation,
            'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
            'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
            'proof_sha256': hashlib.sha256(proof.read_bytes()).hexdigest(),
        })
    report = {
        'result': 'PASS' if all(r['passed'] for r in receipts) else 'FAIL',
        'scope': 'Boundary enforcement controls, not a checker soundness proof.',
        'checker_sha256': hashlib.sha256(checker.read_bytes()).hexdigest(),
        'cases': receipts,
    }
    text = json.dumps(report, indent=2) + '\n'
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(text)
    print(text, end='')
    return 0 if report['result'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
