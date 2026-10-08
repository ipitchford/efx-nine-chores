#!/usr/bin/env python3
"""Necessary counterexample exclusions from cardinality-aware cut-and-choose.

The proof is continuation/structural_nine/cardinality_cut.md.
This file uses only the especially simple sufficient balance 3max <= total,
and global row minima to strengthen the residual-budget premises.
"""
import itertools
import z3


def add_triple_cuts(s,c,margin=False):
    m=len(c[0]);assert m>=7
    totals=[z3.Sum(row) for row in c]
    def gt(a,b):return a-b>=1 if margin else a>b
    count=0
    for k in range(3):
        for pair in itertools.combinations([g for g in range(m) if g!=k],2):
            S=(k,)+pair
            R=[g for g in range(m) if g not in S]
            # This chosen S must be the owner's three cheapest chores.
            not_cheapest=[gt(c[k][g],c[k][h]) for g in pair for h in R]
            for p in range(3):
                if p==k:continue
                q=3-k-p
                sp=z3.Sum(*[c[p][g] for g in S])
                sq=z3.Sum(*[c[q][g] for g in S])
                rp=z3.Sum(*[c[p][g] for g in R])
                s.add(z3.Or(*(not_cheapest+
                    [gt(totals[p],3*sp+c[p][p]),
                     gt(totals[q],3*sq+2*c[q][q])]+
                    [gt(3*c[p][h],rp) for h in R])))
                count+=1
    return count
