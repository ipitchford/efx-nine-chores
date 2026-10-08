#!/usr/bin/env python3
"""Finite independent semantic audit of a fixed-minimum strict static formula.

The parser is Z3; there are no solver calls. Literal EFX is recomputed using
plain Python sums and every owned-chore deletion. This is an encoder audit,
not a universal theorem or independent UNSAT certificate.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
import z3

PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT/'src'))
from verify_encoding import compiled_allocation_clauses
from efx_exact import efx


def canonical(rows):
    m=len(rows[0])
    first=min(range(3),key=lambda i:sum(rows[i]))
    agents=[first]+[i for i in range(3) if i!=first]
    columns=agents+list(range(3,m))
    rows=[[rows[i][g] for g in columns] for i in agents]
    if rows[0][1]>rows[0][2]:
        rows=[rows[0],rows[2],rows[1]]
        for row in rows:row[1],row[2]=row[2],row[1]
    columns=list(range(3))+sorted(range(3,m),key=lambda g:rows[0][g],reverse=True)
    return [[row[g] for g in columns] for row in rows]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path)
    ap.add_argument('--m',type=int,default=9)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--matrices',type=int,default=12)
    args=ap.parse_args()
    started=time.monotonic();m=args.m
    assertions=z3.parse_smt2_file(str(args.input))
    clauses=[a for a in assertions if z3.is_or(a)]
    assert len(clauses)==3**m-3*2**m+3
    domain=[a for a in assertions if not z3.is_or(a)]
    temporary=args.out.with_suffix('.allocation_clauses.smt2')
    holder=z3.Solver();holder.add(*clauses);temporary.write_text(holder.to_smt2())
    coefficients,indices=compiled_allocation_clauses(temporary,m)
    assignments=[a for a in itertools.product(range(3),repeat=m) if len(set(a))==3]
    rng=random.Random(845193)
    matrices=[[[1]*m for _ in range(3)]]
    for k in range(args.matrices-1):
        rows=[rng.sample(range(2,500),m) for _ in range(3)]
        for i in range(3):rows[i][i]=1
        matrices.append(canonical(rows))
    variables=[z3.Real(f'c_{i}_{g}') for i in range(3) for g in range(m)]
    counts=[];canonical_count=0
    for k,rows in enumerate(matrices):
        values=[x for row in rows for x in row]
        vector=np.array(values+[1],dtype=np.int64)
        assert int(np.max(np.abs(vector)))*int(np.max(np.sum(np.abs(coefficients),axis=1)))<2**62
        forbidden=(coefficients@vector>0)[indices].any(axis=1)
        literal=np.array([not efx(rows,a) for a in assignments])
        bad=np.flatnonzero(forbidden!=literal)
        assert len(bad)==0,(k,bad[:10].tolist())
        if k:
            subst=list(zip(variables,map(z3.RealVal,values)))
            assert all(z3.is_true(z3.simplify(z3.substitute(a,*subst))) for a in domain)
            canonical_count+=1
        counts.append(int(np.sum(~literal)))
    if m==9:assert counts[0]==1680
    record=dict(input=str(args.input.resolve()),input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                clauses=len(clauses),domain_assertions=len(domain),matrices=len(matrices),
                canonical_generic_matrices=canonical_count,
                allocation_comparisons=len(matrices)*len(assignments),mismatches=0,
                efx_counts=counts,all_domain_assertions_verified_on_generic_samples=True,
                elapsed_seconds=time.monotonic()-started,
                scope='finite encoding audit; not an UNSAT proof')
    args.out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)


if __name__=='__main__':main()
