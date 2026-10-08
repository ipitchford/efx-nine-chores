#!/usr/bin/env python3
"""Exact EFX nonexistence encoding on the dense generic disjoint-minimum class.
The model is always QF_LRA, never a bounded integer enumeration.
See manuscript for the strict perturbation and relabelling reductions.
"""
import argparse,itertools,json,time,sys
from pathlib import Path
import z3


def build(m,timeout=3600,arith=2,proof=False,normalisation='none',order='descending',row_symmetry=False,rank_case=None,all_trims=True,cuts='none',dominance=False,designated=None):
    if proof:z3.set_param(proof=True)
    s=z3.SolverFor('QF_LRA');s.set(timeout=timeout*1000);s.set('arith.solver',arith)
    c=[[z3.Real(f'c_{i}_{g}') for g in range(m)] for i in range(3)]
    for i in range(3):
        s.add(*[c[i][g]>0 for g in range(m)])
        s.add(*[c[i][g]>c[i][i] for g in range(m) if g!=i])
        if normalisation=='sum':s.add(z3.Sum(c[i])==1)
        elif normalisation=='min':s.add(c[i][i]==1)
    totals=[z3.Sum(row) for row in c]
    cut_count=0
    if cuts!='none':
        # Necessary conditions from protected-bundle cut-and-choose theorem.
        # The global minimum is a lower bound on the remainder minimum.
        for g in range(m):
            for p in range(3):
                for q in range(3):
                    if p==q:continue
                    s.add(z3.Or(3*c[p][g]+c[p][p]<totals[p],3*c[q][g]+2*c[q][q]<totals[q]));cut_count+=1
    if cuts=='pairs':
        for k in range(3):
            p,q=[i for i in range(3) if i!=k]
            for h in range(m):
                if h==k:continue
                not_second=[c[k][t]<c[k][h] for t in range(m) if t not in (k,h)]
                sp=c[p][k]+c[p][h];sq=c[q][k]+c[q][h]
                s.add(z3.Or(*(not_second+[3*sp+c[p][p]<totals[p],3*sq+2*c[q][q]<totals[q]])));cut_count+=1
                s.add(z3.Or(*(not_second+[3*sp+2*c[p][p]<totals[p],3*sq+c[q][q]<totals[q]])));cut_count+=1
    ordered=list(range(3,m))
    if order=='descending':ordered=ordered[::-1]
    if rank_case is None:
        s.add(*[c[0][a]<c[0][b] for a,b in zip(ordered,ordered[1:])])
        if row_symmetry:s.add(c[0][1]<c[0][2])
    else:
        ranks=[None]*(m-1)
        ranks[rank_case[0]]=1;ranks[rank_case[1]]=2
        it=iter(ordered)
        ranks=[next(it) if x is None else x for x in ranks]
        ranks=[0]+ranks
        s.add(*[c[0][a]<c[0][b] for a,b in zip(ranks,ranks[1:])])
    sums=[[z3.RealVal(0)]*(1<<m) for i in range(3)]
    for i in range(3):
        for mask in range(1,1<<m):
            bit=mask&-mask;g=bit.bit_length()-1
            sums[i][mask]=sums[i][mask^bit]+c[i][g]
    clauses=0;positions=0;atom_cache={};automatically_bad=0;dominated_atoms=0
    rank0={g:k for k,g in enumerate(ranks)} if rank_case is not None else None
    def order_implies_less(left,right,i):
        # Costs are strictly positive and pinned minima are unique.
        # With a complete row-0 order, inject the lower-cost items into the
        # higher-cost items. Disjointness makes matched inequalities strict.
        ls=[g for g in range(m) if left>>g&1];rs=[g for g in range(m) if right>>g&1]
        if not ls:return bool(rs)
        if len(ls)>len(rs):return False
        if len(ls)==1 and ls[0]==i:return bool(rs)
        if i==0 and rank0 is not None:
            lrank=sorted((rank0[g] for g in ls),reverse=True)
            rrank=sorted((rank0[g] for g in rs),reverse=True)
            return all(u<v for u,v in zip(lrank,rrank))
        return False
    for a in itertools.product(range(3),repeat=m):
        masks=[0,0,0]
        for g,i in enumerate(a):masks[i]|=1<<g
        if not all(masks):continue # positive costs and m>3 => these fail automatically
        vs=[];auto_bad=False
        for i in range(3):
            own=masks[i]
            if i!=designated and own.bit_count()<2:continue
            trims=[g for g in range(m) if own>>g&1]
            if i==designated:trims=[None]
            elif not all_trims:
                if own>>i&1:trims=[i]
                elif i==0:
                    if rank_case is not None:trims=[next(g for g in ranks if own>>g&1)]
                    else:
                        t=[g for g in ordered if own>>g&1]
                        trims=[g for g in (1,2) if own>>g&1]+t[:1]
                        if row_symmetry and 1 in trims and 2 in trims:trims.remove(2)
            for j in range(3):
                if j==i:continue
                for g in trims:
                    key=(i,own if g is None else own^(1<<g),masks[j])
                    if dominance:
                        if order_implies_less(key[2],key[1],i):
                            auto_bad=True;break
                        if order_implies_less(key[1],key[2],i):
                            dominated_atoms+=1;continue
                    if key not in atom_cache:
                        atom_cache[key]=sums[i][key[1]]>sums[i][key[2]]
                    vs.append(atom_cache[key])
                if auto_bad:break
            if auto_bad:break
        if auto_bad:
            automatically_bad+=1;continue
        s.add(z3.Or(*vs));clauses+=1;positions+=len(vs)
    info={'m':m,'allocations_all':3**m,'allocation_clauses':clauses,'literal_positions':positions,'unique_atoms':len(atom_cache),'assertions':len(s.assertions()),'normalisation':normalisation,'order':order,'row_symmetry':row_symmetry,'rank_case':rank_case,'all_trims':all_trims,'cuts':cuts,'cut_count':cut_count,'dominance':dominance,'automatically_bad':automatically_bad,'dominated_atoms':dominated_atoms,'designated':designated}
    return s,c,info


