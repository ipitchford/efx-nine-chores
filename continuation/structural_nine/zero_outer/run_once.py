#!/usr/bin/env python3
"""One bounded zero-outer check. Preserve a verdict before model handling."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,json,os,resource,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SOURCE=OUT/'zero_minimum_final_outer.smt2'
EXPECTED='7652b9e62a367ac0ee3e09ef8bbb5882831f1292af372e5ae425ff58141a7331'


def write(name,value):
    path=OUT/name;temporary=path.with_suffix('.json.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def main():
    current=int(Path('/sys/fs/cgroup/memory.current').read_text())
    maximum=int(Path('/sys/fs/cgroup/memory.max').read_text())
    assert maximum-current>=1<<30,'Less than 1 GiB cgroup headroom; check not launched'
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    audit=json.loads((ROOT/'continuation/verification/zero_outer_audit.json').read_text())
    assert str(audit['status']).startswith('PASS')
    assert not (OUT/'run1_verdict.json').exists(),'One attempt only; preserve any existing verdict'
    resource.setrlimit(resource.RLIMIT_AS,(600*1024**2,)*2)
    started=time.monotonic()
    write('run1_started.json',dict(utc=datetime.now(timezone.utc).isoformat(),input_sha256=EXPECTED,
          cgroup_headroom_bytes=maximum-current,address_space_mib=600,total_check_budget_seconds=60))
    import z3
    solver=z3.SolverFor('QF_LRA');solver.set(**{'arith.solver':2})
    solver.from_file(str(SOURCE));assert len(solver.assertions())==6305
    timeout=max(1,int((60-(time.monotonic()-started))*1000));solver.set(timeout=timeout)
    write('run1_heartbeat.json',dict(phase='checking',timeout_ms=timeout,utc=datetime.now(timezone.utc).isoformat()))
    tick=time.monotonic();status=solver.check()
    verdict=dict(result=str(status),input=str(SOURCE),input_sha256=EXPECTED,solver=z3.get_version_string(),
                 assertions=6305,timeout_ms=timeout,check_seconds=time.monotonic()-tick,
                 elapsed=time.monotonic()-started,reason_unknown=solver.reason_unknown() if status==z3.unknown else None,
                 max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 scope='Outer model or raw solver result only; no full nine-chore conclusion is certified here.')
    write('run1_verdict.json',verdict);print(json.dumps(verdict),flush=True)
    if status==z3.sat:
        model=solver.model();coordinates={}
        for i in (1,2):
            for g in range(9):
                if g in (0,i):continue
                value=model.eval(z3.Real(f'c_{i}_{g}'),model_completion=True)
                coordinates[f'c_{i}_{g}']=str(Fraction(value.numerator_as_long(),value.denominator_as_long()))
        write('run1_model.json',dict(input_sha256=EXPECTED,coordinates=coordinates,
              scope='Two-row outer candidate only, not a three-agent counterexample.'))
    write('run1_completed.json',dict(utc=datetime.now(timezone.utc).isoformat(),elapsed=time.monotonic()-started,
          result=str(status),input_sha256=EXPECTED))


if __name__=='__main__':main()
