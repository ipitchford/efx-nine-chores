#!/usr/bin/env python3
"""Compose already completed immutable LRA checks without redoing their proofs.

For fresh independent replay, use check_lra_certificate.py. This companion
verifies all input/source/checker/result hashes and all cross-stage identities
before recognizing completion of the three previously executed exact checks.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from lra_certificate_common import atomic_json, capture_files, json_file, require, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--rup-verification', type=Path, required=True)
    parser.add_argument('--arithmetic-verification', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--certificates', type=Path, required=True)
    parser.add_argument('--selected-indices', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(sha256(args.input) == args.expected_sha256, 'input changed')
    _, files = capture_files(args.capture)
    root = Path(__file__).parent
    binding = json_file(args.binding)
    rup = json_file(args.rup_verification)
    arithmetic = json_file(args.arithmetic_verification)
    rows = [
        (binding, 'PASS_ORIGINAL_INPUT_CNF_AND_AFFINE_ATOM_BINDING', 'check_lra_capture.py'),
        (rup, 'PASS_TRIMMED_RUP_REFUTATION_RELATIVE_TO_SELECTED_THEORY_AXIOMS', 'check_lra_rup.py'),
        (arithmetic, 'PASS_SELECTED_THEORY_CLAUSES_EXACT_FARKAS', 'check_lra_farkas.py')]
    common_hash = sha256(root / 'lra_certificate_common.py')
    for report, status, checker in rows:
        require(report['status'] == status, 'an independent stage did not pass')
        require(report['input_sha256'] == args.expected_sha256, 'stages refer to different inputs')
        require(report['captured_files_sha256'] == files, 'captured source changed between stages')
        require(report['checker_sha256'] == sha256(root / checker), 'stage checker source changed')
        require(report['common_sha256'] == common_hash, 'stage parser/arithmetic source changed')
        require(report['callback_assumptions_admitted'] is False, 'callback assumption admitted')
    binding_hash = sha256(args.binding)
    require(rup['input_binding_sha256'] == arithmetic['input_binding_sha256'] == binding_hash,
            'proof stages did not use this exact input binding')
    selected_hash = sha256(args.selected_indices)
    require(rup['selected_indices_sha256'] == arithmetic['selected_indices_sha256'] == selected_hash,
            'arithmetic selection differs from Boolean axioms')
    require(rup['trace_sha256'] == sha256(args.trace), 'checked Boolean trace changed')
    require(arithmetic['certificate_sha256'] == sha256(args.certificates), 'checked arithmetic certificate changed')
    require(rup['selected_theory_clauses'] == arithmetic['selected_theory_clauses'] == arithmetic['checked_theory_clauses'],
            'arithmetic coverage does not match all Boolean theory axioms')
    require(rup['boolean_unsat_checked'] is True and rup['backward_dependency_closure_checked'] is True,
            'final Boolean refutation was not checked')
    sources = ['lra_certificate_common.py', 'check_lra_capture.py', 'check_lra_rup.py',
               'check_lra_farkas.py', 'check_lra_certificate.py', 'bind_completed_lra_checks.py']
    report = dict(status='PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE',
                  verification_mode='binding_of_completed_immutable_independent_checks',
                  input=str(args.input.resolve()), input_sha256=args.expected_sha256,
                  original_smt_reconstructed=True, exact_affine_atoms_checked=True,
                  boolean_rup_refutation_checked=True, all_admitted_theory_axioms_checked=True,
                  callback_assumptions_admitted=False, producer_solver_verdict_trusted=False,
                  solver_or_third_party_numeric_library_invoked_by_independent_checkers=False,
                  completed_proofs_repeated_in_this_binding_step=False,
                  selected_theory_clauses=arithmetic['checked_theory_clauses'],
                  selected_original_clauses=rup['selected_original_clauses'],
                  derived_rup_clauses=rup['derived_clauses'],
                  ordered_reason_positions=rup['ordered_reason_positions'],
                  stage_receipts_sha256={str(args.binding): binding_hash,
                      str(args.rup_verification): sha256(args.rup_verification),
                      str(args.arithmetic_verification): sha256(args.arithmetic_verification)},
                  captured_files_sha256=files, trace_sha256=sha256(args.trace),
                  certificate_sha256=sha256(args.certificates), selected_indices_sha256=selected_hash,
                  checker_sources_sha256={name: sha256(root / name) for name in sources},
                  target_reduction_must_be_verified_separately=True,
                  completed_at_utc=datetime.now(timezone.utc).isoformat())
    atomic_json(args.out, report)
    print(report['status'], report['selected_theory_clauses'], report['derived_rup_clauses'])


if __name__ == '__main__':
    main()
