#!/usr/bin/env python3
"""Check a trimmed, hinted RUP refutation independently, with Python stdlib.

Every source axiom is copied from the bound original CNF or a selected theory
clause. Each derived clause is checked by unit propagation under its negation,
using an ordered list of earlier clause IDs and an explicit final conflict.
No Boolean or arithmetic solver is invoked by this checker.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import resource
import time

from lra_certificate_common import (atomic_json, capture_files, json_file,
    json_lines, require, sha256, validate_clause)


def propagate_check(clause, reasons, known):
    require(type(reasons) is list and bool(reasons), 'RUP step has no conflict reason')
    require(all(type(ident) is int for ident in reasons), 'reason ID must be an integer')
    assignment = {}
    for literal in clause:
        # Negate all literals of the clause being proved.
        assignment[abs(literal)] = literal < 0
    propagated = 0
    for position, ident in enumerate(reasons):
        require(ident in known, 'reason is not an earlier checked clause')
        reason = known[ident]
        unassigned = []
        satisfied = False
        for literal in reason:
            value = assignment.get(abs(literal))
            if value is None:
                unassigned.append(literal)
            elif value == (literal > 0):
                satisfied = True
                break
        require(not satisfied, 'propagation reason is already satisfied')
        if not unassigned:
            require(position == len(reasons) - 1, 'conflict must be the last reason')
            return propagated
        require(len(unassigned) == 1, 'propagation reason is not unit')
        require(position < len(reasons) - 1, 'final reason is not a conflict')
        literal = unassigned[0]
        assignment[abs(literal)] = literal > 0
        propagated += 1
    raise ValueError('RUP propagation finished without a conflict')


def check(capture, binding_path, trace_path, selected_path):
    receipt, files = capture_files(capture)
    binding = json_file(binding_path)
    require(binding.get('status') == 'PASS_ORIGINAL_INPUT_CNF_AND_AFFINE_ATOM_BINDING', 'invalid input binding receipt')
    require(binding['captured_files_sha256'] == files, 'binding receipt does not match capture')
    input_records = list(json_lines(capture / 'input_clauses.jsonl'))
    input_count = len(input_records)
    theory_count = binding['theory_clauses']
    maximum = binding['atom_count'] + 1
    total_axioms = input_count + theory_count
    selected = json_file(selected_path)
    require(type(selected) is list and all(type(i) is int and 0 <= i < theory_count for i in selected),
            'selected theory indices invalid')
    require(selected == sorted(set(selected)), 'selected indices must be sorted and unique')
    selected_set = set(selected)
    theories = {}
    for index, record in enumerate(json_lines(capture / 'theory_clauses.jsonl')):
        if index in selected_set:
            theories[index] = record['clause']
    require(set(theories) == selected_set, 'selected theory source missing')
    known, dependencies, axiom_sources = {}, {}, {}
    previous_derived, derived_count = total_axioms, 0
    selected_inputs = set()
    used_theories = set()
    propagated_total = reason_positions = maximum_reasons = 0
    last_id = None
    saw_derived = False
    for record in json_lines(trace_path):
        kind = record.get('kind')
        ident, clause = record.get('id'), record.get('clause')
        require(type(ident) is int and ident > 0 and ident not in known, 'invalid/duplicate clause ID')
        if kind == 'axiom':
            require(not saw_derived, 'axioms must precede derived proof steps')
            require(set(record) == {'kind', 'id', 'source', 'source_index', 'clause'}, 'unexpected axiom fields')
            source, index = record['source'], record['source_index']
            require(type(index) is int and index >= 0, 'invalid source index')
            if source == 'input':
                require(index < input_count and ident == index + 1, 'input axiom ID/provenance mismatch')
                actual = input_records[index]['clause']
                require(actual is not None and clause == actual, 'input axiom differs from original CNF')
                validate_clause(clause, maximum, allow_reserved=(index == 0))
                if index == 0:
                    require(clause == [1], 'truth axiom differs')
                selected_inputs.add(index)
            elif source == 'theory':
                require(index in theories and ident == input_count + index + 1, 'theory ID/provenance mismatch')
                require(clause == theories[index], 'theory axiom differs from source')
                validate_clause(clause, maximum)
                used_theories.add(index)
            else:
                raise ValueError('unsupported axiom source; callback assumptions are forbidden')
            dependencies[ident] = []
            axiom_sources[ident] = (source, index)
        elif kind == 'rup':
            saw_derived = True
            require(set(record) == {'kind', 'id', 'clause', 'reasons'}, 'unexpected RUP fields')
            require(ident > previous_derived, 'derived clause IDs must increase above all source IDs')
            validate_clause(clause, maximum, allow_reserved=True)
            reasons = record['reasons']
            propagated_total += propagate_check(clause, reasons, known)
            dependencies[ident] = list(reasons)
            reason_positions += len(reasons)
            maximum_reasons = max(maximum_reasons, len(reasons))
            previous_derived = ident
            derived_count += 1
        else:
            raise ValueError('unsupported proof record')
        known[ident] = clause
        last_id = ident
    require(saw_derived and last_id is not None and known[last_id] == [], 'proof does not end in a derived empty clause')
    require(used_theories == selected_set, 'selected theory list is not exactly the admitted theory axioms')
    needed, pending = set(), [last_id]
    while pending:
        ident = pending.pop()
        if ident in needed:
            continue
        needed.add(ident)
        pending.extend(dependencies[ident])
    require(needed == set(known), 'trace contains unused clauses after backward dependency trimming')
    return dict(status='PASS_TRIMMED_RUP_REFUTATION_RELATIVE_TO_SELECTED_THEORY_AXIOMS',
                input_sha256=binding['input_sha256'], capture=str(capture.resolve()),
                captured_files_sha256=files, input_binding_sha256=sha256(binding_path),
                trace_sha256=sha256(trace_path), selected_indices_sha256=sha256(selected_path),
                original_clause_records=input_count, all_source_theory_clauses=theory_count,
                selected_original_clauses=len(selected_inputs), selected_theory_clauses=len(used_theories),
                derived_clauses=derived_count, total_trace_clauses=len(known),
                ordered_reason_positions=reason_positions, maximum_reasons_per_step=maximum_reasons,
                propagated_assignments=propagated_total, final_empty_clause_id=last_id,
                backward_dependency_closure_checked=True,
                callback_assumptions_admitted=False, theory_validity_checked=False,
                boolean_unsat_checked=True, independent_unsat_certificate_complete=False,
                trust_boundary='All selected arithmetic theory axioms still require exact Farkas checking.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--selected-indices', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (700 << 20,) * 2)
    started = time.monotonic()
    report = check(args.capture, args.binding, args.trace, args.selected_indices)
    report.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=time.monotonic() - started,
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  checker_sha256=sha256(__file__),
                  common_sha256=sha256(Path(__file__).with_name('lra_certificate_common.py')))
    atomic_json(args.out, report)
    print(report['status'], report['selected_theory_clauses'], report['derived_clauses'])


if __name__ == '__main__':
    main()
