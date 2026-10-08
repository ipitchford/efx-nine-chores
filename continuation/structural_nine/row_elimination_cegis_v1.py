#!/usr/bin/env python3
"""Exact two-row chamber CEGIS for three-agent nine-chore EFX.

Rows1,2 form the outer problem; the first row is universally eliminated by
an inner QF_LRA check. Each successful inner UNSAT core provides a sufficient
region preserving every deletion inequality for rows1,2 on its allocations.
All inequalities use exact arithmetic. No unknown verdict yields a region.
"""
import argparse
import hashlib
import itertools
import json
from math import gcd,lcm
from pathlib import Path
import resource
import time

p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,required=True)
p.add_argument('--seconds',type=int,default=900)
p.add_argument('--iterations',type=int,default=10000)
p.add_argument('--memory-mib',type=int,default=1450)
p.add_argument('--outer-timeout',type=int,default=90000)
p.add_argument('--inner-timeout',type=int,default=15000)
p.add_argument('--seed-robust',action='store_true')
p.add_argument('--order',choices=['ascending','descending'],default='descending')
args=p.parse_args()
resource.setrlimit(resource.RLIMIT_AS,(args.memory_mib*1024**2,)*2)
import numpy as np
import z3

OUT=args.out;OUT.mkdir(parents=True,exist_ok=True)
(OUT/'regions').mkdir(exist_ok=True);(OUT/'inner').mkdir(exist_ok=True)
START=time.monotonic();DEADLINE=START+args.seconds
M=9;ALL=(1<<M)-1
free=list(range(3,M)) if args.order=='ascending' else list(reversed(range(3,M)))
ROWS=[[z3.Real(f'c_{i}_{g}') for g in range(M)] for i in (1,2)]
FIRST=[z3.Real(f'c_0_{g}') for g in range(M)]
SUBSETS=[[g for g in range(M) if mask>>g&1] for mask in range(1<<M)]
SUMS=[[z3.Sum([row[g] for g in subset]) for subset in SUBSETS] for row in [FIRST]+ROWS]
ALLOCS=[];MASKS=[];ALLOC_IDS=[]
for aid,a in enumerate(itertools.product(range(3),repeat=M)):
    masks=[sum(1<<g for g in range(M) if a[g]==i) for i in range(3)]
    if all(masks):ALLOCS.append(a);MASKS.append(masks);ALLOC_IDS.append(aid)
MASK_ARRAY=np.asarray(MASKS,dtype=np.int64)
ID_TO_INDEX={aid:k for k,aid in enumerate(ALLOC_IDS)}
FIRST_DOMAIN=[FIRST[0]==1]+[FIRST[g]>1 for g in range(1,M)]+[FIRST[1]<FIRST[2]]
FIRST_DOMAIN += [FIRST[a]<FIRST[b] for a,b in zip(free,free[1:])]
outer=z3.SolverFor('QF_LRA');outer.set(**{'arith.solver':2})
OUTER_DOMAIN=[]
for i,row in enumerate(ROWS,1):
    OUTER_DOMAIN += [row[i]==1]+[row[g]>1 for g in range(M) if g!=i]
outer.add(*OUTER_DOMAIN)
bad_first_cache={};region_cache={}

def bad_first(index):
    if index not in bad_first_cache:
        masks=MASKS[index];own=masks[0]
        bad_first_cache[index]=z3.Or(*[SUMS[0][own]-FIRST[g]>SUMS[0][masks[j]]
                                      for g in SUBSETS[own] for j in (1,2)])
    return bad_first_cache[index]

def region_atoms(indices):
    """All exact EFX inequalities, deduplicated by row and coefficient vector."""
    keys={}
    for index in indices:
        masks=MASKS[index]
        for i in (1,2):
            for g in SUBSETS[masks[i]]:
                for j in range(3):
                    if i==j:continue
                    coeff=tuple(int(bool(masks[i]>>h&1))-int(h==g)-int(bool(masks[j]>>h&1)) for h in range(M))
                    key=(i,coeff)
                    # Coefficients with no positive entry are already <=0
                    # for nonnegative costs. The archived raw count records
                    # this harmless domain-based removal separately.
                    if not any(v>0 for v in coeff):continue
                    keys[key]=(i,coeff)
    atoms=[]
    for key,(i,coeff) in sorted(keys.items()):
        if key not in region_cache:
            region_cache[key]=z3.Sum([v*ROWS[i-1][g] for g,v in enumerate(coeff) if v])
        atoms.append((i,coeff,region_cache[key]))
    return atoms

