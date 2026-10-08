#!/usr/bin/env python3
"""Compare static SMT allocation clauses with a separate literal EFX checker.
Z3 is used solely as an SMT syntax parser; no satisfiability calls occur here.
All evaluations use bounded int64 arithmetic with checked coefficient bounds.
"""
import itertools,json,random,time,argparse,sys
from pathlib import Path
import numpy as np
import z3
from efx_exact import efx


def compiled_allocation_clauses(path,m):
    assertions=z3.parse_smt2_file(str(path));nalloc=3**m-3*2**m+3
    clauses=list(assertions)[-nalloc:]
    variables=[z3.Real(f'c_{i}_{g}') for i in range(3) for g in range(m)]
    vid={v.get_id():j for j,v in enumerate(variables)};cache={}
    def linear(e):
        k=e.get_id()
        if k in cache:return cache[k]
        v=np.zeros(3*m+1,dtype=np.int64)
        if k in vid:v[vid[k]]=1
        elif z3.is_rational_value(e):
            assert e.denominator_as_long()==1;v[-1]=e.numerator_as_long()
        elif z3.is_add(e):
            for a in e.children():v+=linear(a)
        elif z3.is_sub(e):
            v+=linear(e.arg(0))
            for a in e.children()[1:]:v-=linear(a)
        elif z3.is_mul(e):
            args=e.children();nonconst=[a for a in args if not z3.is_rational_value(a)];assert len(nonconst)<=1
            factor=1
            for a in args:
                if z3.is_rational_value(a):assert a.denominator_as_long()==1;factor*=a.numerator_as_long()
            v=linear(nonconst[0])*factor if nonconst else v
            if not nonconst:v[-1]=factor
        else:raise ValueError('unsupported arithmetic '+str(e))
        cache[k]=v;return v
    av=[];atomids={};cis=[]
    for clause in clauses:
        args=clause.children() if z3.is_or(clause) else [clause];ids=[]
        for atom in args:
            key=atom.get_id()
            if key not in atomids:
                assert z3.is_gt(atom)
                atomids[key]=len(av);av.append(linear(atom.arg(0))-linear(atom.arg(1)))
            ids.append(atomids[key])
        cis.append(ids)
    av.append(np.zeros(3*m+1,dtype=np.int64));dummy=len(av)-1
    idx=np.full((len(cis),max(map(len,cis))),dummy,dtype=np.int64)
    for k,ids in enumerate(cis):idx[k,:len(ids)]=ids
    return np.array(av),idx


def main():
    p=argparse.ArgumentParser();p.add_argument('--m',type=int,default=9);p.add_argument('--matrices',type=int,default=16);p.add_argument('--out',default='economics_problem2/results/encoding_audit.json');a=p.parse_args();m=a.m;t0=time.monotonic()
    coef,idx=compiled_allocation_clauses(Path(f'economics_problem2/results/root{m}_pruned.smt2'),m)
    allocations=[v for v in itertools.product(range(3),repeat=m) if len(set(v))==3]
    rng=random.Random(20261007);matrices=[[[0]*m for _ in range(3)],[[1]*m for _ in range(3)]]
    for k in range(a.matrices-2):
        c=[rng.sample(range(2,250),m) for _ in range(3)]
        for i in range(3):c[i][i]=1 if k%3 else 0
        if c[0][1]>c[0][2]:
            c=[c[0],c[2],c[1]]
            for row in c:row[1],row[2]=row[2],row[1]
        free=sorted(range(3,m),key=lambda g:c[0][g],reverse=True)
        c=[[row[g] for g in list(range(3))+free] for row in c]
        if k%4==1:c[1]=[7*x for x in c[1]];c[2]=[13*x for x in c[2]]
        matrices.append(c)
    counts=[]
    for k,c in enumerate(matrices):
        v=np.array([x for row in c for x in row]+[1],dtype=np.int64)
        assert int(np.max(np.abs(v)))*int(np.max(np.sum(np.abs(coef),axis=1)))<2**62
        bad=(coef@v>0)[idx].any(axis=1)
        direct=np.array([not efx(c,x) for x in allocations])
        disagreements=np.flatnonzero(bad!=direct)
        assert not len(disagreements),(k,disagreements[:10].tolist())
        counts.append(int(np.sum(~direct)))
    # A zero-cost chore is genuinely load-bearing in the predicate.
    c=[[5,0,1,1],[1,1,1,1],[1,1,1,1]];assignment=(0,0,1,2)
    assert not efx(c,assignment)
    # The positive-only trim mutation would accept this same allocation.
    b=[[g for g,i in enumerate(assignment) if i==j] for j in range(3)]
    positive_only=all(sum(c[i][h] for h in b[i] if h!=g)<=sum(c[i][h] for h in b[j]) for i in range(3) for j in range(3) if i!=j for g in b[i] if c[i][g]>0)
    assert positive_only
    expected={3:6,6:90,9:1680}.get(m)
    if expected is not None:assert counts[1]==expected
    result={'m':m,'matrices':len(matrices),'allocations_per_matrix':len(allocations),'matrix_allocation_pairs':len(matrices)*len(allocations),'disagreements':0,'efx_counts_surjective':counts,'zero_trim_mutation_detected':True,'uniform_expected':expected,'elapsed_s':time.monotonic()-t0,'scope':'finite semantic checks; not a formal encoder proof or universal existence proof'}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
