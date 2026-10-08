"""Exact independent full-deletion checks of the new auxiliary obstructions."""
import itertools,json
from pathlib import Path
from cardinality_cut_check import construction
OUT=Path(__file__).resolve().parent

def inspect(C):
    m=len(C[0]);efx=0;prescribed=[0]*3;first=None
    for a in itertools.product(range(3),repeat=m):
        A=[[g for g in range(m) if a[g]==i] for i in range(3)]
        totals=[[sum(C[i][g] for g in A[j]) for j in range(3)] for i in range(3)]
        ok=all(sum(C[i][h] for h in A[i] if h!=g)<=totals[i][j]
               for i in range(3) for g in A[i] for j in range(3))
        if ok:
            efx+=1
            if first is None:first=a
            for i in range(3):prescribed[i]+=all(totals[i][i]<=totals[i][j] for j in range(3))
    return dict(matrix=C,allocations_checked=3**m,efx_count=efx,prescribed_counts=prescribed,first_efx=first)

C8=[[7,32,20,79,96,115,106,176],[3,15,24,136,358,171,500,294],[20,4,7,235,166,500,56,203]]
C9=[[4,4,4,1,1,1,1,1,1]]*3
D9=[[100,101,102,103,104,105,400,401,402],[101,100,102,103,104,105,400,401,402],[101,102,100,103,104,105,400,401,402]]
records=[inspect(C) for C in (C8,C9,D9)]
assert records[0]['efx_count']==32 and records[0]['prescribed_counts'][0]==0
for rec in records[1:]:
    rec['protected_construction']=construction(rec['matrix'],True)
    assert rec['efx_count']==648 and rec['protected_construction'] is None
    for row in rec['matrix']:
        # The first fixture has H first; the second has H last.
        order=sorted(range(9),key=lambda g:row[g]);H=order[-3:];L=order[:-3]
        assert max(row[g] for g in H)+max(row[g] for g in L)<=min(row[g] for g in H)+2*min(row[g] for g in L)
(OUT/'structural_limitations_check.json').write_text(json.dumps(dict(passed=True,records=records),indent=2))
print(json.dumps(dict(passed=True,records=records),indent=2))
