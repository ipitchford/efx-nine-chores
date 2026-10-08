#!/usr/bin/env python3
"""Prepare or solve the rowwise Cramer/Hadamard bounded ordinary-EFX search.

All 3*m costs are private integers. B=floor((m-1)**(m/2)) gives B8=2401
and B9=11585. There is no common-minimum or row-total constraint.
The default is preparation plus independent finite semantic audit, not solving.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from math import isqrt
from pathlib import Path
import random
import resource
import sys
import time

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(HERE / "ortools_runtime"))
sys.path.insert(0, str(PROJECT / "src"))
import numpy as np
import ortools
from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2
from google.protobuf import text_format
import z3
from efx_exact import efx


def save(path, record):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def canonical(rows):
    rows = [list(row) for row in rows]
    if rows[0][1] > rows[0][2]:
        rows = [rows[0], rows[2], rows[1]]
        for row in rows:
            row[1], row[2] = row[2], row[1]
    order = list(range(3)) + sorted(range(3, len(rows[0])), key=lambda g: rows[0][g], reverse=True)
    return [[row[g] for g in order] for row in rows]


def has_field(constraint, name):
    method = getattr(constraint, "has_" + name, None)
    return method() if method is not None else constraint.HasField(name)


def compile_proto_clauses(proto, m):
    """Read actual CP proto implications and ORs, independently of SMT conversion."""
    d = 3 * m
    names = [v.name for v in proto.variables]
    cost_columns = {k: int(name.split("_")[1]) * m + int(name.split("_")[2])
                    for k, name in enumerate(names) if name.startswith("c_")}
    coefficients, lower, upper, indicator_ids, clauses = [], [], [], [], []
    for constraint in proto.constraints:
        if has_field(constraint, "bool_or"):
            assert not constraint.enforcement_literal
            literals = list(constraint.bool_or.literals)
            assert literals and all(value >= 0 for value in literals)
            clauses.append(literals)
        elif has_field(constraint, "linear") and constraint.enforcement_literal:
            indicators = list(constraint.enforcement_literal)
            assert len(indicators) == 1 and indicators[0] >= 0
            row = [0] * d
            for index, coefficient in zip(constraint.linear.vars, constraint.linear.coeffs):
                assert index in cost_columns
                row[cost_columns[index]] += coefficient
            domain = list(constraint.linear.domain)
            assert len(domain) == 2
            coefficients.append(row)
            lower.append(domain[0]); upper.append(domain[1]); indicator_ids.append(indicators[0])
    assert len(clauses) == 3**m - 3 * 2**m + 3
    assert len(indicator_ids) == len(set(indicator_ids))
    dummy = len(names)
    indices = np.full((len(clauses), max(map(len, clauses))), dummy, dtype=np.int64)
    for k, clause in enumerate(clauses):
        assert set(clause) <= set(indicator_ids)
        indices[k, :len(clause)] = clause
    return (np.array(coefficients, dtype=np.int64), np.array(lower, dtype=np.int64),
            np.array(upper, dtype=np.int64), np.array(indicator_ids, dtype=np.int64),
            indices, dummy + 1)


def proto_failures(compiled, rows):
    coefficients, lower, upper, indicators, indices, size = compiled
    vector = np.array([x for row in rows for x in row], dtype=np.int64)
    assert int(np.max(np.abs(vector))) * int(np.max(np.sum(np.abs(coefficients), axis=1))) < 2**62
    values = coefficients @ vector
    permitted = np.zeros(size, dtype=bool)
    permitted[indicators] = (values >= lower) & (values <= upper)
    return permitted[indices].any(axis=1)


def audit_model(model, m, bound, output):
    compiled = compile_proto_clauses(model.proto, m)
    old_compiled = None
    old_path = HERE / "cpsat8_complete_no_lp.pbtxt"
    if m == 8:
        old_proto = cp_model_pb2.CpModelProto()
        text_format.Parse(old_path.read_text(), old_proto)
        old_compiled = compile_proto_clauses(old_proto, m)
    nonempty = [a for a in itertools.product(range(3), repeat=m) if len(set(a)) == 3]
    empty = [a for a in itertools.product(range(3), repeat=m) if len(set(a)) != 3]
    samples = [("uniform", [[1] * m for _ in range(3)], True)]
    rng = random.Random(2026100700 + m)
    for k in range(4):
        rows = [rng.sample(range(2, 400), m) for _ in range(3)]
        for i in range(3): rows[i][i] = 1
        samples.append((f"common_minimum_{k}", canonical(rows), True))
    for k in range(4):
        rows = [rng.sample(range(10, bound + 1), m) for _ in range(3)]
        for i in range(3): rows[i][i] = i + k + 1
        samples.append((f"independent_minima_{k}", canonical(rows), False))
    counts = []
    old_comparisons = 0
    for label, rows, common in samples:
        bad = proto_failures(compiled, rows)
        direct = np.array([not efx(rows, a) for a in nonempty])
        assert np.array_equal(bad, direct), label
        assert all(not efx(rows, a) for a in empty), label
        if old_compiled is not None and common:
            old_bad = proto_failures(old_compiled, rows)
            assert np.array_equal(old_bad, direct), label
            old_comparisons += len(nonempty)
        if label != "uniform":
            assert all(1 <= value <= bound for row in rows for value in row)
            assert all(rows[i][g] > rows[i][i] for i in range(3) for g in range(m) if i != g)
            assert rows[0][1] < rows[0][2]
            assert all(rows[0][g] > rows[0][g+1] for g in range(3, m-1))
        counts.append(dict(sample=label, efx_allocations=int(np.sum(~direct))))
    assert counts[0]["efx_allocations"] == 1680
    receipt = dict(status="PASS", m=m, search_bound=bound, matrices=len(samples),
                   cp_proto_vs_literal_comparisons=len(samples)*len(nonempty),
                   empty_bundle_allocations_verified_bad=len(samples)*len(empty),
                   complete_allocation_pairs=len(samples)*3**m,
                   mismatches=0, old_common_minimum_cp_comparisons=old_comparisons,
                   old_common_minimum_cp_model=str(old_path) if old_compiled is not None else None,
                   old_common_minimum_cp_sha256=hashlib.sha256(old_path.read_bytes()).hexdigest() if old_compiled is not None else None,
                   counts=counts,
                   scope="Finite independent audit of actual CP proto allocation predicates; no proof of UNSAT.")
    save(output.with_name(output.stem + "_semantic_audit.json"), receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--m", type=int, choices=[8, 9], required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--solve", action="store_true")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--cap-mib", type=int, default=1000)
    parser.add_argument("--linearization", type=int, choices=[0, 1, 2], default=1)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (args.cap_mib << 20, args.cap_mib << 20))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    m = args.m; d = 3 * m; bound = isqrt((m-1)**m)
    source = PROJECT / f"results/root{m}_pruned.smt2"
    started = time.monotonic()
    record = dict(status="preparing", m=m, free_cost_variables=d, search_bound=bound,
                  derived_complete_bound=bound, bound_formula="isqrt((m-1)**m)",
                  bound_proof="row-local vertex, Cramer, and Hadamard argument; independent review confirmed in session",
                  common_minimum=False, rowtotal_least=False, all_different=False,
                  source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  started_at_utc=datetime.now(timezone.utc).isoformat(),
                  address_space_cap_mib=args.cap_mib, timeout_seconds=args.timeout,
                  workers=1, random_seed=0, linearization=args.linearization,
                  solver="OR-Tools CP-SAT " + ortools.__version__,
                  proof_status="no externally checked UNSAT proof")
    target = args.out.with_suffix(".json")
    save(target, record); print(json.dumps(record), flush=True)
    model = cp_model.CpModel()
    names = [f"c_{i}_{g}" for i in range(3) for g in range(m)]
    variables = {name: model.new_int_var(1, bound, name) for name in names}
    rows = [[variables[f"c_{i}_{g}"] for g in range(m)] for i in range(3)]
    expressions = z3.parse_smt2_file(str(source))
    seen = set(); cache = {}
    def linear(expression):
        key = expression.get_id()
        if key in cache: return cache[key]
        coefficients = {}; constant = 0
        if z3.is_rational_value(expression):
            assert expression.denominator_as_long() == 1
            constant = expression.numerator_as_long()
        elif z3.is_const(expression) and expression.decl().kind() == z3.Z3_OP_UNINTERPRETED:
            name = str(expression); assert name in variables; seen.add(name); coefficients[name] = 1
        elif z3.is_add(expression) or z3.is_sub(expression):
            for k, child in enumerate(expression.children()):
                coeff, value = linear(child)
                sign = -1 if z3.is_sub(expression) and k else 1
                constant += sign * value
                for name, value in coeff.items(): coefficients[name] = coefficients.get(name, 0) + sign * value
        elif expression.decl().kind() == z3.Z3_OP_UMINUS:
            coeff, value = linear(expression.arg(0)); coefficients = {name: -value for name, value in coeff.items()}; constant = -value
        else:
            raise ValueError("Unsupported source arithmetic: " + str(expression))
        coefficients = {name: value for name, value in coefficients.items() if value}
        cache[key] = coefficients, constant
        return coefficients, constant
    def inequality(atom):
        op = atom.decl().kind(); assert op in (z3.Z3_OP_GT, z3.Z3_OP_LT)
        left, lc = linear(atom.arg(0)); right, rc = linear(atom.arg(1))
        coeff = left.copy()
        for name, value in right.items(): coeff[name] = coeff.get(name, 0) - value
        constant = lc - rc
        if op == z3.Z3_OP_LT: coeff = {name: -value for name, value in coeff.items()}; constant = -constant
        assert constant == 0
        return tuple(sorted((name, value) for name, value in coeff.items() if value)), 1
    atoms = {}; clause_count = 0; actual_domain = set()
    def cp_expression(coeff): return sum(value * variables[name] for name, value in coeff)
    for assertion in expressions:
        if z3.is_or(assertion):
            literals = []
            for atom in assertion.children():
                key = inequality(atom)
                if key not in atoms:
                    indicator = model.new_bool_var(f"failure_{len(atoms)}")
                    model.add(cp_expression(key[0]) >= key[1]).only_enforce_if(indicator)
                    atoms[key] = indicator
                literals.append(atoms[key])
            model.add_bool_or(literals); clause_count += 1
        else:
            key = inequality(assertion); actual_domain.add(key)
            model.add(cp_expression(key[0]) >= key[1])
    assert seen == set(names)
    expected_domain = set()
    def condition(values): expected_domain.add((tuple(sorted(values.items())), 1))
    for i in range(3):
        for g in range(m):
            condition({f"c_{i}_{g}": 1})
            if g != i: condition({f"c_{i}_{g}": 1, f"c_{i}_{i}": -1})
    condition({"c_0_2": 1, "c_0_1": -1})
    for g in range(3, m-1): condition({f"c_0_{g}": 1, f"c_0_{g+1}": -1})
    assert actual_domain == expected_domain
    assert len(actual_domain) == 7*m-6
    assert clause_count == 3**m-3*2**m+3
    validation = model.validate()
    if validation: raise ValueError(validation)
    proto_path = args.out.with_suffix(".pbtxt")
    model.export_to_file(str(proto_path))
    record.update(model_file=str(proto_path.resolve()), model_sha256=hashlib.sha256(proto_path.read_bytes()).hexdigest(),
                  allocation_clauses=clause_count, shared_atoms=len(atoms), domain_assertions=len(actual_domain))
    semantic = audit_model(model, m, bound, args.out)
    record.update(status="prepared_and_audited_no_solve", semantic_audit=semantic["status"],
                  build_and_audit_seconds=time.monotonic()-started,
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(target, record); print(json.dumps(record), flush=True)
    if not args.solve: return
    current = int(Path("/sys/fs/cgroup/memory.current").read_text())
    maximum = int(Path("/sys/fs/cgroup/memory.max").read_text())
    record.update(launch_memory_current_bytes=current, launch_memory_max_bytes=maximum,
                  launch_headroom_bytes=maximum-current, required_headroom_bytes=1 << 30)
    if maximum-current < 1 << 30:
        record["status"] = "not_started_insufficient_memory_headroom"
        save(target, record); print(json.dumps(record), flush=True); return
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.timeout
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = 0
    solver.parameters.linearization_level = args.linearization
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    record.update(status="running", check_started_at_utc=datetime.now(timezone.utc).isoformat())
    save(target, record); print(json.dumps(record), flush=True)
    checking = time.monotonic()
    with args.out.with_suffix(".search.log").open("w") as log:
        def logging(line): log.write(line + "\n"); log.flush()
        solver.log_callback = logging
        try:
            status = solver.solve(model)
            record.update(status=solver.status_name(status), check_seconds=time.monotonic()-checking,
                          response_statistics=solver.response_stats())
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                costs = [[int(solver.value(value)) for value in row] for row in rows]
                good = [list(a) for a in itertools.product(range(3), repeat=m) if efx(costs, a)]
                record.update(rows=costs, literal_complete_allocations_checked=3**m,
                              literal_efx_count=len(good), literal_efx_allocations=good,
                              conclusion="EXACT_COUNTEREXAMPLE" if not good else "ENCODER_OR_SOLVER_MISMATCH")
            elif status == cp_model.INFEASIBLE:
                record["conclusion"] = "UNSAT_COMPLETE_ROWWISE_BOUND"
            else: record["conclusion"] = "NO_RESULT"
        except Exception as error:
            record.update(status="EXCEPTION_WITHOUT_VERDICT", exception=type(error).__name__ + ": " + str(error),
                          check_seconds=time.monotonic()-checking, conclusion="NO_RESULT")
    record.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(target, record); print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
