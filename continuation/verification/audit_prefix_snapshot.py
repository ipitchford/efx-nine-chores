"""Independent bounded audit of certificates and the running v3 SMT snapshot.

Only the standard-library certificate checker is imported. The SMT formula
is parsed here, without Z3, and all arithmetic is canonicalised over Fraction.
This script does not call a solver or claim global UNSAT.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib.util
from itertools import combinations, product
import json
from math import isqrt
from pathlib import Path
import random
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
VERIFIER = ROOT / 'continuation/extension_geometry/verify_extension_certificate.py'
spec = importlib.util.spec_from_file_location('independent_certificate_checker', VERIFIER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def background():
    result = []
    for i in range(3):
        for g in range(8):
            if g != i:
                q = [0] * 8
                q[g], q[i] = 1, -1
                result.append({'row': i, 'coeffs': q})
    for g, h in [(2, 1), (3, 4), (4, 5), (5, 6), (6, 7)]:
        q = [0] * 8
        q[g], q[h] = 1, -1
        result.append({'row': 0, 'coeffs': q})
    return result


def parse(text):
    tokens = re.findall(r'\(|\)|[^\s()]+', re.sub(r';[^\n]*', '', text))
    stack, roots = [], []
    for t in tokens:
        if t == '(':
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif t == ')':
            assert stack
            stack.pop()
        else:
            assert stack
            stack[-1].append(t)
    assert not stack
    return roots


def sexpr(value):
    return '(' + ' '.join(map(sexpr, value)) + ')' if isinstance(value, list) else value


NAMES = [f'c_{i}_{g}' for i in range(3) for g in range(8)]
VARIABLES = {v: i for i, v in enumerate(NAMES)}


def affine(expr, env=None):
    env = {} if env is None else env
    if isinstance(expr, str):
        if expr in env:
            return env[expr]
        result = [Q(0)] * 25
        if expr in VARIABLES:
            result[VARIABLES[expr]] = Q(1)
        else:
            result[-1] = Q(expr)
        return tuple(result)
    op, *args = expr
    if op == 'let':
        new = dict(env)
        new.update((name, affine(value, env)) for name, value in args[0])
        return affine(args[1], new)
    values = [affine(a, env) for a in args]
    if op == '+':
        return tuple(map(sum, zip(*values))) if values else (Q(0),) * 25
    if op == '-':
        if len(values) == 1:
            return tuple(-q for q in values[0])
        return tuple(values[0][g] - sum(v[g] for v in values[1:]) for g in range(25))
    if op == '*':
        assert len(values) == 2
        a, b = values
        if any(a[:-1]):
            a, b = b, a
        assert not any(a[:-1]), 'Nonlinear term in QF_LRA snapshot'
        return tuple(a[-1] * q for q in b)
    if op == '/':
        assert len(values) == 2 and not any(values[1][:-1]) and values[1][-1]
        return tuple(q / values[1][-1] for q in values[0])
    raise AssertionError(('Unsupported arithmetic operator', op))


def formula(expr):
    op, *args = expr
    if op == 'or':
        return ('or', frozenset(formula(a) for a in args))
    assert op in ('=', '>', '<', '>=', '<=') and len(args) == 2
    a, b = map(affine, args)
    return op, tuple(x - y for x, y in zip(a, b))


def row_form(i, q):
    value = [Q(0)] * 25
    value[8 * i:8 * (i + 1)] = q
    return tuple(value)


def rejection(mutated):
    try:
        checker.verify(mutated)
    except (AssertionError, KeyError, IndexError, ValueError) as e:
        return type(e).__name__ + ': ' + str(e)
    raise AssertionError('A deliberately invalid mutation was accepted')


def boolean_bruteforce(n, clauses, edges):
    for mask in range(1 << n):
        if all(any(mask >> a & 1 for a in clause) for clause in clauses):
            if all(not all(mask >> a & 1 for a in edge) for edge in edges):
                return False
    return True


def boolean_audit():
    count = 0
    for n in range(4):
        positive = [tuple(a for a in range(n) if mask >> a & 1) for mask in range(1 << n)]
        negative = [(a,) for a in range(n)] + list(combinations(range(n), 2))
        for posmask in range(1 << len(positive)):
            clauses = [q for j, q in enumerate(positive) if posmask >> j & 1]
            for negmask in range(1 << len(negative)):
                edges = [q for j, q in enumerate(negative) if negmask >> j & 1]
                expected = boolean_bruteforce(n, clauses, edges)
                try:
                    checker.check_boolean_refutation(n, clauses, edges)
                    observed = True
                except AssertionError:
                    observed = False
                assert expected == observed, (n, clauses, edges)
                count += 1
    rng = random.Random(47183)
    for n in range(4, 9):
        negative = [(a,) for a in range(n)] + list(combinations(range(n), 2))
        for _ in range(200):
            clauses = [rng.sample(range(n), rng.randrange(n + 1)) for _ in range(rng.randrange(12))]
            edges = [q for q in negative if rng.randrange(3) == 0]
            expected = boolean_bruteforce(n, clauses, edges)
            try:
                checker.check_boolean_refutation(n, clauses, edges)
                observed = True
            except AssertionError:
                observed = False
            assert expected == observed
            count += 1
    return count


def main():
    directory = ROOT / 'continuation/prefix_regions_v3'
    smt_bytes = (directory / 'formula.smt2').read_bytes()
    (OUT / 'prefix_v3_snapshot.smt2').write_bytes(smt_bytes)
    config = json.loads((directory / 'config.json').read_text())
    assert config['fixed_minima'] and config['restricted_ninth']
    lower = [[int(g == k) for g in range(8)] for k in (3, 1, 2)]
    bg = background()
    records, receipts, regions = [], [], []
    scope_counts = Counter()
    unique = set()
    maximum_coefficient = 0
    for file in sorted(directory.glob('region_*.json')):
        value = file.read_bytes()
        data = json.loads(value)
        receipt = checker.verify(data)
        assert data.get('domain_inequalities', []) == bg
        old_lower = data.get('extension_domain_lower', [[0] * 8 for _ in range(3)])
        assert len(old_lower) == 3 and all(len(a) == 8 for a in old_lower)
        assert all(a <= b for old, new in zip(old_lower, lower) for a, b in zip(old, new))
        assert len(data['prefix']) == 3 and all(len(row) == 8 for row in data['prefix'])
        scope_counts[receipt['coverage_scope']] += 1
        key = tuple((p['row'], tuple(p['coeffs'])) for p in data['region'])
        if key not in unique:
            unique.add(key)
            regions.append(('or', frozenset(('<', row_form(i, q)) for i, q in key)))
        for p in data['region']:
            maximum_coefficient = max(maximum_coefficient, max(map(abs, p['coeffs']), default=0))
        records.append({'file': str(file.relative_to(ROOT)), 'sha256': digest(value)})
        receipts.append({'file': file.name, **receipt})

    roots = parse(smt_bytes.decode())
    declarations = [x for x in roots if x[0] == 'declare-fun']
    assert len(declarations) == 24
    assert {x[1] for x in declarations} == set(NAMES)
    assert all(x[2:] == [[], 'Real'] for x in declarations)
    assert all(x[0] in ('declare-fun', 'assert', 'check-sat', 'model-add') for x in roots)
    model_add = [x for x in roots if x[0] == 'model-add']
    # SolverFor.sexpr() can append Z3 model-converter metadata. It is not a
    # logical assertion. Validate its narrow shape, then audit the assertion
    # set separately; the report records this portable-SMT export limitation.
    if model_add:
        assert len(model_add) == 24 and {x[1] for x in model_add} == set(NAMES)
        assert all(len(x) == 5 and x[2:4] == [[], 'Real'] for x in model_add)
        assert all(not any(affine(x[4])[:-1]) for x in model_add)
    portable_roots = [x for x in roots if x[0] != 'model-add']
    portable_bytes = ('\n'.join(map(sexpr, portable_roots)) + '\n').encode()
    assert parse(portable_bytes.decode()) == portable_roots
    (OUT / 'prefix_v3_portable_snapshot.smt2').write_bytes(portable_bytes)
    assert [x for x in roots if x[0] == 'check-sat'] == [['check-sat']]
    assertions = [formula(x[1]) for x in roots if x[0] == 'assert']
    expected_base = []
    for i in range(3):
        v = list(row_form(i, [int(g == i) for g in range(8)]))
        v[-1] = -1
        expected_base.append(('=', tuple(v)))
    expected_base += [('>', row_form(p['row'], p['coeffs'])) for p in bg]
    for i in (1, 2):
        v = [Q(0)] * 25
        v[:8], v[8 * i:8 * (i + 1)] = [-1] * 8, [1] * 8
        expected_base.append(('>', tuple(v)))
    base = [q for q in assertions if q[0] != 'or']
    learned = [q for q in assertions if q[0] == 'or']
    assert Counter(base) == Counter(expected_base), 'SMT base domain mismatch'
    assert learned == regions[:len(learned)], 'Learned clauses differ from certificate conjunction complements'
    assert len(learned) <= len(regions)
    assert maximum_coefficient <= 2

    restricted = json.loads((ROOT / 'continuation/extension_geometry/restricted_region.json').read_text())
    checker.verify(restricted)
    mutations = {}
    value = deepcopy(restricted)
    value.pop('extension_domain_lower', None)
    value.pop('coverage_scope', None)
    mutations['erase_extension_bounds_and_scope'] = rejection(value)
    value = deepcopy(restricted)
    value['certificate']['always_incompatibilities'] = []
    value['certificate']['premised_incompatibilities'] = []
    mutations['erase_all_boolean_conflicts'] = rejection(value)
    value = deepcopy(restricted)
    value['linear_reduction']['derivations'].pop()
    mutations['omit_one_raw_derivation'] = rejection(value)
    value = deepcopy(restricted)
    found = False
    for d in value['linear_reduction']['derivations']:
        for label in ('retained', 'background', 'coordinates'):
            if d.get(label):
                d[label][0]['weight'] = -1
                found = True
                break
        if found:
            break
    assert found
    mutations['negative_conic_weight'] = rejection(value)
    zero = {'status': 'covered', 'prefix': [[0], [0], [0]], 'region': [],
            'cover': [{'allocation': [0, 1], 'lower': [0, 0, 0], 'upper': [None, None, None]}],
            'certificate': {'atoms': [{'row': 0, 'side': 'lower', 'coeffs': [0]}],
                            'allocation_clauses': [[0]],
                            'always_incompatibilities': [[0]], 'premised_incompatibilities': []}}
    zero_receipt = checker.verify(zero)
    value = deepcopy(zero)
    value['cover'][0]['allocation'] = [0, 0]
    mutations['unrecorded_deletion_of_owned_zero_cost_chore'] = rejection(value)

    boolean_systems = boolean_audit()
    surjective, maximum_support, comparison_count = 0, 0, 0
    for allocation in product(range(3), repeat=9):
        sizes = [allocation.count(i) for i in range(3)]
        if min(sizes) == 0:
            continue
        surjective += 1
        for i in range(3):
            for j in range(3):
                if i != j:
                    support = sizes[i] - 1 + sizes[j]
                    maximum_support = max(maximum_support, support)
                    comparison_count += sizes[i]
                    assert support <= 7
    assert surjective == 18150 and maximum_support == 7
    bound = isqrt(8**25)
    assert bound == 194368031998 and bound**2 <= 8**25 < (bound + 1)**2
    rng = random.Random(837491)
    strict_score_cases = 0
    for _ in range(10000):
        rows = []
        for i in range(3):
            costs = iter(rng.sample(range(2, 202), 8))
            rows.append([1 if g == i else next(costs) for g in range(9)])
        scores = [sum(row) - max(row[3:]) for row in rows]
        selected = min(range(3), key=scores.__getitem__)
        removed = max(range(3, 9), key=rows[selected].__getitem__)
        prefix_totals = [sum(row) - row[removed] for row in rows]
        assert prefix_totals[selected] == min(prefix_totals)
        assert rows[selected][removed] >= max(rows[selected][g] for g in range(3, 9) if g != removed)
        if all(scores[selected] < scores[j] for j in range(3) if j != selected):
            strict_score_cases += 1
            assert all(prefix_totals[selected] < prefix_totals[j] for j in range(3) if j != selected)

    report = {
        'status': 'PASS_BOUNDED_AUDIT_NOT_GLOBAL_UNSAT',
        'python': sys.version,
        'elapsed_seconds': time.monotonic() - START,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'certificates_verified': len(receipts),
        'scope_counts': dict(scope_counts),
        'max_boolean_states_per_certificate': max(r['propositional_states'] for r in receipts),
        'max_region_coefficient_abs': maximum_coefficient,
        'formula': {'sha256': digest(smt_bytes), 'base_assertions': len(base),
                    'learned_region_clauses': len(learned),
                    'portable_sha256': digest(portable_bytes),
                    'portable_ast_equals_raw_without_model_add': True,
                    'nonstandard_model_add_commands': len(model_add),
                    'status': 'EXACT_ASSERTION_CORRESPONDENCE_NO_SOLVER_RUN'},
        'mutations_rejected': mutations,
        'zero_boundary_valid_certificate': zero_receipt,
        'boolean_systems_compared_to_exhaustive_truth_table': boolean_systems,
        'integer_bound': {'value': bound, 'surjective_allocations': surjective,
                          'literal_comparisons': comparison_count, 'maximum_support': maximum_support},
        'deletion_reduction_samples': 10000,
        'strict_score_samples': strict_score_cases,
        'verifier_sha256': digest(VERIFIER.read_bytes()),
        'source_manifest': records,
        'certificate_receipts': receipts,
    }
    (OUT / 'prefix_snapshot_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_manifest', 'certificate_receipts')}, indent=2))


if __name__ == '__main__':
    main()
