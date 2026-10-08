#!/usr/bin/env python3
"""Replay a complete captured-LRA UNSAT certificate using only Python stdlib.

Stages: reconstruct original SMT-to-CNF/affine binding; independently check a
trimmed RUP refutation; verify exact Farkas certificates for every theory axiom
in that refutation. Only all three completed stages establish input UNSAT.
This does not replace a separate proof that the SMT input models the target.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import resource
import time

import check_lra_capture
import check_lra_farkas
import check_lra_rup
from lra_certificate_common import atomic_json, require, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--certificates', type=Path, required=True)
    parser.add_argument('--selected-indices', type=Path, required=True)
    parser.add_argument('--out-directory', type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (700 << 20,) * 2)
    started = time.monotonic()
    args.out_directory.mkdir(parents=True, exist_ok=False)
    binding = check_lra_capture.check(args.input, args.expected_sha256, args.capture)
    binding_path = args.out_directory / 'input_binding.json'
    atomic_json(binding_path, binding)
    print('PASS original input and affine atom binding', flush=True)
    rup = check_lra_rup.check(args.capture, binding_path, args.trace, args.selected_indices)
    rup_path = args.out_directory / 'rup_verification.json'
    atomic_json(rup_path, rup)
    print('PASS trimmed Boolean RUP refutation', flush=True)
    arithmetic = check_lra_farkas.check(args.capture, binding_path, args.certificates,
                                      args.selected_indices)
    arithmetic_path = args.out_directory / 'arithmetic_verification.json'
    atomic_json(arithmetic_path, arithmetic)
    require(rup['input_sha256'] == arithmetic['input_sha256'] == args.expected_sha256,
            'stages have different input identities')
    require(rup['selected_indices_sha256'] == arithmetic['selected_indices_sha256'],
            'arithmetic coverage differs from Boolean axioms')
    require(rup['selected_theory_clauses'] == arithmetic['checked_theory_clauses'],
            'arithmetic coverage count mismatch')
    root = Path(__file__).parent
    sources = ['lra_certificate_common.py', 'check_lra_capture.py',
               'check_lra_rup.py', 'check_lra_farkas.py', 'check_lra_certificate.py']
    report = dict(status='PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE',
                  input=str(args.input.resolve()), input_sha256=args.expected_sha256,
                  original_smt_reconstructed=True, exact_affine_atoms_checked=True,
                  boolean_rup_refutation_checked=True, all_admitted_theory_axioms_checked=True,
                  callback_assumptions_admitted=False, producer_solver_verdict_trusted=False,
                  solver_or_third_party_numeric_library_invoked=False,
                  selected_theory_clauses=arithmetic['checked_theory_clauses'],
                  selected_original_clauses=rup['selected_original_clauses'],
                  derived_rup_clauses=rup['derived_clauses'],
                  input_binding_sha256=sha256(binding_path),
                  rup_verification_sha256=sha256(rup_path),
                  arithmetic_verification_sha256=sha256(arithmetic_path),
                  captured_files_sha256=binding['captured_files_sha256'],
                  trace_sha256=sha256(args.trace), certificate_sha256=sha256(args.certificates),
                  selected_indices_sha256=sha256(args.selected_indices),
                  checker_sources_sha256={name: sha256(root / name) for name in sources},
                  target_reduction_must_be_verified_separately=True,
                  completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=time.monotonic() - started,
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    atomic_json(args.out_directory / 'complete_verification.json', report)
    print(report['status'], report['selected_theory_clauses'], report['derived_rup_clauses'], flush=True)


if __name__ == '__main__':
    main()
