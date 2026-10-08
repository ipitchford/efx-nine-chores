"""Independently reconstruct every zero-minimum allocation clause, without Z3.

Streaming SMT parsing keeps memory bounded. Exact integer affine vectors are
compared with literal owned-deletion rows after six fixed substitutions. The
minimal-deletion selection is reconstructed from the stated partial order.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import resource
import signal
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (480 * 1024**2,) * 2)
signal.alarm(29)
START = time.monotonic()
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REFERENCES = (1, 0, 0)


def parse(value):
    stack, roots = [], []
    for token in re.findall(r"\(|\)|[^\s()]+", value):
        if token == "(":
            row = []
            (stack[-1] if stack else roots).append(row)
            stack.append(row)
        elif token == ")":
            assert stack
            stack.pop()
        else:
            assert stack
            stack[-1].append(token)
    assert not stack and len(roots) == 1
    return roots[0]


def commands(file):
    depth = 0
    lines = []
    with file.open() as stream:
        for line in stream:
            line = line.split(";", 1)[0]
            if not line.strip():
                continue
            assert '"' not in line and '|' not in line
            depth += line.count("(") - line.count(")")
            assert depth >= 0
            lines.append(line)
            if depth == 0:
                yield parse(" ".join(lines))
                lines = []
    assert depth == 0 and not lines


def expand_let(expr, env=None):
    env = {} if env is None else env
    if isinstance(expr, str):
        return env.get(expr, expr)
    if expr[0] == "let":
        assert len(expr) == 3
        bindings = expr[1]
        assert len({b[0] for b in bindings}) == len(bindings)
        # SMT-LIB let bindings are simultaneous: each right-hand side is
        # interpreted in the outer environment, not in its sibling bindings.
        new = dict(env)
        new.update((name, expand_let(value, env)) for name, value in bindings)
        return expand_let(expr[2], new)
    return [expand_let(part, env) for part in expr]


def audit(m):
    file = ROOT / f"continuation/exact_search/zero_minimum{m}_reference_strict.smt2"
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    width = 3 * m + 1
    variables = {f"c_{i}_{g}": m * i + g for i in range(3) for g in range(m)
                 if g not in (i, REFERENCES[i])}

    def affine(expr):
        if isinstance(expr, str):
            v = [0] * width
            if expr in variables:
                v[variables[expr]] = 1
            else:
                q = Fraction(expr)
                assert q.denominator == 1
                v[-1] = q.numerator
            return tuple(v)
        op, *args = expr
        values = [affine(a) for a in args]
        if op == "+":
            return tuple(map(sum, zip(*values))) if values else (0,) * width
        if op == "-":
            if len(values) == 1:
                return tuple(-q for q in values[0])
            return tuple(values[0][k] - sum(a[k] for a in values[1:]) for k in range(width))
        if op == "*":
            assert len(values) == 2
            a, b = values
            if any(a[:-1]):
                a, b = b, a
            assert not any(a[:-1])
            return tuple(a[-1] * q for q in b)
        raise AssertionError(("Unexpected arithmetic operator", op))

    def atom(expr):
        op, left, right = expr
        assert op in (">", "<")
        a, b = affine(left), affine(right)
        if op == "<":
            a, b = b, a
        return tuple(x - y for x, y in zip(a, b))

    def substituted(i, q):
        row = [0] * width
        for g, value in enumerate(q):
            if g == i:
                continue
            if g == REFERENCES[i]:
                row[-1] += value
            else:
                row[m * i + g] += value
        return tuple(row)

    def known_less(h, g, i):
        if h == i:
            return True
        if i != 0:
            return False
        return (h in (1, 2) and g in (1, 2) and h < g) or (h >= 3 and g >= 3 and h > g)

    expected_domain = []
    for i in range(3):
        for g in range(m):
            if g not in (i, REFERENCES[i]):
                q = [0] * m
                q[g] = 1
                expected_domain.append(substituted(i, q))
    q = [0] * m
    q[1], q[2] = -1, 1
    expected_domain.append(substituted(0, q))
    for g in range(3, m - 1):
        q = [0] * m
        q[g], q[g + 1] = 1, -1
        expected_domain.append(substituted(0, q))
    allocations = (a for a in product(range(3), repeat=m) if len(set(a)) == 3)
    domain, declarations = [], []
    clause_count = literal_positions = zero_deletion_positions = 0
    assertion_count = 0
    logic = checks = 0
    fixture_clause = None
    fixture_allocation = (0, 1, 2, 0, 1, 1, 2, 2, 2)
    for command in commands(file):
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
            expr = expand_let(command[1])
            assertion_count += 1
            if assertion_count <= len(expected_domain):
                domain.append(atom(expr))
                continue
            assert expr[0] == "or"
            allocation = next(allocations)
            bundles = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
            expected = set()
            for i, owned in enumerate(bundles):
                if len(owned) <= 1:
                    continue
                minima = [g for g in owned if not any(h != g and known_less(h, g, i) for h in owned)]
                assert minima
                for removed in minima:
                    for j in range(3):
                        if j == i:
                            continue
                        q = [int(g in owned and g != removed) - int(g in bundles[j]) for g in range(m)]
                        assert sum(bool(v) for v in q) <= m - 2
                        expected.add(substituted(i, q))
                        zero_deletion_positions += removed == i
            actual = [atom(a) for a in expr[1:]]
            assert set(actual) == expected, (m, clause_count, allocation)
            literal_positions += len(actual)
            clause_count += 1
            if m == 9 and allocation == fixture_allocation:
                fixture_clause = actual
    assert next(allocations, None) is None
    assert Counter(domain) == Counter(expected_domain)
    assert len(declarations) == len(set(declarations)) == len(variables)
    assert set(declarations) == set(variables)
    assert logic == checks == 1
    assert clause_count == 3**m - 3 * 2**m + 3
    if m == 9:
        fixture = json.loads((OUT / "zero_minimum_normalization_audit.json").read_text())["zero_deletion_mutation_fixture"]
        vector = [Fraction(v) for row in fixture["normalized_rows"] for v in row] + [Fraction(1)]
        assert fixture_clause and any(sum(q * v for q, v in zip(a, vector)) > 0 for a in fixture_clause)
    assert hashlib.sha256(file.read_bytes()).hexdigest() == digest
    return {
        "status": "PASS_ALL_SERIALIZED_ZERO_MINIMUM_CLAUSES_RECONSTRUCTED_WITH_STDLIB",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "m": m, "input": str(file.relative_to(ROOT)), "input_sha256": digest,
        "free_real_variables": len(variables), "domain_assertions": len(domain),
        "allocation_clauses": clause_count, "total_assertions": assertion_count,
        "literal_positions_checked": literal_positions,
        "pinned_zero_deletion_positions_reconstructed": zero_deletion_positions,
        "zero_deletion_mutation_fixture_rejected_by_actual_clause": True if m == 9 else None,
        "scope": "Every serialized affine failure atom and every allocation clause is compared exactly against independent literal reconstruction with only the justified possible-minimum deletion pruning. All free-variable declarations, positive/reference/order domain assertions and command shapes are checked. Pinned zero deletions remain included. No solver or global coverage check is run.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("m", type=int, choices=(8, 9))
    parser.add_argument("--output")
    args = parser.parse_args()
    report = audit(args.m)
    output = Path(args.output) if args.output else OUT / f"zero_minimum{args.m}_formula_audit.json"
    if not output.is_absolute():
        output = ROOT / output
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
