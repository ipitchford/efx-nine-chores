#!/usr/bin/env python3
"""Orient all nontrivial linear comparisons and exclude their equality hyperplanes.
This is an equisatisfiable dense-cell reduction for open counterexample sets,
not pointwise equivalence at matrices lying on comparison hyperplanes.
"""
import z3,argparse,time,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--m',type=int,required=True);p.add_argument('--timeout',type=int,default=600);p.add_argument('--out',required=True);p.add_argument('--proof',action='store_true');p.add_argument('--arith',type=int,default=2);a=p.parse_args()
if a.proof:z3.set_param(proof=True)
t0=time.monotonic();forms=z3.parse_smt2_file(a.input);xs=[z3.Real(f'c_{i}_{g}') for i in range(3) for g in range(a.m)];dim=len(xs);ids={v.get_id():k for k,v in enumerate(xs)};lc={};atoms={};signs=[];defs=[]
def lin(e):
 k=e.get_id()
 if k in lc:return lc[k]
 v=[0]*dim
 if k in ids:v[ids[k]]=1
 elif z3.is_rational_value(e):assert e.numerator_as_long()==0
 elif z3.is_add(e):
  for b in e.children():v=[x+y for x,y in zip(v,lin(b))]
 elif z3.is_sub(e):
  v=list(lin(e.arg(0)))
  for b in e.children()[1:]:v=[x-y for x,y in zip(v,lin(b))]
 elif z3.is_mul(e):
  cs=[b for b in e.children() if z3.is_rational_value(b)];vs=[b for b in e.children() if not z3.is_rational_value(b)];assert len(vs)==1
  mul=1
  for b in cs:assert b.denominator_as_long()==1;mul*=b.numerator_as_long()
  v=[mul*x for x in lin(vs[0])]
 elif z3.is_uminus(e):v=[-x for x in lin(e.arg(0))]
 else:raise ValueError(str(e))
 lc[k]=tuple(v);return lc[k]
def convert(e):
 if z3.is_or(e):return z3.Or(*[convert(b) for b in e.children()])
 if z3.is_and(e):return z3.And(*[convert(b) for b in e.children()])
 assert z3.is_gt(e) or z3.is_lt(e)
 v=[x-y for x,y in zip(lin(e.arg(0)),lin(e.arg(1)))]
 if z3.is_lt(e):v=[-x for x in v]
 if not any(v):return z3.BoolVal(False)
 d=math.gcd(*v);v=[x//d for x in v];sgn=next(x for x in v if x)
 if sgn<0:v=[-x for x in v]
 key=tuple(v)
 if key not in atoms:
  b=z3.Bool(f'b{len(atoms)}');atoms[key]=b;terms=[x if vj==1 else -x if vj==-1 else vj*x for x,vj in zip(xs,v) if vj];f=z3.Sum(terms)
  defs.extend([z3.Or(z3.Not(b),f>=1),z3.Or(b,f<=-1)])
 return atoms[key] if sgn>0 else z3.Not(atoms[key])
bforms=[convert(f) for f in forms]
s=z3.SolverFor('QF_LRA');s.set(timeout=a.timeout*1000);s.set('arith.solver',a.arith);s.add(*defs,*bforms);t1=time.monotonic()
Path(a.out+'.smt2').write_text(s.sexpr()+'\n(check-sat)\n')
print(json.dumps({'stage':'built','source_assertions':len(forms),'sign_atoms':len(atoms),'assertions':len(s.assertions()),'build_s':t1-t0}),flush=True)
r=s.check();rec={'input':a.input,'scope':'generic nonzero comparison cells','m':a.m,'status':str(r),'sign_atoms':len(atoms),'check_s':time.monotonic()-t1,'build_s':t1-t0,'statistics':str(s.statistics())}
if r==z3.unknown:rec['reason_unknown']=s.reason_unknown()
if r==z3.sat:rec['costs']=[[str(s.model().eval(xs[i*a.m+g])) for g in range(a.m)] for i in range(3)]
if r==z3.unsat and a.proof:Path(a.out+'.z3proof').write_text(s.proof().sexpr())
Path(a.out+'.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True)
