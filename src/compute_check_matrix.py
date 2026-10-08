#!/usr/bin/env python3
"""Independent, definition-level exact verifier, including empty bundles/zeros.

This intentionally does not import either CEGIS evaluator. For every one of
3^m labelled allocations it directly quantifies all owned removals.
"""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path


def check(rows, designated=None):
    assert len(rows)==3 and len({len(r) for r in rows})==1
    assert all(v>=0 for row in rows for v in row)
    m=len(rows[0])
    count=0
    efx_count=0
    witnesses=[]
    for owners in itertools.product(range(3),repeat=m):
        bundles=[[g for g in range(m) if owners[g]==i] for i in range(3)]
        costs=[[sum((rows[i][g] for g in bundles[j]),Fraction(0)) for j in range(3)] for i in range(3)]
        efx=all(costs[i][i]-rows[i][g]<=costs[i][j]
                for i in range(3) for j in range(3) if i!=j for g in bundles[i])
        if not efx:
            continue
        efx_count+=1
        if designated is not None and any(costs[designated][designated]>costs[designated][j] for j in range(3) if j!=designated):
            continue
        count+=1
        if len(witnesses)<10:
            witnesses.append(bundles)
    return dict(agents=3,chores=m,allocations_checked=3**m,EFX_allocations=efx_count,
                designated_agent=designated,target_allocations=count,witnesses=witnesses,
                exact_counterexample=(count==0))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('matrix')
    ap.add_argument('--designated',type=int,choices=(0,1,2))
    ap.add_argument('--out')
    args=ap.parse_args()
    path=Path(args.matrix)
    raw=path.read_bytes()
    data=json.loads(raw,parse_float=str)
    rows=data['rows'] if isinstance(data,dict) else data
    rows=[[Fraction(v) for v in row] for row in rows]
    result=check(rows,args.designated)
    result.update(input_path=str(path),input_sha256=hashlib.sha256(raw).hexdigest())
    if args.out:
        Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
