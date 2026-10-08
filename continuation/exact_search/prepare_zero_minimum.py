#!/usr/bin/env python3
"""Prepare and audit exact zero-minimum, positive-reference EFX formulas.

No satisfiability check is made. Frozen allocation clauses are substituted
exactly; their new domain is rebuilt explicitly. A separate literal checker
evaluates every owned-chore deletion, including deletions of zero-cost chores.
"""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import resource
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (1000 << 20, 1000 << 20))
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
import numpy as np
import z3
from efx_exact import efx
from verify_encoding import compiled_allocation_clauses

REFERENCES = [1, 0, 0]
SOURCE_HASHES = {
    8: "6ded8e5f8277d7f6860c8e206dd4e1f17860998fe877c20b862e78d5be12bde6",
    9: "9f8f4cb07528ce39e6eff07420cfde8069d2cf40899a7f088c87f1a4195a8776",
}


def save(path, record):
    path.write_text(json.dumps(record, indent=2) + "\n")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def canonical(rows):
    rows = [row[:] for row in rows]
    if rows[0][1] > rows[0][2]:
        rows = [rows[0], rows[2], rows[1]]
        for row in rows:
            row[1], row[2] = row[2], row[1]
    columns = list(range(3)) + sorted(range(3, len(rows[0])), key=lambda g: rows[0][g], reverse=True)
    return [[row[g] for g in columns] for row in rows]


def prepare(m):
    start = time.monotonic()
    source = PROJECT / f"results/root{m}_pruned.smt2"
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_digest == SOURCE_HASHES[m]
    original = list(z3.parse_smt2_file(str(source)))
    nalloc = 3 ** m - 3 * 2 ** m + 3
    c = [[z3.Real(f"c_{i}_{g}") for g in range(m)] for i in range(3)]
    expected_domain = []
    for i in range(3):
        expected_domain += [c[i][g] > 0 for g in range(m)]
        expected_domain += [c[i][g] > c[i][i] for g in range(m) if g != i]
    expected_domain += [c[0][g + 1] < c[0][g] for g in range(3, m - 1)]
    expected_domain += [c[0][1] < c[0][2]]
    assert len(original) == len(expected_domain) + nalloc
    assert {z3.simplify(a).sexpr() for a in original[:-nalloc]} == {
        z3.simplify(a).sexpr() for a in expected_domain}
    assert all(z3.is_or(a) for a in original[-nalloc:])
    substitutions = [(c[i][i], z3.RealVal(0)) for i in range(3)]
    substitutions += [(c[i][REFERENCES[i]], z3.RealVal(1)) for i in range(3)]
    domain = [c[i][g] > 0 for i in range(3) for g in range(m)
              if g not in (i, REFERENCES[i])]
    domain += [z3.substitute(c[0][1] < c[0][2], *substitutions)]
    domain += [z3.substitute(c[0][g + 1] < c[0][g], *substitutions)
               for g in range(3, m - 1)]
    clauses = [z3.substitute(a, *substitutions) for a in original[-nalloc:]]
    holder = z3.SolverFor("QF_LRA")
    holder.add(*(domain + clauses))
    path = HERE / f"zero_minimum{m}_reference_strict.smt2"
    path.write_text("; Separate zero-minimum normalization; literal EFX includes zero deletions.\n"
                    "; Diagonal minima are zero; references [1,0,0] are one.\n"
                    "(set-logic QF_LRA)\n" + holder.sexpr() + "\n(check-sat)\n")
    parsed = list(z3.parse_smt2_file(str(path)))
    assert len(parsed) == len(domain) + nalloc
    assert all(z3.simplify(a).eq(z3.simplify(b)) for a, b in zip(domain + clauses, parsed))
    declared = set()
    visited = set()
    def visit(expr):
        if expr.get_id() in visited:
            return
        visited.add(expr.get_id())
        if z3.is_const(expr) and expr.decl().kind() == z3.Z3_OP_UNINTERPRETED:
            declared.add(str(expr))
        for child in expr.children():
            visit(child)
    for assertion in parsed:
        visit(assertion)
    expected_variables = {str(c[i][g]) for i in range(3) for g in range(m)
                          if g not in (i, REFERENCES[i])}
    assert declared == expected_variables
    receipt = dict(status="prepared_no_solver_call", created_at_utc=utcnow(), m=m,
                   input=str(path), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   input_bytes=path.stat().st_size, source=str(source), source_sha256=source_digest,
                   fixed_minima=0, fixed_reference_cost=1, reference_columns=REFERENCES,
                   free_real_variables=len(declared), assertions=len(parsed),
                   domain_assertions=len(domain), allocation_clauses=nalloc,
                   source_domain_exactly_verified=True,
                   all_allocation_clauses_exactly_substituted=True,
                   serialized_roundtrip_all_assertions="PASS", row_total_constraints=False,
                   zero_cost_owned_chore_deletions_included=True,
                   reduction_note="zero_minimum_reduction.md",
                   elapsed_seconds=time.monotonic() - start)
    save(HERE / f"zero_minimum{m}_reference_preparation.json", receipt)
    print(json.dumps(receipt), flush=True)
    return path, domain


