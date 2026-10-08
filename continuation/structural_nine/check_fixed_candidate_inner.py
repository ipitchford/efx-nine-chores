#!/usr/bin/env python3
"""One supervised candidate check, with a durable verdict before extraction."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,itertools,json,os,resource,subprocess,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'fixed_zero_outer_candidate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):
    target=OUT/name;temporary=target.with_suffix(target.suffix+'.tmp')
    with temporary.open('w') as f:
        json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    temporary.replace(target)
def utc():return datetime.now(timezone.utc).isoformat()

def worker():
    resource.setrlimit(resource.RLIMIT_AS,(600*1024**2,)*2)
    import z3
    sys.path.insert(0,str(HERE.parent))
    from certify_row_cores import certify
    from verify_row_cores import verify
    start=time.monotonic();deadline=start+60
    prep=json.loads((OUT/'preparation.json').read_text())
    compatible=prep['compatible_allocations'];positive=None
    for name in ('zero','positive'):
        source=Path(prep['inputs'][name]['path']);assert sha(source)==prep['inputs'][name]['sha256']
        formulas=list(z3.parse_smt2_file(str(source)));n=prep['inputs'][name]['domain_assertions']
        solver=z3.SolverFor('QF_LRA');solver.set(**{'arith.solver':2,'unsat_core':True})
        solver.add(*formulas[:n])
        gates=[z3.Bool(f'a_{r["allocation_id"]}') for r in compatible]
        for gate,failure in zip(gates,formulas[n:]):solver.add(z3.Implies(gate,failure))
        solver.set(timeout=max(1,int((deadline-time.monotonic())*1000)))
        write('worker_heartbeat.json',dict(stage=name+'_check',utc=utc(),elapsed=time.monotonic()-start))
        tick=time.monotonic();status=solver.check(*gates)
        verdict=dict(result=str(status),input_sha256=sha(source),input=str(source),
            solver=z3.get_version_string(),check_seconds=time.monotonic()-tick,
            elapsed=time.monotonic()-start,reason=solver.reason_unknown() if status==z3.unknown else None)
        write(name+'_verdict.json',verdict);print(json.dumps(verdict),flush=True)
        if status==z3.sat:
            model=solver.model()
            row=[]
            for g in range(9):
                if name=='zero' and g in (0,1):row.append(Fraction(g));continue
                v=model.eval(z3.Real(f'c_0_{g}'),model_completion=True)
                row.append(Fraction(v.numerator_as_long(),v.denominator_as_long()))
            matrix=[row]+[[Fraction(v) for v in r] for r in prep['fixed_rows']]
            witnesses=[]
            for aid,a in enumerate(itertools.product(range(3),repeat=9)):
                A=[[g for g in range(9) if a[g]==i] for i in range(3)]
                if all(sum(matrix[i][h] for h in A[i] if h!=g)<=sum(matrix[i][h] for h in A[j])
                       for i in range(3) for g in A[i] for j in range(3)):
                    witnesses.append(aid)
            report=dict(matrix=[[str(v) for v in r] for r in matrix],allocations_checked=3**9,
                literal_deletion_efx_allocations=witnesses,input_sha256=sha(source))
            write(name+'_full_model_check.json',report)
            assert not witnesses,'SAT input was not a counterexample under exhaustive literal verification'
            break
        if status!=z3.unsat:break
        ids={int(str(v)[2:]) for v in solver.unsat_core()}
        write(name+'_raw_core.json',dict(allocation_ids=sorted(ids),input_sha256=sha(source)))
        if name=='positive':positive=(solver,gates,formulas,n,ids)
    if positive is not None:
        solver,gates,formulas,n,ids=positive
        keep=[k for k,r in enumerate(compatible) if r['allocation_id'] in ids]
        checks=[]
        for index in list(keep):
            remaining=deadline-time.monotonic()
            if remaining<=0:break
            solver.set(timeout=max(1,min(1000,int(remaining*1000))))
            trial=[k for k in keep if k!=index];status=solver.check(*(gates[k] for k in trial))
            checks.append(dict(allocation_id=compatible[index]['allocation_id'],result=str(status)))
            if status==z3.unsat:keep=trial
        allocations=[compatible[k]['allocation'] for k in keep]
        ids=[compatible[k]['allocation_id'] for k in keep]
        raw=set()
        for a in allocations:
            for i in (1,2):
                for removed in range(9):
                    if a[removed]!=i:continue
                    for j in range(3):
                        if i==j:continue
                        v=tuple(int(a[g]==i and g!=removed)-int(a[g]==j) for g in range(9))
                        if any(x>0 for x in v):raw.add((i,v))
        raw=sorted(raw)
        def dominates(a,b):return a[0]==b[0] and sum(a[1])<=sum(b[1]) and all(a[1][g]<=b[1][g] for g in range(9) if g!=a[0])
        zeros={i:(i,(0,)*9) for i in (1,2)}
        surviving=[a for a in raw if not dominates(a,zeros[a[0]])]
        retained=[a for a in surviving if not any(a!=b and dominates(a,b) for b in surviving)]
        dominance=[dict(raw_index=k,zero=dominates(a,zeros[a[0]]),retained_index=None if dominates(a,zeros[a[0]]) else next(j for j,b in enumerate(retained) if dominates(a,b))) for k,a in enumerate(raw)]
        core=z3.SolverFor('QF_LRA');core.add(*formulas[:n],*(formulas[n+k] for k in keep))
        corefile=OUT/'positive_core.smt2';corefile.write_text(core.sexpr()+'\n(check-sat)\n')
        record=dict(core_size=len(ids),core_allocation_ids=ids,core_allocations=allocations,
            core_sha256=sha(corefile),other_rows=prep['fixed_rows'],inner_method='QF_LRA_solver',
            region_atoms=[dict(agent=i,coefficients=list(v)) for i,v in raw],
            compressed_region_atoms=[dict(agent=i,coefficients=list(v)) for i,v in retained],
            dominance_certificate=dominance,compression_counts=dict(raw=len(raw),kept=len(retained)),
            source_positive_input_sha256=prep['inputs']['positive']['sha256'],minimization_checks=checks)
        fixed=[[Fraction(v) for v in r] for r in prep['fixed_rows']]
        assert all(sum(v[g]*fixed[i-1][g] for g in range(9))<=0 for i,v in raw)
        write('region.json',record)
        write('worker_heartbeat.json',dict(stage='certifying',core_size=len(ids),utc=utc()))
        certificate=certify(record,{},timeout=max(1,min(5000,int((85-(time.monotonic()-start))*1000))))
        verification=verify(certificate)
        write('exact_certificate.json',certificate);write('certificate_verification.json',verification)
        print(json.dumps(dict(stage='certified',core_size=len(ids),verification=verification)),flush=True)
    write('worker_completed.json',dict(utc=utc(),elapsed=time.monotonic()-start))

def supervise():
    assert not (OUT/'supervisor_started.json').exists(),'Preserve the one authorized attempt'
    prep=json.loads((OUT/'preparation.json').read_text())
    for source in prep['inputs'].values():assert sha(Path(source['path']))==source['sha256']
    current=int(Path('/sys/fs/cgroup/memory.current').read_text());maximum=int(Path('/sys/fs/cgroup/memory.max').read_text())
    assert maximum-current>=1<<30,'Insufficient headroom'
    start=time.monotonic();write('supervisor_started.json',dict(utc=utc(),memory_mib=600,solver_budget_seconds=60,hard_wall_seconds=90,headroom_bytes=maximum-current,worker_sha256=sha(Path(__file__))))
    with (OUT/'worker.log').open('w') as log:
        child=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker'],stdout=log,stderr=subprocess.STDOUT)
        termination='child_completed'
        try:
            while child.poll() is None:
                elapsed=time.monotonic()-start;write('supervisor_heartbeat.json',dict(utc=utc(),elapsed=elapsed))
                if elapsed>=90:
                    termination='hard_wall_killed';child.kill();child.wait();break
                try:child.wait(timeout=min(5,90-elapsed))
                except subprocess.TimeoutExpired:pass
        finally:
            if child.poll() is None:child.kill();child.wait();termination='supervisor_interrupted'
            verdicts={n:json.loads((OUT/(n+'_verdict.json')).read_text()) for n in ('zero','positive') if (OUT/(n+'_verdict.json')).exists()}
            report=dict(status=termination,child_returncode=child.returncode,elapsed=time.monotonic()-start,utc=utc(),verdicts=verdicts)
            write('supervisor_completed.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':
    worker() if '--worker' in sys.argv else supervise()
