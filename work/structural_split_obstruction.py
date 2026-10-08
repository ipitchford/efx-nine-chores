"""Exact 3-variable search after splitting one fixed eight-chore column in two."""
from itertools import product
from pathlib import Path
import argparse,json,time
import z3


def solve(C,h,timeout):
    start=time.monotonic();x=[z3.Real(f'split_{i}') for i in range(3)]
    s=z3.SolverFor('QF_LRA');s.set(timeout=1000*timeout);s.set('arith.solver',2)
    for i in range(3):s.add(x[i]>=0,x[i]<=C[i][h])
    count=0
    for a in product(range(3),repeat=9):
        bundles=[[g for g in range(9) if a[g]==i] for i in range(3)]
        cost=[[sum(C[i][g] for g in bundles[j] if g<8) for j in range(3)] for i in range(3)]
        delta=[int(a[8]==j)-int(a[h]==j) for j in range(3)]
        bad=[];trivial=False
        for i in range(3):
            for g in bundles[i]:
                for j in range(3):
                    if j==i:continue
                    constant=cost[i][i]-(C[i][g] if g<8 else 0)-cost[i][j]
                    coefficient=delta[i]-(int(g==8)-int(g==h))-delta[j]
                    if coefficient==0:
                        if constant>0:trivial=True;break
                    else:bad.append(coefficient*x[i]+constant>0)
                if trivial:break
            if trivial:break
        if not trivial:s.add(z3.Or(bad));count+=1
    built=time.monotonic();r=s.check();end=time.monotonic()
    out=dict(split_column=h,result=str(r),clauses=count,build_s=built-start,check_s=end-built)
    if r==z3.sat:
        model=s.model();out['split_off']=[str(model.eval(v)) for v in x]
    if r==z3.unknown:out['reason']=s.reason_unknown()
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--timeout',type=int,default=60);a=p.parse_args()
    C=json.loads(Path('economics_problem2/work/structural_p8_obstruction_verified.json').read_text())['matrix']
    results=[]
    for h in range(8):
        result=solve(C,h,a.timeout);results.append(result);print(json.dumps(result),flush=True)
        Path('economics_problem2/work/structural_split_obstruction.json').write_text(json.dumps(dict(matrix=C,results=results),indent=2))
        if result['result']=='sat':break


if __name__=='__main__':main()
