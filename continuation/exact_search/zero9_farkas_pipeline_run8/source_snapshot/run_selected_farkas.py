#!/usr/bin/env python3
"""Supervise exact-candidate generation for a frozen RUP-selected theory set."""
import argparse,hashlib,json,os,resource,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def atomic(path,data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as stream:
        stream.write(json.dumps(data,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
    tmp.replace(path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--selected',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=120);p.add_argument('--hard-seconds',type=int,default=150)
    p.add_argument('--memory-mib',type=int,default=600);a=p.parse_args()
    assert a.seconds>0 and a.hard_seconds>=a.seconds and a.memory_mib>0
    assert not a.out.exists(),'Preserve previous receipts'
    selection=json.loads(a.selected.read_text());assert isinstance(selection,list)
    a.out.mkdir(parents=True);runner=HERE/'prepare_lra_boolean_certificate.py'
    snapshot=a.out/'source_snapshot';snapshot.mkdir()
    for source in (runner,Path(__file__).resolve()):
        target=snapshot/source.name
        with target.open('wb') as stream:
            stream.write(source.read_bytes());stream.flush();os.fsync(stream.fileno())
        assert digest(source)==digest(target)
    frozen_runner=(snapshot/runner.name).resolve()
    command=[sys.executable,'-u',str(frozen_runner),'--capture',str(a.capture.resolve()),
        '--selected-theories',str(a.selected.resolve()),'--out',str((a.out/'artifacts').resolve()),
        '--seconds',str(a.seconds),'--memory-mib',str(a.memory_mib)]
    inputs={str(path.resolve()):digest(path) for path in [runner,frozen_runner,a.selected,a.capture/'receipt.json']}
    started=time.monotonic();launch=dict(utc=utc(),command=command,input_hashes=inputs,
        selected_theories=len(selection),memory_mib=a.memory_mib,seconds=a.seconds,hard_seconds=a.hard_seconds)
    atomic(a.out/'started.json',launch);print(json.dumps(launch),flush=True)
    def limit():resource.setrlimit(resource.RLIMIT_AS,(a.memory_mib*1024**2,)*2)
    reason='child_completed'
    with (a.out/'worker.log').open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
        try:
            while child.poll() is None:
                elapsed=time.monotonic()-started;atomic(a.out/'heartbeat.json',dict(utc=utc(),elapsed=elapsed))
                if elapsed>=a.hard_seconds:child.kill();child.wait();reason='hard_wall_killed';break
                try:child.wait(timeout=min(5,a.hard_seconds-elapsed))
                except subprocess.TimeoutExpired:pass
        finally:
            if child.poll() is None:child.kill();child.wait();reason='supervisor_interrupted'
            summary_file=a.out/'artifacts/preparation.json'
            summary=json.loads(summary_file.read_text()) if summary_file.exists() else None
            certificate=a.out/'artifacts/arithmetic_certificates.jsonl'
            readback=None
            if certificate.exists():
                count=0
                with certificate.open() as source:
                    for line in source:
                        json.loads(line);count+=1
                readback=dict(records=count,sha256=digest(certificate))
                if summary:
                    readback['matches_manifest']=(count==summary['certified_theory_clauses'] and readback['sha256']==summary['certificates_sha256'])
                    if not readback['matches_manifest']:reason='completed_artifact_mismatch'
            report=dict(status=reason,returncode=child.returncode,utc=utc(),elapsed=time.monotonic()-started,
                inputs_unchanged=all(digest(Path(path))==value for path,value in inputs.items()),
                generation_status=summary.get('status') if summary else None,
                exact_candidates=summary.get('certified_theory_clauses') if summary else None,
                methods=summary.get('methods') if summary else None,
                certificate_readback=readback,
                scope='Multiplier producer completion only. The independent arithmetic and RUP checks establish acceptance.')
            atomic(a.out/'terminal.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':main()
