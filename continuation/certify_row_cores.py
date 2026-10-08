#!/usr/bin/env python3
"""Export exact rational alternatives for every branch of row-0 core failure.

Each branch is a finite strict homogeneous linear system A x > 0.
A nonzero nonnegative vector w with w^T A=0 certifies its impossibility.
The generator uses Z3 only to find weights. The separate checker below
uses no solver and validates all coefficient identities and branches.
"""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import time
import z3


def domain_rows():
    ans=[(1,)+(0,)*8]
    for g in range(1,9):
        a=[0]*9;a[g]=1;a[0]=-1;ans.append(tuple(a))
    for g,h in [(2,1),(7,8),(6,7),(5,6),(4,5),(3,4)]:
        a=[0]*9;a[g]=1;a[h]=-1;ans.append(tuple(a))
    return ans


def failure_clauses(allocations):
    clauses=[]
    for a in allocations:
        forms=set()
        own=[g for g in range(9) if a[g]==0]
        if 0 in own:
            trims=[0]
        else:
            pinned=[g for g in (1,2) if g in own]
            free=[g for g in own if g>=3]
            trims=pinned[:1]+([max(free)] if free else [])
        for g in trims:
            for j in (1,2):
                forms.add(tuple(int(a[h]==0 and h!=g)-int(a[h]==j)
                                for h in range(9)))
        clauses.append(sorted(forms))
    return clauses


def certify(record, cache, timeout=30000):
    clauses=failure_clauses(record['core_allocations'])
    domain=domain_rows()
    branches=sorted(set(tuple(sorted(set(choice)))
                       for choice in itertools.product(*clauses)))
    certificates=[]
    for branch in branches:
        if branch in cache:
            weights=cache[branch]
        else:
            A=domain+list(branch)
            w=z3.Reals(' '.join(f'row_core_weight_{j}' for j in range(len(A))))
            s=z3.SolverFor('QF_LRA');s.set(timeout=timeout)
            s.add(*(v>=0 for v in w),z3.Sum(w)==1)
            for g in range(9):
                s.add(z3.Sum(*[v*a[g] for v,a in zip(w,A) if a[g]])==0)
            status=s.check()
            if status!=z3.sat:
                raise AssertionError(('No exact alternative certificate',str(status),branch))
            model=s.model()
            weights=[str(model.eval(v,model_completion=True)) for v in w]
            cache[branch]=weights
        certificates.append({'failure_rows':[list(a) for a in branch],
                             'weights':weights})
    return {'status':'certified','format_version':2,
            'trim_reduction':'minimal_owned_items_in_partial_order',
            'claim':'Every row-0 cost vector in the stated partial-order cone has EFX inequalities for at least one listed allocation.',
            'method':'Exhaustive failure-branch enumeration with nonnegative rational linear alternatives',
            'core_allocation_ids':record['core_allocation_ids'],
            'core_allocations':record['core_allocations'],
            'other_region_atoms':record['region_atoms'],
            'domain_rows':[list(a) for a in domain],
            'failure_clauses':[[list(a) for a in cl] for cl in clauses],
            'branches':certificates,
            'source_core_sha256':record['core_sha256']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--limit',type=int)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    from verify_row_cores import verify
    start=time.monotonic();cache={};receipts=[]
    files=sorted(a.source.glob('*.json'))
    if a.limit is not None:files=files[:a.limit]
    for number,file in enumerate(files):
        target=a.out/file.name
        if target.exists():
            data=json.loads(target.read_text())
        else:
            data=certify(json.loads(file.read_text()),cache)
        receipt=verify(data)
        if not target.exists():target.write_text(json.dumps(data,indent=2)+'\n')
        receipts.append({'file':file.name,**receipt,
                         'certificate_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
        if number%10==0:
            print(json.dumps({'completed':number+1,'elapsed_seconds':time.monotonic()-start,
                              'cached_alternatives':len(cache),'last_branches':len(data['branches'])}),flush=True)
    report={'status':'PASS','cores':len(receipts),'elapsed_seconds':time.monotonic()-start,
            'receipts':receipts}
    (a.out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='receipts'}),flush=True)


if __name__=='__main__':main()
