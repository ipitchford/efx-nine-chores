#!/usr/bin/env python3
"""Exact designated-agent-EF CEGIS for the conditional P(8) reduction.

Target P(m): every nonnegative additive instance admits complete EFX with
agent 0 ordinary envy-free. The searched domain pins distinct minima for
agents 1 and 2; ruling this domain out proves P(m) only in combination with
the strengthened shared-minimum insertion lemma and P(m-1).
"""
import argparse
import itertools
import json
from pathlib import Path
import random
import time

import z3

from compute_cegis import integer_rows, partitions


def designated_allocations(rows, allocations, m):
    costs, trims = [], []
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
        if costs[0][a[0]] > min(costs[0][a[1]], costs[0][a[2]]):
            continue
        if all(trims[i][a[i]] <= min(costs[i][a[j]] for j in range(3) if j != i)
               for i in (1,2)):
            good.append(a)
    return good


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--m', type=int, default=8)
    ap.add_argument('--out', default='economics_problem2/work/compute_designated8')
    ap.add_argument('--timeout', type=int, default=600)
    ap.add_argument('--max-iterations', type=int, default=10000)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--arith-solver', type=int, default=2)
    ap.add_argument('--proof', action='store_true')
    ap.add_argument('--resume-allocations')
    ap.add_argument('--seed-near-cases')
    ap.add_argument('--neighbourhood', type=int, default=0)
    ap.add_argument('--all-three-minima', action='store_true')
    args = ap.parse_args()
    rng = random.Random(args.seed)
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
    for row in C:
        solver.add(*(value >= 1 for value in row))
    for i in (range(3) if args.all_three_minima else (1,2)):
        pinned = i if args.all_three_minima else i-1
        for k in range(m):
            if k != pinned:
                solver.add(C[i][k] - C[i][pinned] >= 1)
    if args.all_three_minima:
        solver.add(C[0][2]-C[0][1] >= 1)
    else:
        solver.add(C[0][1]-C[0][0] >= 1)
    for k in range(3 if args.all_three_minima else 2,m-1):
        solver.add(C[0][k+1]-C[0][k] >= 1)
    sums = [[z3.Sum([C[i][k] for k in members[s]]) for s in range(1<<m)] for i in range(3)]

    def clause(a):
        alternatives = [sums[0][a[0]] - sums[0][a[j]] >= 1 for j in (1,2)]
        for i in (1,2):
            mine = members[a[i]]
            if len(mine) == 1:
                continue
            pinned = i if args.all_three_minima else i-1
            if pinned in mine:
                mine = [pinned]
            for k in mine:
                for j in range(3):
                    if j != i:
                        alternatives.append(sums[i][a[i] ^ (1<<k)]-sums[i][a[j]] >= 1)
        return z3.Or(alternatives)

    seen = set()
    if args.resume_allocations:
        seen.update(map(tuple,json.loads(Path(args.resume_allocations).read_text())))
    if args.seed_near_cases:
        records = json.loads(Path(args.seed_near_cases).read_text())['records']
        for record in records:
            p = record['designated_agent']
            rows = [record['rows'][i] for i in [p]+[j for j in range(3) if j!=p]]
            seen.update(designated_allocations(rows, allocations, m))
    for a in sorted(seen):
        solver.add(clause(a))
    t0 = time.monotonic()
    history = []
    best = float('inf')
    (out / 'allocations.json').write_text(json.dumps(sorted(seen))+'\n')
    (out / 'formula.smt2').write_text(solver.to_smt2())
    for iteration in range(args.max_iterations):
        ts = time.monotonic()
        status = solver.check()
        entry = dict(iteration=iteration, status=str(status), clauses=len(seen),
                     check_seconds=time.monotonic()-ts, elapsed_seconds=time.monotonic()-t0)
        if status == z3.sat:
            rows = integer_rows(solver.model(),C)
            good = designated_allocations(rows,allocations,m)
            refinements = set(good)
            if good:
                # Any allocation-failure clause is necessary for a true target
                # counterexample. These neighbours merely choose useful clauses;
                # they introduce no restriction on the searched cost matrices.
                for sample in range(args.neighbourhood):
                    radius = (1,3,10,30)[sample % 4]
                    neighbour = [[100*v+rng.randint(-radius*v,radius*v)
                                  for v in row] for row in rows]
                    refinements.update(designated_allocations(neighbour,allocations,m))
            unseen = sorted(refinements-seen)
            entry.update(designated_EF_allocations=len(good),max_integer=max(map(max,rows)),newly_added=len(unseen))
            if args.neighbourhood:
                entry.update(neighbourhood_samples=args.neighbourhood,
                             neighbourhood_union_allocations=len(refinements))
            (out / 'last_model.json').write_text(json.dumps(rows,indent=2)+'\n')
            (out / f'model_{iteration:04}.json').write_text(json.dumps(rows,indent=2)+'\n')
            if len(good) < best:
                best = len(good)
                (out / 'fewest_model.json').write_text(json.dumps(dict(rows=rows,allocations=good),indent=2)+'\n')
            if not good:
                entry['conclusion'] = 'EXACT_COUNTEREXAMPLE_TO_DESIGNATED_EF_TARGET'
                (out / 'counterexample.json').write_text(json.dumps(rows,indent=2)+'\n')
            elif not unseen:
                raise AssertionError('Previously forbidden allocation remained designated-EF+EFX')
            else:
                for a in unseen:
                    solver.add(clause(a))
                    seen.add(a)
        elif status == z3.unknown:
            entry['reason'] = solver.reason_unknown()
        else:
            entry['conclusion'] = ('UNSAT_ALL_THREE_MINIMUM_DOMAIN' if args.all_three_minima
                                   else 'UNSAT_DISJOINT_OTHER_AGENT_MINIMUM_DOMAIN')
            if args.proof:
                (out / 'proof.z3').write_text(solver.proof().sexpr()+'\n')
        history.append(entry)
        print(json.dumps(entry),flush=True)
        (out / 'history.json').write_text(json.dumps(history,indent=2)+'\n')
        (out / 'allocations.json').write_text(json.dumps(sorted(seen))+'\n')
        (out / 'formula.smt2').write_text(solver.to_smt2())
        if status != z3.sat or not good:
            break


if __name__ == '__main__':
    main()
