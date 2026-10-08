"""Extract and independently verify an explicit allocation cover for a fixed prefix.

With eight cost columns fixed, each labelled allocation's EFX locus in the
three new costs is a closed axis-aligned box. Z3 only chooses a small cover;
the verifier uses integer arithmetic for the box derivation and exact rational
sample points in all cells of the finite breakpoint arrangement.
"""
from fractions import Fraction
from itertools import product
from pathlib import Path
import json,time
import z3


def allocation_box(C,a):
    bundles=[[g for g in range(9) if a[g]==i] for i in range(3)]
    cost=[[sum(C[i][g] for g in bundles[j] if g<8) for j in range(3)] for i in range(3)]
    lower=[0,0,0];upper=[None,None,None]
    for i in range(3):
        for g in bundles[i]:
            for j in range(3):
                if i==j:continue
                c=cost[i][i]-(C[i][g] if g<8 else 0)-cost[i][j]
                k=(a[8]==i)-(g==8)-(a[8]==j)
                if k==0:
                    if c>0:return None
                elif k==1:upper[i]=-c if upper[i] is None else min(upper[i],-c)
                elif k==-1:lower[i]=max(lower[i],c)
                else:raise AssertionError(k)
    if any(upper[i] is not None and lower[i]>upper[i] for i in range(3)):return None
    return tuple(lower),tuple(upper)


def certify(C,cover):
    for entry in cover:
        box=allocation_box(C,entry['allocation'])
        assert box==(tuple(entry['lower']),tuple(entry['upper']))
    samples=[]
    for i in range(3):
        b=sorted(set([0]+[entry[k][i] for entry in cover for k in ['lower','upper'] if entry[k][i] is not None and entry[k][i]>0]))
        samples.append([Fraction(a+b,2) for a,b in zip(b,b[1:])]+[Fraction(b[-1]+1)])
    count=0
    for x in product(*samples):
        assert any(all(entry['lower'][i]<=x[i] and (entry['upper'][i] is None or x[i]<=entry['upper'][i]) for i in range(3)) for entry in cover),x
        count+=1
    return dict(boxes=len(cover),sampled_open_cells=count,sample_counts=list(map(len,samples)),result='PASS',boundary_argument='Each allocation box is closed; a finite union is closed. The sampled cells cover a dense subset of the nonnegative orthant. Hence the closed union covers all boundaries too.')


def main():
    started=time.monotonic()
    C=json.loads(Path('economics_problem2/work/structural_p8_obstruction_verified.json').read_text())['matrix']
    unique={}
    for a in product(range(3),repeat=9):
        box=allocation_box(C,a)
        if box is not None:unique.setdefault(box,a)
    e=[z3.Real(f'x{i}') for i in range(3)]
    s=z3.SolverFor('QF_LRA');s.set('arith.solver',2);s.add(*(x>=0 for x in e))
    entries=[]
    for n,((lo,hi),a) in enumerate(unique.items()):
        term=z3.Or([e[i]<lo[i] for i in range(3) if lo[i]>0]+[e[i]>hi[i] for i in range(3) if hi[i] is not None])
        entries.append(dict(allocation=list(a),lower=list(lo),upper=list(hi)))
        s.assert_and_track(term,z3.Bool(f'box{n}'))
    assert s.check()==z3.unsat
    indices=[int(str(a)[3:]) for a in s.unsat_core()]
    # Remove redundant members from the already small core.
    changed=True
    while changed:
        changed=False
        for removed in list(indices):
            trial=[j for j in indices if j!=removed]
            q=z3.SolverFor('QF_LRA');q.add(*(x>=0 for x in e))
            for j in trial:
                lo=entries[j]['lower'];hi=entries[j]['upper']
                q.add(z3.Or([e[i]<lo[i] for i in range(3) if lo[i]>0]+[e[i]>hi[i] for i in range(3) if hi[i] is not None]))
            if q.check()==z3.unsat:indices=trial;changed=True
    cover=[entries[j] for j in indices]
    certificate=dict(fixed_matrix=C,cover=cover,verification=certify(C,cover),all_distinct_nonempty_boxes=len(unique),elapsed_s=time.monotonic()-started)
    Path('economics_problem2/work/structural_extension_cover.json').write_text(json.dumps(certificate,indent=2))
    print(json.dumps(certificate),flush=True)


if __name__=='__main__':main()
