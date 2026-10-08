"""Reconstruct the new fixed-two-row inner inputs without a solver.

Every complete allocation is independently tested for literal EFX of the two
fixed rows, including empty bundles and deletions of owned zero-cost chores.
Every resulting first-row failure clause is reconstructed in both inputs.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
from itertools import product
import json
from math import lcm
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


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location("candidate_streaming", HERE / "audit_zero_minimum_formula.py")
    syntax = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(syntax)
    signal.setitimer(signal.ITIMER_REAL, max(0.01, 29 - (time.monotonic() - START)))
    directory = ROOT / "continuation/structural_nine/fixed_zero_outer_candidate"
    prep_bytes = (directory / "preparation.json").read_bytes()
    prep = json.loads(prep_bytes)
    model_file = ROOT / "continuation/structural_nine/zero_outer/run1_model.json"
    assert sha(model_file.read_bytes()) == prep["source_sha256"]
    model = json.loads(model_file.read_text())["coordinates"]
    rows = [[Fraction(1) if g == 0 else Fraction(0) if g == i else Fraction(model[f"c_{i}_{g}"])
             for g in range(9)] for i in (1, 2)]
    assert rows == [[Fraction(v) for v in row] for row in prep["fixed_rows"]]
    scale = lcm(*(v.denominator for row in rows for v in row))
    integral = [[int(v * scale) for v in row] for row in rows]
    compatible = []
    for aid, allocation in enumerate(product(range(3), repeat=9)):
        bundles = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
        good = True
        for i, row in zip((1, 2), integral):
            totals = [sum(row[g] for g in bundle) for bundle in bundles]
            if any(totals[i] - row[g] > totals[j]
                   for g in bundles[i] for j in range(3) if j != i):
                good = False
                break
        if good:
            compatible.append({"allocation_id": aid, "allocation": list(allocation)})
    assert len(compatible) == 892 and compatible == prep["compatible_allocations"]
    outputs = []
    for mode in ("zero", "positive"):
        variables = {f"c_0_{g}": g for g in range(9) if mode == "positive" or g >= 2}

        def affine(e):
            if isinstance(e, str):
                v = [0] * 10
                if e in variables:
                    v[variables[e]] = 1
                else:
                    q = Fraction(e)
                    assert q.denominator == 1
                    v[-1] = q.numerator
                return tuple(v)
            op, *children = e
            values = [affine(c) for c in children]
            if op == "+":
                return tuple(map(sum, zip(*values))) if values else (0,) * 10
            if op == "-":
                if len(values) == 1:
                    return tuple(-v for v in values[0])
                return tuple(values[0][k] - sum(v[k] for v in values[1:]) for k in range(10))
            if op == "*":
                assert len(values) == 2
                a, b = values
                if any(a[:-1]):
                    a, b = b, a
                assert not any(a[:-1])
                return tuple(a[-1] * v for v in b)
            raise AssertionError(("unsupported affine operator", op))

        def atom(e):
            relation, left, right = e
            assert relation in (">", "<", "=")
            a, b = affine(left), affine(right)
            if relation == "<":
                a, b, relation = b, a, ">"
            return relation, tuple(x - y for x, y in zip(a, b))

        def vector(terms, constant=0):
            v = [0] * 10
            for g, q in terms:
                v[g] += q
            v[-1] = constant
            return tuple(v)

        if mode == "zero":
            expected_domain = [(">", vector([(g, 1)])) for g in range(2, 9)]
            expected_domain += [(">", vector([(2, 1)], -1))]
        else:
            expected_domain = [("=", vector([(0, 1)], -1))]
            expected_domain += [(">", vector([(g, 1)], -1)) for g in range(1, 9)]
            expected_domain += [(">", vector([(2, 1), (1, -1)]))]
        expected_domain += [(">", vector([(g, 1), (g + 1, -1)])) for g in range(3, 8)]
        source = directory / f"{mode}_inner.smt2"
        digest = sha(source.read_bytes())
        assert digest == prep["inputs"][mode]["sha256"]
        declarations, domain = [], []
        assertions = clauses = positions = checks = 0
        for command in syntax.commands(source):
            op = command[0]
            if op == "declare-fun":
                assert command[2:] == [[], "Real"]
                declarations.append(command[1])
            elif op == "set-logic":
                assert command == ["set-logic", "QF_LRA"]
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
                allocation = compatible[clauses]["allocation"]
                bundles = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
                expected = set()
                for removed in bundles[0]:
                    for target in (1, 2):
                        coefficients = [int(g in bundles[0] and g != removed) - int(g in bundles[target]) for g in range(9)] + [0]
                        if mode == "zero":
                            coefficients[-1] = coefficients[1]
                            coefficients[0] = coefficients[1] = 0
                        expected.add((">", tuple(coefficients)))
                if e == "false":
                    actual = []
                elif e[0] == "or":
                    actual = [atom(a) for a in e[1:]]
                else:
                    actual = [atom(e)]
                assert set(actual) == expected, (mode, clauses, allocation)
                positions += len(actual)
                clauses += 1
        assert Counter(domain) == Counter(expected_domain)
        assert declarations and len(declarations) == len(set(declarations)) == len(variables)
        assert set(declarations) == set(variables)
        assert checks == 1 and clauses == 892
        assert assertions == prep["inputs"][mode]["assertions"]
        assert sha(source.read_bytes()) == digest
        outputs.append({"mode": mode, "input": str(source.relative_to(ROOT)), "input_sha256": digest,
                        "declarations": len(declarations), "free_variables_after_equalities": 7 if mode == "zero" else 8,
                        "domain_assertions": len(domain), "allocation_failure_assertions": clauses,
                        "total_assertions": assertions, "literal_positions_checked": positions})
    report = {
        "status": "PASS_ALL_COMPLETE_ALLOCATIONS_AND_BOTH_NEW_INNER_INPUTS_WITH_STDLIB",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "source_model_sha256": sha(model_file.read_bytes()), "preparation_sha256": sha(prep_bytes),
        "allocations_checked": 19683, "fixed_row_compatible_allocations": 892,
        "fixed_rows": [[str(v) for v in row] for row in rows], "inputs": outputs,
        "script_sha256": sha(Path(__file__).read_bytes()),
        "scope": "Both fixed other rows are literal-EFX-tested over all complete allocations, including empty bundles and owned-zero deletions. Every compatible allocation's complete first-row failure disjunction and each domain assertion is independently reconstructed. These are fixed-candidate existential first-row inputs, not universal nine-chore formulas; no solver is run.",
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (HERE / "fixed_candidate_inner_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
