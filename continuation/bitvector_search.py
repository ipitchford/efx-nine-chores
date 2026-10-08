#!/usr/bin/env python3
"""Exact finite EFX counterexample search using unsigned bit vectors.

The complete integer bound is row-local; row minima remain independent.
Every subset sum is widened enough to preclude arithmetic overflow.
An UNSAT solver response is not an independently checked proof object.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import resource
import time
import z3


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(path, obj):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2) + '\n')
    temp.replace(path)


def minimum_candidates(i, owned):
    if i in owned:
        return [i]
    if i:
        return owned
    fixed = [g for g in owned if g in (1, 2)]
    free = [g for g in owned if g >= 3]
    return ([min(fixed)] if fixed else []) + ([max(free)] if free else [])


def make_formula(m, bound):
    cost_width = bound.bit_length()
    sum_width = (m * bound).bit_length()
    c = [[z3.BitVec(f'c_{i}_{g}', cost_width) for g in range(m)] for i in range(3)]
    s = z3.SolverFor('QF_BV')
    for i in range(3):
        for g in range(m):
            s.add(z3.UGT(c[i][g], 0), z3.ULE(c[i][g], bound))
            if g != i:
                s.add(z3.UGT(c[i][g], c[i][i]))
    s.add(z3.ULT(c[0][1], c[0][2]))
    s.add(*[z3.UGT(c[0][g], c[0][g+1]) for g in range(3, m-1)])
    domain = list(s.assertions())
    totals = []
    for i in range(3):
        sums = [z3.BitVecVal(0, sum_width)] * (1 << m)
        for mask in range(1, 1 << m):
            bit = mask & -mask
            g = bit.bit_length() - 1
            sums[mask] = sums[mask ^ bit] + z3.ZeroExt(sum_width-cost_width, c[i][g])
        totals.append(sums)
    atoms, atom_ids, clauses, allocations = [], {}, [], []
    for assignment in itertools.product(range(3), repeat=m):
        if len(set(assignment)) != 3:
            continue
        masks = [sum(1 << g for g, owner in enumerate(assignment) if owner == i) for i in range(3)]
        literals = []
        for i in range(3):
            owned = [g for g in range(m) if assignment[g] == i]
            for g in minimum_candidates(i, owned):
                residual = masks[i] ^ (1 << g)
                if residual == 0:
                    continue
                for j in range(3):
                    if j == i:
                        continue
                    key = (i, residual, masks[j])
                    if key not in atom_ids:
                        atom_ids[key] = len(atoms)
                        atoms.append((key, z3.UGT(totals[i][residual], totals[i][masks[j]])))
                    literals.append(atom_ids[key])
        literals = sorted(set(literals))
        s.add(z3.Or(*[atoms[k][1] for k in literals]))
        clauses.append(literals)
        allocations.append(assignment)
    assert len(allocations) == 3**m - 3*2**m + 3
    return s, c, domain, atoms, clauses, allocations, cost_width, sum_width


def literal_good(rows, assignment):
    bundles = [[g for g, owner in enumerate(assignment) if owner == i] for i in range(3)]
    for i in range(3):
        own = sum(rows[i][g] for g in bundles[i])
        for j in range(3):
            if j != i:
                other = sum(rows[i][g] for g in bundles[j])
                for g in bundles[i]:
                    if own - rows[i][g] > other:
                        return False
    return True


def audit(c, domain, atoms, clauses, allocations, m, bound):
    rng = random.Random(20261007)
    fixtures = []
    for _ in range(3):
        rows = []
        for i in range(3):
            base = rng.randint(1, 10)
            values = rng.sample(range(base+1, min(bound+1, base+150)), m-1)
            row = [None] * m
            row[i] = base
            for g, value in zip((g for g in range(m) if g != i), values):
                row[g] = value
            rows.append(row)
        rows[0][1:3] = sorted(rows[0][1:3])
        rows[0][3:] = sorted(rows[0][3:], reverse=True)
        fixtures.append((rows, True))
    high = []
    for i in range(3):
        row = [bound-m+1] * m
        for offset, g in enumerate((g for g in range(m) if g != i), 1):
            row[g] += offset
        high.append(row)
    high[0][3:] = sorted(high[0][3:], reverse=True)
    fixtures += [(high, True), ([[bound]*m for _ in range(3)], False), ([[0]*m for _ in range(3)], False)]
    records = []
    for rows, canonical in fixtures:
        substitutions = [(c[i][g], z3.BitVecVal(rows[i][g], c[i][g].size())) for i in range(3) for g in range(m)]
        domain_truth = all(z3.is_true(z3.simplify(z3.substitute(expr, *substitutions))) for expr in domain)
        assert domain_truth == canonical
        truths = []
        for (i, left, right), expr in atoms:
            observed = z3.is_true(z3.simplify(z3.substitute(expr, *substitutions)))
            expected = sum(rows[i][g] for g in range(m) if left >> g & 1) > sum(rows[i][g] for g in range(m) if right >> g & 1)
            assert observed == expected
            truths.append(observed)
        good = 0
        for assignment, clause in zip(allocations, clauses):
            failed = any(truths[k] for k in clause)
            expected = not literal_good(rows, assignment)
            assert failed == expected
            good += not failed
        records.append(dict(rows=rows, canonical_domain=canonical, surjective_efx_allocations=good))
    return dict(status='PASS', fixtures=records, actual_bv_atoms_checked=len(fixtures)*len(atoms),
                allocation_clauses_checked=len(fixtures)*len(allocations),
                exact_comparison='Actual unsigned bit-vector AST against independently summed integer deletion inequalities')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--m', type=int, choices=[8,9], required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--timeout', type=int, default=120)
    p.add_argument('--memory-mib', type=int, default=850)
    p.add_argument('--prepare-only', action='store_true')
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (a.memory_mib << 20,)*2)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    bound = math.isqrt((a.m-1)**a.m)
    record = dict(status='starting', started_utc=stamp(), m=a.m, bound=bound,
                  private_integer_row_minima=True, solver='Z3 '+z3.get_version_string(),
                  cap_mib=a.memory_mib, timeout_seconds=a.timeout,
                  proof_status='No independently checked UNSAT proof object')
    save(a.out.with_suffix('.json'), record)
    try:
        s, c, domain, atoms, clauses, allocations, cw, sw = make_formula(a.m, bound)
        formula = s.sexpr() + '\n(check-sat)\n'
        a.out.with_suffix('.smt2').write_text(formula)
        checked = audit(c, domain, atoms, clauses, allocations, a.m, bound)
        save(a.out.with_suffix('.audit.json'), checked)
        record.update(status='prepared', assertions=len(s.assertions()), unique_atoms=len(atoms),
                      cost_width=cw, sum_width=sw, maximum_sum=a.m*bound,
                      input_sha256=hashlib.sha256(formula.encode()).hexdigest(),
                      build_audit_seconds=time.monotonic()-start)
        save(a.out.with_suffix('.json'), record)
        print(json.dumps(record), flush=True)
        if a.prepare_only:
            return
        s.set(timeout=a.timeout*1000, random_seed=0)
        record.update(status='running', check_started_utc=stamp())
        save(a.out.with_suffix('.json'), record)
        began = time.monotonic()
        verdict = s.check()
        record.update(status=str(verdict), check_seconds=time.monotonic()-began, statistics=str(s.statistics()))
        if verdict == z3.unknown:
            record['reason_unknown'] = s.reason_unknown()
        elif verdict == z3.sat:
            model = s.model()
            rows = [[model.eval(v, model_completion=True).as_long() for v in row] for row in c]
            efx = [a for a in itertools.product(range(3), repeat=a.m) if literal_good(rows, a)]
            record.update(integer_rows=rows, complete_allocations_checked=3**a.m,
                          efx_count=len(efx), exact_counterexample_replay='PASS' if not efx else 'FAIL')
            assert not efx
    except BaseException as e:
        record.update(status='exception_without_verdict', exception_type=type(e).__name__, exception=str(e))
        raise
    finally:
        record.update(ended_utc=stamp(), elapsed_seconds=time.monotonic()-start,
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(a.out.with_suffix('.json'), record)
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
