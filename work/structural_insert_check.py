"""Independent integer audit of designated-envyfree-preserving insertion."""
from itertools import product
from pathlib import Path
import json


def residual(cost, bundle):
    return sum(cost[g] for g in bundle)-min((cost[g] for g in bundle),default=0)


def acceptable(costs, bundles):
    if any(sum(costs[0][g] for g in bundles[0])>sum(costs[0][g] for g in bundles[j]) for j in [1,2]):
        return False
    return all(residual(costs[i],bundles[i])<=sum(costs[i][g] for g in bundles[j]) for i in [1,2] for j in range(3) if i!=j)


def insert(costs, bundles, new):
    """Input costs already includes new item column; initially unallocated."""
    nxt={i:min(range(3),key=lambda j:sum(costs[i][g] for g in bundles[j])) for i in [1,2]}
    cycle=None
    for start in [1,2]:
        path=[];u=start
        while u!=0 and u not in path:
            path.append(u);u=nxt[u]
        if u!=0:
            cycle=path[path.index(u):];break
    if cycle:
        result=[list(b) for b in bundles]
        for i in cycle:result[i]=list(bundles[nxt[i]])
        result[cycle[0]].append(new)
        return result,'cycle'+str(len(cycle))
    augmented=[list(b) for b in bundles];augmented[0].append(new)
    j=min(range(3),key=lambda a:sum(costs[0][g] for g in augmented[a]))
    if j==0:return augmented,'retained'
    result=[list(b) for b in bundles];result[0]=list(bundles[j])
    u=j;length=0
    while u!=0:
        v=nxt[u];result[u]=list(augmented[v]);u=v;length+=1
    return result,'path'+str(length)


def main():
    m=3
    counts=dict(input_matrices=0,initial_allocations=0,insertions=0,branches={})
    for flat in product([0,1],repeat=3*m):
        base=[list(flat[i*m:(i+1)*m]) for i in range(3)];counts['input_matrices']+=1
        for a in product(range(3),repeat=m):
            bundles=[[g for g in range(m) if a[g]==i] for i in range(3)]
            if not acceptable(base,bundles):continue
            counts['initial_allocations']+=1
            for e0 in [0,1]:
                for e1 in range(min(base[1])+1):
                    for e2 in range(min(base[2])+1):
                        costs=[base[i]+[e] for i,e in enumerate([e0,e1,e2])]
                        new,branch=insert(costs,bundles,m)
                        assert sorted(g for b in new for g in b)==list(range(m+1))
                        assert acceptable(costs,new),(costs,bundles,new,branch)
                        counts['insertions']+=1
                        counts['branches'][branch]=counts['branches'].get(branch,0)+1
    counts.update(result='PASS',domain='all 3x3 binary matrices; all initial designated-EF+EFX allocations; all binary new costs meeting minimum premise',scope='finite implementation audit of proved insertion lemma; not the universal nine-chore target')
    Path('economics_problem2/work/structural_insert_check.json').write_text(json.dumps(counts,indent=2))
    print(json.dumps(counts),flush=True)


if __name__=='__main__':main()
