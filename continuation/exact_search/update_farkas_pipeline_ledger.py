#!/usr/bin/env python3
"""Index sealed, mutually disjoint pipeline candidates; no proof acceptance."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os

BASE=Path(__file__).resolve().parent
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
seen=set();parts=[];wall=0
for run in sorted(BASE.glob('zero9_farkas_pipeline_run*'),key=lambda p:int(p.name.rsplit('run',1)[1])):
    terminal=run/'terminal.json'
    if not terminal.exists():continue
    result=json.loads(terminal.read_text())
    if result.get('generation_status')!='COMPLETE_EXACT_MULTIPLIER_CANDIDATES':continue
    assert result['returncode']==0 and result['inputs_unchanged']
    manifest=run/'artifacts/preparation.json';prepared=json.loads(manifest.read_text())
    certificate=run/'artifacts/arithmetic_certificates.jsonl'
    digest=sha(certificate)
    assert digest==prepared['certificates_sha256']==result['certificate_readback']['sha256']
    indices=[]
    with certificate.open() as f:
        for line in f:indices.append(json.loads(line)['clause_index'])
    assert all(type(i) is int for i in indices)
    assert len(indices)==len(set(indices))==prepared['certified_theory_clauses']
    assert not seen.intersection(indices),'Repeated arithmetic production across sealed batches'
    seen.update(indices);wall+=result['elapsed']
    number=int(run.name.rsplit('run',1)[1]);selection=BASE/f'zero9_farkas_pipeline_selection{number}'
    paths=[terminal,manifest,certificate,run/'started.json',
        run/'source_snapshot/prepare_lra_boolean_certificate.py',
        run/'source_snapshot/run_selected_farkas.py',
        selection/'selection_provenance.json',selection/'selected_theory_indices.json',
        selection/'candidate_justifications_prefix.jsonl',selection/'memory_guard.json']
    paths += sorted(selection.glob('memory_guard_*failed.json'))
    parts.append(dict(batch=number,records=len(indices),producer_wall_seconds=result['elapsed'],
        files={str(p.relative_to(BASE.parent.parent)):sha(p) for p in paths}))
report=dict(status='SEALED_DISJOINT_ARITHMETIC_CANDIDATES_ONLY',
    updated_at_utc=datetime.now(timezone.utc).isoformat(),completed_batches=len(parts),
    distinct_candidate_theories=len(seen),total_producer_wall_seconds=wall,parts=parts,
    independent_arithmetic_checked=False,final_selected_set_coverage_checked=False,
    independent_nine_certificate_complete=False)
target=BASE/'zero9_farkas_pipeline_ledger.json';partial=target.with_suffix('.json.partial')
with partial.open('w') as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
partial.replace(target);fd=os.open(BASE,os.O_RDONLY);os.fsync(fd);os.close(fd)
print(json.dumps({k:v for k,v in report.items() if k!='parts'}))
