#!/usr/bin/env python3
"""Enumerate and certify every pair of allocations with all own minima.

There are 3^6=729 such allocations. Pairs containing a robust single
allocation are omitted because the single-allocation regions cover them.
Every retained pair has an exact certificate for each failure combination.
"""
import argparse
from copy import deepcopy
import itertools
import json
from pathlib import Path
import time

from pair_seeds import bad_rows, code, gaps, incompatible


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    start=time.monotonic();items=[];robust=0;records=[];cache={}
    for tail in itertools.product(range(3),repeat=6):
        allocation=(0,1,2)+tail
        rows=bad_rows(allocation)
        transformed=[tuple(gaps(q)) for q in rows]
        if all(all(v<=0 for v in q) for q in transformed):
            robust+=1
        else:items.append((allocation,rows,transformed))
    for first,second in itertools.combinations(items,2):
        branches=[]
        for j,k in itertools.product(range(2),repeat=2):
            u,v=first[2][j],second[2][k]
            key=tuple(sorted((u,v)))
            if key not in cache:cache[key]=incompatible(*key)
            certificate=cache[key]
            if certificate is None:break
            certificate=deepcopy(certificate)
            if key!=(u,v):certificate['atom_weights'].reverse()
            branches.append(dict(first_atom=j,second_atom=k,**certificate))
        if len(branches)==4:
            records.append(dict(allocation_ids=[code(first[0]),code(second[0])],
                allocations=[first[0],second[0]],
                first_row_bad_coefficients=[first[1],second[1]],
                proof_branches=branches))
    result=dict(family='all_minimum_owning_allocations',order='descending',
        normalisation='positive pinned minima',
        gap_coordinates=['c00','c01-c00','c02-c01','c08-c00','c07-c08',
                         'c06-c07','c05-c06','c04-c05','c03-c04'],
        minimum_owning_allocations=729,robust_singles=robust,
        nonrobust_allocations=len(items),all_pairs_considered=729*728//2,
        pairs_after_robust_single_removal=len(items)*(len(items)-1)//2,
        certified_pairs=len(records),records=records,
        seconds=time.monotonic()-start)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))


if __name__=='__main__':main()
