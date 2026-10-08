"""Exact fixed-prefix EFX cover and a linear sufficient extension region.

Public API: analyse_prefix(C, timeout_ms=30000, minimise=True,
                          domain_inequalities=None, extension_domain_lower=None).
For a covered prefix, result['region'] contains row-local homogeneous linear
inequalities: sum(coeffs[g] * C[row][g]) >= 0.  Every nonnegative matrix in
that region admits an EFX extension for EVERY nonnegative ninth column.
If optional domain_inequalities are supplied in the same coefficient format,
the guarantee applies within that explicitly recorded background domain.
Optional extension_domain_lower is a list of three nonnegative integer
coefficient vectors. It restricts the guarantee to ninth columns satisfying
x_i >= dot(extension_domain_lower[i], C[i]); its default is all zero.
For an uncovered prefix, result['new_column'] is an exact rational witness.

The method is general in the number of prefix chores, with three agents.
It does not assume a fixed cheapest-item order.  Certificate clauses retain
all deletion inequalities, including zero-cost deletions.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import time

import z3


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def serial_number(x):
    x = Fraction(x)
    return int(x) if x.denominator == 1 else str(x)


def allocation_box(C, allocation):
    """Literal all-deletions reference derivation for one extended allocation."""
    m = len(C[0])
    A = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
    V = [[sum(C[i][g] for g in A[j] if g < m) for j in range(3)] for i in range(3)]
    lo = [Fraction(0)] * 3
    hi = [None] * 3
    for i in range(3):
        for g in A[i]:
            for j in range(3):
                if j == i:
                    continue
                c = V[i][i] - (C[i][g] if g < m else 0) - V[i][j]
                sign = int(allocation[m] == i) - int(g == m) - int(allocation[m] == j)
                if sign == 0:
                    if c > 0:
                        return None
                elif sign == 1:
                    hi[i] = -c if hi[i] is None else min(hi[i], -c)
                elif sign == -1:
                    lo[i] = max(lo[i], c)
                else:
                    raise AssertionError(sign)
    if any(hi[i] is not None and hi[i] < lo[i] for i in range(3)):
        return None
    return tuple(lo), tuple(hi)


def enumerate_boxes(C):
    """Fast independently phrased box extraction using old bundle residuals."""
    m = len(C[0])
    sums = [[Fraction(0)] * (1 << m) for _ in range(3)]
    residual = [[Fraction(0)] * (1 << m) for _ in range(3)]
    for i in range(3):
        for mask in range(1, 1 << m):
            members = [g for g in range(m) if mask >> g & 1]
            sums[i][mask] = sum(C[i][g] for g in members)
            residual[i][mask] = sums[i][mask] - min(C[i][g] for g in members)
    unique = {}
    for a in product(range(3), repeat=m):
        masks = [sum(1 << g for g in range(m) if a[g] == i) for i in range(3)]
        V = [[sums[i][masks[j]] for j in range(3)] for i in range(3)]
        r = [residual[i][masks[i]] for i in range(3)]
        for k in range(3):
            others = [i for i in range(3) if i != k]
            if masks[k] and V[k][k] > min(V[k][i] for i in others):
                continue
            if any(r[i] > V[i][next(j for j in others if j != i)] for i in others):
                continue
            lo = tuple(Fraction(0) if i == k else max(Fraction(0), r[i] - V[i][k]) for i in range(3))
            hi = tuple(min(V[k][i] for i in others) - r[k] if i == k and masks[k] else None for i in range(3))
            key = lo, hi
            unique.setdefault(key, tuple(a) + (k,))
    return [dict(allocation=a, lower=lo, upper=hi) for (lo, hi), a in unique.items()]


def znum(x):
    x = Fraction(x)
    return z3.RealVal(f"{x.numerator}/{x.denominator}")


def box_complement(entry, x):
    return z3.Or(*([x[i] < znum(entry['lower'][i]) for i in range(3) if entry['lower'][i] > 0]
                  + [x[i] > znum(entry['upper'][i]) for i in range(3) if entry['upper'][i] is not None]))


def choose_cover(boxes, timeout_ms, minimise, lower_baseline=None):
    x = z3.Reals('extension_x0 extension_x1 extension_x2')
    s = z3.SolverFor('QF_LRA')
    s.set(timeout=timeout_ms)
    baseline = [Fraction(0)] * 3 if lower_baseline is None else lower_baseline
    assert len(baseline) == 3 and all(v >= 0 for v in baseline)
    s.add(*(x[i] >= znum(baseline[i]) for i in range(3)))
    labels = [z3.Bool(f'cover_box_{j}') for j in range(len(boxes))]
    for label, box in zip(labels, boxes):
        s.add(z3.Implies(label, box_complement(box, x)))
    status = s.check(*labels)
    if status == z3.sat:
        model = s.model()
        witness = [Fraction(str(model.eval(v, model_completion=True))) for v in x]
        return 'uncovered', witness
    if status != z3.unsat:
        return 'unknown', s.reason_unknown()
    selected = [int(str(b).rsplit('_', 1)[1]) for b in s.unsat_core()]
    if minimise:
        for index in tuple(selected):
            trial = [j for j in selected if j != index]
            if s.check(*(labels[j] for j in trial)) == z3.unsat:
                selected = trial
    return 'covered', [boxes[j] for j in selected]


def literal_forms(allocation, m):
    """Return constant nonnegative premises and strict outside-box atoms.

    atom (row, 'upper', q) means x_row > q.C_row;
    atom (row, 'lower', q) means x_row < q.C_row.
    Constant premise (row,q) means q.C_row >= 0.
    """
    constant = set()
    atoms = set()
    k = allocation[m]
    for i in range(3):
        for g in range(m + 1):
            if allocation[g] != i:
                continue
            for j in range(3):
                if i == j:
                    continue
                q = tuple(int(allocation[h] == i and h != g) - int(allocation[h] == j) for h in range(m))
                sign = int(k == i and g != m) - int(k == j)
                if sign == 0:
                    premise = tuple(-a for a in q)
                    # Nonnegative coefficients need no premise beyond C >= 0.
                    if any(a < 0 for a in premise):
                        constant.add((i, premise))
                elif sign == 1:
                    atoms.add((i, 'upper', tuple(-a for a in q)))
                elif sign == -1:
                    atoms.add((i, 'lower', q))
                else:
                    raise AssertionError(sign)
    return sorted(constant), sorted(atoms)


def generalise_cover(C, cover, timeout_ms, minimise, extension_domain_lower=None):
    """Extract a propositional refutation supported by linear prefix premises."""
    m = len(C[0])
    lower_domain = [[0] * m for _ in range(3)] if extension_domain_lower is None else extension_domain_lower
    forms = [literal_forms(box['allocation'], m) for box in cover]
    atoms = sorted(set(a for _, aa in forms for a in aa))
    index = {a: j for j, a in enumerate(atoms)}
    bools = [z3.Bool(f'ext_atom_{j}') for j in range(len(atoms))]
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    assumptions = []
    labels = {}
    for b, (_, aa) in enumerate(forms):
        name = z3.Bool(f'ext_allocation_{b}')
        labels[str(name)] = ('box', b)
        assumptions.append(name)
        solver.add(z3.Implies(name, z3.Or(*(bools[index[a]] for a in aa))))

    # Multiple arithmetic incompatibilities may share one linear premise.
    grouped = {}
    always_edges = []
    for b, lower in enumerate(atoms):
        i, side, q = lower
        if side != 'lower':
            continue
        lv = dot(q, C[i])
        if lv <= dot(lower_domain[i], C[i]):
            premise = (i, tuple(a - c for a, c in zip(lower_domain[i], q)))
            edge = (b,)
            if all(c >= 0 for c in premise[1]):
                always_edges.append(edge)
            else:
                grouped.setdefault(premise, []).append(edge)
        for a, upper in enumerate(atoms):
            if upper[0] != i or upper[1] != 'upper':
                continue
            if dot(upper[2], C[i]) >= lv:
                premise = (i, tuple(u - l for u, l in zip(upper[2], q)))
                edge = (a, b)
                if all(c >= 0 for c in premise[1]):
                    always_edges.append(edge)
                else:
                    grouped.setdefault(premise, []).append(edge)
    for edge in always_edges:
        solver.add(z3.Or(*(z3.Not(bools[j]) for j in edge)))
    premises = sorted(grouped)
    for p, premise in enumerate(premises):
        name = z3.Bool(f'ext_premise_{p}')
        labels[str(name)] = ('premise', p)
        assumptions.append(name)
        solver.add(z3.Implies(name, z3.And(*(z3.Or(*(z3.Not(bools[j]) for j in edge)) for edge in grouped[premise]))))
    status = solver.check(*assumptions)
    if status != z3.unsat:
        raise AssertionError(('Numeric cover must have a Boolean refutation', str(status)))
    selected = list(solver.unsat_core())
    if minimise:
        # First drop arithmetic premises; then remove superfluous allocations.
        selected.sort(key=lambda x: labels[str(x)][0] == 'box')
        for item in tuple(selected):
            trial = [x for x in selected if not x.eq(item)]
            if solver.check(*trial) == z3.unsat:
                selected = trial
    kept_boxes = sorted(labels[str(x)][1] for x in selected if labels[str(x)][0] == 'box')
    kept_premises = sorted(labels[str(x)][1] for x in selected if labels[str(x)][0] == 'premise')
    region = set(premises[j] for j in kept_premises)
    for j in kept_boxes:
        region.update(forms[j][0])
    for i, q in region:
        assert dot(q, C[i]) >= 0, (i, q)
    return {
        'region': [dict(row=i, coeffs=list(q)) for i, q in sorted(region)],
        'cover': [cover[j] for j in kept_boxes],
        'certificate': {
            'atoms': [dict(row=i, side=side, coeffs=list(q)) for i, side, q in atoms],
            'allocation_clauses': [[index[a] for a in forms[j][1]] for j in kept_boxes],
            'always_incompatibilities': [list(edge) for edge in always_edges],
            'premised_incompatibilities': [dict(row=premises[j][0], coeffs=list(premises[j][1]), edges=[list(edge) for edge in grouped[premises[j]]]) for j in kept_premises],
        },
        'arithmetic_premise_count': len(kept_premises),
        'constant_premise_count_before_deduplication': sum(len(forms[j][0]) for j in kept_boxes),
    }


def reduce_region(result, timeout_ms=30000):
    """Remove linearly implied conditions, retaining exact conic witnesses.

    Every removed row inequality is represented as a nonnegative rational
    combination of retained row inequalities and coordinate nonnegativity.
    The replay therefore needs no arithmetic decision procedure.
    """
    original = result.get('unreduced_region', result['region'])
    background = result.get('domain_inequalities', [])
    m = len(original[0]['coeffs']) if original else len(result['prefix'][0])
    kept_global = []
    for i in range(3):
        selected = [j for j, v in enumerate(original) if v['row'] == i]
        c = z3.Reals(' '.join(f'redundancy_c_{i}_{g}' for g in range(m)))
        s = z3.SolverFor('QF_LRA')
        s.set(timeout=timeout_ms)
        s.add(*(x >= 0 for x in c))
        for v in background:
            if v['row'] == i:
                s.add(z3.Sum(*(q * x for q, x in zip(v['coeffs'], c))) >= 0)
        labels = {j: z3.Bool(f'redundancy_assumption_{j}') for j in selected}
        exprs = {j: z3.Sum(*(q * x for q, x in zip(original[j]['coeffs'], c))) for j in selected}
        for j in selected:
            s.add(z3.Implies(labels[j], exprs[j] >= 0))
        for j in tuple(selected):
            s.push()
            s.add(exprs[j] < 0)
            if s.check(*(labels[k] for k in selected if k != j)) == z3.unsat:
                selected.remove(j)
            s.pop()
        kept_global.extend(selected)
    final = [original[j] for j in kept_global]
    derivations = []
    for i in range(3):
        row_final = [(j, v['coeffs']) for j, v in enumerate(final) if v['row'] == i]
        row_background = [(j, v['coeffs']) for j, v in enumerate(background) if v['row'] == i]
        generators = [q for _, q in row_final] + [q for _, q in row_background] + [tuple(int(a == g) for a in range(m)) for g in range(m)]
        weights = z3.Reals(' '.join(f'conic_weight_{i}_{j}' for j in range(len(generators))))
        s = z3.SolverFor('QF_LRA')
        s.set(timeout=timeout_ms)
        s.add(*(w >= 0 for w in weights))
        for target_index, target in enumerate(original):
            if target['row'] != i:
                continue
            if target_index in kept_global:
                derivations.append(dict(target_index=target_index, retained=[dict(index=kept_global.index(target_index), weight=1)], background=[], coordinates=[]))
                continue
            s.push()
            for g in range(m):
                s.add(z3.Sum(*(w * q[g] for w, q in zip(weights, generators))) == target['coeffs'][g])
            status = s.check()
            if status != z3.sat:
                raise AssertionError(('Missing conic redundancy witness', i, target_index, str(status)))
            model = s.model()
            w = [Fraction(str(model.eval(x, model_completion=True))) for x in weights]
            retained = [dict(index=row_final[j][0], weight=serial_number(a)) for j, a in enumerate(w[:len(row_final)]) if a]
            back_weights = w[len(row_final):len(row_final) + len(row_background)]
            back = [dict(index=row_background[j][0], weight=serial_number(a)) for j, a in enumerate(back_weights) if a]
            coordinates = [dict(index=j, weight=serial_number(a)) for j, a in enumerate(w[len(row_final) + len(row_background):]) if a]
            derivations.append(dict(target_index=target_index, retained=retained, background=back, coordinates=coordinates))
            s.pop()
    result['unreduced_region'] = original
    result['region'] = final
    result['linear_reduction'] = dict(original_count=len(original), retained_count=len(final), derivations=sorted(derivations, key=lambda x: x['target_index']))


def verify_certificate(C, result):
    """Replay the symbolic argument, including all actual allocation literals."""
    assert result['status'] == 'covered'
    C = [[Fraction(v) for v in row] for row in C]
    m = len(C[0])
    lower_domain = result.get('extension_domain_lower', [[0] * m for _ in range(3)])
    assert len(lower_domain) == 3 and all(len(q) == m and all(isinstance(v, int) and v >= 0 for v in q) for q in lower_domain)
    background = result.get('domain_inequalities', [])
    assert all(dot(v['coeffs'], C[v['row']]) >= 0 for v in background)
    raw_region = result.get('unreduced_region', result['region'])
    region = {(v['row'], tuple(v['coeffs'])) for v in raw_region}
    if 'linear_reduction' in result:
        assert len(result['linear_reduction']['derivations']) == len(raw_region)
        for d in result['linear_reduction']['derivations']:
            target = raw_region[d['target_index']]
            combination = [Fraction(0)] * m
            for term in d['retained']:
                source = result['region'][term['index']]
                weight = Fraction(term['weight'])
                assert source['row'] == target['row'] and weight >= 0
                combination = [a + weight * b for a, b in zip(combination, source['coeffs'])]
            for term in d.get('background', []):
                source = background[term['index']]
                weight = Fraction(term['weight'])
                assert source['row'] == target['row'] and weight >= 0
                combination = [a + weight * b for a, b in zip(combination, source['coeffs'])]
            for term in d['coordinates']:
                weight = Fraction(term['weight'])
                assert weight >= 0
                combination[term['index']] += weight
            assert combination == target['coeffs']
    cert = result['certificate']
    atoms = [(v['row'], v['side'], tuple(v['coeffs'])) for v in cert['atoms']]
    index = {a: j for j, a in enumerate(atoms)}
    expected_clauses = []
    for entry in result['cover']:
        assert allocation_box(C, entry['allocation']) == (tuple(Fraction(v) for v in entry['lower']), tuple(None if v is None else Fraction(v) for v in entry['upper']))
        constants, literals = literal_forms(entry['allocation'], m)
        assert set(constants) <= region
        expected_clauses.append([index[a] for a in literals])
    assert expected_clauses == cert['allocation_clauses']
    b = [z3.Bool(f'certificate_atom_{j}') for j in range(len(atoms))]
    s = z3.Solver()
    s.add(*(z3.Or(*(b[j] for j in clause)) for clause in expected_clauses))

    def edge_premise(edge):
        if len(edge) == 1:
            i, side, q = atoms[edge[0]]
            assert side == 'lower'
            return i, tuple(a - v for a, v in zip(lower_domain[i], q))
        assert len(edge) == 2
        i, upper, u = atoms[edge[0]]
        j, lower, l = atoms[edge[1]]
        assert i == j and upper == 'upper' and lower == 'lower'
        return i, tuple(a - c for a, c in zip(u, l))

    for edge in cert['always_incompatibilities']:
        assert all(v >= 0 for v in edge_premise(edge)[1])
        s.add(z3.Or(*(z3.Not(b[j]) for j in edge)))
    for group in cert['premised_incompatibilities']:
        premise = group['row'], tuple(group['coeffs'])
        assert premise in region
        assert dot(premise[1], C[premise[0]]) >= 0
        for edge in group['edges']:
            assert edge_premise(edge) == premise
            s.add(z3.Or(*(z3.Not(b[j]) for j in edge)))
    assert s.check() == z3.unsat
    scope = 'ninth_columns_above_recorded_linear_lower_bounds' if any(v for q in lower_domain for v in q) else 'all_nonnegative_ninth_columns'
    assert result.get('coverage_scope', scope) == scope
    return {'status': 'PASS', 'coverage_scope': scope, 'method': 'literal EFX box derivation, linear premise identity checks, and propositional UNSAT replay'}


def analyse_prefix(C, timeout_ms=30000, minimise=True, domain_inequalities=None, extension_domain_lower=None):
    started = time.monotonic()
    C = [[Fraction(v) for v in row] for row in C]
    assert len(C) == 3 and len(set(map(len, C))) == 1
    assert all(v >= 0 for row in C for v in row)
    m = len(C[0])
    lower_domain = [[0] * m for _ in range(3)] if extension_domain_lower is None else extension_domain_lower
    assert len(lower_domain) == 3 and all(len(q) == m and all(isinstance(v, int) and v >= 0 for v in q) for q in lower_domain)
    boxes = enumerate_boxes(C)
    status, value = choose_cover(boxes, timeout_ms, minimise, [dot(q, row) for q, row in zip(lower_domain, C)])
    result = dict(status=status, prefix=[[serial_number(v) for v in row] for row in C], distinct_boxes=len(boxes))
    if any(v for q in lower_domain for v in q):
        result['extension_domain_lower'] = [list(q) for q in lower_domain]
        result['coverage_scope'] = 'ninth_columns_above_recorded_linear_lower_bounds'
    else:
        result['coverage_scope'] = 'all_nonnegative_ninth_columns'
    if domain_inequalities:
        result['domain_inequalities'] = [dict(row=int(v['row']), coeffs=[int(q) for q in v['coeffs']]) for v in domain_inequalities]
        assert all(0 <= v['row'] < 3 and len(v['coeffs']) == len(C[0]) for v in result['domain_inequalities'])
        assert all(dot(v['coeffs'], C[v['row']]) >= 0 for v in result['domain_inequalities'])
    if status == 'uncovered':
        assert all(value[i] >= dot(lower_domain[i], C[i]) for i in range(3))
        result['new_column'] = [serial_number(v) for v in value]
        # Independent literal full enumeration checks any putative counterexample.
        full = [row + [value[i]] for i, row in enumerate(C)]
        good = 0
        for a in product(range(3), repeat=len(full[0])):
            A = [[g for g in range(len(a)) if a[g] == i] for i in range(3)]
            V = [[sum(full[i][g] for g in A[j]) for j in range(3)] for i in range(3)]
            good += all(V[i][i] - full[i][g] <= V[i][j] for i in range(3) for g in A[i] for j in range(3))
        result['literal_efx_count'] = good
        assert good == 0
    elif status == 'unknown':
        result['reason'] = value
    else:
        result.update(generalise_cover(C, value, timeout_ms, minimise, lower_domain))
        if minimise:
            reduce_region(result, timeout_ms)
        result['verification'] = verify_certificate(C, result)
    result['elapsed_s'] = time.monotonic() - started
    return result


def json_default(x):
    if isinstance(x, Fraction):
        return serial_number(x)
    raise TypeError(type(x).__name__)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--columns', type=int, default=8)
    p.add_argument('--timeout-ms', type=int, default=30000)
    p.add_argument('--no-minimise', action='store_true')
    a = p.parse_args()
    value = json.loads(Path(a.input).read_text())
    if isinstance(value, dict):
        value = next(value[k] for k in ('matrix', 'rows', 'prefix', 'fixed_matrix') if k in value)
    result = analyse_prefix([row[:a.columns] for row in value], a.timeout_ms, not a.no_minimise)
    Path(a.output).write_text(json.dumps(result, indent=2, default=json_default) + '\n')
    summary = {k: v for k, v in result.items() if k not in ('certificate', 'prefix', 'cover', 'region', 'unreduced_region', 'linear_reduction')}
    summary['region_inequalities'] = len(result.get('region', []))
    print(json.dumps(summary, default=json_default))


if __name__ == '__main__':
    main()
