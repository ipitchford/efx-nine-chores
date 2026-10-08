#!/usr/bin/env python3
"""Exact ordinal first-row certificates for pairs of allocations.

All agents own their pinned minima. One nonprescribed bundle is held
fixed, and the remaining six free chores are distributed between agent0
and the other agent. This gives exactly (5^6-3^6)/2=7448 pairs per choice
of fixed nonprescribed agent. Every accepted pair has a rational certificate
for all four combinations of first-row failure inequalities.
"""
import argparse
from fractions import Fraction
import itertools,json,time
from pathlib import Path

def code(a):
    value=0
    for owner in a:value=3*value+owner
    return value

def gaps(q):
    return [sum(q),q[1]+q[2],q[2]]+[sum(q[g] for g in range(3,upper+1)) for upper in range(8,2,-1)]

def bad_rows(a):
    return [tuple(int(a[g]==0 and g!=0)-int(a[g]==j) for g in range(9)) for j in (1,2)]

def frac(x):return [x.numerator,x.denominator]

def incompatible(u,v):
    if all(x<=0 for x in u):alpha,beta=Fraction(1),Fraction(0)
    elif all(x<=0 for x in v):alpha,beta=Fraction(0),Fraction(1)
    else:
        low=Fraction(0);high=None
        for a,b in zip(u,v):
            if a==0:
                if b>0:return None
            elif a>0:
                bound=Fraction(-b,a)
                high=bound if high is None else min(high,bound)
            else:low=max(low,Fraction(-b,a))
        if high is not None and low>high:return None
        alpha,beta=low,Fraction(1)
    combo=[alpha*a+beta*b for a,b in zip(u,v)]
    assert alpha>=0 and beta>=0 and alpha+beta>0 and all(x<=0 for x in combo)
    return dict(atom_weights=[frac(alpha),frac(beta)],gap_weights=[frac(-x) for x in combo])

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--both',action='store_true');args=p.parse_args()
    start=time.monotonic();records=[];counts=[]
    for fixed in ((1,2) if args.both else (2,)):
        other=3-fixed;count=0;robust=0;accepted=0
        for mask in range(1<<6):
            B={fixed}|{g+3 for g in range(6) if mask>>g&1}
            R=[g for g in range(3,9) if g not in B]
            possibilities=[]
            for allocation_mask in range(1<<len(R)):
                a=[None]*9;a[0]=0;a[fixed]=fixed;a[other]=other
                for g in B:a[g]=fixed
                for j,g in enumerate(R):a[g]=0 if allocation_mask>>j&1 else other
                rows=bad_rows(a);U=[gaps(row) for row in rows]
                possibilities.append((tuple(a),rows,U))
            for (a,ar,au),(b,br,bu) in itertools.combinations(possibilities,2):
                count+=1
                if all(all(x<=0 for x in row) for row in au) or all(all(x<=0 for x in row) for row in bu):
                    robust+=1;continue
                branches=[]
                for j,k in itertools.product(range(2),repeat=2):
                    cert=incompatible(au[j],bu[k])
                    if cert is None:break
                    branches.append(dict(first_atom=j,second_atom=k,**cert))
                if len(branches)!=4:continue
                accepted+=1;records.append(dict(fixed_agent=fixed,allocation_ids=[code(a),code(b)],
                    allocations=[a,b],first_row_bad_coefficients=[ar,br],proof_branches=branches))
        assert count==7448
        counts.append(dict(fixed_agent=fixed,pairs_considered=count,already_has_robust_allocation=robust,new_certified_pairs=accepted))
    result=dict(order='descending',normalisation='positive pinned minima',gap_coordinates=['c00','c01-c00','c02-c01','c08-c00','c07-c08','c06-c07','c05-c06','c04-c05','c03-c04'],
                counts=counts,certified_pairs=len(records),records=records,seconds=time.monotonic()-start)
    args.out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))

if __name__=='__main__':main()
