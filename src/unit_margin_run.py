#!/usr/bin/env python3
import z3,argparse,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--timeout',type=int,default=1800);p.add_argument('--out',required=True);p.add_argument('--proof',action='store_true');p.add_argument('--arith',type=int,default=2);args=p.parse_args()
if args.proof:z3.set_param(proof=True)
t0=time.monotonic();formula=z3.parse_smt2_file(args.input);cache={}
def convert(x):
 k=x.get_id()
 if k in cache:return cache[k]
 if z3.is_gt(x):r=x.arg(0)>=x.arg(1)+1
 elif z3.is_lt(x):r=x.arg(0)+1<=x.arg(1)
 elif z3.is_or(x):r=z3.Or(*[convert(y) for y in x.children()])
 elif z3.is_and(x):r=z3.And(*[convert(y) for y in x.children()])
 else:raise ValueError('Expected positive Boolean combination of homogeneous strict inequalities: '+str(x))
 cache[k]=r;return r
s=z3.SolverFor('QF_LRA');s.set(timeout=args.timeout*1000);s.set('arith.solver',args.arith);s.add(*[convert(a) for a in formula]);t1=time.monotonic()
Path(args.out+'.smt2').write_text(s.sexpr()+'\n(check-sat)\n')
print(json.dumps({'stage':'built','assertions':len(formula),'build_s':t1-t0}),flush=True)
r=s.check();info={'input':args.input,'encoding':'homogeneous-strict-to-unit-margin','solver':'z3-'+z3.get_version_string(),'status':str(r),'build_s':t1-t0,'check_s':time.monotonic()-t1,'statistics':str(s.statistics())}
if r==z3.unknown:info['reason_unknown']=s.reason_unknown()
if r==z3.sat:info['model']=str(s.model())
if r==z3.unsat and args.proof:Path(args.out+'.z3proof').write_text(s.proof().sexpr())
Path(args.out+'.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info),flush=True)
