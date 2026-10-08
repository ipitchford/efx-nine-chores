#!/usr/bin/env python3
"""Freeze the literal row-0 failure problem at a verified two-row candidate."""
from fractions import Fraction
import hashlib, itertools, json
from pathlib import Path
import z3

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'continuation/structural_nine/zero_outer/run1_model.json'
OUT=ROOT/'continuation/structural_nine/fixed_zero_outer_candidate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    data=json.loads(SOURCE.read_text())
    fixed=[]
    for i in (1,2):
        fixed.append([Fraction(1) if g==0 else Fraction(0) if g==i else
                      Fraction(data['coordinates'][f'c_{i}_{g}']) for g in range(9)])
    compatible=[]
    for aid,allocation in enumerate(itertools.product(range(3),repeat=9)):
        bundles=[[g for g in range(9) if allocation[g]==i] for i in range(3)]
        if all(sum(fixed[i-1][h] for h in bundles[i] if h!=removed)<=
               sum(fixed[i-1][h] for h in bundles[j])
               for i in (1,2) for removed in bundles[i] for j in range(3) if j!=i):
            compatible.append(dict(allocation_id=aid,allocation=list(allocation)))
    c=[z3.Real(f'c_0_{g}') for g in range(9)]
    def failures(row):
        result=[]
        for record in compatible:
            a=record['allocation'];own=[g for g in range(9) if a[g]==0]
            result.append(z3.Or(*[
                z3.Sum([row[h] for h in own if h!=removed])>
                z3.Sum([row[h] for h in range(9) if a[h]==j])
                for removed in own for j in (1,2)]))
        return result
    zero=[z3.RealVal(0),z3.RealVal(1)]+c[2:]
    domains={
        'zero':[zero[g]>0 for g in range(2,9)]+[zero[2]>1]+
               [zero[g]<zero[g-1] for g in range(8,3,-1)],
        'positive':[c[0]==1]+[c[g]>1 for g in range(1,9)]+[c[1]<c[2]]+
                   [c[g]<c[g-1] for g in range(8,3,-1)]}
    inputs={}
    for name,row in [('zero',zero),('positive',c)]:
        solver=z3.SolverFor('QF_LRA');solver.add(*domains[name],*failures(row))
        target=OUT/f'{name}_inner.smt2';target.write_text(solver.sexpr()+'\n(check-sat)\n')
        inputs[name]=dict(path=str(target.resolve()),sha256=sha(target),
                          domain_assertions=len(domains[name]),assertions=len(solver.assertions()),
                          free_variables=7 if name=='zero' else 8)
    record=dict(status='prepared_not_solved',source=str(SOURCE.resolve()),source_sha256=sha(SOURCE),
        fixed_rows=[[str(x) for x in row] for row in fixed],
        all_allocations_checked=3**9,compatible_allocations=compatible,inputs=inputs,
        scope='Existential first-row costs in the canonical strict order; both other rows fixed exactly. Every compatible allocation contributes the disjunction of all literal owned-item deletion failures. Includes nonsurjective allocations if compatible.',
        zero_domain='c00=0,c01=1,c02>1, all c0g>0 for g>=2, c08<c07<c06<c05<c04<c03',
        positive_domain='c00=1, all c0g>1 for g>=1, c01<c02, c08<c07<c06<c05<c04<c03')
    (OUT/'preparation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='compatible_allocations'}|dict(compatible_count=len(compatible))))

if __name__=='__main__':main()