def main():
    p=argparse.ArgumentParser();p.add_argument('--m',type=int,default=9);p.add_argument('--timeout',type=int,default=3600);p.add_argument('--arith',type=int,default=2);p.add_argument('--proof',action='store_true');p.add_argument('--normalisation',choices=['none','sum','min'],default='none');p.add_argument('--order',choices=['ascending','descending'],default='descending');p.add_argument('--row-symmetry',action='store_true');p.add_argument('--rank-case',type=int,nargs=2);p.add_argument('--prune',action='store_true');p.add_argument('--out',default='economics_problem2/results/root9');p.add_argument('--export',action='store_true');args=p.parse_args()
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    s,c,info=build(args.m,args.timeout,args.arith,args.proof,args.normalisation,args.order,args.row_symmetry,args.rank_case,not args.prune)
    built=time.monotonic();info.update(solver='z3-'+z3.get_version_string(),build_s=built-start,arith=args.arith)
    print(json.dumps({'stage':'built',**info}),flush=True)
    if args.export:Path(str(out)+'.smt2').write_text(s.sexpr()+'\n(check-sat)\n')
    status=s.check();end=time.monotonic();info.update(status=str(status),check_s=end-built,statistics=str(s.statistics()))
    if status==z3.unknown:info['reason_unknown']=s.reason_unknown()
    if status==z3.sat:
        model=s.model();info['costs']=[[str(model.eval(x,model_completion=True)) for x in row] for row in c]
    if status==z3.unsat and args.proof:
        Path(str(out)+'.z3proof').write_text(s.proof().sexpr())
    Path(str(out)+'.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info),flush=True)
if __name__=='__main__':main()
