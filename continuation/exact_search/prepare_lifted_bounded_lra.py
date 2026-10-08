#!/usr/bin/env python3
"""Prepare the common-minimum-one, integer-margin lifting relaxation.

All variables are REAL. A bounded even integer representative proves the
forward existence implication; any real model with positive failure margins
is itself a counterexample. No satisfiability call occurs in this script.
"""
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import resource
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (800 << 20, 800 << 20))
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
import numpy as np
import z3
from efx_exact import efx

SOURCE_HASHES = {
    8: "6ded8e5f8277d7f6860c8e206dd4e1f17860998fe877c20b862e78d5be12bde6",
    9: "9f8f4cb07528ce39e6eff07420cfde8069d2cf40899a7f088c87f1a4195a8776",
}


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def canonical(rows):
    rows = [row[:] for row in rows]
    if rows[0][1] > rows[0][2]:
        rows = [rows[0], rows[2], rows[1]]
        for row in rows:
            row[1], row[2] = row[2], row[1]
    columns = list(range(3)) + sorted(range(3, len(rows[0])), key=lambda g: rows[0][g], reverse=True)
    return [[row[g] for g in columns] for row in rows]


def affine_parser(variables):
    ids = {v.get_id(): i for i, v in enumerate(variables)}
    cache = {}
    size = len(variables) + 1
    def affine(expr):
        key = expr.get_id()
        if key in cache:
            return cache[key]
        result = np.zeros(size, dtype=np.int64)
        if key in ids:
            result[ids[key]] = 1
        elif z3.is_rational_value(expr):
            assert expr.denominator_as_long() == 1
            result[-1] = expr.numerator_as_long()
        elif z3.is_add(expr) or z3.is_sub(expr):
            for k, child in enumerate(expr.children()):
                result += (-1 if z3.is_sub(expr) and k else 1) * affine(child)
        elif z3.is_mul(expr):
            nonconstant = []
            factor = 1
            for child in expr.children():
                if z3.is_rational_value(child):
                    assert child.denominator_as_long() == 1
                    factor *= child.numerator_as_long()
                else:
                    nonconstant.append(child)
            assert len(nonconstant) <= 1
            if nonconstant:
                result = factor * affine(nonconstant[0])
            else:
                result[-1] = factor
        else:
            raise ValueError("Unsupported actual affine syntax: " + str(expr))
        cache[key] = result
        return result
    return affine


