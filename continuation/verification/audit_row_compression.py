"""Literal, integer-only audit of row-region compression and outer assertions.

No solver is run. Seed first-row guarantees are checked by threshold counts
for each linear extension of the recorded partial order. Nonseed inner-core
claims require their separate exact certificates.
"""
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import resource
import signal
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (480 * 1024**2,) * 2)
signal.alarm(29)
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DIR = ROOT / 'continuation/structural_nine/row_elimination_compressed'
START = time.monotonic()
VARS = {f'c_{i}_{g}': 9 * (i - 1) + g for i in (1, 2) for g in range(9)}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def allocation(aid):
    assert type(aid) is int and 0 <= aid < 3**9
    value = aid
    answer = [0] * 9
    for g in range(8, -1, -1):
        value, answer[g] = divmod(value, 3)
    assert set(answer) == {0, 1, 2}
    return answer


def literal_other_rows(ids):
    forms = set()
    for aid in ids:
        a = allocation(aid)
        bundles = [[g for g in range(9) if a[g] == i] for i in range(3)]
        for i in (1, 2):
            for removed in bundles[i]:
                for j in range(3):
                    if i == j:
                        continue
                    v = [0] * 9
                    for g in bundles[i]:
                        if g != removed:
                            v[g] += 1
                    for g in bundles[j]:
                        v[g] -= 1
                    if any(x > 0 for x in v):
                        forms.add((i, tuple(v)))
    return forms


def atom(p):
    assert type(p['agent']) is int and p['agent'] in (1, 2)
    q = p['coefficients']
    assert isinstance(q, list) and len(q) == 9 and all(type(v) is int for v in q)
    return p['agent'], tuple(q)


def check_region(record, ids):
    raw = [atom(p) for p in record['region_atoms']]
    retained = [atom(p) for p in record['compressed_region_atoms']]
    assert len(raw) == len(set(raw)) and len(retained) == len(set(retained))
    assert set(raw) == literal_other_rows(ids)
    assert set(retained) <= set(raw)
    assert record['compression_counts'] == {'raw': len(raw), 'kept': len(retained)}
    proofs = record['dominance_certificate']
    assert sorted(p['raw_index'] for p in proofs) == list(range(len(raw)))
    for proof in proofs:
        assert type(proof['raw_index']) is int
        i, a = raw[proof['raw_index']]
        if proof['zero']:
            assert proof['retained_index'] is None
            b = (0,) * 9
        else:
            assert type(proof['retained_index']) is int and 0 <= proof['retained_index'] < len(retained)
            j, b = retained[proof['retained_index']]
            assert i == j
        difference = [a[g] - b[g] for g in range(9)]
        # Expansion in the positive minimum and all nonnegative surpluses.
        assert sum(difference) <= 0
        assert all(difference[g] <= 0 for g in range(9) if g != i)
    return raw, retained


def seed_orders():
    result = []
    for p1, p2 in combinations(range(1, 9), 2):
        values = [None] * 9
        values[0], values[p1], values[p2] = 0, 1, 2
        free = iter([8, 7, 6, 5, 4, 3])
        for p in range(1, 9):
            if values[p] is None:
                values[p] = next(free)
        thresholds = [sum(1 << g for g in values[t:]) for t in range(9)]
        result.append((values, thresholds))
    assert len(result) == 28
    return result


ORDERS = seed_orders()


def check_seed(aid):
    a = allocation(aid)
    masks = [sum(1 << g for g in range(9) if a[g] == i) for i in range(3)]
    for order, thresholds in ORDERS:
        cheapest = next(g for g in order if a[g] == 0)
        residue = masks[0] ^ (1 << cheapest)
        for target in masks[1:]:
            assert all((residue & t).bit_count() <= (target & t).bit_count() for t in thresholds)


def parse(value):
    roots, stack = [], []
    for token in re.findall(r'\(|\)|[^\s()]+', re.sub(r';[^\n]*', '', value)):
        if token == '(':
            row = []
            (stack[-1] if stack else roots).append(row)
            stack.append(row)
        elif token == ')':
            assert stack
            stack.pop()
        else:
            assert stack
            stack[-1].append(token)
    assert not stack
    return roots


def affine(e):
    if isinstance(e, str):
        v = [0] * 19
        if e in VARS:
            v[VARS[e]] = 1
        else:
            q = Fraction(e)
            v[-1] = q.numerator if q.denominator == 1 else q
        return tuple(v)
    op, *parts = e
    args = [affine(p) for p in parts]
    if op == '+':
        return tuple(map(sum, zip(*args))) if args else (0,) * 19
    if op == '-':
        if len(args) == 1:
            return tuple(-q for q in args[0])
        return tuple(args[0][g] - sum(a[g] for a in args[1:]) for g in range(19))
    if op == '*':
        assert len(args) == 2
        a, b = args
        if any(a[:-1]):
            a, b = b, a
        assert not any(a[:-1])
        return tuple(a[-1] * q for q in b)
    if op == '/':
        assert len(args) == 2 and not any(args[1][:-1])
        return tuple(Fraction(q, args[1][-1]) for q in args[0])
    raise AssertionError(('Unsupported operator', op))


