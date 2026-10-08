#!/usr/bin/env python3
"""Cheap exact D8 falsifier: freeze two rows and solve for the third."""
import argparse,json,math
from fractions import Fraction
from pathlib import Path
import z3
from compute_cegis import partitions
from compute_designated_cegis import designated_allocations

def solve(rows,free,timeout):
    m=len(rows[0]);allocations=list(partitions(m));full=(1<<m)-1
    members=[[g for g in range(m) if mask>>g&1] for mask in range(1<<m)]
    fixed_sums=[[sum(row[g] for g in members[mask]) for mask in range(1<<m)] for row in rows]
    x=[z3.Real(f'x_{g}') for g in range(m)]
    s=z3.SolverFor('QF_LRA');s.set(timeout=timeout*1000);s.set('smt.arith.solver',2)
    s.add(x[free]==1,*(x[g]>1 for g in range(m) if g!=free))
    sums=[z3.Sum([x[g] for g in members[mask]]) for mask in range(1<<m)]
    relevant=0
    for a in allocations:
        good=True
        for i in range(3):
            if i==free:continue
            trim=fixed_sums[i][a[i]]
            if i!=0:trim-=min(rows[i][g] for g in members[a[i]])
            if trim>min(fixed_sums[i][a[j]] for j in range(3) if i!=j):good=False;break
        if not good:continue
        relevant+=1
        if free==0:
            bad=[sums[a[0]]>sums[a[j]] for j in (1,2)]
        else:
            trims=[free] if free in members[a[free]] else members[a[free]]
            bad=[sums[a[free]^(1<<g)]>sums[a[j]] for g in trims for j in range(3) if j!=free]
        s.add(z3.Or(bad))
    status=s.check();out=dict(free_row=free,status=str(status),clauses=relevant)
    if status==z3.sat:
        model=s.model();rat=[]
        for v in x:
            val=model.eval(v);rat.append(Fraction(val.numerator_as_long(),val.denominator_as_long()))
        scale=math.lcm(*(v.denominator for v in rat));new=[[v for v in r] for r in rows];new[free]=[int(v*scale) for v in rat]
        target=designated_allocations(new,allocations,m)
        assert not target
        out.update(rows=new,designated_EF_allocations=0)
    elif status==z3.unknown:out['reason']=s.reason_unknown()
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('matrix');ap.add_argument('--timeout',type=int,default=3);ap.add_argument('--out',required=True);args=ap.parse_args()
    rows=json.loads(Path(args.matrix).read_text());rows=rows['rows'] if isinstance(rows,dict) else rows
    results=[solve(rows,i,args.timeout) for i in range(3)]
    Path(args.out).write_text(json.dumps(dict(source=args.matrix,results=results),indent=2)+'\n')
    print(json.dumps(results,indent=2))
