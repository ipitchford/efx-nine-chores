#!/usr/bin/env python3
"""Bounded nine-chore cases with all second minima among other pinned minima.
This covers only a subclass unless D8 is separately proved. No conditional
premise is assumed by any SMT file exported here.
"""
import argparse,json,time,resource
from pathlib import Path
import z3
from strict_lra import build
p=argparse.ArgumentParser();p.add_argument('--timeout',type=int,default=45);p.add_argument('--out',default='economics_problem2/results/second_min_cases');args=p.parse_args()
resource.setrlimit(resource.RLIMIT_AS,(2200*1024**2,resource.RLIM_INFINITY))
out=Path(args.out);out.mkdir(parents=True,exist_ok=True);records=[]
for graph,second in [('cycle',(1,2,0)),('tail',(1,0,0))]:
 for rank in range(1,8):
  start=time.monotonic();s,c,info=build(9,timeout=args.timeout,arith=2,all_trims=False,cuts='pairs',dominance=True,rank_case=(0,rank))
  for i in range(3):
   s.add(*[c[i][second[i]]<c[i][g] for g in range(9) if g not in (i,second[i])])
  prefix=out/f'{graph}_{rank}';Path(str(prefix)+'.smt2').write_text(s.sexpr()+'\n(check-sat)\n')
  t=time.monotonic();status=s.check();record={**info,'second_minima':second,'graph':graph,'rank':rank,'status':str(status),'build_s':t-start,'check_s':time.monotonic()-t,'scope':'only this second-minimum graph and row-0 rank cone; D8 not assumed'}
  if status==z3.unknown:record['reason_unknown']=s.reason_unknown()
  if status==z3.sat:record['costs']=[[str(s.model().eval(v,model_completion=True)) for v in row] for row in c]
  Path(str(prefix)+'.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
  (out/'summary.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(record),flush=True)
