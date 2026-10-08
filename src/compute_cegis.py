#!/usr/bin/env python3
"""Exact CEGIS for three-agent, nine-chore complete EFX.

Every refinement is the disjunction that a particular labelled allocation
fails complete EFX. UNSAT therefore proves that the entire counterexample
class is empty, even if only a subset of all allocations has been added.
SAT after exhaustive exact enumeration is an exact rational counterexample.
Positive, distinct-minimum instances suffice by openness and the shared
minimum insertion reduction. This script alone does not prove that reduction.
"""
import argparse
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path
import time

import z3


def partitions(m):
    full = (1 << m) - 1
    for a in range(1, full):
        rest = full ^ a
        b = rest
        while b:
            c = rest ^ b
            if c:
                yield a, b, c
            b = (b - 1) & rest


def evaluate_efx(rows, allocations, m):
    costs = []
    trims = []
    for row in rows:
        sums = [0] * (1 << m)
        mins = [None] * (1 << m)
        for mask in range(1, 1 << m):
            bit = mask & -mask
            k = bit.bit_length() - 1
            tail = mask ^ bit
            sums[mask] = sums[tail] + row[k]
            mins[mask] = row[k] if not tail else min(row[k], mins[tail])
        costs.append(sums)
        trims.append([0] + [sums[s] - mins[s] for s in range(1, 1 << m)])
    good = []
    for a in allocations:
        if all(trims[i][a[i]] <= min(costs[i][a[j]] for j in range(3) if j != i)
               for i in range(3)):
            good.append(a)
    return good


