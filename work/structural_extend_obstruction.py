"""Fix verified eight-column P8 obstruction; search arbitrary ninth column."""
from itertools import product
from pathlib import Path
import argparse,json,time
import z3


def main(timeout,cheap0):
    started=time.monotonic()
    C=json.loads(Path('economics_problem2/work/structural_p8_obstruction_verified.json').read_text())['matrix']
    e=[z3.Real(f'e_{i}') for i in range(3)]
    s=z3.SolverFor('QF_LRA');s.set(timeout=1000*timeout);s.set('arith.solver',2)
    s.add(*(x>=0 for x in e))
    if cheap0:s.add(e[0]<=min(C[0]))
    count=0
    for a in product(range(3),repeat=9):
        b=[[g for g in range(9) if a[g]==i] for i in range(3)]
        sums=[[sum(C[i][g] for g in b[j] if g<8) for j in range(3)] for i in range(3)]
        bad=[];trivial=False
        for i in range(3):
            for g in b[i]:
                for j in range(3):
                    if i==j:continue
                    const=sums[i][i]-(C[i][g] if g<8 else 0)-sums[i][j]
                    coeff=int(a[8]==i)-int(g==8)-int(a[8]==j)
                    if coeff==0:
                        if const>0:trivial=True;break
                    elif coeff==1:bad.append(e[i]>-const)
                    elif coeff==-1:bad.append(e[i]<const)
                    else:raise AssertionError(coeff)
                if trivial:break
            if trivial:break
        if not trivial:s.add(z3.Or(bad));count+=1
    built=time.monotonic();answer=s.check();ended=time.monotonic()
    out=dict(result=str(answer),cheap_for_agent0=cheap0,nontrivial_allocation_clauses=count,build_s=built-started,check_s=ended-built)
    if answer==z3.sat:
        mod=s.model();out['ninth_column']=[str(mod.eval(x)) for x in e]
    if answer==z3.unknown:out['reason']=s.reason_unknown()
    suffix='cheap0' if cheap0 else 'arbitrary'
    Path(f'economics_problem2/work/structural_extension_{suffix}.json').write_text(json.dumps(out,indent=2))
    Path(f'economics_problem2/work/structural_extension_{suffix}.smt2').write_text(s.to_smt2())
    print(json.dumps(out),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--timeout',type=int,default=300);p.add_argument('--cheap0',action='store_true');a=p.parse_args();main(a.timeout,a.cheap0)
