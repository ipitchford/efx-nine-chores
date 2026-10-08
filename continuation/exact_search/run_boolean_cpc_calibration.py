#!/usr/bin/env python3
"""Bounded Boolean CPC producer stage; replay remains a separate operation."""
import hashlib,json,os,resource,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'zero8_clause_capture_run2/boolean'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def atomic(path,data):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)

def main():
    prep=json.loads((OUT/'preparation.json').read_text());source=OUT/'all_clauses.smt2'
    assert sha(source)==prep['boolean_sha256'];assert not (OUT/'producer_started.json').exists()
    runner=HERE/'check_boolean_cvc5.py'
    command=[sys.executable,'-u',str(runner),str(source),
        '--expected-input-sha256',prep['boolean_sha256'],
        '--verdict-report',str(OUT/'verdict.json'),'--export-status-report',str(OUT/'export_status.json'),
        '--output',str(OUT/'proof'),'--report',str(OUT/'export_report.json'),
        '--core-prefix',str(OUT/'core'),'--timeout','120','--address-space-mib','1200']
    def limit():resource.setrlimit(resource.RLIMIT_AS,(1200*1024**2,)*2)
    started=time.monotonic();launch=dict(utc=utc(),command=command,input_sha256=sha(source),runner_sha256=sha(runner),memory_mib=1200,solver_seconds=120,hard_wall_seconds=180)
    atomic(OUT/'producer_started.json',launch);print(json.dumps(launch),flush=True)
    reason='child_completed'
    with (OUT/'producer.log').open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
        try:
            while child.poll() is None:
                elapsed=time.monotonic()-started;atomic(OUT/'producer_heartbeat.json',dict(utc=utc(),elapsed=elapsed))
                if elapsed>=180:child.kill();child.wait();reason='hard_wall_killed';break
                try:child.wait(timeout=min(5,180-elapsed))
                except subprocess.TimeoutExpired:pass
        finally:
            if child.poll() is None:child.kill();child.wait();reason='supervisor_interrupted'
            verdict=json.loads((OUT/'verdict.json').read_text()) if (OUT/'verdict.json').exists() else None
            result=dict(status=reason,returncode=child.returncode,utc=utc(),elapsed=time.monotonic()-started,
                solver_verdict=verdict['result'] if verdict else None,input_sha256=sha(source),
                input_unchanged=sha(source)==prep['boolean_sha256'],core_saved=(OUT/'core.json').exists(),proof_saved=(OUT/'proof.cpc').exists())
            atomic(OUT/'producer_terminal.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