def integer_rows(model, variables):
    result = []
    for row in variables:
        rat = []
        for v in row:
            r = model.eval(v, model_completion=True)
            rat.append(Fraction(r.numerator_as_long(), r.denominator_as_long()))
        scale = math.lcm(*(f.denominator for f in rat))
        ints = [int(f * scale) for f in rat]
        divisor = math.gcd(*ints)
        result.append([v // divisor for v in ints])
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--m', type=int, default=9)
    ap.add_argument('--out', default='economics_problem2/work/compute_cegis')
    ap.add_argument('--timeout', type=int, default=600)
    ap.add_argument('--max-iterations', type=int, default=10000)
    ap.add_argument('--batch', type=int, default=100000)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--arith-solver', type=int, default=2)
    ap.add_argument('--no-normalize', action='store_true')
    ap.add_argument('--min-normalize', action='store_true')
    ap.add_argument('--unit-margin', action='store_true')
    ap.add_argument('--large-chore-cuts', action='store_true')
    ap.add_argument('--agent-symmetry', action='store_true')
    ap.add_argument('--singleton-cuts', action='store_true')
    ap.add_argument('--rank-case', nargs=2, type=int)
    ap.add_argument('--proof', action='store_true')
    ap.add_argument('--resume-allocations')
    args = ap.parse_args()
    if args.proof:
        z3.set_param(proof=True)
    m = args.m
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'config.json').write_text(json.dumps(vars(args),indent=2)+'\n')
    allocations = list(partitions(m))
    members = [[k for k in range(m) if s & (1 << k)] for s in range(1 << m)]
    C = [[z3.Real(f'c_{i}_{k}') for k in range(m)] for i in range(3)]
    solver = z3.SolverFor('QF_LRA')
    solver.set(timeout=args.timeout * 1000, random_seed=args.seed)
    solver.set('smt.arith.solver', args.arith_solver)
    def positive(value):
        return value >= 1 if args.unit_margin else value > 0
    for i, row in enumerate(C):
        if args.unit_margin:
            assert not args.min_normalize
        elif args.min_normalize:
            solver.add(row[i] == 1)
        elif not args.no_normalize:
            solver.add(z3.Sum(row) == 1)
        for k, value in enumerate(row):
            solver.add(positive(value))
            if k != i:
                solver.add(positive(value - row[i]))
    for k in range(3, m - 1):
        solver.add(positive(C[0][k + 1] - C[0][k]))
    rank_order = None
    if args.rank_case:
        r1,r2 = args.rank_case
        assert 0 <= r1 < r2 < m-1
        rank_order = [None] * (m-1)
        rank_order[r1], rank_order[r2] = 1,2
        free = iter(range(3,m))
        rank_order = [0] + [next(free) if k is None else k for k in rank_order]
        for a,b in zip(rank_order,rank_order[1:]):
            solver.add(positive(C[0][b]-C[0][a]))
    if args.agent_symmetry:
        solver.add(positive(C[0][2] - C[0][1]))
        if args.min_normalize:
            for j in (1,2):
                solver.add(z3.Sum(C[0]) >= z3.Sum(C[j]))
        elif not args.no_normalize and not args.unit_margin:
            for j in (1,2):
                solver.add(C[0][0] <= C[j][j])
    if args.large_chore_cuts:
        for k in range(m):
            for i,j in itertools.combinations(range(3),2):
                solver.add(z3.Or(positive(z3.Sum(C[i]) - 3*C[i][k]),
                                 positive(z3.Sum(C[j]) - 3*C[j][k])))
    if args.singleton_cuts:
        for i in range(3):
            for x,y in itertools.combinations([k for k in range(m) if k!=i],2):
                trimmed = z3.Sum(C[i]) - C[i][x] - C[i][y] - C[i][i]
                solver.add(z3.Or(positive(trimmed-C[i][x]),positive(trimmed-C[i][y])))
    subset_costs = [[z3.Sum([C[i][k] for k in members[s]])
                     for s in range(1 << m)] for i in range(3)]
    
    def clause(a):
        alternatives = []
        for i in range(3):
            mine = members[a[i]]
            # Known global minima and sorted row-0 free items remove redundant
            # removal candidates, never add an assumption about an unknown order.
            if i in mine:
                mine = [i]
            elif i == 0 and rank_order is not None:
                mine = [next(k for k in rank_order if k in mine)]
            elif i == 0:
                first_free = next((k for k in mine if k >= 3), None)
                mine = [k for k in mine if k < 3 or k == first_free]
                if args.agent_symmetry and 1 in mine and 2 in mine:
                    mine.remove(2)
            for k in mine:
                if len(members[a[i]]) == 1:
                    continue  # A zero trim cannot exceed a positive other bundle.
                for j in range(3):
                    if j != i:
                        alternatives.append(positive(subset_costs[i][a[i] ^ (1 << k)] - subset_costs[i][a[j]]))
        return z3.Or(alternatives)
    
    seen = set()
    if args.resume_allocations:
        for a in json.loads(Path(args.resume_allocations).read_text()):
            a = tuple(a)
            solver.add(clause(a))
            seen.add(a)
    t0 = time.monotonic()
    history = []
    best_good = float('inf')
    for iteration in range(args.max_iterations):
        ts = time.monotonic()
        status = solver.check()
        entry = dict(iteration=iteration, status=str(status), clauses=len(seen),
                     check_seconds=time.monotonic()-ts, elapsed_seconds=time.monotonic()-t0)
        if status == z3.sat:
            rows = integer_rows(solver.model(), C)
            good = evaluate_efx(rows, allocations, m)
            unseen = [a for a in good if a not in seen]
            entry.update(efx_allocations=len(good), max_integer=max(map(max, rows)), newly_added=min(len(unseen),args.batch))
            (out / 'last_model.json').write_text(json.dumps(rows, indent=2)+'\n')
            (out / f'model_{iteration:04}.json').write_text(json.dumps(rows,indent=2)+'\n')
            if len(good) < best_good:
                best_good = len(good)
                (out / 'fewest_efx_model.json').write_text(json.dumps(dict(rows=rows,efx_allocations=good),indent=2)+'\n')
            if not good:
                entry['conclusion'] = 'EXACT_RATIONAL_COUNTEREXAMPLE'
                (out / 'counterexample.json').write_text(json.dumps(rows, indent=2)+'\n')
            elif not unseen:
                raise AssertionError('model satisfied a previously forbidden allocation')
            else:
                # In default mode add every exact EFX allocation at the candidate.
                for a in unseen[:args.batch]:
                    solver.add(clause(a))
                    seen.add(a)
        elif status == z3.unknown:
            entry['reason'] = solver.reason_unknown()
        else:
            entry['conclusion'] = 'UNSAT_COUNTEREXAMPLE_SUBFORMULA'
            if args.proof:
                (out / 'proof.z3').write_text(solver.proof().sexpr()+'\n')
        history.append(entry)
        print(json.dumps(entry), flush=True)
        (out / 'history.json').write_text(json.dumps(history,indent=2)+'\n')
        (out / 'allocations.json').write_text(json.dumps(sorted(seen))+'\n')
        (out / 'formula.smt2').write_text(solver.to_smt2())
        if status != z3.sat or not good:
            break


if __name__ == '__main__':
    main()