def prepare_and_audit(m):
    start = time.monotonic()
    zero_bound = math.isqrt((m - 2) * (m - 1) ** (m - 2))
    upper = 2 * zero_bound
    source = PROJECT / f"results/root{m}_pruned.smt2"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == SOURCE_HASHES[m]
    original = list(z3.parse_smt2_file(str(source)))
    nalloc = 3 ** m - 3 * 2 ** m + 3
    source_clauses = original[-nalloc:]
    assert all(z3.is_or(a) for a in source_clauses)
    c = [[z3.Real(f"c_{i}_{g}") for g in range(m)] for i in range(3)]
    variables = [v for row in c for v in row]
    expected_source_domain = []
    for i in range(3):
        expected_source_domain += [c[i][g] > 0 for g in range(m)]
        expected_source_domain += [c[i][g] > c[i][i] for g in range(m) if g != i]
    expected_source_domain += [c[0][1] < c[0][2]]
    expected_source_domain += [c[0][g + 1] < c[0][g] for g in range(3, m - 1)]
    assert len(original) == nalloc + len(expected_source_domain)
    assert {z3.simplify(a).sexpr() for a in original[:-nalloc]} == {
        z3.simplify(a).sexpr() for a in expected_source_domain}
    substitutions = [(c[i][i], z3.RealVal(1)) for i in range(3)]
    domain = []
    for i in range(3):
        for g in range(m):
            if g != i:
                domain += [c[i][g] >= 2, c[i][g] <= upper]
    domain += [c[0][2] - c[0][1] >= 2]
    domain += [c[0][g] - c[0][g + 1] >= 2 for g in range(3, m - 1)]
    atom_cache = {}
    def transform(atom):
        key = atom.get_id()
        if key not in atom_cache:
            assert z3.is_gt(atom)
            atom_cache[key] = z3.substitute(atom.arg(0) - atom.arg(1), *substitutions) >= 1
        return atom_cache[key]
    clauses = [z3.Or(*(transform(a) for a in clause.children())) for clause in source_clauses]
    holder = z3.SolverFor("QF_LRA")
    holder.add(*(domain + clauses))
    path = HERE / f"lifted{m}_common_minimum_unit_margin.smt2"
    path.write_text("; REAL relaxation justified by zero-minimum integer representative and lifting.\n"
                    "; Minima=1, nonminima in [2,2Z_m], canonical order gaps>=2, failure margins>=1.\n"
                    "(set-logic QF_LRA)\n" + holder.sexpr() + "\n(check-sat)\n")
    parsed = list(z3.parse_smt2_file(str(path)))
    assert len(parsed) == len(domain) + nalloc
    assert all(z3.simplify(a).eq(z3.simplify(b)) for a, b in zip(domain + clauses, parsed))
    actual_clauses = parsed[-nalloc:]
    affine = affine_parser(variables)
    vectors, atom_ids, clause_indices = [], {}, []
    positions = 0
    support_max = 0
    source_target_pairs = set()
    for original_clause, actual_clause in zip(source_clauses, actual_clauses):
        assert z3.is_or(actual_clause) and original_clause.num_args() == actual_clause.num_args()
        indices = []
        for source_atom, actual_atom in zip(original_clause.children(), actual_clause.children()):
            assert z3.is_gt(source_atom) and z3.is_ge(actual_atom)
            pair = source_atom.get_id(), actual_atom.get_id()
            if pair not in source_target_pairs:
                source_target_pairs.add(pair)
                raw = affine(source_atom.arg(0)) - affine(source_atom.arg(1))
                assert raw[-1] == 0 and set(raw[:-1]).issubset({-1, 0, 1})
                support = int(np.count_nonzero(raw[:-1]))
                support_max = max(support_max, support)
                assert support <= m - 2
                assert len({g // m for g, x in enumerate(raw[:-1]) if x}) == 1
                expected = raw.copy()
                for i in range(3):
                    expected[-1] += expected[i * m + i]
                    expected[i * m + i] = 0
                expected[-1] -= 1
                actual = affine(actual_atom.arg(0)) - affine(actual_atom.arg(1))
                assert np.array_equal(expected, actual)
            key = actual_atom.get_id()
            if key not in atom_ids:
                atom_ids[key] = len(vectors)
                vectors.append(affine(actual_atom.arg(0)) - affine(actual_atom.arg(1)))
            indices.append(atom_ids[key])
            positions += 1
        clause_indices.append(indices)
    # Padding is false for a >=0 atom, not the zero vector.
    padding = np.zeros(3 * m + 1, dtype=np.int64)
    padding[-1] = -1
    vectors.append(padding)
    dummy = len(vectors) - 1
    index = np.full((nalloc, max(map(len, clause_indices))), dummy, dtype=np.int64)
    for k, ids in enumerate(clause_indices):
        index[k, :len(ids)] = ids
    coefficients = np.array(vectors)
    all_assignments = list(itertools.product(range(3), repeat=m))
    surjective = [a for a in all_assignments if len(set(a)) == 3]
    rng = random.Random(860101 + m)
    samples = []
    tied = [[1] * m for _ in range(3)]
    for i in range(3):
        tied[i][i] = 0
    samples.append((tied, False))
    for k in range(9):
        rows = [rng.sample(range(1, min(zero_bound, 300) + 1), m) for i in range(3)]
        for i in range(3):
            rows[i][i] = 0
        samples.append((canonical(rows), True))
    counts = []
    for sample, (zero, strict) in enumerate(samples):
        lifted = [[1 if g == i else 2 * zero[i][g] for g in range(m)] for i in range(3)]
        assert all(2 <= lifted[i][g] <= upper for i in range(3) for g in range(m) if g != i)
        vector = np.array([v for row in lifted for v in row] + [1], dtype=np.int64)
        assert int(np.max(np.abs(vector))) * int(np.max(np.sum(np.abs(coefficients), axis=1))) < 2 ** 62
        encoded_bad = (coefficients @ vector >= 0)[index].any(axis=1)
        literal_bad = np.array([not efx(lifted, a) for a in surjective])
        assert np.array_equal(encoded_bad, literal_bad)
        for assignment in all_assignments:
            assert efx(zero, assignment) == efx(lifted, assignment), (sample, assignment)
        if strict:
            substitutions_for_sample = list(zip(variables, map(z3.RealVal, vector[:-1].tolist())))
            assert all(z3.is_true(z3.simplify(z3.substitute(a, *substitutions_for_sample))) for a in parsed[:-nalloc])
        counts.append(int(np.sum(~literal_bad)))
    receipt = dict(status="PREPARED_AND_AUDITED_NO_SOLVE", created_at_utc=datetime.now(timezone.utc).isoformat(),
                   m=m, input=str(path), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   input_bytes=path.stat().st_size, source=str(source), source_sha256=digest,
                   zero_integer_bound=zero_bound, fixed_minimum=1, nonminimum_lower=2, nonminimum_upper=upper,
                   canonical_nonminimum_order_margin=2, allocation_failure_margin=1,
                   variable_type="Real", free_variables=3 * (m - 1), integrality_imposed=False, evenness_imposed=False,
                   assertions=len(parsed), domain_assertions=len(domain), allocation_clauses=nalloc,
                   literal_positions=positions, distinct_source_target_atom_pairs=len(source_target_pairs),
                   source_coefficient_support_max=support_max, actual_affine_coefficient_audit="PASS",
                   source_domain_verified=True, serialized_roundtrip="PASS", row_total_constraints=False,
                   literal_lifting_audit="PASS: all sampled complete allocations have identical EFX truth before and after the integer lift",
                   lift_definition="c_i(i)=1; c_i(g)=2*z_i(g) for g!=i; no whole-row addition",
                   lift_margin_identity="F_lift=2*F_zero+a_i(i), with a_i(i) in {-1,0,1}",
                   matrices=len(samples), canonical_strict_matrices=9,
                   complete_matrix_allocation_pairs=len(samples) * len(all_assignments),
                   serialized_formula_literal_comparisons=len(samples) * len(surjective),
                   efx_counts=counts, coefficient_and_literal_mismatches=0,
                   theorem="zero_minimum_reduction.md, positive lifting corollary",
                   pointwise_equivalence_for_arbitrary_real_matrices=False,
                   proof_status="No solver call; existence reduction and finite implementation audits only",
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   elapsed_seconds=time.monotonic() - start,
                   max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(HERE / f"lifted{m}_common_minimum_preparation.json", receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    for m in (8, 9):
        prepare_and_audit(m)