def integer_row(model,row):
    vals=[model.eval(v,model_completion=True) for v in row]
    scale=lcm(*(v.denominator_as_long() for v in vals))
    result=[v.numerator_as_long()*(scale//v.denominator_as_long()) for v in vals]
    d=gcd(*result)
    return [v//d for v in result]

def fixed_compatible(rows):
    sums=[];res=[]
    for row in rows:
        ss=[0]*(1<<M);mn=[0]*(1<<M)
        for mask in range(1,1<<M):
            b=mask&-mask;g=b.bit_length()-1;prev=mask^b
            ss[mask]=ss[prev]+row[g];mn[mask]=min(mn[prev],row[g]) if prev else row[g]
        sums.append(ss);res.append([ss[k]-mn[k] for k in range(1<<M)])
    if max(map(max,sums))<(1<<62):
        good=np.ones(len(MASKS),dtype=bool)
        for ridx,i in enumerate((1,2)):
            ss=np.asarray(sums[ridx],dtype=np.int64);rr=np.asarray(res[ridx],dtype=np.int64)
            for j in range(3):
                if i!=j:good &= rr[MASK_ARRAY[:,i]]<=ss[MASK_ARRAY[:,j]]
        return np.flatnonzero(good).tolist()
    return [a for a,masks in enumerate(MASKS) if all(res[ridx][masks[i]]<=sums[ridx][masks[j]] for ridx,i in enumerate((1,2)) for j in range(3) if i!=j)]

def literal_full(C):
    count=0;first=None
    for a in itertools.product(range(3),repeat=M):
        A=[[g for g in range(M) if a[g]==i] for i in range(3)]
        ok=all(sum(C[i][h] for h in A[i] if h!=g)<=sum(C[i][h] for h in A[j])
               for i in range(3) for g in A[i] for j in range(3))
        if ok:
            count+=1
            if first is None:first=a
    return count,first

def robust_first_indices():
    orders=[]
    for r1,r2 in itertools.combinations(range(1,M),2):
        order=[None]*M;order[0]=0;order[r1]=1;order[r2]=2
        it=iter(free)
        for pos in range(1,M):
            if order[pos] is None:order[pos]=next(it)
        rank={g:r for r,g in enumerate(order)};orders.append(rank)
    answer=[]
    for index,masks in enumerate(MASKS):
        own=SUBSETS[masks[0]]
        good=True
        for rank in orders:
            residual=sorted((rank[g] for g in own),reverse=True)[:-1]
            for j in (1,2):
                target=sorted((rank[g] for g in SUBSETS[masks[j]]),reverse=True)
                if len(residual)>len(target) or any(a>b for a,b in zip(residual,target)):
                    good=False;break
            if not good:break
        if good:answer.append(index)
    return answer

def save_outer():
    text=outer.sexpr()+'\n(check-sat)\n';(OUT/'outer.smt2').write_text(text)
    return hashlib.sha256(text.encode()).hexdigest()

history=[];termination=None
if args.seed_robust:
    seed_start=time.monotonic();robust=robust_first_indices()
    for index in robust:
        atoms=region_atoms([index]);outer.add(z3.Or(*[expr>0 for _,_,expr in atoms]))
    (OUT/'robust_seed.json').write_text(json.dumps(dict(order=args.order,full_orders=28,
        allocation_ids=[ALLOC_IDS[index] for index in robust],allocations=[ALLOCS[index] for index in robust]),indent=2))
    print(json.dumps(dict(stage='robust_seed',count=len(robust),seconds=time.monotonic()-seed_start)),flush=True)

for iteration in range(args.iterations):
    remaining=DEADLINE-time.monotonic()
    if remaining<=0:termination='deadline';break
    outer.set(timeout=min(args.outer_timeout,int(remaining*1000)))
    t=time.monotonic();outer_status=outer.check();outer_seconds=time.monotonic()-t
    if outer_status!=z3.sat:
        termination='outer_'+str(outer_status)
        rec=dict(iteration=iteration,status=str(outer_status),outer_seconds=outer_seconds)
        if outer_status==z3.unknown:rec['reason']=outer.reason_unknown()
        history.append(rec);print(json.dumps(rec),flush=True);break
    model=outer.model();rows=[integer_row(model,row) for row in ROWS]
    compatible=fixed_compatible(rows)
    inner=z3.SolverFor('QF_LRA');inner.set(**{'arith.solver':2});inner.set(unsat_core=True)
    remaining=DEADLINE-time.monotonic()
    inner.set(timeout=max(1,min(args.inner_timeout,int(remaining*1000))))
    inner.add(*FIRST_DOMAIN)
    for index in compatible:inner.assert_and_track(bad_first(index),f'a_{ALLOC_IDS[index]}')
    t=time.monotonic();status=inner.check();inner_seconds=time.monotonic()-t
    rec=dict(iteration=iteration,outer_seconds=outer_seconds,inner_seconds=inner_seconds,
             compatible_allocations=len(compatible),status=str(status),other_rows=rows)
    if status==z3.unsat:
        ids=[int(str(a).split('_')[1]) for a in inner.unsat_core()]
        indices=[ID_TO_INDEX[aid] for aid in ids]
        assert all(index in compatible for index in indices)
        core=z3.SolverFor('QF_LRA');core.add(*FIRST_DOMAIN)
        core.add(*(bad_first(index) for index in indices))
        core_text=core.sexpr()+'\n(check-sat)\n'
        core_file=OUT/'inner'/f'{iteration:05d}.smt2';core_file.write_text(core_text)
        atoms=region_atoms(indices)
        # At the sampled model every archived premise must hold exactly.
        assert all(sum(v*rows[i-1][g] for g,v in enumerate(coeff))<=0 for i,coeff,_ in atoms)
        outer.add(z3.Or(*[expr>0 for _,_,expr in atoms]))
        rec.update(core_size=len(ids),core_allocation_ids=ids,
                   core_allocations=[ALLOCS[index] for index in indices],
                   region_atoms=[dict(agent=i,coefficients=coeff) for i,coeff,_ in atoms],
                   core_sha256=hashlib.sha256(core_text.encode()).hexdigest())
        (OUT/'regions'/f'{iteration:05d}.json').write_text(json.dumps(rec,indent=2))
        print(json.dumps({k:v for k,v in rec.items() if k not in ('other_rows','core_allocations','core_allocation_ids','region_atoms','core_sha256')}|dict(region_atoms=len(atoms),elapsed=time.monotonic()-START)),flush=True)
    elif status==z3.sat:
        first=integer_row(inner.model(),FIRST);C=[first]+rows
        count,witness=literal_full(C)
        rec.update(matrix=C,full_exact_efx_count=count,first_efx=witness,allocations_checked=3**M)
        assert count==0, 'An inner SAT model failed the independent full allocation check'
        (OUT/'counterexample.json').write_text(json.dumps(rec,indent=2))
        termination='verified_counterexample';print(json.dumps(rec),flush=True)
    else:
        rec['reason']=inner.reason_unknown();termination='inner_unknown';print(json.dumps(rec),flush=True)
    history.append(rec)
    (OUT/'history.json').write_text(json.dumps(history,indent=2))
    if iteration%25==0:save_outer()
    if status!=z3.unsat:break
    del inner
else:termination='iteration_limit'

sha=save_outer()
(OUT/'history.json').write_text(json.dumps(history,indent=2))
summary=dict(termination=termination,regions=sum(h['status']=='unsat' and 'core_size' in h for h in history),
             seconds=time.monotonic()-START,outer_sha256=sha,
             max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             solver=z3.get_version_string(),args={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
             status_scope='Exploratory exact solver record; no externally checked proof is implied by raw UNSAT')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
