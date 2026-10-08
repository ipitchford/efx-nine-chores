#!/usr/bin/env python3
"""Freeze compressed outer-row premises for all labelled allocations."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--robust-reference',type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    robust=set(json.loads(args.robust_reference.read_text())['allocation_ids'])
    atoms=[];atom_ids={};allocations=[]
    for aid,a in enumerate(itertools.product(range(3),repeat=9)):
        if set(a)!={0,1,2}:continue
        regions=[];raw=[]
        for i in (1,2):
            own={g for g in range(9) if a[g]==i}
            trims=[i] if i in own else sorted(own)
            forms={}
            for removed in trims:
                for j in range(3):
                    if i==j:continue
                    q=tuple(int(g in own and g!=removed)-int(a[g]==j) for g in range(9))
                    u=(sum(q),)+tuple(q[g] for g in range(9) if g!=i)
                    if any(v>0 for v in u):forms[u]=q
            kept=[u for u in sorted(forms) if not any(
                u!=v and all(x<=y for x,y in zip(u,v)) for v in forms)]
            indices=[]
            for u in kept:
                if u not in atom_ids:
                    atom_ids[u]=len(atoms);atoms.append(u)
                indices.append(atom_ids[u])
            regions.append(indices)
            raw.append([dict(coefficients=forms[u],gap_coefficients=u) for u in kept])
        allocations.append(dict(allocation_id=aid,robust=aid in robust,
                                row_atoms=regions,retained_outer_rows=raw))
    lines=[f'{len(allocations)} {len(atoms)} {len(robust)}']
    lines += [' '.join(map(str,a)) for a in atoms]
    lines += [' '.join(map(str,[a['allocation_id'],int(a['robust']),len(a['row_atoms'][0]),
         len(a['row_atoms'][1])]+a['row_atoms'][0]+a['row_atoms'][1])) for a in allocations]
    text='\n'.join(lines)+'\n';(args.out/'prune_input.txt').write_text(text)
    data=dict(allocations=allocations,atom_table=atoms,
        coordinate_convention='Pinned minimum t; eight positive differences c_g-t in increasing item order',
        compression='Delete the pinned minimum when owned; otherwise retain all owned deletions. Drop nonpositive forms and componentwise dominated forms.',
        input_sha256=hashlib.sha256(text.encode()).hexdigest())
    (args.out/'prune_input_index.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(allocations=len(allocations),unique_outer_atoms=len(atoms),
                         input_sha256=data['input_sha256'])))


if __name__=='__main__':main()
