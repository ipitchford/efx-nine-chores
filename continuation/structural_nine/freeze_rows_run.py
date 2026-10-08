#!/usr/bin/env python3
"""Freeze a completed supervised row run and its exact assertion order."""
import argparse
from datetime import datetime,timezone
import collections
import hashlib
import json
from pathlib import Path
import shutil


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args();run=args.run
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    terminal=json.loads((run/'terminal_receipt.json').read_text())
    summary=json.loads((run/'summary.json').read_text())
    assert terminal['child_returncode']==0
    assert sha(run/'outer.smt2')==summary['outer_sha256']
    history=[r for r in json.loads((run/'history.json').read_text()) if 'core_size' in r]
    region_files=sorted((run/'regions').glob('*.json'))
    assert len(history)==len(region_files)==summary['regions']
    assert [r.get('artifact_stem',f"{r['iteration']:05d}") for r in history]==[p.stem for p in region_files]
    shutil.copy2(run/'outer.smt2',run/'outer_final.smt2')
    ordered=[]
    for kind,name in [('robust_single','seed_regions.json'),('resumed','resumed_regions.json'),('static_pair','paired_seed_regions.json')]:
        source=run/name
        if not source.exists():continue
        records=json.loads(source.read_text())
        ordered.append(dict(kind=kind,source=str(source.resolve()),source_sha256=sha(source),
                            records=len(records),order='JSON array order'))
    new=[];methods=collections.Counter();sizes=collections.Counter()
    for source in region_files:
        record=json.loads(source.read_text());methods[record['inner_method']]+=1;sizes[record['core_size']]+=1
        core=run/'inner'/source.with_suffix('.smt2').name
        assert sha(core)==record['core_sha256']
        item=dict(source=str(source.resolve()),source_sha256=sha(source),
                  core_source=str(core.resolve()),core_sha256=sha(core),
                  allocation_ids=record['core_allocation_ids'])
        candidates=[run/'exact_pair_certificates'/source.name,run/'exact_fallback_certificates'/source.name]
        certificates=[p for p in candidates if p.exists()]
        assert len(certificates)==1, f'Exactly one direct certificate is required for {source}'
        certificate=certificates[0];data=json.loads(certificate.read_text())
        assert data['source_core_sha256']==record['core_sha256']
        assert data['core_allocation_ids']==record['core_allocation_ids']
        item.update(certificate=str(certificate.resolve()),certificate_sha256=sha(certificate),
                    certificate_kind='direct_pair' if certificate.parent.name=='exact_pair_certificates' else 'direct_fallback')
        new.append(item)
    manifest=dict(status='frozen_after_completed_supervised_run',utc=datetime.now(timezone.utc).isoformat(),
                  terminal_termination=summary['termination'],outer=str((run/'outer_final.smt2').resolve()),
                  outer_sha256=sha(run/'outer_final.smt2'),domain_assertions=18,
                  ordered_sources=ordered,ordered_new_regions=new,new_region_count=len(new),
                  representative_model_count=len({r['iteration'] for r in history}),
                  new_methods=dict(methods),new_core_sizes=dict(sizes),
                  total_assertions=18+sum(x['records'] for x in ordered)+len(new),
                  global_nine_chore_verdict='unresolved' if summary['termination'] not in ('outer_unsat','verified_counterexample') else 'decisive_candidate_requires_separate_final_verification',
                  terminal_receipt_sha256=sha(run/'terminal_receipt.json'))
    resume=run/'resume_manifest.json'
    if resume.exists():manifest.update(resume_pruning_manifest=str(resume.resolve()),resume_pruning_manifest_sha256=sha(resume))
    (run/'frozen_outer_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('ordered_new_regions','ordered_sources')}))


if __name__=='__main__':main()
