"""Independent exact audit of the actual strict_lra rank-pruned predicates.

The source module is not edited. A solver proxy records the allocation at each
actual allocation-clause assertion. We decode its returned arithmetic AST into
integer coefficient vectors, then compare each of all 3^9 predicates against
an independently written direct EFX checker on exact canonical integer matrices.
"""
import hashlib
import importlib.util
import inspect
from itertools import combinations,product
from pathlib import Path
import json,time
import numpy as np
import z3

SOURCE=Path('economics_problem2/src/strict_lra.py')
spec=importlib.util.spec_from_file_location('rank_source',SOURCE)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
REAL_SOLVER=z3.SolverFor


class RecordingSolver:
    def __init__(self,*a,**kw):self.s=REAL_SOLVER(*a,**kw);self.recorded={}
    def __getattr__(self,name):return getattr(self.s,name)
    def add(self,*args):
        frame=inspect.currentframe().f_back
        if frame.f_code.co_name=='build' and 'a' in frame.f_locals and 'auto_bad' in frame.f_locals:
            a=frame.f_locals['a']
            assert len(args)==1 and isinstance(a,tuple)
            self.recorded[a]=args[0]
        self.s.add(*args)


def canonical_costs(case,trial,m=9):
    rank=[None]*(m-1);rank[case[0]]=1;rank[case[1]]=2
    free=iter(range(m-1,2,-1));rank=[0]+[next(free) if x is None else x for x in rank]
    rng=np.random.default_rng(94121+trial+101*case[0]+997*case[1])
    C=np.zeros((3,m),dtype=np.int64)
    if trial==0:ordered=np.arange(1,m+1)
    elif trial==1:ordered=np.array([1,2,4,8,16,32,64,128,256])
    else:ordered=np.cumsum(rng.integers(1,1001,size=m))
    C[0,rank]=ordered
    for i in [1,2]:
        C[i]=rng.choice(np.arange(2,10002),size=m,replace=False)
        C[i,i]=1
    return C


def decode_clauses(recorded,m=9):
    size=3*m+1;memo={};atomids={};coeff=[];clauses={}
    def lin(x):
        key=x.get_id()
        if key in memo:return memo[key]
        v=np.zeros(size,dtype=np.int64)
        if z3.is_rational_value(x):
            assert x.denominator_as_long()==1;v[-1]=x.numerator_as_long()
        elif z3.is_const(x):
            _,i,g=str(x).split('_');v[int(i)*m+int(g)]=1
        elif x.decl().kind()==z3.Z3_OP_ADD:
            for y in x.children():v+=lin(y)
        elif x.decl().kind()==z3.Z3_OP_SUB:
            v=lin(x.arg(0)).copy()
            for y in x.children()[1:]:v-=lin(y)
        elif x.decl().kind()==z3.Z3_OP_UMINUS:v=-lin(x.arg(0))
        elif x.decl().kind()==z3.Z3_OP_TO_REAL:v=lin(x.arg(0))
        else:raise AssertionError(('unexpected arithmetic',x))
        memo[key]=v;return v
    for a,clause in recorded.items():
        atoms=[]
        if not z3.is_false(clause):
            assert z3.is_or(clause)
            for atom in clause.children():
                assert atom.decl().kind()==z3.Z3_OP_GT
                key=tuple(lin(atom.arg(0))-lin(atom.arg(1)))
                if key not in atomids:atomids[key]=len(coeff);coeff.append(key)
                atoms.append(atomids[key])
        clauses[a]=atoms
    return np.array(coeff,dtype=np.int64),clauses


def verify_case(case):
    z3.SolverFor=RecordingSolver
    try:s,c,info=mod.build(9,timeout=1,normalisation='none',row_symmetry=True,rank_case=case,all_trims=False,cuts='none',dominance=True)
    finally:z3.SolverFor=REAL_SOLVER
    matrix,clauses=decode_clauses(s.recorded)
    assert len(clauses)==info['allocation_clauses']
    empty=sum(1 for a in product(range(3),repeat=9) if len(set(a))<3)
    assert 3**9-len(clauses)==empty+info['automatically_bad']
    tested=0
    for trial in range(3):
        C=canonical_costs(case,trial)
        assert all(C[i,i]<C[i,g] for i in range(3) for g in range(9) if g!=i)
        truth=matrix@np.append(C.ravel(),1)>0
        for a in product(range(3),repeat=9):
            bundles=[[g for g in range(9) if a[g]==i] for i in range(3)]
            direct_bad=False
            for i in range(3):
                residual=sum(int(C[i,g]) for g in bundles[i])-min((int(C[i,g]) for g in bundles[i]),default=0)
                if any(residual>sum(int(C[i,g]) for g in bundles[j]) for j in range(3) if j!=i):direct_bad=True;break
            actual_bad=any(truth[x] for x in clauses[a]) if a in clauses else True
            assert bool(actual_bad)==direct_bad,(case,trial,C.tolist(),a,direct_bad,actual_bad)
            tested+=1
    return dict(case=list(case),predicates_compared=tested,canonical_matrices=3,empty_allocations_skipped=empty,source_info=info,result='PASS')


def main():
    start=time.monotonic()
    cases=list(combinations(range(8),2))
    assert len(cases)==28
    results=[verify_case(c) for c in [(0,1),(0,7),(3,5),(6,7)]]
    out=dict(source=str(SOURCE),sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),canonical_rank_cases=[list(c) for c in cases],rank_case_count=len(cases),checked_cases=results,total_predicates_compared=sum(r['predicates_compared'] for r in results),elapsed_s=time.monotonic()-start,result='PASS')
    Path('economics_problem2/work/structural_rank_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)


if __name__=='__main__':main()
