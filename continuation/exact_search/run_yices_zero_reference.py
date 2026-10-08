#!/usr/bin/env python3
"""Actively supervised, input-bound independent Yices corroboration only."""
import argparse,hashlib,json,os,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXPECTED={8:'20d56e8ecd4bfad40ad5c7786c7865442c9961569dabb9e1a8dfe415b584c08f',
          9:'65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def atomic(path,data):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as f:json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    temporary.replace(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--m',type=int,choices=[8,9],required=True)
    a=p.parse_args();m=a.m
    source=HERE/f'zero_minimum{m}_reference_strict.smt2';assert sha(source)==EXPECTED[m]
    out=HERE/f'zero_minimum{m}_yices_reference_run1';assert not out.exists(),'Preserve earlier attempt'
    if m==9:
        calibration=json.loads((HERE/'zero_minimum8_yices_reference_run1/terminal.json').read_text())
        assert calibration['solver_verdict']=='unsat' and calibration['returncode']==0,'Nine only after successful eight calibration'
    seconds,hard,memory=(45,60,400) if m==8 else (900,950,700)
    binary=HERE/'yices/yices-2.7.0/bin/yices-smt2'
    assert sha(binary)=='eab7efbff2a6f0cce2fcd2c25cb4a94e0e048c902d8ef9e6fd7d7989aa54c501'
    current=int(Path('/sys/fs/cgroup/memory.current').read_text());maximum=int(Path('/sys/fs/cgroup/memory.max').read_text())
    stats=dict(line.split() for line in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())
    anonymous=int(stats['anon']);assert maximum-anonymous>(memory+500)*1024**2
    out.mkdir();original=source.read_bytes()
    data=original if b'(set-logic' in original else b'(set-logic QF_LRA)\n'+original
    submitted=out/'submitted.smt2';submitted.write_bytes(data)
    command=[str(binary),'--stats',f'--timeout={seconds}',str(submitted)]
    start=time.monotonic()
    def limit():resource.setrlimit(resource.RLIMIT_AS,(memory*1024**2,)*2)
    launch=dict(utc=utc(),input=str(source),input_sha256=sha(source),submitted_sha256=sha(submitted),
        adaptation='Only prepended (set-logic QF_LRA) when absent; original assertion bytes preserved exactly.',
        binary_sha256=sha(binary),command=command,solver_seconds=seconds,hard_wall_seconds=hard,
        address_space_mib=memory,memory_current=current,anonymous_memory=anonymous,
        scope='Independent solver verdict only; this is not an externally checked proof.')
    atomic(out/'started.json',launch);print(json.dumps(launch),flush=True)
    verdict=None;reason='child_completed'
    with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,preexec_fn=limit)
        try:
            while child.poll() is None:
                elapsed=time.monotonic()-start
                lines=(out/'stdout.log').read_text(errors='replace').splitlines()
                actual=next((v for v in lines if v in ('sat','unsat','unknown')),None)
                if actual is not None and verdict is None:
                    verdict=actual;atomic(out/'verdict.json',dict(result=verdict,utc=utc(),elapsed=elapsed,input_sha256=EXPECTED[m]))
                atomic(out/'heartbeat.json',dict(utc=utc(),elapsed=elapsed,solver_verdict=verdict))
                if elapsed>=hard:reason='hard_wall_killed';child.kill();child.wait();break
                try:child.wait(timeout=min(5,hard-elapsed))
                except subprocess.TimeoutExpired:pass
        finally:
            if child.poll() is None:child.kill();child.wait();reason='supervisor_interrupted'
            lines=(out/'stdout.log').read_text(errors='replace').splitlines()
            actual=next((v for v in lines if v in ('sat','unsat','unknown')),None)
            if actual is not None and verdict is None:
                verdict=actual;atomic(out/'verdict.json',dict(result=verdict,utc=utc(),elapsed=time.monotonic()-start,input_sha256=EXPECTED[m]))
            record=dict(status=reason,returncode=child.returncode,solver_verdict=verdict,
                elapsed=time.monotonic()-start,utc=utc(),input_sha256=EXPECTED[m],
                input_unchanged=sha(source)==EXPECTED[m],submitted_sha256=sha(submitted),
                stdout_sha256=sha(out/'stdout.log'),stderr_sha256=sha(out/'stderr.log'),
                scope='Independent solver corroboration only; no proof certificate was produced.')
            atomic(out/'terminal.json',record);print(json.dumps(record),flush=True)

if __name__=='__main__':main()
