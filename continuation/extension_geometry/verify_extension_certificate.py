"""Independent, standard-library-only checker for extension-region certificates.

This file deliberately does not import the oracle, Z3, NumPy, or a solver.
It reconstructs literal EFX comparisons and checks rational conic identities.
The final finite Boolean refutation is exhaustively checked by a memoised
choice recursion over the selected allocations' positive clauses.
"""
from fractions import Fraction
from functools import lru_cache
from itertools import product
import argparse
import json
from pathlib import Path


def vector(value, m):
    assert isinstance(value, list) and len(value) == m
    assert all(isinstance(x, int) for x in value)
    return tuple(value)


def inequality(value, m):
    assert value['row'] in (0, 1, 2)
    return value['row'], vector(value['coeffs'], m)


def check_boolean_refutation(atom_count, clauses, edges):
    clauses = [frozenset(q) for q in clauses]
    assert all(all(isinstance(a, int) and 0 <= a < atom_count for a in q) for q in clauses)
    conflicts = [0] * atom_count
    blocked = 0
    for edge in edges:
        assert len(edge) in (1, 2)
        assert all(isinstance(a, int) and 0 <= a < atom_count for a in edge)
        if len(edge) == 1:
            blocked |= 1 << edge[0]
        else:
            a, b = edge
            conflicts[a] |= 1 << b
            conflicts[b] |= 1 << a
    covered = [sum(1 << j for j, q in enumerate(clauses) if a in q) for a in range(atom_count)]

    @lru_cache(None)
    def refute(blocked, satisfied):
        remaining = [([a for a in q if not (blocked >> a & 1)], j)
                     for j, q in enumerate(clauses) if not (satisfied >> j & 1)]
        if not remaining:
            return False
        choices, _ = min(remaining, key=lambda item: len(item[0]))
        # The shortest outstanding clause must contain some true atom.
        # Every possible choice has to lead to a contradiction.
        return all(refute(blocked | conflicts[a], satisfied | covered[a]) for a in choices)

    assert refute(blocked, 0), 'Boolean cover certificate is satisfiable'
    return refute.cache_info().currsize


def verify(data):
    assert data['status'] == 'covered'
    C = [[Fraction(v) for v in row] for row in data['prefix']]
    assert len(C) == 3 and len(set(map(len, C))) == 1
    m = len(C[0])
    assert all(v >= 0 for row in C for v in row)
    lower_domain = data.get('extension_domain_lower', [[0] * m for _ in range(3)])
    assert len(lower_domain) == 3
    lower_domain = [vector(q, m) for q in lower_domain]
    assert all(q >= 0 for row in lower_domain for q in row)
    region = [inequality(v, m) for v in data['region']]
    raw = [inequality(v, m) for v in data.get('unreduced_region', data['region'])]
    background = [inequality(v, m) for v in data.get('domain_inequalities', [])]
    assert all(sum(q[g] * C[i][g] for g in range(m)) >= 0 for i, q in region + raw + background)

    if 'linear_reduction' in data:
        steps = data['linear_reduction']['derivations']
        assert sorted(d['target_index'] for d in steps) == list(range(len(raw)))
        for d in steps:
            i, target = raw[d['target_index']]
            total = [Fraction(0)] * m
            for label, source_list in [('retained', region), ('background', background)]:
                for term in d.get(label, []):
                    j, source = source_list[term['index']]
                    weight = Fraction(term['weight'])
                    assert j == i and weight >= 0
                    for g in range(m):
                        total[g] += weight * source[g]
            for term in d['coordinates']:
                assert 0 <= term['index'] < m
                weight = Fraction(term['weight'])
                assert weight >= 0
                total[term['index']] += weight
            assert tuple(total) == target
    else:
        assert set(raw) <= set(region)

    cert = data['certificate']
    atoms = []
    for a in cert['atoms']:
        i, q = inequality(a, m)
        assert a['side'] in ('upper', 'lower')
        atoms.append((i, a['side'], q))
    assert len(set(atoms)) == len(atoms)
    atom_index = {a: j for j, a in enumerate(atoms)}
    expected = []
    for box in data['cover']:
        allocation = box['allocation']
        assert len(allocation) == m + 1 and all(a in (0, 1, 2) for a in allocation)
        bundles = [[g for g, a in enumerate(allocation) if a == i] for i in range(3)]
        literals = set()
        lo = [Fraction(0)] * 3
        hi = [None] * 3
        for i in range(3):
            for removed in bundles[i]:
                remaining = set(bundles[i]) - {removed}
                for j in range(3):
                    if i == j:
                        continue
                    other = set(bundles[j])
                    # EFX is q.C + sign*x_i <= 0.
                    q = tuple(int(g in remaining) - int(g in other) for g in range(m))
                    sign = int(m in remaining) - int(m in other)
                    constant = sum(q[g] * C[i][g] for g in range(m))
                    if sign == 0:
                        needed = tuple(-v for v in q)
                        assert all(v >= 0 for v in needed) or (i, needed) in raw
                        assert constant <= 0
                    elif sign == 1:
                        bound = tuple(-v for v in q)
                        literals.add(atom_index[(i, 'upper', bound)])
                        hi[i] = -constant if hi[i] is None else min(hi[i], -constant)
                    elif sign == -1:
                        literals.add(atom_index[(i, 'lower', q)])
                        lo[i] = max(lo[i], constant)
                    else:
                        raise AssertionError(sign)
        assert lo == [Fraction(v) for v in box['lower']]
        assert hi == [None if v is None else Fraction(v) for v in box['upper']]
        expected.append(literals)
    assert [set(c) for c in cert['allocation_clauses']] == expected

    def premise_for(edge):
        assert len(edge) in (1, 2)
        if len(edge) == 1:
            i, side, q = atoms[edge[0]]
            assert side == 'lower'
            return i, tuple(a - v for a, v in zip(lower_domain[i], q))
        i, upper, u = atoms[edge[0]]
        j, lower, l = atoms[edge[1]]
        assert i == j and upper == 'upper' and lower == 'lower'
        return i, tuple(a - b for a, b in zip(u, l))

    edges = []
    for edge in cert['always_incompatibilities']:
        _, q = premise_for(edge)
        assert all(v >= 0 for v in q)
        edges.append(edge)
    for group in cert['premised_incompatibilities']:
        p = inequality(group, m)
        assert p in raw
        for edge in group['edges']:
            assert premise_for(edge) == p
            edges.append(edge)
    states = check_boolean_refutation(len(atoms), expected, edges)
    scope = 'ninth_columns_above_recorded_linear_lower_bounds' if any(v for row in lower_domain for v in row) else 'all_nonnegative_ninth_columns'
    assert data.get('coverage_scope', scope) == scope
    return dict(status='PASS', prefix_columns=m, cover_allocations=len(expected),
                region_inequalities=len(region), background_inequalities=len(background),
                conic_identities=len(data.get('linear_reduction', {}).get('derivations', [])),
                propositional_states=states,
                coverage_scope=scope, extension_domain_lower=[list(q) for q in lower_domain],
                method='Independent literal reconstruction, exact rational linear identities, exhaustive Boolean choice recursion; standard library only')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('certificates', nargs='+')
    p.add_argument('--output')
    a = p.parse_args()
    results = []
    for value in a.certificates:
        result = dict(file=value, **verify(json.loads(Path(value).read_text())))
        results.append(result)
        print(json.dumps(result))
    if a.output:
        Path(a.output).write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
