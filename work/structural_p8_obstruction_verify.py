"""Exact independent verification of the stronger P8 counterexample."""
from fractions import Fraction
from itertools import product
from math import lcm,gcd
from functools import reduce
from pathlib import Path
import json


def main():
    src=Path('economics_problem2/work/structural_designated_reduced_m8_seed0.json')
    model=json.loads(src.read_text())['matrix']
    rows=[]
    for row in model:
        r=list(map(Fraction,row));d=lcm(*(x.denominator for x in r))
        ints=[int(x*d) for x in r];g=reduce(gcd,ints);rows.append([x//g for x in ints])
    efx=[];p=[[],[],[]];witnesses=[]
    for a in product(range(3),repeat=8):
        bundles=[[g for g in range(8) if a[g]==i] for i in range(3)]
        sums=[[sum(rows[i][g] for g in bundles[j]) for j in range(3)] for i in range(3)]
        violations=[]
        for i in range(3):
            for g in bundles[i]:
                for j in range(3):
                    if i!=j and sums[i][i]-rows[i][g]>sums[i][j]:violations.append((i,g,j,sums[i][i]-rows[i][g]-sums[i][j]))
        envyfree=[all(sums[i][i]<=sums[i][j] for j in range(3)) for i in range(3)]
        if not violations:
            efx.append(list(a))
            for i in range(3):
                if envyfree[i]:p[i].append(list(a))
        if not envyfree[0]:
            j=next(j for j in range(3) if sums[0][0]>sums[0][j]);witnesses.append(dict(kind='envy',agent=0,other=j,margin=sums[0][0]-sums[0][j]))
        else:
            v=next((v for v in violations if v[0]!=0),None)
            assert v is not None,('P8 unexpectedly holds for allocation',a)
            i,g,j,margin=v;witnesses.append(dict(kind='EFX',agent=i,other=j,removed=g,margin=margin))
    result=dict(matrix=rows,row_totals=list(map(sum,rows)),allocations_checked=3**8,EFX_count=len(efx),designated_counts=[len(x) for x in p],EFX_allocations=efx,minimum_failure_margin=min(x['margin'] for x in witnesses),status='Exact rational counterexample to P8 only; not a counterexample to ordinary eight- or nine-chore EFX')
    Path('economics_problem2/work/structural_p8_obstruction_verified.json').write_text(json.dumps(result,indent=2))
    Path('economics_problem2/work/structural_p8_obstruction_witnesses.json').write_text(json.dumps(witnesses,separators=(',',':')))
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
