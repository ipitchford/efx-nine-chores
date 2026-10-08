#!/usr/bin/env python3
"""Certify complete saved fallback records without modifying the live worker."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import resource
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(500*1024**2,)*2)
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
    from certify_row_cores import certify
    from verify_row_cores import verify
    out=args.run/'exact_fallback_certificates';out.mkdir(exist_ok=True)
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    started=time.monotonic();cache={};receipts=[];incomplete=[]
    for source in sorted((args.run/'regions').glob('*.json')):
        try:
            original_bytes=source.read_bytes();record=json.loads(original_bytes)
        except json.JSONDecodeError:
            incomplete.append(str(source));continue
        if record.get('inner_method')!='QF_LRA_solver':continue
        core=args.run/'inner'/source.with_suffix('.smt2').name
        assert sha(core)==record['core_sha256']
        target=out/source.name
        if target.exists():certificate=json.loads(target.read_text())
        else:certificate=certify(record,cache)
        assert certificate['source_core_sha256']==record['core_sha256']
        assert certificate['core_allocation_ids']==record['core_allocation_ids']
        result=verify(certificate)
        assert source.read_bytes()==original_bytes
        if not target.exists():
            temporary=target.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(certificate,indent=2)+'\n');temporary.replace(target)
        receipts.append(dict(source=str(source.resolve()),source_sha256=sha(source),
                             core_sha256=record['core_sha256'],certificate=str(target.resolve()),
                             certificate_sha256=sha(target),verification=result))
    result=dict(status='PASS_COMPLETE_SAVED_FALLBACKS',utc=datetime.now(timezone.utc).isoformat(),
                elapsed=time.monotonic()-started,cores=len(receipts),receipts=receipts,
                skipped_incomplete_files=incomplete,
                scope='All fallback records complete at this scan. This is not a global coverage verdict.')
    receipt=out/f'verification_checkpoint_{len(receipts):05d}.json'
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='receipts'}))


if __name__=='__main__':main()
