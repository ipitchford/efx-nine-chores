#!/usr/bin/env python3
"""Normalize the archived designated-agent D8 formula and audit, without solving.

The source requires ordinary EF for agent 0 and literal EFX for agents 1
and 2. Independent positive row scaling makes each pinned minimum one.
Agent 0 remains designated; no row-total comparison or cross-row gauge is added.
"""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import re
import resource
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (900 << 20, 900 << 20))
PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
import numpy as np
import z3
from efx_exact import efx
from verify_encoding import compiled_allocation_clauses


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(rows):
    rows = [list(row) for row in rows]
    if rows[0][1] > rows[0][2]:
        rows = [rows[0], rows[2], rows[1]]
        for row in rows:
            row[1], row[2] = row[2], row[1]
    columns = list(range(3)) + sorted(range(3, 8), key=lambda g: rows[0][g], reverse=True)
    return [[row[g] for g in columns] for row in rows]


def integer_vector(rows):
    values = [Fraction(x) for row in rows for x in row] + [Fraction(1)]
    denominator = math.lcm(*(x.denominator for x in values))
    return np.array([int(x * denominator) for x in values], dtype=np.int64)


def evaluate(coefficients, indices, rows):
    vector = integer_vector(rows)
    assert int(np.max(np.abs(vector))) * int(np.max(np.sum(np.abs(coefficients), axis=1))) < 2**62
    return (coefficients @ vector > 0)[indices].any(axis=1)


