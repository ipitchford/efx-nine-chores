#!/usr/bin/env python3
"""Finite, independently literal audit of designated-agent allocation clauses.

This does not solve an SMT problem or prove an unrestricted encoding theorem.
It evaluates the frozen clause arrays on exact matrices, including boundary
matrices outside their canonical domain, and compares them with all EFX
comparisons plus ordinary envy-freeness for designated agent 0.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time

import z3


ROOT = Path(__file__).resolve().parents[1]


def literal(matrix, allocation):
    bundles = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            for removed in bundles[i]:
                remaining = sum(matrix[i][g] for g in bundles[i] if g != removed)
                other = sum(matrix[i][g] for g in bundles[j])
                if remaining > other:
                    return False
    own = sum(matrix[0][g] for g in bundles[0])
    return all(own <= sum(matrix[0][g] for g in bundles[j]) for j in (1, 2))


def main() -> int:
    started = time.perf_counter()
    receipts = []
    source_matrix = [
        [37, 51, 59, 255, 264, 325, 355],
        [12, 57, 90, 511, 1343, 643, 1878],
        [2885, 595, 1010, 33353, 23598, 71016, 7970],
    ]
    for m, source in [
        (6, ROOT / 'work/structural_designated_m6.standard.smt2'),
        (7, ROOT / 'work/structural_designated_reduced_m7_seed0.standard.smt2'),
    ]:
        allocations = [a for a in itertools.product(range(3), repeat=m) if m == 6 or len(set(a)) == 3]
        assertions = list(z3.parse_smt2_file(str(source)))
        clauses = assertions[-len(allocations):]
        expected_prefix = 26 if m == 6 else 41
        if len(assertions) - len(allocations) != expected_prefix:
            raise ValueError('frozen assertion coverage/count changed')
        matrices = [
            ('zero', [[0] * m for _ in range(3)]),
            ('uniform', [[1] * m for _ in range(3)]),
            ('zero_cost_boundaries', [[0] * m, [g % 3 for g in range(m)], [(2 * g + 1) % 4 for g in range(m)]]),
            ('unbalanced_rational', [[Fraction(row[g], i + 3) for g in range(m)] for i, row in enumerate(source_matrix)]),
        ]
        counts = []
        for label, matrix in matrices:
            substitutions = [(z3.Real(f'c_{i}_{g}'), z3.RealVal(str(matrix[i][g]))) for i in range(3) for g in range(m)]
            accepted = 0
            for allocation, clause in zip(allocations, clauses):
                expected = literal(matrix, allocation)
                evaluated = z3.simplify(z3.substitute(clause, *substitutions))
                if not (z3.is_true(evaluated) or z3.is_false(evaluated)):
                    raise ValueError('a grounded failure clause did not reduce to Boolean')
                if z3.is_true(evaluated) == expected:
                    raise AssertionError(f'm={m}, matrix={label}, allocation={allocation}: disagreement')
                accepted += int(expected)
            if label == 'uniform' and accepted != (90 if m == 6 else 420):
                raise AssertionError('uniform designated-agent count differs from independent combinatorial count')
            counts.append({'matrix': label, 'accepted_allocations_in_tested_domain': accepted})
        receipts.append({
            'm': m, 'input': str(source), 'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'domain_assertions': expected_prefix, 'allocation_clauses': len(clauses),
            'matrix_count': len(matrices), 'matrix_allocation_pairs': len(matrices) * len(clauses),
            'zero_cost_chores_quantified': True,
            'allocation_domain': 'all complete labelled allocations' if m == 6 else 'all complete nonempty labelled allocations',
            'disagreements': 0, 'counts': counts,
        })
    report = {
        'result': 'PASS', 'solver_used_for_search': False,
        'evaluation_library': 'Z3 ' + z3.get_version_string(),
        'scope': 'Finite allocation-clause equivalence audit with independent literal EFX+EF predicate; not a universal encoder proof.',
        'cases': receipts, 'elapsed_s': round(time.perf_counter() - started, 6),
    }
    text = json.dumps(report, indent=2) + '\n'
    (ROOT / 'results/designated_semantic_audit.json').write_text(text)
    print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