def formula_audit(m, path, domain):
    start = time.monotonic()
    coef, index = compiled_allocation_clauses(path, m)
    assignments = list(itertools.product(range(3), repeat=m))
    surjective = [a for a in assignments if len(set(a)) == 3]
    empty = [a for a in assignments if len(set(a)) < 3]
    rng = random.Random(731004 + m)
    matrices = []
    tied = [[1] * m for _ in range(3)]
    for i in range(3):
        tied[i][i] = 0
    matrices.append(("tied_positive_off_minimum_control", tied, False))
    for k in range(9):
        rows = [rng.sample(range(2, 101), m) for _ in range(3)]
        for i in range(3):
            rows[i][i] = 0
        matrices.append((f"canonical_generic_{k}", canonical(rows), True))
    counts = []
    variables = [v for row in [[z3.Real(f"c_{i}_{g}") for g in range(m)] for i in range(3)] for v in row]
    max_integer_product = 0
    for label, rows, strict in matrices:
        refs = [rows[i][REFERENCES[i]] for i in range(3)]
        assert all(refs)
        common = math.lcm(*refs)
        values = [x * (common // refs[i]) for i, row in enumerate(rows) for x in row]
        vector = np.array(values + [common], dtype=np.int64)
        product_bound = int(np.max(np.abs(vector))) * int(np.max(np.sum(np.abs(coef), axis=1)))
        assert product_bound < 2 ** 62
        max_integer_product = max(max_integer_product, product_bound)
        encoded_bad = (coef @ vector > 0)[index].any(axis=1)
        literal_bad = np.array([not efx(rows, a) for a in surjective])
        mismatches = np.flatnonzero(encoded_bad != literal_bad)
        assert len(mismatches) == 0, (label, mismatches[:10].tolist())
        assert all(not efx(rows, a) for a in empty), label
        normalized = [z3.RealVal(str(Fraction(x, refs[i]))) for i, row in enumerate(rows) for x in row]
        if strict:
            substitutions = list(zip(variables, normalized))
            assert all(z3.is_true(z3.simplify(z3.substitute(a, *substitutions))) for a in domain), label
        counts.append(dict(label=label, literal_efx_count=int(np.sum(~literal_bad)), strict_domain_checked=strict))
    receipt = dict(status="PASS", created_at_utc=utcnow(), m=m,
                   input=str(path), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   matrices=len(matrices), canonical_strict_matrices=9,
                   surjective_allocation_comparisons=len(matrices) * len(surjective),
                   empty_bundle_allocations_checked=len(matrices) * len(empty),
                   complete_matrix_allocation_pairs=len(matrices) * len(assignments),
                   mismatches=0, maximum_checked_int64_product_bound=max_integer_product,
                   reference_scaling="exact common-denominator integer arithmetic",
                   literal_checker=str(PROJECT / "src/efx_exact.py"),
                   literal_checker_sha256=hashlib.sha256((PROJECT / "src/efx_exact.py").read_bytes()).hexdigest(),
                   efx_counts=counts, elapsed_seconds=time.monotonic() - start,
                   scope="Finite encoder audit, not a universal proof or a solver verdict.")
    save(HERE / f"zero_minimum{m}_reference_semantic_audit.json", receipt)
    print(json.dumps(receipt), flush=True)


def lowering_audit():
    start = time.monotonic()
    rng = random.Random(93007)
    records = []
    subset_pairs = 0
    allocation_pairs = 0
    for m in (8, 9):
        samples = [[[1] * m for _ in range(3)], [[0] * m for _ in range(3)]]
        samples += [[rng.sample(range(1, 121), m) for _ in range(3)] for k in range(8)]
        assignments = list(itertools.product(range(3), repeat=m))
        for k, rows in enumerate(samples):
            minima = [min(range(m), key=lambda g: rows[i][g]) for i in range(3)]
            lowered = [row[:] for row in rows]
            for i in range(3):
                lowered[i][minima[i]] = 0
                for mask in range(1 << m):
                    bundle = [g for g in range(m) if mask >> g & 1]
                    old_residual = sum(rows[i][g] for g in bundle) - min((rows[i][g] for g in bundle), default=0)
                    new_residual = sum(lowered[i][g] for g in bundle) - min((lowered[i][g] for g in bundle), default=0)
                    assert old_residual == new_residual
                    assert sum(lowered[i][g] for g in bundle) <= sum(rows[i][g] for g in bundle)
                    subset_pairs += 1
            before = after = 0
            for a in assignments:
                old_good, new_good = efx(rows, a), efx(lowered, a)
                assert not new_good or old_good, (m, k, a)
                before += old_good
                after += new_good
                allocation_pairs += 1
            records.append(dict(m=m, sample=k, efx_before=before, efx_after=after))
    control = [[5, 0, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]]
    assignment = (0, 0, 1, 2)
    assert not efx(control, assignment)
    bundles = [[g for g, i in enumerate(assignment) if i == j] for j in range(3)]
    positive_only = all(sum(control[i][h] for h in bundles[i] if h != g) <= sum(control[i][h] for h in bundles[j])
                        for i in range(3) for j in range(3) if i != j for g in bundles[i] if control[i][g] > 0)
    assert positive_only
    arithmetic = {}
    for m in (8, 9):
        radicand = (m - 2) * (m - 1) ** (m - 2)
        bound = math.isqrt(radicand)
        assert bound ** 2 <= radicand < (bound + 1) ** 2
        arithmetic[str(m)] = dict(dimension=m - 1, radicand=radicand, bound=bound,
                                 lower_square=bound ** 2, upper_square=(bound + 1) ** 2,
                                 positive_private_integer_variables=3 * (m - 1),
                                 normalized_free_real_variables=3 * (m - 2),
                                 cost_bits=bound.bit_length(), maximum_row_sum=(m - 1) * bound,
                                 sum_bits=((m - 1) * bound).bit_length())
    receipt = dict(status="PASS", created_at_utc=utcnow(),
                   allocation_inclusion="EFX(lowered) is a subset of EFX(original)",
                   matrix_allocation_pairs=allocation_pairs, subset_residual_pairs=subset_pairs,
                   residual_mismatches=0, inclusion_violations=0,
                   zero_deletion_mutation_detected=True,
                   mutation_control=dict(costs=control, assignment=assignment,
                                         literal_efx=False, positive_cost_deletions_only=True),
                   determinant_arithmetic=arithmetic, samples=records,
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   elapsed_seconds=time.monotonic() - start,
                   scope="Finite literal controls and exact arithmetic supplement the mathematical proof; no solver call.")
    save(HERE / "zero_minimum_reduction_audit.json", receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    lowering_audit()
    for m in (8, 9):
        path, domain = prepare(m)
        formula_audit(m, path, domain)
