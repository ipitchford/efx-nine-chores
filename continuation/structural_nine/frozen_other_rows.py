"""Search P8 failure by varying only the prescribed row.

Rows 1 and 2 are fixed exactly, so their EFX-compatible allocations can be
filtered before solving. Eight real variables remain. All complete
allocations are accounted for; integer/rational SAT models are replayed
against the literal full target.
"""
import hashlib
import itertools
import json
from math import gcd, lcm
from pathlib import Path
import resource
import time
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
import z3

OUT=Path(__file__).resolve().parent
OTHER=[[3,15,24,136,358,171,500,294],[20,4,7,235,166,500,56,203]]
allocs=[]
for a in itertools.product(range(3),repeat=8):
    A=[[g for g in range(8) if a[g]==i] for i in range(3)]
    if all(all(sum(OTHER[i-1][h] for h in A[i] if h!=g)<=sum(OTHER[i-1][h] for h in A[j])
               for g in A[i] for j in range(3)) for i in (1,2)):
        allocs.append((a,A))

def solve(kind,g):
    beg=time.monotonic();c=[z3.Real(f'v_{j}') for j in range(8)]
    s=z3.SolverFor('QF_LRA');s.set(timeout=15000,**{'arith.solver':2})
    s.add(*(x>0 for x in c))
    if kind=='distinct':s.add(*(c[g]<c[j] for j in range(8) if j!=g))
    else:
        s.add(c[0]<c[g],*(c[g]<c[j] for j in range(8) if j not in (0,g)))
    for a,A in allocs:
        total=[z3.Sum([c[h] for h in b]) for b in A]
        s.add(z3.Or(total[0]>total[1],total[0]>total[2]))
    fn=OUT/f'frozen_others_{kind}_{g}.smt2';fn.write_text(s.to_smt2())
    start=time.monotonic();r=s.check()
    rec=dict(kind=kind,column=g,result=str(r),assertions=len(s.assertions()),
             filtered_allocations=len(allocs),build_seconds=start-beg,check_seconds=time.monotonic()-start,
             formula_sha256=hashlib.sha256(fn.read_bytes()).hexdigest())
    if r==z3.unknown:rec['reason']=s.reason_unknown()
    elif r==z3.sat:
        m=s.model();vals=[m.eval(x) for x in c]
        scale=lcm(*(v.denominator_as_long() for v in vals))
        row=[v.numerator_as_long()*(scale//v.denominator_as_long()) for v in vals]
        d=gcd(*row);row=[v//d for v in row]
        C=[row]+OTHER;count=0;pcount=0
        for a in itertools.product(range(3),repeat=8):
            A=[[h for h in range(8) if a[h]==i] for i in range(3)]
            T=[[sum(C[i][h] for h in b) for b in A] for i in range(3)]
            efx=all(T[i][i]-C[i][h]<=T[i][j] for i in range(3) for h in A[i] for j in range(3))
            if efx:
                count+=1;pcount+=all(T[0][0]<=T[0][j] for j in range(3))
        assert pcount==0
        rec.update(matrix=C,efx_count=count,prescribed0_efx_count=pcount,verified_all_allocations=6561)
    (OUT/f'frozen_others_{kind}_{g}.json').write_text(json.dumps(rec,indent=2))
    print(json.dumps(rec),flush=True)
    return rec

if __name__=='__main__':
    results=[]
    for kind,g in itertools.product(('distinct','second'),range(2,8)):
        results.append(solve(kind,g))
    (OUT/'frozen_other_rows_results.json').write_text(json.dumps(results,indent=2))
