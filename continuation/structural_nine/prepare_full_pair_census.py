#!/usr/bin/env python3
"""Freeze exact first-row failure clauses for all nonempty allocations."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


def transformed(q):
    return (sum(q),q[1]+q[2],q[2])+tuple(
        sum(q[g] for g in range(3,upper+1)) for upper in range(8,2,-1))


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--robust-reference',type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    atoms=[];atom_ids={};allocations=[];robust=[];surjective=0
    for aid,a in enumerate(itertools.product(range(3),repeat=9)):
        if set(a)!={0,1,2}:continue
        surjective+=1;own={g for g in range(9) if a[g]==0}
        if 0 in own:trims=[0]
        else:
            pinned=[g for g in (1,2) if g in own]
            free=[g for g in own if g>=3]
            trims=pinned[:1]+([max(free)] if free else [])
        rows={}
        for removed in trims:
            for other in (1,2):
                q=tuple(int(g in own and g!=removed)-int(a[g]==other) for g in range(9))
                u=transformed(q)
                if any(v>0 for v in u):rows[u]=q
        kept=[u for u in sorted(rows) if not any(
            u!=v and all(x<=y for x,y in zip(u,v)) for v in rows)]
        if not kept:robust.append(aid);continue
        indices=[]
        for u in kept:
            if u not in atom_ids:
                atom_ids[u]=len(atoms)
                atoms.append(dict(coefficients=rows[u],gap_coefficients=u))
            indices.append(atom_ids[u])
        flags=sum(int(a[i]==i)<<i for i in range(3))
        allocations.append(dict(allocation_id=aid,allocation=a,minimum_ownership_flags=flags,
                                failure_atoms=indices,minimal_trims=trims))
    reference=json.loads(args.robust_reference.read_text())
    assert set(robust)==set(reference['allocation_ids'])
    assert surjective==18150 and len(robust)==3238
    lines=[f'{len(allocations)} {len(atoms)} {len(robust)} {surjective}']
    lines += [' '.join(map(str,a['gap_coefficients'])) for a in atoms]
    lines += [' '.join(map(str,[a['allocation_id'],a['minimum_ownership_flags'],
                               len(a['failure_atoms'])]+a['failure_atoms'])) for a in allocations]
    source='\n'.join(lines)+'\n';(args.out/'input.txt').write_text(source)
    data=dict(domain='c00>0; c01>c00; c02>c01; c08>c00; c07>c08; ...; c03>c04',
        reduction='Minimal owned deletions in the two-chain partial order; drop impossible and dominated failure atoms',
        surjective_allocations=surjective,robust_allocation_ids=robust,
        nonrobust_allocations=len(allocations),unique_feasible_atoms=len(atoms),
        atom_table=atoms,allocations=allocations,
        input_sha256=hashlib.sha256(source.encode()).hexdigest())
    (args.out/'input_index.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k not in ('atom_table','allocations','robust_allocation_ids')},indent=2))


if __name__=='__main__':main()
