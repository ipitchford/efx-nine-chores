#!/usr/bin/env python3
"""Exact three-agent EFX nonexistence through unlabelled EFX graphs.

Hall's theorem is used as a different Boolean factorisation, not as a new
existence theorem. Positive, distinct-minimum canonicalisation is justified
in the existing manuscript. Each optional unit-margin constraint is obtained
by common positive scaling of the finitely many strict inequalities.
"""
import argparse
import itertools
import json
import resource
import time
from pathlib import Path
import z3


def partitions(m):
    """Each partition into exactly three nonempty, unlabelled bundles once."""
    def rec(a, largest):
        if len(a) == m:
            if largest == 2:
                masks = [0, 0, 0]
                for g, b in enumerate(a):
                    masks[b] |= 1 << g
                yield tuple(masks)
            return
        for b in range(min(largest + 1, 2) + 1):
            yield from rec(a + [b], max(largest, b))
    yield from rec([0], 0)


def build(m=9, timeout=300, arith=2, mode='hall', margin=False,
          gauge=False, normalise=False, order='descending',
          equivalence=False, max_size=None, proof=False):
    if proof:
        z3.set_param(proof=True)
    s = z3.SolverFor('QF_LRA')
    s.set(timeout=int(timeout * 1000), **{'arith.solver': arith})
    c = [[z3.Real(f'c_{i}_{g}') for g in range(m)] for i in range(3)]
    def pos(x):
        return x >= 1 if margin else x > 0
    for i in range(3):
        s.add(*[pos(c[i][g]) for g in range(m)])
        s.add(*[pos(c[i][g]-c[i][i]) for g in range(m) if g != i])
        if normalise:
            assert not margin
            s.add(z3.Sum(c[i]) == 1)
    if gauge:
        assert not normalise
        s.add(c[0][0] == c[1][1], c[1][1] == c[2][2])
    free = list(range(3, m))
    if order == 'descending':
        free.reverse()
    s.add(*[pos(c[0][b]-c[0][a]) for a,b in zip(free,free[1:])])
    s.add(pos(c[0][2]-c[0][1]))
    domain = len(s.assertions())
    sums = [[z3.RealVal(0)] * (1 << m) for _ in range(3)]
    for i in range(3):
        for mask in range(1, 1 << m):
            bit = mask & -mask
            sums[i][mask] = sums[i][mask ^ bit] + c[i][bit.bit_length()-1]
    atom_cache = {}
    def rejection(i, b, part):
        if b.bit_count() == 1:
            return z3.BoolVal(False)
        if (b >> i) & 1:
            trims = [i]
        elif i == 0:
            trims = [g for g in (1, 2) if (b >> g) & 1]
            if len(trims) == 2:
                trims.pop()
            trims += [g for g in free if (b >> g) & 1][:1]
        else:
            trims = [g for g in range(m) if (b >> g) & 1]
        vals = []
        for other in part:
            if other == b:
                continue
            for g in trims:
                key = i, b ^ (1 << g), other
                if key not in atom_cache:
                    atom_cache[key] = pos(sums[i][key[1]]-sums[i][key[2]])
                vals.append(atom_cache[key])
        return z3.Or(*vals)
    npart = 0
    nb = 0
    for pidx, part in enumerate(partitions(m)):
        if max_size is not None and max(b.bit_count() for b in part) > max_size:
            continue
        npart += 1
        bad = []
        for i in range(3):
            row = []
            for k,b in enumerate(part):
                expr = rejection(i,b,part)
                if z3.is_false(expr) or mode == 'direct-hall':
                    row.append(expr)
                else:
                    bv = z3.Bool(f'bad_{pidx}_{i}_{k}')
                    s.add(bv == expr if equivalence else z3.Implies(bv, expr))
                    row.append(bv)
                    nb += 1
            bad.append(row)
        if mode == 'match':
            for perm in itertools.permutations(range(3)):
                s.add(z3.Or(*[bad[i][perm[i]] for i in range(3)]))
        else:
            # Each agent has an acceptable minimum-total bundle. Thus the
            # singleton-agent Hall obstructions cannot occur. The remaining
            # obstructions are a globally rejected bundle, or two agents
            # restricted to the same single possible bundle.
            terms = [z3.And(*[bad[i][k] for i in range(3)]) for k in range(3)]
            for i,j in itertools.combinations(range(3),2):
                for k in range(3):
                    terms.append(z3.And(*[bad[h][b] for h in (i,j)
                                          for b in range(3) if b != k]))
            s.add(z3.Or(*terms))
    return s,c,dict(m=m,partitions=npart,domain_assertions=domain,
                   auxiliary_booleans=nb,unique_atoms=len(atom_cache),
                   assertions=len(s.assertions()),mode=mode,unit_margin=margin,
                   common_minimum_gauge=gauge,normalise=normalise,
                   equivalence=equivalence,max_size=max_size)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--m',type=int,default=9)
    ap.add_argument('--timeout',type=float,default=300)
    ap.add_argument('--arith',type=int,default=2)
    ap.add_argument('--mode',choices=['hall','direct-hall','match'],default='hall')
    ap.add_argument('--margin',action='store_true')
    ap.add_argument('--gauge',action='store_true')
    ap.add_argument('--normalise',action='store_true')
    ap.add_argument('--equivalence',action='store_true')
    ap.add_argument('--max-size',type=int)
    ap.add_argument('--proof',action='store_true')
    ap.add_argument('--memory-mib',type=int,default=2300)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(args.memory_mib*1024**2,)*2)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    t0=time.monotonic()
    s,c,info=build(args.m,args.timeout,args.arith,args.mode,args.margin,args.gauge,
                   args.normalise,equivalence=args.equivalence,
                   max_size=args.max_size,proof=args.proof)
    info.update(z3_version=z3.get_version_string(),build_seconds=time.monotonic()-t0)
    out.with_suffix('.smt2').write_text(s.sexpr()+'\n(check-sat)\n')
    print(json.dumps({'stage':'built',**info}),flush=True)
    t1=time.monotonic(); status=s.check()
    info.update(status=str(status),check_seconds=time.monotonic()-t1,
                statistics=str(s.statistics()))
    if status == z3.unknown:
        info['reason_unknown']=s.reason_unknown()
    if status == z3.sat:
        model=s.model()
        info['costs']=[[str(model.eval(v,model_completion=True)) for v in row] for row in c]
    if status == z3.unsat and args.proof:
        out.with_suffix('.z3proof').write_text(s.proof().sexpr())
    out.with_suffix('.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info),flush=True)


if __name__ == '__main__':
    main()
