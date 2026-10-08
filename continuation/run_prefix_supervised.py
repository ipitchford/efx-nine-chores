#!/usr/bin/env python3
"""Run the bounded-prefix refinement with a durable, enforced wall limit."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'continuation'/'prefix_regions_bounded1'
HARD=650

def now():return datetime.now(timezone.utc).isoformat()

def save(path,record):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(record,indent=2)+'\n')
    temporary.replace(path)

def alarm():
    signal.signal(signal.SIGALRM,signal.SIG_DFL)
    signal.alarm(HARD)

def main():
    command=[sys.executable,'-u',str(ROOT/'continuation'/'prefix_cegis.py'),
             '--out',str(OUT),'--resume','--fixed-minima','--restricted-ninth',
             '--bounded-representative','--deadline','600','--check-timeout','60',
             '--memory-mib','1800','--max-steps','5000']
    record={'status':'starting','started_utc':now(),'command':command,
            'algorithm_budget_seconds':600,'hard_wall_seconds':HARD,
            'runner_sha256':hashlib.sha256((ROOT/'continuation'/'prefix_cegis.py').read_bytes()).hexdigest(),
            'resumed_region_files':len(list(OUT.glob('region_*.json'))),
            'scope':'A bounded necessary-condition relaxation. SAT alone is not a counterexample.'}
    target=OUT/'supervisor.json'
    save(target,record);save(OUT/'supervisor_started.json',record)
    started=time.monotonic()
    with (OUT/'run.log').open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                                 start_new_session=True,preexec_fn=alarm)
        record.update(status='running',child_pid=process.pid)
        save(target,record)
        killed=False
        try:
            while process.poll() is None:
                remaining=HARD-(time.monotonic()-started)
                if remaining<=0:
                    os.killpg(process.pid,signal.SIGKILL);killed=True
                    process.wait(timeout=5)
                    break
                try:process.wait(timeout=min(5,remaining))
                except subprocess.TimeoutExpired:
                    record.update(heartbeat_utc=now(),elapsed_seconds=time.monotonic()-started)
                    save(target,record)
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGKILL);killed=True
                process.wait(timeout=5)
            result_path=OUT/'result.json'
            result=json.loads(result_path.read_text()) if result_path.exists() else None
            record.update(status='completed_with_algorithm_result' if result else 'terminated_without_algorithm_result',
                          result=result,child_returncode=process.returncode,hard_killed=killed,
                          finished_utc=now(),elapsed_seconds=time.monotonic()-started,
                          completed_region_files=len(list(OUT.glob('region_*.json'))))
            save(target,record)
            print(json.dumps(record),flush=True)

if __name__=='__main__':main()
