import argparse,time,json
from pathlib import Path
import z3
from strict_lra import build
p=argparse.ArgumentParser();p.add_argument('--m',type=int,default=9);p.add_argument('--timeout',type=int,default=1800);p.add_argument('--out',default='economics_problem2/results/root9_cuts');p.add_argument('--case',nargs=2,type=int);p.add_argument('--proof',action='store_true');p.add_argument('--normalisation',default='none');args=p.parse_args()
t0=time.monotonic()
s,c,info=build(args.m,args.timeout,proof=args.proof,normalisation=args.normalisation,row_symmetry=True,rank_case=args.case,all_trims=False,cuts='pairs')
t1=time.monotonic();print(json.dumps({'stage':'built',**info,'build_s':t1-t0}),flush=True)
Path(args.out+'.smt2').write_text(s.sexpr()+'\n(check-sat)\n')
r=s.check();info.update(status=str(r),check_s=time.monotonic()-t1,build_s=t1-t0,statistics=str(s.statistics()),solver='z3-'+z3.get_version_string())
if r==z3.unknown:info['reason_unknown']=s.reason_unknown()
if r==z3.sat:info['costs']=[[str(s.model().eval(x)) for x in row] for row in c]
if r==z3.unsat and args.proof:Path(args.out+'.z3proof').write_text(s.proof().sexpr())
Path(args.out+'.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info),flush=True)
