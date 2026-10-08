#!/usr/bin/env python3
"""Independently check paired ordinal seeds using only exact stdlib arithmetic.

The first row has c00 > 0, c00 < c01 < c02, and
c00 < c08 < c07 < c06 < c05 < c04 < c03. Every seed allocation
gives item 0 to agent 0, so deleting item 0 is the largest remainder.
Each of the four possible pairs of failure inequalities is contradicted
by an archived nonnegative rational linear identity in positive gaps.
"""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path


def rational(value):
    assert isinstance(value, list) and len(value) == 2
    assert all(type(v) is int for v in value) and value[1] > 0
    return Fraction(*value)


def verify(data):
    assert data['order'] == 'descending'
    family = data.get('family', 'fixed_nonprescribed_bundle')
    assert family in ('fixed_nonprescribed_bundle', 'all_minimum_owning_allocations')
    assert data['gap_coordinates'] == [
        'c00', 'c01-c00', 'c02-c01', 'c08-c00', 'c07-c08',
        'c06-c07', 'c05-c06', 'c04-c05', 'c03-c04']
    # Cost of each item as a sum of the nine positive independent gaps.
    cost_from_gap = [[1] + [0] * 8 for _ in range(9)]
    cost_from_gap[1][1] = 1
    cost_from_gap[2][1] = cost_from_gap[2][2] = 1
    for g in range(3, 9):
        for k in range(3, 12-g):
            cost_from_gap[g][k] = 1

    seen = set()
    checked_branches = 0
    counts = {1: 0, 2: 0}
    for record in data['records']:
        allocations = record['allocations']
        ids = record['allocation_ids']
        assert len(allocations) == len(ids) == 2
        if family == 'fixed_nonprescribed_bundle':
            fixed = record['fixed_agent']
            assert type(fixed) is int and fixed in (1, 2)
            counts[fixed] += 1
        pair = tuple(sorted(ids))
        assert len(set(pair)) == 2 and pair not in seen
        seen.add(pair)
        failure_rows = []
        gap_rows = []
        for a, aid in zip(allocations, ids):
            assert isinstance(a, list) and len(a) == 9
            assert all(type(v) is int and v in (0, 1, 2) for v in a)
            assert a[:3] == [0, 1, 2]
            assert type(aid) is int
            assert aid == sum(v * 3 ** (8-g) for g, v in enumerate(a))
            rows = [[int(a[g] == 0 and g != 0) - int(a[g] == j)
                     for g in range(9)] for j in (1, 2)]
            failure_rows.append(rows)
            gap_rows.append([[sum(q[g] * cost_from_gap[g][k] for g in range(9))
                              for k in range(9)] for q in rows])
        if family == 'fixed_nonprescribed_bundle':
            assert [g for g in range(9) if allocations[0][g] == fixed] == [
                g for g in range(9) if allocations[1][g] == fixed]
        assert record['first_row_bad_coefficients'] == failure_rows
        seen_branches = set()
        for branch in record['proof_branches']:
            j, k = branch['first_atom'], branch['second_atom']
            assert type(j) is int and type(k) is int and j in (0, 1) and k in (0, 1)
            assert (j, k) not in seen_branches
            seen_branches.add((j, k))
            weights = list(map(rational, branch['atom_weights']))
            extra = list(map(rational, branch['gap_weights']))
            assert len(weights) == 2 and len(extra) == 9
            assert all(w >= 0 for w in weights + extra) and sum(weights) > 0
            assert all(weights[0] * gap_rows[0][j][h] +
                       weights[1] * gap_rows[1][k][h] + extra[h] == 0
                       for h in range(9))
            checked_branches += 1
        assert seen_branches == set(itertools.product(range(2), repeat=2))
    assert data['certified_pairs'] == len(seen)
    if family == 'fixed_nonprescribed_bundle':
        assert {r['fixed_agent']: r['new_certified_pairs'] for r in data['counts']} == counts
    return dict(status='PASS', certified_pairs=len(seen),
                exhaustive_failure_branches=checked_branches, family=family,
                counts=counts if family == 'fixed_nonprescribed_bundle' else {},
                verification='Literal deletion coefficients and exact nonnegative rational identities; standard library only')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('file', type=Path)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    result = dict(source=str(args.file),
                  source_sha256=hashlib.sha256(args.file.read_bytes()).hexdigest(),
                  **verify(json.loads(args.file.read_text())))
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
