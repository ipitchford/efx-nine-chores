import argparse,time,json
from pathlib import Path
import z3
from strict_lra import build
p=argparse.ArgumentParser();p.add_argument('--m',type=int,default=8);p.add_argument('--timeout',type=int,default=900);p.add_argument('--out',default='economics_problem2/results/D8_root');p.add_argument('--proof',action='store_true');p.add_argument('--normalisation',default='none');a=p.parse_args();t0=time.monotonic()
s,c,info=build(a.m,a.timeout,proof=a.proof,normalisation=a.normalisation,row_symmetry=True,all_trims=False,designated=0);t1=time.monotonic()
Path(a.out+'.smt2').write_text(s.sexpr()+'\n(check-sat)\n');print(json.dumps({'stage':'built',**info,'build_s':t1-t0}),flush=True)
r=s.check();info.update(status=str(r),build_s=t1-t0,check_s=time.monotonic()-t1,statistics=str(s.statistics()))
if r==z3.unknown:info['reason_unknown']=s.reason_unknown()
if r==z3.sat:info['costs']=[[str(s.model().eval(x)) for x in row] for row in c]
if r==z3.unsat and a.proof:Path(a.out+'.z3proof').write_text(s.proof().sexpr())
Path(a.out+'.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info),flush=True)
