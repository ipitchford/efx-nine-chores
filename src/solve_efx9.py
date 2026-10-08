#!/usr/bin/env python3
"""Find a complete zero-inclusive EFX allocation for a rational 3 x 9 matrix.

Python standard library only. JSON decimal numbers and fraction strings are
read exactly. No SMT solver, floating tolerance, or theorem certificate is
needed to run this finite allocation finder.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import product
import json
from math import lcm
import os
from pathlib import Path
import sys
import tempfile


def parse_costs(payload):
    rows = payload.get("costs") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("exactly three cost rows are required")
    costs = []
    for row in rows:
        if not isinstance(row, list) or len(row) != 9:
            raise ValueError("each row must contain exactly nine costs")
        converted = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
                raise ValueError("costs must be integers, exact decimal strings, or fraction strings")
            try:
                q = Fraction(value)
            except (ValueError, ZeroDivisionError) as exc:
                raise ValueError("each cost must be a finite rational number") from exc
            if q < 0:
                raise ValueError("costs must be nonnegative")
            converted.append(q)
        costs.append(converted)
    return costs


def integer_rows(costs):
    """Independent positive row scaling preserves all EFX comparisons."""
    denominators = [lcm(*(q.denominator for q in row)) for row in costs]
    return [[int(q * den) for q in row] for row, den in zip(costs, denominators)]


def subset_tables(row):
    total = [0] * (1 << 9)
    minimum = [0] * (1 << 9)
    residual = [0] * (1 << 9)
    for mask in range(1, 1 << 9):
        bit = mask & -mask
        chore = bit.bit_length() - 1
        rest = mask ^ bit
        total[mask] = total[rest] + row[chore]
        minimum[mask] = row[chore] if not rest else min(minimum[rest], row[chore])
        residual[mask] = total[mask] - minimum[mask]
    return total, residual


def find_assignment(costs):
    """Return the first EFX assignment and the number of assignments examined."""
    tables = [subset_tables(row) for row in integer_rows(costs)]
    examined = 0
    for assignment in product(range(3), repeat=9):
        examined += 1
        masks = [0, 0, 0]
        for chore, owner in enumerate(assignment):
            masks[owner] |= 1 << chore
        if all(tables[i][1][masks[i]] <= tables[i][0][masks[j]]
               for i in range(3) for j in range(3) if i != j):
            return assignment, examined
    return None, examined


def literal_certificate(costs, assignment):
    """Re-evaluate every original deletion inequality using exact Fractions."""
    bundles = [[g for g, owner in enumerate(assignment) if owner == i] for i in range(3)]
    inequalities = []
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            target = sum((costs[i][h] for h in bundles[j]), Fraction(0))
            for removed in bundles[i]:
                residual = sum((costs[i][h] for h in bundles[i] if h != removed), Fraction(0))
                if residual > target:
                    raise AssertionError("returned assignment fails a literal EFX inequality")
                inequalities.append({
                    "evaluating_agent": i + 1,
                    "comparison_agent": j + 1,
                    "removed_chore": removed + 1,
                    "removed_cost": str(costs[i][removed]),
                    "remaining_owned_cost": str(residual),
                    "comparison_bundle_cost": str(target),
                    "slack": str(target - residual),
                })
    return bundles, inequalities


def solve(payload):
    costs = parse_costs(payload)
    assignment, examined = find_assignment(costs)
    if assignment is None:
        # A finite negative result would be directly reviewable; do not hide it
        # behind an assumption that the theorem or implementation is correct.
        return {"status": "NO_EFX_ALLOCATION_FOUND", "assignments_examined": examined,
                "costs": [[str(q) for q in row] for row in costs]}
    bundles, inequalities = literal_certificate(costs, assignment)
    return {
        "status": "EFX_ALLOCATION_FOUND_AND_LITERALLY_VERIFIED",
        "indexing": "agents and chores are numbered from 1",
        "arithmetic": "exact rational input; integer search; exact rational certificate",
        "zero_cost_deletions_included": True,
        "empty_bundles_allowed": True,
        "costs": [[str(q) for q in row] for row in costs],
        "assignment_by_chore": [i + 1 for i in assignment],
        "bundles": [[g + 1 for g in bundle] for bundle in bundles],
        "assignments_examined": examined,
        "maximum_assignments": 19683,
        "literal_inequalities_checked": len(inequalities),
        "efx_certificate": inequalities,
    }


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", nargs="?", help="JSON file; omit to read standard input")
    parser.add_argument("--out", help="also write the complete result to this JSON file")
    args = parser.parse_args()
    try:
        raw = Path(args.matrix).read_text() if args.matrix else sys.stdin.read()
        payload = json.loads(raw, parse_float=str,
                             parse_constant=lambda s: (_ for _ in ()).throw(ValueError("nonfinite cost: " + s)))
        result = solve(payload)
        rendered = json.dumps(result, indent=2) + "\n"
        if args.out:
            atomic_write(args.out, rendered)
        sys.stdout.write(rendered)
        return 0 if result["status"] == "EFX_ALLOCATION_FOUND_AND_LITERALLY_VERIFIED" else 2
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