def boolform(e):
    op, *args = e
    if op == 'or':
        return op, frozenset(boolform(a) for a in args)
    assert op in ('=', '>') and len(args) == 2
    a, b = map(affine, args)
    return op, tuple(x - y for x, y in zip(a, b))


def clause(retained):
    forms = []
    for i, q in retained:
        v = [0] * 19
        v[9 * (i - 1):9 * i] = q
        forms.append(('>', tuple(v)))
    return 'or', frozenset(forms)


def main():
    raw_outer = (DIR / 'outer.smt2').read_bytes()
    (OUT / 'row_compressed_outer_snapshot.smt2').write_bytes(raw_outer)
    seed_bytes = (DIR / 'seed_regions.json').read_bytes()
    resumed_bytes = (DIR / 'resumed_regions.json').read_bytes()
    seed_meta_bytes = (DIR / 'robust_seed.json').read_bytes()
    seeds, resumed, seed_meta = map(json.loads, (seed_bytes, resumed_bytes, seed_meta_bytes))
    assert seed_meta['order'] == 'descending' and seed_meta['full_orders'] == 28
    assert [r['allocation_id'] for r in seeds] == seed_meta['allocation_ids']
    assert [allocation(aid) for aid in seed_meta['allocation_ids']] == seed_meta['allocations']
    expected, raw_count, kept_count = [], 0, 0
    manifest = []
    for record in seeds:
        aid = record['allocation_id']
        check_seed(aid)
        raw, kept = check_region(record, [aid])
        expected.append(clause(kept))
        raw_count += len(raw)
        kept_count += len(kept)
    for record in resumed:
        source = Path(record['source'])
        source = source if source.is_absolute() else ROOT / source
        original = json.loads(source.read_text())
        assert record['core_allocation_ids'] == original['core_allocation_ids']
        assert [allocation(aid) for aid in record['core_allocation_ids']] == original['core_allocations']
        assert record['core_sha256'] == original['core_sha256']
        core_source = Path(record['core_source'])
        core_source = core_source if core_source.is_absolute() else ROOT / core_source
        assert sha(core_source.read_bytes()) == record['core_sha256']
        raw, kept = check_region(record, record['core_allocation_ids'])
        expected.append(clause(kept))
        raw_count += len(raw)
        kept_count += len(kept)
    new_count = 0
    for file in sorted((DIR / 'regions').glob('[0-9]*.json')):
        value = file.read_bytes()
        record = json.loads(value)
        assert [allocation(aid) for aid in record['core_allocation_ids']] == record['core_allocations']
        assert sha((DIR / 'inner' / file.with_suffix('.smt2').name).read_bytes()) == record['core_sha256']
        raw, kept = check_region(record, record['core_allocation_ids'])
        expected.append(clause(kept))
        raw_count += len(raw)
        kept_count += len(kept)
        manifest.append({'file': str(file.relative_to(ROOT)), 'sha256': sha(value)})
        new_count += 1
    roots = parse(raw_outer.decode())
    assert all(r[0] in ('declare-fun', 'assert', 'check-sat') for r in roots)
    declarations = [r for r in roots if r[0] == 'declare-fun']
    assert len(declarations) == 18 and {r[1] for r in declarations} == set(VARS)
    assert all(r[2:] == [[], 'Real'] for r in declarations)
    assert [r for r in roots if r[0] == 'check-sat'] == [['check-sat']]
    assertions = [boolform(r[1]) for r in roots if r[0] == 'assert']
    base = [r for r in assertions if r[0] != 'or']
    actual = [r for r in assertions if r[0] == 'or']
    expected_base = []
    for i in (1, 2):
        for g in range(9):
            v = [0] * 19
            v[9 * (i - 1) + g], v[-1] = 1, -1
            expected_base.append(('=' if g == i else '>', tuple(v)))
    assert Counter(base) == Counter(expected_base)
    assert actual == expected[:len(actual)]
    assert len(actual) <= len(expected)
    report = {'status': 'PASS_SEED_COMPRESSION_AND_ASSERTION_BINDING_NOT_GLOBAL_UNSAT',
              'python': sys.version, 'elapsed_seconds': time.monotonic() - START,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'seed_regions_verified': len(seeds), 'seed_orders_each': 28,
              'resumed_regions_verified': len(resumed), 'new_regions_verified': new_count,
              'raw_literal_atoms': raw_count, 'retained_atoms': kept_count,
              'outer_base_assertions': len(base), 'outer_learned_clauses': len(actual),
              'outer_snapshot_sha256': sha(raw_outer),
              'outer_portable_without_model_add': True,
              'seed_regions_sha256': sha(seed_bytes), 'resumed_regions_sha256': sha(resumed_bytes),
              'robust_seed_sha256': sha(seed_meta_bytes),
              'new_core_proof_limit': 'The audit binds the archived new inner core files by hash but does not certify their UNSAT; separate row-core alternatives remain necessary.',
              'new_region_manifest': manifest}
    (OUT / 'row_compression_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'new_region_manifest'}, indent=2))


if __name__ == '__main__':
    main()
