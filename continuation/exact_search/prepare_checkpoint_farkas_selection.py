#!/usr/bin/env python3
"""Seal a complete-line untrusted dependency prefix and select theory reasons.

No RUP or arithmetic validity is accepted here. The result only schedules
clause-local candidate production against a completed, bound capture.
"""
import argparse, hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def write(path, data):
    partial=path.with_suffix(path.suffix+'.partial')
    with partial.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    partial.replace(path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def write_json(path,data):write(path,(json.dumps(data,indent=2)+'\n').encode())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['checkpoint','capture','binding','producer-started','out']:
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--exclude-artifact',type=Path,action='append',default=[])
    p.add_argument('--external-source-cache-ids',action='store_true',
        help='Producer v7 uses cached-source proof IDs above captured RUP IDs; chronology is checked only in its final internal-ID trace')
    a=p.parse_args()
    if a.out.exists():raise ValueError('Use a fresh output directory')
    binding=json.loads(a.binding.read_text())
    assert binding['status']=='PASS_ORIGINAL_INPUT_CNF_AND_AFFINE_ATOM_BINDING'
    capture_hashes={name:sha(a.capture/name) for name in binding['captured_files_sha256']}
    assert capture_hashes==binding['captured_files_sha256']
    producer=json.loads(a.producer_started.read_text())
    assert str(a.capture.resolve()) in producer['configuration']['argv']
    input_count=binding['original_clause_records'];theory_count=binding['theory_clauses']
    lower=input_count+1;upper=input_count+theory_count
    observed_size=a.checkpoint.stat().st_size
    with a.checkpoint.open('rb') as f:raw=f.read(observed_size)
    assert len(raw)==observed_size
    cut=raw.rfind(b'\n')+1
    raw=raw[:cut]
    assert raw,'No complete checkpoint records yet'
    with a.checkpoint.open('rb') as f:assert f.read(cut)==raw,'Existing source prefix changed'
    selected=set();seen=set();count=0
    for line in raw.splitlines():
        record=json.loads(line);d=record['id']
        assert record['kind']=='rup' and type(d) is int and d>upper and d not in seen
        seen.add(d)
        for reason in record['reasons']:
            assert type(reason) is int and reason>0
            if not a.external_source_cache_ids:assert reason<d
            if lower<=reason<=upper:selected.add(reason-lower)
        count+=1
    all_referenced=len(selected);excluded=set();provenance=[]
    for directory in a.exclude_artifact:
        manifest_path=directory/'preparation.json';certificate=directory/'arithmetic_certificates.jsonl'
        manifest=json.loads(manifest_path.read_text())
        assert manifest['capture_receipt_sha256']==capture_hashes['receipt.json']
        assert sha(certificate)==manifest['certificates_sha256']
        indices=[]
        with certificate.open() as f:
            for line in f:
                index=json.loads(line)['clause_index']
                assert type(index) is int and 0<=index<theory_count
                indices.append(index)
        assert len(indices)==len(set(indices))==manifest['certified_theory_clauses']
        excluded.update(indices)
        provenance.append(dict(directory=str(directory.resolve()),records=len(indices),
            manifest_sha256=sha(manifest_path),certificates_sha256=sha(certificate)))
    selected=sorted(selected-excluded)
    a.out.mkdir(parents=True)
    prefix=a.out/'candidate_justifications_prefix.jsonl';write(prefix,raw)
    selection=a.out/'selected_theory_indices.json';write_json(selection,selected)
    assert sha(prefix)==hashlib.sha256(raw).hexdigest()
    assert len(prefix.read_bytes().splitlines())==count
    report=dict(status='SEALED_UNTRUSTED_DEPENDENCY_PREFIX_THEORY_SELECTION',
        completed_at_utc=datetime.now(timezone.utc).isoformat(),
        source_checkpoint=str(a.checkpoint.resolve()),source_size_observed=observed_size,
        sealed_prefix_bytes=cut,ignored_unterminated_suffix_bytes=observed_size-cut,
        sealed_prefix_records=count,sealed_prefix_sha256=sha(prefix),
        producer_started_sha256=sha(a.producer_started),
        producer_configuration_sha256=producer['configuration_sha256'],
        selector_sha256=sha(Path(__file__)),
        external_source_cache_ids=a.external_source_cache_ids,
        input_binding_sha256=sha(a.binding),capture_hashes=capture_hashes,
        first_theory_global_id=lower,last_theory_global_id=upper,
        all_referenced_theories=all_referenced,previously_generated_candidates=len(excluded),
        prior_artifacts=provenance,selected_theories=len(selected),selection_sha256=sha(selection),
        original_checkpoint_modified=False,boolean_validity_checked=False,
        arithmetic_validity_checked=False,final_selection_coverage_claimed=False)
    write_json(a.out/'selection_provenance.json',report)
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
