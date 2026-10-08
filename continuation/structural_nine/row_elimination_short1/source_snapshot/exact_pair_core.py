#!/usr/bin/env python3
"""Direct exact alternatives for a selected pair; no solver is used here."""
from fractions import Fraction
import itertools


def domain_rows():
    rows=[(1,)+(0,)*8]
    for g in range(1,9):
        row=[0]*9;row[g]=1;row[0]=-1;rows.append(tuple(row))
    for g,h in [(2,1),(7,8),(6,7),(5,6),(4,5),(3,4)]:
        row=[0]*9;row[g]=1;row[h]=-1;rows.append(tuple(row))
    return rows


def gaps(row):
    return [sum(row),row[1]+row[2],row[2]]+[
        sum(row[g] for g in range(3,upper+1)) for upper in range(8,2,-1)]


def failure_clauses(allocations):
    clauses=[]
    for a in allocations:
        own={g for g in range(9) if a[g]==0}
        if 0 in own:trims=[0]
        else:
            pinned=[g for g in (1,2) if g in own]
            free=[g for g in own if g>=3]
            trims=pinned[:1]+([max(free)] if free else [])
        clauses.append(sorted({tuple(int(g in own and g!=removed)-int(a[g]==j)
                                     for g in range(9))
                               for removed in trims for j in (1,2)}))
    return clauses


def branch_weights(branch):
    transformed=[gaps(q) for q in branch]
    if len(branch)==1:
        assert all(v<=0 for v in transformed[0]);weights=[Fraction(1)]
    else:
        assert len(branch)==2
        u,v=transformed
        if all(x<=0 for x in u):weights=[Fraction(1),Fraction(0)]
        elif all(x<=0 for x in v):weights=[Fraction(0),Fraction(1)]
        else:
            lower=Fraction(0);upper=None
            for x,y in zip(u,v):
                if x==0:assert y<=0,'Selected pair does not cover the first row'
                elif x>0:
                    bound=Fraction(-y,x);upper=bound if upper is None else min(upper,bound)
                else:lower=max(lower,Fraction(-y,x))
            assert upper is None or lower<=upper,'Selected pair does not cover the first row'
            weights=[lower,Fraction(1)]
    combo=[sum(w*u[g] for w,u in zip(weights,transformed)) for g in range(9)]
    assert all(v<=0 for v in combo)
    result=[Fraction(0)]*15+weights
    for k,index in enumerate([0,1,9,8,10,11,12,13,14]):result[index]=-combo[k]
    return [str(v) for v in result]


def certify(record):
    assert len(record['core_allocations'])==2
    clauses=failure_clauses(record['core_allocations'])
    branches=sorted({tuple(sorted(set(choice))) for choice in itertools.product(*clauses)})
    return dict(status='certified',format_version=2,
        trim_reduction='minimal_owned_items_in_partial_order',
        claim='Every first-row vector in the stated partial-order cone makes at least one listed allocation EFX for agent 0.',
        method='Direct rational two-inequality alternatives; independently checked after construction',
        core_allocation_ids=list(record['core_allocation_ids']),
        core_allocations=[list(a) for a in record['core_allocations']],
        other_region_atoms=[dict(agent=a['agent'],coefficients=list(a['coefficients']))
                            for a in record['region_atoms']],
        domain_rows=[list(row) for row in domain_rows()],
        failure_clauses=[[list(row) for row in clause] for clause in clauses],
        branches=[dict(failure_rows=[list(row) for row in branch],weights=branch_weights(branch)) for branch in branches],
        source_core_sha256=record['core_sha256'])


def generic_rows(rows):
    assert isinstance(rows,(list,tuple)) and len(rows)==2
    assert all(isinstance(row,(list,tuple)) and len(row)==9 and
               all(type(v) is int and v>0 for v in row) for row in rows)
    result=[];directions=[];scale=3281
    for pinned,row in enumerate(rows,1):
        assert all(row[g]>row[pinned] for g in range(9) if g!=pinned)
        direction=[0]*9;power=1
        for g in range(9):
            if g!=pinned:direction[g]=power;power*=3
        assert sum(direction)==3280 and scale>sum(direction)
        new=[scale*v+d for v,d in zip(row,direction)]
        assert all(new[g]>new[pinned] for g in range(9) if g!=pinned)
        sums={0}
        for v in new:sums|={x+v for x in list(sums)}
        assert len(sums)==512
        result.append(new);directions.append(direction)
    return result,dict(scale=scale,directions=directions,
        conclusion='Every nonzero old subset-sum sign is preserved and all subset-sum ties are removed')
