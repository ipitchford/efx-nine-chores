#!/usr/bin/env python3
"""Independent stdlib-only exact check of a row-elimination certificate."""
from fractions import Fraction
import argparse
import itertools
import json
from pathlib import Path


def exact_row(value):
    assert isinstance(value,list) and len(value)==9
    assert all(type(v) is int for v in value), 'coefficients must be exact integers'
    return tuple(value)


def verify(data):
    assert data['status']=='certified'
    domain=[]
    # c00 > 0; every other chore > c00; c01<c02; c08<c07<...<c03.
    for plus,minus in [(0,None)]+[(g,0) for g in range(1,9)]+[(2,1)]+[(g,g+1) for g in range(3,8)]:
        v=[0]*9;v[plus]+=1
        if minus is not None:v[minus]-=1
        domain.append(tuple(v))
    stored_domain=[exact_row(row) for row in data['domain_rows']]
    assert set(domain)==set(stored_domain)
    assert len(domain)==len(data['domain_rows'])
    # Use the documented stored order only after matching the whole domain.
    domain=stored_domain
    less=[[False]*9 for _ in range(9)]
    for row in domain:
        plus=[g for g,v in enumerate(row) if v==1]
        minus=[g for g,v in enumerate(row) if v==-1]
        if len(plus)==len(minus)==1:less[minus[0]][plus[0]]=True
    for k in range(9):
        for i in range(9):
            for j in range(9):less[i][j]=less[i][j] or (less[i][k] and less[k][j])
    clauses=[];other=set()
    allocations=data['core_allocations']
    assert len(allocations)==len(data['core_allocation_ids'])
    for a,aid in zip(allocations,data['core_allocation_ids']):
        assert all(type(owner) is int for owner in a) and type(aid) is int
        assert len(a)==9 and set(a)=={0,1,2}
        assert aid==sum(owner*3**(8-g) for g,owner in enumerate(a))
        bundles=[{g for g,owner in enumerate(a) if owner==i} for i in range(3)]
        failures=set()
        minima={g for g in bundles[0] if not any(less[h][g] for h in bundles[0])}
        if data.get('format_version',1)==2:
            assert data['trim_reduction']=='minimal_owned_items_in_partial_order'
            assert all(g in minima or any(less[h][g] for h in minima) for g in bundles[0])
        else:
            assert data.get('format_version',1)==1
        for i in range(3):
            for removed in bundles[i]:
                remainder=bundles[i]-{removed}
                for j in range(3):
                    if i==j:continue
                    v=tuple(int(g in remainder)-int(g in bundles[j]) for g in range(9))
                    if i==0:
                        if data.get('format_version',1)==1 or removed in minima:
                            failures.add(v)
                    elif any(x>0 for x in v):other.add((i,v))
        clauses.append(failures)
    assert [set(exact_row(row) for row in c) for c in data['failure_clauses']]==clauses
    assert all(type(p['agent']) is int for p in data['other_region_atoms'])
    assert {(p['agent'],exact_row(p['coefficients'])) for p in data['other_region_atoms']}==other
    expected={tuple(sorted(set(choice))) for choice in itertools.product(*clauses)}
    seen=set()
    for branch in data['branches']:
        chosen=tuple(exact_row(row) for row in branch['failure_rows'])
        assert chosen in expected and chosen not in seen
        seen.add(chosen)
        matrix=domain+list(chosen)
        assert all(type(w) in (str,int) for w in branch['weights'])
        weights=list(map(Fraction,branch['weights']))
        assert len(weights)==len(matrix)
        assert all(w>=0 for w in weights) and sum(weights)>0
        assert all(sum(w*row[g] for w,row in zip(weights,matrix))==0 for g in range(9))
    assert seen==expected
    return {'status':'PASS','core_allocations':len(allocations),
            'exhaustive_failure_branches':len(expected),
            'other_region_inequalities':len(other),
            'verification':'Literal deletion coefficients, exhaustive branch coverage, exact rational nonnegative linear identities; standard library only'}


def main():
    p=argparse.ArgumentParser();p.add_argument('files',nargs='+');a=p.parse_args()
    for file in a.files:print(json.dumps({'file':file,**verify(json.loads(Path(file).read_text()))}))


if __name__=='__main__':main()
