"""Designated-EF QF_LRA target after shared-minimum removal for other agents.

Genericity is used: a counterexample is in an open set, so costs can all be
strictly positive and pairwise distinct within each row. Agent 0 remains fixed.
Agents 1 and 2 have disjoint cheapest chores (else strengthened KMS insertion
reduces to m-1); these chores become columns 0 and 1 respectively. Swapping
agents 1 and 2, and these pinned columns, orders row0 on columns 0,1. Columns
2...m-1 are independently sorted by row0.
"""
import argparse
import itertools
import json
import time
from pathlib import Path
import z3


def solve(m, timeout, seed, dump_only=False, proof=False):
    if proof:z3.set_param(proof=True)
    start=time.monotonic()
    c=[[z3.Real(f'c_{i}_{g}') for g in range(m)] for i in range(3)]
    s=z3.SolverFor('QF_LRA');s.set(timeout=timeout*1000);s.set('arith.solver',2);s.set(random_seed=seed)
    for row in c:
        s.add(*(x>0 for x in row),z3.Sum(row)==1)
    for i in [1,2]:
        s.add(*(c[i][i-1]<c[i][g] for g in range(m) if g!=i-1))
    s.add(c[0][0]<c[0][1])
    s.add(*(c[0][g]<c[0][g+1] for g in range(2,m-1)))
    for a in itertools.product(range(3),repeat=m):
        b=[[g for g in range(m) if a[g]==i] for i in range(3)]
        if not all(b):
            continue # positive costs and m>=3 force nonempty in target
        sums=[[z3.Sum([c[i][g] for g in b[j]]) for j in range(3)] for i in range(3)]
        bad=[sums[0][0]>sums[0][j] for j in [1,2]]
        for i in [1,2]:
            for g in b[i]:
                for j in range(3):
                    if i!=j:bad.append(sums[i][i]-c[i][g]>sums[i][j])
        s.add(z3.Or(bad))
    built=time.monotonic()
    smt_path=Path(f'economics_problem2/work/structural_designated_reduced_m{m}_seed{seed}.smt2')
    smt_path.write_text(s.to_smt2())
    if dump_only:
        print(json.dumps(dict(m=m,result='dump_only',smt2=str(smt_path),assertions=len(s.assertions()))),flush=True)
        return
    result=s.check();end=time.monotonic()
    out=dict(m=m,target='EFX and agent 0 envy-free; minima other two agents distinct',result=str(result),seed=seed,build_s=built-start,check_s=end-built)
    if result==z3.sat:
        model=s.model();out['matrix']=[[str(model.eval(x)) for x in row] for row in c]
    if result==z3.unknown:out['reason']=s.reason_unknown()
    if result==z3.unsat and proof:
        proof_path=Path(f'economics_problem2/work/structural_designated_reduced_m{m}_seed{seed}.z3proof')
        proof_path.write_text(s.proof().sexpr());out['proof_path']=str(proof_path);out['proof_bytes']=proof_path.stat().st_size
    print(json.dumps(out),flush=True)
    suffix='_proof_replay' if proof else ''
    Path(f'economics_problem2/work/structural_designated_reduced_m{m}_seed{seed}{suffix}.json').write_text(json.dumps(out,indent=2))
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--m',type=int,default=8);p.add_argument('--timeout',type=int,default=1800);p.add_argument('--seed',type=int,default=0);p.add_argument('--dump-only',action='store_true');p.add_argument('--proof',action='store_true');a=p.parse_args();solve(a.m,a.timeout,a.seed,a.dump_only,a.proof)
