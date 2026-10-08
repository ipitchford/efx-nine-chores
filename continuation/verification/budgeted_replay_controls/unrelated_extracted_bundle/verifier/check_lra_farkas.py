#!/usr/bin/env python3
"""Verify exact mixed-strict Farkas certificates for selected theory clauses.

For atom a.x+b<=0, a positive theory literal is negated to -a.x-b<0;
a negative theory literal is negated to a.x+b<=0. Nonnegative weights
whose variable sum vanishes yield a contradiction when the summed constant
is positive, or is zero and a strict premise has positive weight.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import resource
import time

from lra_certificate_common import (atomic_json, capture_files, json_file,
    json_lines, rational, read_atoms, require, sha256, validate_clause)


def verify_weights(clause, weights, atoms, width):
    require(type(weights) is list, 'weights must be sparse pairs')
    used = set()
    total = [Fraction(0)] * width
    strict_weight = Fraction(0)
    for pair in weights:
        require(type(pair) is list and len(pair) == 2, 'bad weight pair')
        position, value = pair
        require(type(position) is int and 0 <= position < len(clause) and position not in used,
                'duplicate or invalid literal position')
        used.add(position)
        weight = rational(value)
        require(weight >= 0, 'negative Farkas multiplier')
        literal = clause[position]
        require(abs(literal) in atoms, 'uninterpreted/reserved theory literal')
        sign = -1 if literal > 0 else 1
        for j, coefficient in enumerate(atoms[abs(literal)]):
            total[j] += sign * weight * coefficient
        if literal > 0:
            strict_weight += weight
    require(not any(total[:-1]), 'weighted variable coefficients do not cancel')
    constant = total[-1]
    require(constant >= 0 and (constant > 0 or strict_weight > 0),
            'multipliers do not prove a strict/weak contradiction')
    return constant, strict_weight, len(weights)


def check(capture, binding_path, certificates, selected_path):
    receipt, files = capture_files(capture)
    binding = json_file(binding_path)
    require(binding.get('status') == 'PASS_ORIGINAL_INPUT_CNF_AND_AFFINE_ATOM_BINDING', 'invalid input binding receipt')
    require(binding['captured_files_sha256'] == files, 'binding receipt does not match capture')
    metadata = json_file(capture / 'metadata.json')
    require(binding['input_sha256'] == metadata['input_sha256'], 'bound input mismatch')
    atoms = read_atoms(capture / 'atoms.jsonl', len(metadata['variables']) + 1)
    selected = json_file(selected_path)
    require(type(selected) is list and all(type(i) is int and i >= 0 for i in selected), 'selected indices must be nonnegative integers')
    require(selected == sorted(set(selected)), 'selected indices must be increasing and unique')
    selected_set = set(selected)
    clauses = {}
    theory_count = 0
    for index, record in enumerate(json_lines(capture / 'theory_clauses.jsonl')):
        require(set(record) == {'clause'}, 'unexpected theory record')
        if index in selected_set:
            clauses[index] = validate_clause(record['clause'], len(atoms) + 1)
        theory_count += 1
    require(set(clauses) == selected_set, 'selected theory index outside source')
    seen, strict_proofs, positive_constant_proofs, multiplier_count = set(), 0, 0, 0
    for record in json_lines(certificates):
        require({'clause_index', 'clause', 'weights'} <= set(record), 'missing certificate fields')
        index = record['clause_index']
        require(type(index) is int and index in selected_set and index not in seen,
                'extra, duplicated, or unselected certificate')
        clause = record['clause']
        validate_clause(clause, len(atoms) + 1)
        require(clause == clauses[index], 'certificate copied a different theory clause')
        constant, strict_weight, count = verify_weights(clause, record['weights'], atoms,
                                                      len(metadata['variables']) + 1)
        seen.add(index)
        strict_proofs += int(constant == 0 and strict_weight > 0)
        positive_constant_proofs += int(constant > 0)
        multiplier_count += count
    require(seen == selected_set, 'selected theory-clause certificate coverage incomplete')
    return dict(status='PASS_SELECTED_THEORY_CLAUSES_EXACT_FARKAS',
                input_sha256=metadata['input_sha256'], capture=str(capture.resolve()),
                captured_files_sha256=files, input_binding_sha256=sha256(binding_path),
                certificate_sha256=sha256(certificates), selected_indices_sha256=sha256(selected_path),
                all_source_theory_clauses=theory_count, selected_theory_clauses=len(selected),
                checked_theory_clauses=len(seen), multiplier_positions=multiplier_count,
                strict_zero_constant_contradictions=strict_proofs,
                positive_constant_contradictions=positive_constant_proofs,
                float_arithmetic_used=False, callback_assumptions_admitted=False,
                original_input_rebinding_performed_in_this_stage=False,
                original_input_binding_carried_by_hash=True,
                boolean_unsat_checked=False, independent_unsat_certificate_complete=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--certificates', type=Path, required=True)
    parser.add_argument('--selected-indices', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (480 << 20,) * 2)
    started = time.monotonic()
    report = check(args.capture, args.binding, args.certificates, args.selected_indices)
    report.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=time.monotonic() - started,
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  checker_sha256=sha256(__file__),
                  common_sha256=sha256(Path(__file__).with_name('lra_certificate_common.py')))
    atomic_json(args.out, report)
    print(report['status'], report['checked_theory_clauses'])


if __name__ == '__main__':
    main()
