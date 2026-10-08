#!/usr/bin/env python3
"""Solve a hash-pinned static formula and preserve startup and terminal receipts.

An UNSAT result is a solver result, not an externally checked proof.
Every SAT model is converted to integer rows and checked literally against
all 3**m complete labeled allocations, including allocations with empty bundles.
"""
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

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
import z3


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def save(path, record):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(record, indent=2) + "\n")
    temp.replace(path)


def exact_model_audit(model, m):
    fractions = []
    rows = []
    for i in range(3):
        row = []
        for g in range(m):
            value = z3.RealVal(1) if i == g else model.eval(z3.Real(f"c_{i}_{g}"), model_completion=True)
            row.append(Fraction(value.numerator_as_long(), value.denominator_as_long()))
        denominator = math.lcm(*(v.denominator for v in row))
        integers = [int(v * denominator) for v in row]
        divisor = math.gcd(*integers)
        rows.append([v // divisor for v in integers])
        fractions.append([str(v) for v in row])
    good = []
    checked = 0
    literal_checks = 0
    for assignment in itertools.product(range(3), repeat=m):
        bundles = [[g for g in range(m) if assignment[g] == i] for i in range(3)]
        okay = True
        for i in range(3):
            own = sum(rows[i][g] for g in bundles[i])
            for j in range(3):
                if i == j:
                    continue
                other = sum(rows[i][g] for g in bundles[j])
                for g in bundles[i]:
                    literal_checks += 1
                    if own - rows[i][g] > other:
                        okay = False
                        break
                if not okay:
                    break
            if not okay:
                break
        checked += 1
        if okay:
            good.append(bundles)
    return dict(rational_rows=fractions, integer_rows=rows,
                complete_labeled_allocations_checked=checked,
                literal_deletion_comparisons=literal_checks,
                efx_allocation_count=len(good), efx_allocations=good,
                sat_semantic_check="PASS" if not good else "FAIL")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--cap-mib", type=int, default=2450)
    parser.add_argument("--arith", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--m", type=int, default=9)
    args = parser.parse_args()
    limit = args.cap_mib << 20
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data = args.input.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != args.expected_sha256:
        raise RuntimeError(f"Frozen-input hash mismatch: {digest}")
    record = dict(status="starting", started_at_utc=utcnow(),
                  input=str(args.input.resolve()), input_sha256=digest,
                  input_bytes=len(data), solver="z3-" + z3.get_version_string(),
                  timeout_seconds=args.timeout, address_space_cap_mib=args.cap_mib,
                  arith_solver=args.arith, random_seed=args.seed,
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
                      parse_seconds=checking-started, check_started_at_utc=utcnow())
        save(target, record)
        print(json.dumps(record), flush=True)
        result = solver.check()
        record.update(status=str(result), check_seconds=time.monotonic()-checking,
                      statistics=str(solver.statistics()))
        if result == z3.sat:
            model_path = args.out.with_suffix(".model.smt2")
            model_path.write_text(solver.model().sexpr() + "\n")
            record["model_path"] = str(model_path.resolve())
            record.update(exact_model_audit(solver.model(), args.m))
        elif result == z3.unknown:
            record["reason_unknown"] = solver.reason_unknown()
    except BaseException as error:
        record.update(status="exception_without_solver_verdict", exception_type=type(error).__name__,
                      exception=str(error))
        raise
    finally:
        record.update(finished_at_utc=utcnow(), elapsed_seconds=time.monotonic()-started,
                      max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(target, record)
        print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
