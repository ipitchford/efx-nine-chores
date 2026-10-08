"""Prototype exact elimination of row 0 for a frozen pair of other rows.

An UNSAT core of the row-0 allocation clauses supplies a whole sufficient
region in the 18-dimensional space of rows 1 and 2: preserve their EFX
inequalities for every allocation appearing in that core.
"""
import itertools,json,resource,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
import z3
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def solve(C,name,timeout=20000):
    beg=time.monotonic();m=9;other=C[1:];filtered=[]
    for a in itertools.product(range(3),repeat=m):
        A=[[g for g in range(m) if a[g]==i] for i in range(3)]
        if not all(A):continue
        if all(all(sum(other[i-1][h] for h in A[i] if h!=g)<=sum(other[i-1][h] for h in A[j])
                   for g in A[i] for j in range(3)) for i in (1,2)):
            filtered.append((a,A))
    c=[z3.Real(f'r0_{g}') for g in range(m)]
    s=z3.SolverFor('QF_LRA');s.set(timeout=timeout,**{'arith.solver':2});s.set(unsat_core=True)
    s.add(*(v>0 for v in c),*(c[0]<c[g] for g in range(1,m)))
    s.add(c[1]<c[2],*(c[g]<c[g+1] for g in range(3,m-1)))
    for idx,(a,A) in enumerate(filtered):
        totals=[z3.Sum([c[h] for h in B]) for B in A]
        bad=z3.Or(*[totals[0]-c[g]>totals[j] for g in A[0] for j in (1,2)])
        s.assert_and_track(bad,f'a_{idx}')
    start=time.monotonic();result=s.check()
    rec=dict(name=name,result=str(result),other_rows=other,filtered_allocations=len(filtered),build_seconds=start-beg,check_seconds=time.monotonic()-start)
    if result==z3.unknown:rec['reason']=s.reason_unknown()
    elif result==z3.unsat:
        ids=[int(str(a).split('_')[1]) for a in s.unsat_core()]
        rec['core_size']=len(ids);rec['core_allocations']=[filtered[idx][0] for idx in ids]
    else:rec['first_row']=[str(s.model().eval(cg)) for cg in c]
    (OUT/f'frozen_nine_{name}.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec),flush=True)
    return rec

if __name__=='__main__':
    for name,fn in [('rank','work/compute_rank_0_1/fewest_efx_model.json'),('unit','work/compute_cegis_unit/last_model.json')]:
        d=json.loads((ROOT/fn).read_text());C=d if isinstance(d,list) else d.get('rows',d.get('costs'))
        solve(C,name)
