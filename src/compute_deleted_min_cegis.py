#!/usr/bin/env python3
"""Exact CEGIS for three simultaneous deleted-minimum P(8) obstructions.

If a nine-chore counterexample exists with distinct global minima, deleting
agent i's minimum must defeat complete EFX with i ordinary envy-free, for
each i. Restoring that minimum otherwise supplies a nine-chore EFX witness.
SAT for these weaker necessary conditions is not a nine-chore counterexample.
The optional --include-nine mode also refines by every full EFX allocation.
"""
import argparse
import json
from pathlib import Path
import time

import z3

from compute_cegis import evaluate_efx, integer_rows, partitions
from compute_designated_cegis import designated_allocations


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='economics_problem2/work/compute_deleted_min9')
    ap.add_argument('--timeout',type=int,default=600)
    ap.add_argument('--seed',type=int,default=0)
    ap.add_argument('--seed-matrix')
    ap.add_argument('--resume-clauses')
    ap.add_argument('--resume-nine-allocations')
    ap.add_argument('--include-nine',action='store_true')
    ap.add_argument('--proof',action='store_true')
    args=ap.parse_args()
    if args.proof:z3.set_param(proof=True)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    (out/'config.json').write_text(json.dumps(vars(args),indent=2)+'\n')
    m=9
    C=[[z3.Real(f'c_{i}_{g}') for g in range(m)] for i in range(3)]
    s=z3.SolverFor('QF_LRA');s.set(timeout=args.timeout*1000,random_seed=args.seed);s.set('smt.arith.solver',2)
    for i,row in enumerate(C):
        s.add(*(v>=1 for v in row))
        s.add(*(row[g]-row[i]>=1 for g in range(m) if g!=i))
    s.add(C[0][2]-C[0][1]>=1)
    s.add(*(C[0][g+1]-C[0][g]>=1 for g in range(3,m-1)))
    members=[[g for g in range(m) if mask>>g&1] for mask in range(1<<m)]
    sums=[[z3.Sum([C[i][g] for g in members[mask]]) for mask in range(1<<m)] for i in range(3)]
    atom_cache={}
    def atom(i,a,b):
        key=i,a,b
        if key not in atom_cache:atom_cache[key]=sums[i][a]-sums[i][b]>=1
        return atom_cache[key]
    def clause(removed,a):
        bad=[]
        if removed>=0:
            bad.extend(atom(removed,a[removed],a[j]) for j in range(3) if j!=removed)
        for i in range(3):
            if i==removed:continue
            mine=members[a[i]]
            if len(mine)<2:continue
            if i in mine:mine=[i]
            elif i==0:
                free=next((g for g in mine if g>=3),None)
                mine=[g for g in mine if g in (1,2) or g==free]
                if 1 in mine and 2 in mine:mine.remove(2)
            for g in mine:
                bad.extend(atom(i,a[i]^(1<<g),a[j]) for j in range(3) if j!=i)
        return z3.Or(bad)
    allocations8=list(partitions(8));allocations9=list(partitions(9))
    def analyse(rows):
        refinements=set();counts=[]
        for removed in range(3):
            row_order=[removed]+[i for i in range(3) if i!=removed]
            reduced=[[rows[i][g] for g in range(9) if g!=removed] for i in row_order]
            good=designated_allocations(reduced,allocations8,8)
            counts.append(len(good))
            for a in good:
                original=[0,0,0]
                lowmask=(1<<removed)-1
                for k,i in enumerate(row_order):
                    low=a[k]&lowmask
                    original[i]=low|((a[k]^low)<<1)
                refinements.add((removed,*original))
        full=evaluate_efx(rows,allocations9,9)
        if args.include_nine:
            refinements.update((-1,*a) for a in full)
        return refinements,counts,full
    seen=set()
    if args.resume_clauses:
        seen.update(map(tuple,json.loads(Path(args.resume_clauses).read_text())))
    if args.resume_nine_allocations:
        assert args.include_nine
        seen.update((-1,*a) for a in json.loads(Path(args.resume_nine_allocations).read_text()))
    if args.seed_matrix:
        rows=json.loads(Path(args.seed_matrix).read_text())
        if isinstance(rows,dict):rows=rows['rows']
        seen.update(analyse(rows)[0])
    for removed,*a in sorted(seen):s.add(clause(removed,a))
    t0=time.monotonic();history=[]
    (out/'clauses.json').write_text(json.dumps(sorted(seen))+'\n')
    (out/'formula.smt2').write_text(s.to_smt2())
    for iteration in range(30000):
        t1=time.monotonic();status=s.check()
        entry=dict(iteration=iteration,status=str(status),clauses=len(seen),check_seconds=time.monotonic()-t1,elapsed_seconds=time.monotonic()-t0)
        stop=False
        if status==z3.sat:
            rows=integer_rows(s.model(),C)
            ref,counts,full=analyse(rows)
            new=ref-seen
            entry.update(deleted_min_designated_EF_counts=counts,full_EFX_allocations=len(full),newly_added=len(new))
            (out/'last_model.json').write_text(json.dumps(rows,indent=2)+'\n')
            (out/f'model_{iteration:04}.json').write_text(json.dumps(rows,indent=2)+'\n')
            if not full:
                entry['conclusion']='EXACT_NINE_CHORE_EFX_COUNTEREXAMPLE'
                (out/'counterexample.json').write_text(json.dumps(rows,indent=2)+'\n');stop=True
            elif not any(counts) and not args.include_nine:
                entry['conclusion']='SIMULTANEOUS_DELETED_MINIMUM_OBSTRUCTIONS_EXIST_BUT_FULL_EFX_EXISTS'
                (out/'obstruction.json').write_text(json.dumps(dict(rows=rows,full_EFX_allocations=full),indent=2)+'\n');stop=True
            else:
                if not new:raise AssertionError('No new necessary failure clause at a SAT candidate')
                for removed,*a in sorted(new):s.add(clause(removed,a))
                seen.update(new)
        elif status==z3.unsat:
            entry['conclusion']='UNSAT_NECESSARY_COUNTEREXAMPLE_CONDITIONS'
            if args.proof:(out/'proof.z3').write_text(s.proof().sexpr()+'\n')
            stop=True
        else:
            entry['reason']=s.reason_unknown();stop=True
        history.append(entry);print(json.dumps(entry),flush=True)
        (out/'history.json').write_text(json.dumps(history,indent=2)+'\n')
        (out/'clauses.json').write_text(json.dumps(sorted(seen))+'\n')
        (out/'formula.smt2').write_text(s.to_smt2())
        if stop:break


if __name__=='__main__':main()
