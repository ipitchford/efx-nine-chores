"""Independently reconstruct bounded positive-lift allocation formulas.

This checks every serialized clause with only the Python standard library.
It does not import the generator or invoke a solver. The bound is an exact
counterexample-existence reduction, not an exhausted finite domain.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
from itertools import product
import json
from math import isqrt
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
START = time.monotonic()
resource.setrlimit(resource.RLIMIT_AS, (480 * 1024**2,) * 2)
signal.alarm(29)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("m", type=int, choices=(8, 9))
    args = parser.parse_args()
    m = args.m
    spec = importlib.util.spec_from_file_location("lifted_streaming", HERE / "audit_zero_minimum_formula.py")
    syntax = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(syntax)
    signal.setitimer(signal.ITIMER_REAL, max(0.01, 29 - (time.monotonic() - START)))
    file = ROOT / f"continuation/exact_search/lifted{m}_common_minimum_unit_margin.smt2"
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    bound = isqrt((m - 2) * (m - 1)**(m - 2))
    upper = 2 * bound
    width = 3 * m + 1
    variables = {f"c_{i}_{g}": m * i + g for i in range(3) for g in range(m) if g != i}

    def affine(e):
        if isinstance(e, str):
            v = [0] * width
            if e in variables:
                v[variables[e]] = 1
            else:
                number = Fraction(e)
                assert number.denominator == 1
                v[-1] = number.numerator
            return tuple(v)
        op, *children = e
        values = [affine(c) for c in children]
        if op == "+":
            return tuple(map(sum, zip(*values))) if values else (0,) * width
        if op == "-":
            if len(values) == 1:
                return tuple(-v for v in values[0])
            return tuple(values[0][k] - sum(v[k] for v in values[1:]) for k in range(width))
        if op == "*":
            assert len(values) == 2
            a, b = values
            if any(a[:-1]):
                a, b = b, a
            assert not any(a[:-1])
            return tuple(a[-1] * v for v in b)
        raise AssertionError(("unsupported affine syntax", op))

    def atom(e):
        relation, left, right = e
        assert relation in (">=", "<=")
        a, b = affine(left), affine(right)
        if relation == "<=":
            a, b = b, a
        return tuple(x - y for x, y in zip(a, b))

    def substitute(i, coefficients, margin=0):
        v = [0] * width
        v[-1] = coefficients[i] - margin
        for g, q in enumerate(coefficients):
            if g != i:
                v[m * i + g] = q
        return tuple(v)

    expected_domain = []
    for i in range(3):
        for g in range(m):
            if g == i:
                continue
            q = [0] * m
            q[g] = 1
            expected_domain.append(substitute(i, q, 2))
            q[g] = -1
            expected_domain.append(substitute(i, q, -upper))
    q = [0] * m
    q[2], q[1] = 1, -1
    expected_domain.append(substitute(0, q, 2))
    for g in range(3, m - 1):
        q = [0] * m
        q[g], q[g + 1] = 1, -1
        expected_domain.append(substitute(0, q, 2))

    def definitely_cheaper(h, g, i):
        if h == i:
            return True
        if g == i or i != 0:
            return False
        return (h == 1 and g == 2) or (h >= 3 and g >= 3 and h > g)

    allocations = (a for a in product(range(3), repeat=m) if len(set(a)) == 3)
    domain, declarations = [], []
    assertions = clauses = positions = logic = checks = 0
    for command in syntax.commands(file):
        op = command[0]
        if op == "set-logic":
            assert command == ["set-logic", "QF_LRA"]
            logic += 1
        elif op == "declare-fun":
            assert command[2:] == [[], "Real"]
            declarations.append(command[1])
        elif op == "check-sat":
            assert command == ["check-sat"]
            checks += 1
        else:
            assert op == "assert" and len(command) == 2
            e = syntax.expand_let(command[1])
            assertions += 1
            if assertions <= len(expected_domain):
                domain.append(atom(e))
                continue
            assert e[0] == "or"
            allocation = next(allocations)
            bundles = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
            expected = set()
            for i, owned in enumerate(bundles):
                if len(owned) <= 1:
                    continue
                minima = [g for g in owned if not any(h != g and definitely_cheaper(h, g, i) for h in owned)]
                assert minima
                for removed in minima:
                    for j in range(3):
                        if j == i:
                            continue
                        q = [int(g in owned and g != removed) - int(g in bundles[j]) for g in range(m)]
                        expected.add(substitute(i, q, 1))
            actual = [atom(a) for a in e[1:]]
            assert set(actual) == expected, (m, clauses, allocation)
            positions += len(actual)
            clauses += 1
    assert next(allocations, None) is None
    assert logic == checks == 1
    assert len(declarations) == len(set(declarations)) == len(variables)
    assert set(declarations) == set(variables)
    assert Counter(domain) == Counter(expected_domain)
    assert clauses == 3**m - 3 * 2**m + 3
    assert hashlib.sha256(file.read_bytes()).hexdigest() == digest
    report = {
        "status": "PASS_ALL_SERIALIZED_LIFTED_FORMULA_CLAUSES_RECONSTRUCTED_WITH_STDLIB",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "m": m, "input": str(file.relative_to(ROOT)), "input_sha256": digest,
        "zero_integer_bound": bound, "positive_integer_bound": upper,
        "fixed_minima": 1, "nonminimum_lower_bound": 2,
        "nonminimum_order_margin": 2, "allocation_failure_margin": 1,
        "free_real_variables": len(variables), "domain_assertions": len(domain),
        "allocation_clauses": clauses, "total_assertions": assertions,
        "literal_positions_reconstructed": positions,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Every declaration, exact domain bound and order margin, and every retained literal in every allocation clause is independently reconstructed from the EFX definition. The real formula does not impose integrality or evenness. Its forward implication uses the proved integer-lifting representative, and any satisfying real matrix has a designated failure of margin at least one for each allocation. No solver is run and no global result is asserted.",
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (HERE / f"lifted{m}_formula_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
