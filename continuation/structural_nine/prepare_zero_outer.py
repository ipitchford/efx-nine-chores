#!/usr/bin/env python3
"""Rebuild the final verified outer exclusions with zero pinned minima.

No solver is invoked. The old 18 domain assertions are replaced, not
substituted, by a fresh 14-variable positive domain. Every learned exclusion
is reconstructed from its independently bound literal compressed predicates.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'continuation/structural_nine/row_elimination_batch1'
OUT=ROOT/'continuation/structural_nine/zero_outer'
EXPECTED='1fc2bec83744678c33126d36e26ea535ff31bab494e8a6c4f9ad662d46214ec4'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value):return str(value) if value>=0 else f'(- {-value})'


def predicate(atom):
    agent=atom['agent'];coefficient=atom['coefficients']
    assert type(agent) is int and agent in (1,2)
    assert len(coefficient)==9 and all(type(v) is int and -1<=v<=1 for v in coefficient)
    terms=[]
    if coefficient[0]:terms.append(number(coefficient[0]))
    for g,v in enumerate(coefficient):
        if g in (0,agent) or not v:continue
        symbol=f'c_{agent}_{g}'
        terms.append(symbol if v==1 else f'(- {symbol})')
    expression='0' if not terms else terms[0] if len(terms)==1 else '(+ '+' '.join(terms)+')'
    return f'(> {expression} 0)'


def main():
    assert sha(RUN/'outer_final.smt2')==EXPECTED
    manifest=json.loads((RUN/'frozen_outer_manifest.json').read_text())
    assert manifest['outer_sha256']==EXPECTED and manifest['total_assertions']==6309
    audit=ROOT/'continuation/verification/batch1_outer_audit.json'
    aud=json.loads(audit.read_text());assert aud['outer_sha256']==EXPECTED and aud['status'].startswith('PASS')
    records=[];bindings=[]
    for source in manifest['ordered_sources']:
        path=Path(source['source']);assert sha(path)==source['source_sha256']
        data=json.loads(path.read_text());assert len(data)==source['records']
        records.extend(data);bindings.append(dict(path=str(path),sha256=sha(path),records=len(data)))
    for source in manifest['ordered_new_regions']:
        path=Path(source['source']);assert sha(path)==source['source_sha256']
        records.append(json.loads(path.read_text()));bindings.append(dict(path=str(path),sha256=sha(path),records=1))
    assert len(records)==6291
    free=[(i,g) for i in (1,2) for g in range(9) if g not in (0,i)]
    lines=['; Zero-minimum image of the independently bound final row outer formula.',
           '; The old minimum-one domain is replaced by a fresh domain.',
           '; c_1_1=c_2_2=0; c_1_0=c_2_0=1; every remaining cost is strictly positive.',
           '(set-logic QF_LRA)']
    lines.extend(f'(declare-fun c_{i}_{g} () Real)' for i,g in free)
    lines.extend(f'(assert (> c_{i}_{g} 0))' for i,g in free)
    for record in records:
        atoms=record.get('compressed_region_atoms',record['region_atoms'])
        predicates=[predicate(a) for a in atoms]
        clause='false' if not predicates else predicates[0] if len(predicates)==1 else '(or '+' '.join(predicates)+')'
        lines.append('(assert '+clause+')')
    lines.append('(check-sat)')
    OUT.mkdir(exist_ok=True);formula=OUT/'zero_minimum_final_outer.smt2'
    formula.write_text('\n'.join(lines)+'\n')
    receipt=dict(status='prepared_not_solved',utc=datetime.now(timezone.utc).isoformat(),
        source_outer=str((RUN/'outer_final.smt2').resolve()),source_outer_sha256=EXPECTED,
        source_audit=str(audit),source_audit_sha256=sha(audit),
        source_manifest_sha256=sha(RUN/'frozen_outer_manifest.json'),
        formula=str(formula.resolve()),formula_sha256=sha(formula),bytes=formula.stat().st_size,
        real_variables=14,domain_assertions=14,retained_exclusions=6291,total_assertions=6305,
        substitutions={'c_1_1':0,'c_2_2':0,'c_1_0':1,'c_2_0':1},
        domain_policy='Replace all original 18 domain assertions; do not substitute into their minimum-one equations.',
        proof_transfer='Finite unions of closed first-row EFX sets extend the positive-minimum core guarantees to a zero minimum. Other-row dominance uses only minimum >= 0. Every nonminimum reference is positive and may be normalized to one.',
        source_bindings=bindings)
    (OUT/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='source_bindings'}))


if __name__=='__main__':main()
