#!/usr/bin/env python3
import argparse,hashlib,json,resource,sys,time
from pathlib import Path
import z3
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
sys.path.insert(0,str(Path(__file__).parent/'exact_search'))
from strict_lra import build
from gauge_solver import transform
from cardinality_cuts import add_triple_cuts

p=argparse.ArgumentParser();p.add_argument('--m',type=int,default=8)
p.add_argument('--timeout',type=int,default=180);p.add_argument('--out',required=True)
p.add_argument('--memory-mib',type=int,default=1800)
a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(a.memory_mib*1024**2,)*2)
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);t=time.monotonic()
old,c,info=build(a.m,timeout=a.timeout,all_trims=False,row_symmetry=True,cuts='pairs')
extra=add_triple_cuts(old,c)
# The common-minimum gauge permits a remaining three-fold agent symmetry:
# row 0 can be chosen to have smallest normalised total.
# Express it after gauge substitution, not on the unnormalised input rows.
subs=[(c[1][1],c[0][0]),(c[2][2],c[0][0])];cache={}
s=z3.SolverFor('QF_LRA');s.set(timeout=a.timeout*1000,**{'arith.solver':2})
for expr in old.assertions():s.add(transform(expr,subs,cache))
s.add(z3.substitute(z3.Sum(c[0])-z3.Sum(c[1]),*subs)<=0,
      z3.substitute(z3.Sum(c[0])-z3.Sum(c[2]),*subs)<=0)
del old
formula=s.sexpr()+'\n(check-sat)\n';out.with_suffix('.smt2').write_text(formula)
info.update(triple_cuts=extra,row0_smallest_normalised_total=True,method='common minimum, unit margins, pairs and balanced protected triples',
            formula_sha256=hashlib.sha256(formula.encode()).hexdigest(),
            build_seconds=time.monotonic()-t)
print(json.dumps({'stage':'built',**info}),flush=True);t=time.monotonic();status=s.check()
info.update(status=str(status),check_seconds=time.monotonic()-t,statistics=str(s.statistics()))
if status==z3.unknown:info['reason_unknown']=s.reason_unknown()
if status==z3.sat:
    mo=s.model();info['costs']=[[str(mo.eval(z3.substitute(v,*subs),model_completion=True)) for v in row] for row in c]
out.with_suffix('.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info),flush=True)
