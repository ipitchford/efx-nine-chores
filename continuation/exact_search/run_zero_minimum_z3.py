#!/usr/bin/env python3
"""Hash-pinned zero-minimum LRA worker with proof capture and literal SAT replay."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import resource
import sys
import time

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
import z3
from efx_exact import efx

REFERENCES = [1, 0, 0]


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def save(path, record):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def exact_model_audit(model, m):
    rational_rows, integer_rows = [], []
    for i in range(3):
        row = []
        for g in range(m):
            if g == i:
                value = z3.RealVal(0)
            elif g == REFERENCES[i]:
                value = z3.RealVal(1)
            else:
                value = model.eval(z3.Real(f"c_{i}_{g}"), model_completion=True)
            assert z3.is_rational_value(value)
            row.append(Fraction(value.numerator_as_long(), value.denominator_as_long()))
        denominator = math.lcm(*(value.denominator for value in row))
        integers = [int(value * denominator) for value in row]
        divisor = math.gcd(*integers)
        assert divisor > 0
        integer_rows.append([value // divisor for value in integers])
        rational_rows.append([str(value) for value in row])
    for i, row in enumerate(integer_rows):
        assert row[i] == 0
        assert all(row[g] > 0 for g in range(m) if g != i)
    assert integer_rows[0][1] < integer_rows[0][2]
    assert all(integer_rows[0][g] > integer_rows[0][g + 1] for g in range(3, m - 1))
    good = []
    checked = 0
    zero_deletions = 0
    for assignment in itertools.product(range(3), repeat=m):
        bundles = [[g for g in range(m) if assignment[g] == i] for i in range(3)]
        okay = True
        for i in range(3):
            own = sum(integer_rows[i][g] for g in bundles[i])
            for j in range(3):
                if i == j:
                    continue
                other = sum(integer_rows[i][g] for g in bundles[j])
                for g in bundles[i]:
                    zero_deletions += integer_rows[i][g] == 0
                    if own - integer_rows[i][g] > other:
                        okay = False
        # The second checker independently rebuilds all literal deletion sums.
        assert okay == efx(integer_rows, assignment)
        checked += 1
        if okay:
            good.append(assignment)
    assert checked == 3 ** m and zero_deletions > 0
    return dict(rational_rows=rational_rows, integer_rows=integer_rows,
                complete_labeled_allocations_checked=checked,
                explicit_zero_deletion_comparisons=zero_deletions,
                two_literal_checkers_agree=True,
                efx_allocation_count=len(good), efx_allocations=good,
                sat_semantic_check="PASS" if not good else "FAIL")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("--cap-mib", type=int, required=True)
    parser.add_argument("--arith", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--m", type=int, required=True)
    parser.add_argument("--proof", action="store_true")
    args = parser.parse_args()
    cap = args.cap_mib << 20
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    if args.proof:
        z3.set_param(proof=True)
    data = args.input.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert digest == args.expected_sha256
    record = dict(status="starting", started_at_utc=utcnow(),
                  input=str(args.input.resolve()), input_sha256=digest,
                  input_bytes=len(data), solver="z3-" + z3.get_version_string(),
                  timeout_seconds=args.timeout, address_space_cap_mib=args.cap_mib,
                  arith_solver=args.arith, random_seed=args.seed,
                  fixed_minima=0, reference_columns=REFERENCES, reference_cost=1,
                  free_real_variables=3 * (args.m - 2), proof_generation_enabled=args.proof,
                  proof_status="no independently checked proof")
    target = args.out.with_suffix(".json")
    save(target, record)
    print(json.dumps(record), flush=True)
    started = time.monotonic()
    try:
        solver = z3.SolverFor("QF_LRA")
        solver.set(timeout=args.timeout * 1000, random_seed=args.seed)
        solver.set("arith.solver", args.arith)
        solver.from_string(data.decode())
        del data
        checking = time.monotonic()
        record.update(status="running", assertions=len(solver.assertions()),
                      parse_seconds=checking - started, check_started_at_utc=utcnow())
        save(target, record)
        print(json.dumps(record), flush=True)
        result = solver.check()
        record.update(status=str(result), solver_verdict=str(result),
                      check_seconds=time.monotonic() - checking,
                      statistics=str(solver.statistics()))
        # Preserve the solver result before potentially large proof/model export.
        save(target, record)
        print(json.dumps(record), flush=True)
        if result == z3.sat:
            model_path = args.out.with_suffix(".model.smt2")
            model_path.write_text(solver.model().sexpr() + "\n")
            record["model_path"] = str(model_path)
            record.update(exact_model_audit(solver.model(), args.m))
        elif result == z3.unknown:
            record["reason_unknown"] = solver.reason_unknown()
        elif args.proof:
            proof_path = args.out.with_suffix(".z3proof")
            proof_path.write_text(solver.proof().sexpr() + "\n")
            record.update(proof_path=str(proof_path), proof_bytes=proof_path.stat().st_size,
                          proof_sha256=hashlib.sha256(proof_path.read_bytes()).hexdigest(),
                          proof_status="native Z3 proof exported; not independently checked")
    except BaseException as error:
        if record.get("solver_verdict") not in ("sat", "unsat", "unknown"):
            record["status"] = "exception_without_solver_verdict"
        record.update(exception_type=type(error).__name__, exception=str(error))
        raise
    finally:
        record.update(finished_at_utc=utcnow(), elapsed_seconds=time.monotonic() - started,
                      max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(target, record)
        print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
