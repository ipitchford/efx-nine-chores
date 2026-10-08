#!/usr/bin/env python3
"""Heuristic counterexample search by crossing current EFX boundaries.

All candidates are positive integer matrices. Floating point is used only
for acceptance probabilities. Every recorded count is an integer comparison
over all18150 surjective allocations; final best candidates also use an
independent literal all19683-allocation implementation below.
"""
import argparse
from collections import Counter
import itertools
import json
import math
from pathlib import Path
import random
import time

import numpy as np


def literal_full(rows):
    good=[]
    for owners in itertools.product(range(3),repeat=9):
        bundles=[[g for g in range(9) if owners[g]==i] for i in range(3)]
        if all(sum(rows[i][h] for h in bundles[i] if h!=g)<=sum(rows[i][h] for h in bundles[j])
               for i in range(3) for j in range(3) if i!=j for g in bundles[i]):
            good.append([sum(1<<g for g in b) for b in bundles])
    return good


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=300)
    ap.add_argument('--seed',type=int,default=173)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(args.seed)
    bits=((np.arange(512)[:,None]>>np.arange(9))&1).astype(np.int64)
    alloc=[]
    for a in range(1,511):
        r=511^a;b=r
        while b:
            if r^b:alloc.append((a,b,r^b))
            b=(b-1)&r
    alloc=np.asarray(alloc,dtype=np.int64)
    row_index=np.arange(3)[:,None]
    others=((1,2),(0,2),(0,1))
    def row_info(row,i):
        sums=bits@row
        mins=np.min(np.where(bits,row,2**60),axis=1)
        residual=sums-mins;residual[0]=0
        valid=residual[alloc[:,i]]<=np.minimum(sums[alloc[:,others[i][0]]],sums[alloc[:,others[i][1]]])
        return sums,residual,valid
    raw=json.loads(args.input.read_text())
    if isinstance(raw,dict):raw=raw['rows']
    seed=np.asarray(raw,dtype=np.int64)
    def initialise(rows):
        infos=[row_info(rows[i],i) for i in range(3)]
        return np.array([x[0] for x in infos]),np.array([x[1] for x in infos]),np.array([x[2] for x in infos])
    rows=seed.copy();sums,residual,valid=initialise(rows)
    good=np.flatnonzero(np.all(valid,axis=0));count=len(good)
    best=count;best_rows=rows.copy();started=time.monotonic();last_improvement=0
    visits=Counter();history=[];attempts=0;accepted=0;restart=0
    def save(iteration):
        actual=literal_full(best_rows.tolist())
        assert len(actual)==best
        record=dict(rows=best_rows.tolist(),efx_count=best,efx_allocations=actual,
                    iteration=iteration,elapsed_seconds=time.monotonic()-started,
                    all_allocations_checked=19683,exact_integer_comparisons=True)
        (args.out/'best.json').write_text(json.dumps(record,indent=2)+'\n')
        history.append({k:v for k,v in record.items() if k not in ('rows','efx_allocations')})
        (args.out/'history.json').write_text(json.dumps(history,indent=2)+'\n')
        print(json.dumps(history[-1]),flush=True)
    save(0)
    while time.monotonic()-started<args.seconds and best:
        attempts+=1
        if attempts-last_improvement>2500:
            restart+=1
            base=best_rows if restart%5 else seed
            sigma=[0.01,0.03,0.1,0.3,0.7][restart%5]
            rows=np.maximum(1,np.array([[round(x*math.exp(rng.gauss(0,sigma))) for x in row] for row in base],dtype=np.int64))
            sums,residual,valid=initialise(rows);good=np.flatnonzero(np.all(valid,axis=0));count=len(good)
            last_improvement=attempts;visits.clear()
        if not len(good):
            best=0;best_rows=rows.copy();save(attempts);break
        a=alloc[rng.choice(good)]
        mutations=[]
        for i in range(3):
            own=[g for g in range(9) if a[i]>>g&1]
            if len(own)<2:continue
            removed=min(own,key=lambda g:rows[i,g])
            for j in others[i]:
                delta=int(sums[i,a[j]]-residual[i,a[i]])+1
                assert delta>=1
                for g in own:
                    if g!=removed and rows[i,g]+delta<10**9:mutations.append((i,g,delta))
                for g in range(9):
                    if a[j]>>g&1 and rows[i,g]>delta:mutations.append((i,g,-delta))
        rng.shuffle(mutations)
        candidates=[]
        for i,g,delta in mutations[:8]:
            row=rows[i].copy();row[g]+=delta
            ss,rr,vv=row_info(row,i)
            gv=vv&valid[others[i][0]]&valid[others[i][1]]
            nc=int(np.count_nonzero(gv));ng=np.flatnonzero(gv)
            key=(i,g,int(row[g]),nc)
            score=nc+min(visits[key],10)*0.2+rng.random()*0.05
            candidates.append((score,nc,i,g,row,ss,rr,vv,ng,key))
        if not candidates:continue
        selected=min(candidates,key=lambda x:x[0])
        _,nc,i,g,row,ss,rr,vv,ng,key=selected
        temperature=[0.05,0.3,1,2,4][(attempts//500)%5]
        if nc<=count or rng.random()<math.exp((count-nc)/temperature):
            visits[key]+=1;accepted+=1
            rows[i]=row;sums[i]=ss;residual[i]=rr;valid[i]=vv;good=ng;count=nc
            if count<best:
                best=count;best_rows=rows.copy();last_improvement=attempts;save(attempts)
        if attempts%1000==0:
            print(json.dumps(dict(attempts=attempts,accepted=accepted,best=best,current=count,restarts=restart,elapsed=time.monotonic()-started)),flush=True)
    (args.out/'receipt.json').write_text(json.dumps(dict(seed=args.seed,attempts=attempts,accepted=accepted,restarts=restart,best=best,elapsed_seconds=time.monotonic()-started,status='counterexample' if not best else 'heuristic completed; no counterexample'),indent=2)+'\n')


if __name__=='__main__':main()
