"""Independent finite verification of the cardinality constrained greedy split.

Standard library only; exact nonnegative integer arithmetic and literal EFX.
The finite verification supports the implementation, not a universal claim.
"""
from itertools import combinations, combinations_with_replacement, product
import json
from pathlib import Path
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]

def residual(costs, bundle):
    return sum(costs[g] for g in bundle)-min((costs[g] for g in bundle),default=0)

def greedy(costs, chores=None):
    chores=list(range(len(costs))) if chores is None else list(chores)
    bundles=[[],[]]
    for g in sorted(chores,key=lambda g:(-costs[g],g)):
        j=min(range(2),key=lambda j:(sum(costs[h] for h in bundles[j]),len(bundles[j]),j))
        bundles[j].append(g)
    return bundles

def literal_efx(C,A):
    return all(sum(C[i][h] for h in A[i] if h!=g)<=sum(C[i][h] for h in A[j])
               for i in range(3) for g in A[i] for j in range(3))

def construction(C, exhaustive_subsets=False):
    m=len(C[0]); tot=list(map(sum,C))
    for k in range(3):
        candidates=(combinations(range(m),n) for n in range(1,m-3)) if exhaustive_subsets else [[tuple(sorted(range(m),key=lambda g:C[k][g])[:3])]]
        for collection in candidates:
            for S in collection:
                R=[g for g in range(m) if g not in S]
                if len(R)<4:continue
                if residual(C[k],S)>sum(sorted(C[k][g] for g in R)[:2]):continue
                for p in range(3):
                    if p==k:continue
                    q=3-k-p
                    d=[min(C[i][g] for g in R) for i in range(3)]
                    s=[sum(C[i][g] for g in S) for i in range(3)]
                    if 2*max(C[p][g] for g in R)+d[p]>tot[p]-s[p]:continue
                    if 3*s[p]+d[p]<tot[p] or 3*s[q]+2*d[q]<tot[q]:continue
                    B,D=greedy(C[p],R)
                    assert len(B)>=2 and len(D)>=2
                    if sum(C[q][g] for g in B)>sum(C[q][g] for g in D):B,D=D,B
                    A=[None,None,None];A[k]=list(S);A[p]=D;A[q]=B
                    assert literal_efx(C,A)
                    return dict(owner=k,cutter=p,chooser=q,bundles=A)
    return None

def main():
    start=time.monotonic(); checked=0; true=0
    for n in range(4,10):
        for row in combinations_with_replacement(range(6),n):
            condition=2*max(row)+min(row)<=sum(row)
            B,D=greedy(row)
            assert residual(row,B)<=sum(row[g] for g in D)
            assert residual(row,D)<=sum(row[g] for g in B)
            assert (len(B)>=2 and len(D)>=2)==condition
            if n<=7:
                exists=any(residual(row,A)<=sum(row[g] for g in set(range(n))-set(A))
                           and residual(row,set(range(n))-set(A))<=sum(row[g] for g in A)
                           for size in range(2,n-1) for A in combinations(range(n),size))
                assert exists==condition
            checked+=1;true+=condition
    fixtures={"unit9":[[1]*9 for _ in range(3)],"zero9":[[0]*9 for _ in range(3)]}
    for name,path in [
        ("rank_fewest",ROOT/"work/compute_rank_0_1/fewest_efx_model.json"),
        ("unit_cegis_last",ROOT/"work/compute_cegis_unit/last_model.json"),
    ]:
        if path.exists():
            data=json.loads(path.read_text()); rows=data if isinstance(data,list) else data.get("rows",data.get("costs"))
            if rows is not None:fixtures[name]=rows
    report={"single_row_instances":checked,"satisfying_cardinality_condition":true,
            "integer_cost_range":[0,5],"chore_counts":list(range(4,10)),"literal_exhaustive_partition_counts_up_to":7,
            "fixtures":{name:{"triple":construction(C),"all_protected_subsets":construction(C,True)} for name,C in fixtures.items()},
            "seconds":time.monotonic()-start,"passed":True}
    (OUT/"cardinality_cut_check.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