def main():
    started = time.monotonic()
    source = PROJECT / "results/D8_root.smt2"
    destination = Path(__file__).resolve().parent / "D8_fixed_strict_uncoupled.smt2"
    source_hash = digest(source)
    assert source_hash == "700a33e91a5ba54c777ee18a720f72c6e2537139be843902093b0eef01e5f1d0"
    old = list(z3.parse_smt2_file(str(source)))
    substitutions = [(z3.Real(f"c_{i}_{i}"), z3.RealVal(1)) for i in range(3)]
    transformed = [z3.substitute(a, *substitutions) for a in old]
    holder = z3.SolverFor("QF_LRA")
    holder.add(*transformed)
    destination.write_text(holder.to_smt2())
    parsed = list(z3.parse_smt2_file(str(destination)))
    assert len(parsed) == len(transformed) == 5846
    assert all(a.eq(b) for a, b in zip(transformed, parsed))
    domain = [a for a in parsed if not z3.is_or(a)]
    clauses = [a for a in parsed if z3.is_or(a)]
    assert len(domain) == 50 and len(clauses) == 5796
    cross_row_domain = [a.sexpr() for a in domain if len(set(re.findall(r"c_([0-2])_", a.sexpr()))) > 1]
    assert not cross_row_domain
    assert not any(re.search(r"c_([0-2])_\1\b", a.sexpr()) for a in parsed)
    preparation = dict(status="prepared_without_solver_call", source=str(source), source_sha256=source_hash,
                       frozen_input=str(destination), frozen_input_sha256=digest(destination),
                       assertions=5846, allocation_clauses=5796, domain_assertions=50,
                       variables=21, fixed_minima=["c_0_0=1", "c_1_1=1", "c_2_2=1"],
                       ordinary_ef_agents=[0], efx_agents=[1, 2], strict_failure_atoms=True,
                       cross_row_domain_assertions=cross_row_domain, row_total_comparisons=False,
                       normalization="independent positive row scaling to pinned minimum one",
                       exact_substitution_roundtrip="all 5846 parsed assertions identical",
                       created_at_utc=datetime.now(timezone.utc).isoformat())
    destination.with_name("D8_fixed_strict_uncoupled_preparation.json").write_text(json.dumps(preparation, indent=2) + "\n")

    source_coeff, source_indices = compiled_allocation_clauses(source, 8)
    fixed_coeff, fixed_indices = compiled_allocation_clauses(destination, 8)
    all_allocations = list(itertools.product(range(3), repeat=8))
    nonempty = [a for a in all_allocations if len(set(a)) == 3]
    empty = [a for a in all_allocations if len(set(a)) != 3]
    samples = [("uniform_one", [[1] * 8 for _ in range(3)])]
    rng = random.Random(20261007)
    for k in range(10):
        rows = [rng.sample(range(2, 500), 8) for _ in range(3)]
        for i in range(3):
            rows[i][i] = 1
            rows[i] = [(i + 2) * (k + 1) * value for value in rows[i]]
        samples.append((f"generic_row_scaled_{k}", canonical(rows)))
    fewest = json.loads((PROJECT / "work/compute_designated8_allmin/fewest_model.json").read_text())["rows"]
    samples.append(("previous_one_witness_candidate", canonical(fewest)))
    near = json.loads((PROJECT / "results/D8_small_permutations.json").read_text())[0]["matrix"]
    samples.append(("previous_three_witness_candidate", canonical(near)))
    variables = [z3.Real(f"c_{i}_{g}") for i in range(3) for g in range(8)]
    counts = []
    mutation_counts = []
    for label, rows in samples:
        normalized = [[Fraction(x, row[i]) for x in row] for i, row in enumerate(rows)]
        original_bad = evaluate(source_coeff, source_indices, rows)
        fixed_bad = evaluate(fixed_coeff, fixed_indices, normalized)
        direct_bad = np.array([not efx(normalized, a, designated=0) for a in nonempty])
        assert np.array_equal(original_bad, fixed_bad), label
        assert np.array_equal(fixed_bad, direct_bad), label
        assert all(not efx(normalized, a, designated=0) for a in empty), label
        direct_original = [efx(rows, a, designated=0) for a in nonempty]
        assert direct_original == list(~direct_bad), label
        if label != "uniform_one":
            values = [z3.RealVal(str(value)) for row in normalized for value in row]
            replace = list(zip(variables, values))
            assert all(z3.is_true(z3.simplify(z3.substitute(a, *replace))) for a in domain), label
        good_count = int(np.sum(~direct_bad))
        ordinary_count = sum(efx(normalized, a) for a in nonempty)
        counts.append(dict(sample=label, designated_ef_efx_allocations=good_count,
                           ordinary_efx_allocations=ordinary_count))
        mutation_counts.append(ordinary_count - good_count)
    assert counts[0]["designated_ef_efx_allocations"] == 560
    assert counts[-2]["designated_ef_efx_allocations"] == 1
    assert counts[-1]["designated_ef_efx_allocations"] == 3
    assert all(value > 0 for value in mutation_counts)
    zero_rows = [[1, 1, 1, 1], [5, 0, 1, 1], [1, 1, 1, 1]]
    zero_assignment = (1, 1, 0, 2)
    assert not efx(zero_rows, zero_assignment, designated=0)
    bundles = [[g for g in range(4) if zero_assignment[g] == i] for i in range(3)]
    positive_only = all(sum(zero_rows[i][h] for h in bundles[i] if h != g) <= sum(zero_rows[i][h] for h in bundles[j])
                        for i in (1, 2) for j in range(3) if i != j for g in bundles[i] if zero_rows[i][g] > 0)
    designated_okay = all(sum(zero_rows[0][h] for h in bundles[0]) <= sum(zero_rows[0][h] for h in bundles[j]) for j in (1, 2))
    assert positive_only and designated_okay
    audit = dict(status="PASS", input_sha256=digest(destination), source_sha256=source_hash,
                 matrices=len(samples), allocation_clause_comparisons=len(samples) * len(nonempty),
                 complete_allocations_checked=len(samples) * len(all_allocations),
                 empty_bundle_allocations_verified_bad=len(samples) * len(empty),
                 source_vs_normalized_mismatches=0, normalized_vs_literal_mismatches=0,
                 literal_positive_row_scaling_mismatches=0,
                 all_generic_domain_samples_verified=True,
                 designated_ef_to_efx_mutation_detected=True, zero_deletion_mutation_detected=True,
                 allocation_counts=counts, elapsed_seconds=time.monotonic() - started,
                 max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 scope="finite independent formula-semantic audit; no target solve and no UNSAT proof")
    destination.with_name("D8_fixed_strict_uncoupled_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(dict(preparation=preparation, audit=audit)), flush=True)


if __name__ == "__main__":
    main()
