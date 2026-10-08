#!/usr/bin/env python3
"""Literal zero-tolerant EFX checker. Python integers/Fraction, no optimiser.
The checker is intentionally independent of the symbolic encoders.
"""
import itertools,json,argparse
from fractions import Fraction
from pathlib import Path


def costs_from_json(payload):
    if isinstance(payload,dict):payload=payload['costs']
    c=[[Fraction(x) for x in row] for row in payload]
    if not c or not c[0] or any(len(r)!=len(c[0]) for r in c):raise ValueError('rectangular nonempty cost matrix required')
    if any(x<0 for r in c for x in r):raise ValueError('costs must be nonnegative')
    return c


def efx(c,assignment,designated=None):
    n=len(c);m=len(c[0]);bundles=[[g for g in range(m) if assignment[g]==i] for i in range(n)]
    for i in range(n):
        own=sum(c[i][g] for g in bundles[i])
        for j in range(n):
            if i==j:continue
            other=sum(c[i][h] for h in bundles[j])
            if designated==i and own>other:return False
            for g in bundles[i]:
                if sum(c[i][h] for h in bundles[i] if h!=g)>other:return False
    return True


def enumerate_efx(c,designated=None):
    return [a for a in itertools.product(range(len(c)),repeat=len(c[0])) if efx(c,a,designated)]


def main():
    p=argparse.ArgumentParser();p.add_argument('matrix');p.add_argument('--out');p.add_argument('--designated',type=int);a=p.parse_args()
    c=costs_from_json(json.loads(Path(a.matrix).read_text()));res=enumerate_efx(c,a.designated)
    payload={'n':len(c),'m':len(c[0]),'allocations_checked':len(c)**len(c[0]),'efx_count':len(res),'designated':a.designated,'first_allocation':res[0] if res else None,'counterexample':not res,'arithmetic':'exact Fraction'}
    if a.out:Path(a.out).write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
