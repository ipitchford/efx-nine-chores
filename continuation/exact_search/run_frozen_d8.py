#!/usr/bin/env python3
"""One bounded D8 solve: prescribed agent 0 EF, agents 1 and 2 literal EFX.

This runner is deliberately distinct from the ordinary-EFX main9 runner.
A SAT model is checked against all 6561 complete allocations for both
predicates, and can only be a D8 counterexample if the prescribed count is zero.
"""
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
BASE = Path(__file__).resolve().parent


def save(path, record):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def main():
    source = BASE / "D8_fixed_strict_uncoupled.smt2"
    output = BASE / "D8_fixed_strict_uncoupled_calibration.json"
    expected = "2d0b7a3dbe1ae88f46b1413e7fc17af5c53ca734ccd0b2ecf67fa8d5498fe17c"
    data = source.read_bytes()
    input_hash = hashlib.sha256(data).hexdigest()
    assert input_hash == expected
    cgroup = Path("/sys/fs/cgroup")
    current = int((cgroup / "memory.current").read_text())
    maximum = int((cgroup / "memory.max").read_text())
    record = dict(status="preparing", input=str(source), input_sha256=input_hash,
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  started_at_utc=datetime.now(timezone.utc).isoformat(),
                  timeout_seconds=120, address_space_cap_mib=750, arith_solver=2, random_seed=0,
                  ordinary_ef_agents=[0], efx_agents=[1, 2],
                  launch_memory_current_bytes=current, launch_memory_max_bytes=maximum,
                  launch_headroom_bytes=maximum-current, required_headroom_bytes=1 << 30,
                  proof_status="no independently checked proof", solver_verdict="none")
    if maximum - current < 1 << 30:
        record["status"] = "not_started_insufficient_memory_headroom"
        save(output, record)
        print(json.dumps(record), flush=True)
        return
    resource.setrlimit(resource.RLIMIT_AS, (750 << 20, 750 << 20))
    sys.path.insert(0, str(PROJECT / "src"))
    import z3
    from efx_exact import efx
    record["solver"] = "z3-" + z3.get_version_string()
    save(output, record)
    print(json.dumps(record), flush=True)
    started = time.monotonic()
    try:
        solver = z3.SolverFor("QF_LRA")
        solver.set(timeout=120000, random_seed=0)
        solver.set("arith.solver", 2)
        solver.from_string(data.decode())
        del data
        checking = time.monotonic()
        record.update(status="running", assertions=len(solver.assertions()),
                      parse_seconds=checking-started, check_started_at_utc=datetime.now(timezone.utc).isoformat())
        save(output, record)
        print(json.dumps(record), flush=True)
        result = solver.check()
        record.update(status=str(result), solver_verdict=str(result),
                      check_seconds=time.monotonic()-checking, statistics=str(solver.statistics()))
        save(output, record)
        if result == z3.sat:
            model = solver.model()
            model_path = output.with_suffix(".model.smt2")
            model_path.write_text(model.sexpr() + "\n")
            rational = []
            rows = []
            for i in range(3):
                row = []
                for g in range(8):
                    value = z3.RealVal(1) if i == g else model.eval(z3.Real(f"c_{i}_{g}"), model_completion=True)
                    row.append(Fraction(value.numerator_as_long(), value.denominator_as_long()))
                assert row[i] == 1 and all(value > 1 for g, value in enumerate(row) if g != i)
                denominator = math.lcm(*(value.denominator for value in row))
                integer = [int(value * denominator) for value in row]
                divisor = math.gcd(*integer)
                rows.append([value // divisor for value in integer])
                rational.append([str(value) for value in row])
            designated = []
            ordinary = []
            checked = 0
            for allocation in itertools.product(range(3), repeat=8):
                if efx(rows, allocation, designated=0):
                    designated.append(allocation)
                if efx(rows, allocation):
                    ordinary.append(allocation)
                checked += 1
            record.update(model_path=str(model_path), rational_rows=rational, integer_rows=rows,
                          complete_allocations_checked=checked, prescribed_agent=0,
                          designated_ef_efx_count=len(designated), designated_ef_efx_allocations=designated,
                          ordinary_efx_count=len(ordinary), ordinary_efx_first_allocations=ordinary[:10],
                          sat_semantic_check="PASS" if not designated else "FAIL",
                          exact_D8_counterexample=not designated,
                          exact_ordinary_EFX_counterexample=not ordinary)
        elif result == z3.unknown:
            record["reason_unknown"] = solver.reason_unknown()
    except BaseException as error:
        record.update(status="exception", exception_type=type(error).__name__, exception=str(error))
        raise
    finally:
        record.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),
                      elapsed_seconds=time.monotonic()-started,
                      max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(output, record)
        print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
