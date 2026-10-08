#!/usr/bin/env python3
"""Learn exact sufficient extension regions in the eight-column prefix.

No bounded integer assumption is used: all costs are real and homogeneous.
Each excluded conjunction is certified to cover every ninth cost column.
An UNSAT result would still require replay/certification before publication.
"""
import argparse
import atexit
from datetime import datetime, timezone
from fractions import Fraction
from functools import reduce
import json
import math
from pathlib import Path
import resource
import signal
import sys
import time
import z3

sys.path.insert(0, str(Path(__file__).parent/'extension_geometry'))
from extension_oracle import analyse_prefix, verify_certificate, serial_number, reduce_region
from verify_extension_certificate import verify as independent_verify


def canonical_background():
    bg=[]
    def add(i,g,h):
        q=[0]*8;q[g]=1;q[h]=-1
        bg.append({'row':i,'coeffs':q})
    for i in range(3):
        for g in range(8):
            if g!=i:add(i,g,i)
    add(0,2,1)
    for g in range(3,7):add(0,g,g+1)
    return bg


def serial(v):
    if isinstance(v,Fraction):
        return serial_number(v)
    if isinstance(v,dict):
        return {k:serial(w) for k,w in v.items()}
    if isinstance(v,(list,tuple)):
        return [serial(w) for w in v]
    return v


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',required=True)
    ap.add_argument('--deadline',type=float,default=1800)
    ap.add_argument('--check-timeout',type=int,default=120)
    ap.add_argument('--oracle-timeout',type=int,default=30)
    ap.add_argument('--arith',type=int,default=2)
    ap.add_argument('--max-steps',type=int,default=10000)
    ap.add_argument('--memory-mib',type=int,default=1800)
    ap.add_argument('--resume',action='store_true')
    ap.add_argument('--fixed-minima',action='store_true')
    ap.add_argument('--restricted-ninth',action='store_true')
    ap.add_argument('--bounded-representative',action='store_true',
                    help='Use the independently justified B=11585 representative bound and row-local margins 1/B.')
    args=ap.parse_args()
    if args.bounded_representative:
        assert args.fixed_minima and args.restricted_ninth
    resource.setrlimit(resource.RLIMIT_AS,(args.memory_mib*1024**2,)*2)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    t0=time.monotonic()
    started=datetime.now(timezone.utc).isoformat()
    run_path=out/('run_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    run_record={'status':'running','started_utc':started,'config':vars(args),
                'note':'Only an explicit solver verdict establishes SAT or UNSAT.'}
    def save_run():
        run_path.write_text(json.dumps(run_record,indent=2)+'\n')
    def record_incomplete_exit():
        if run_record['status']=='running':
            run_record.update(status='interrupted_without_verdict',
                              ended_utc=datetime.now(timezone.utc).isoformat(),
                              elapsed_seconds=time.monotonic()-t0)
            save_run()
    def on_terminate(signum,frame):
        raise KeyboardInterrupt('termination requested')
    signal.signal(signal.SIGTERM,on_terminate)
    atexit.register(record_incomplete_exit)
    save_run()
    c=[[z3.Real(f'c_{i}_{g}') for g in range(8)] for i in range(3)]
    s=z3.SolverFor('QF_LRA')
    s.set(timeout=args.check_timeout*1000,**{'arith.solver':args.arith})
    def save_formula():
        # A checked SolverFor may emit nonstandard model-add metadata.
        # Export the identical assertions from a fresh, unrun solver.
        portable=z3.SolverFor('QF_LRA')
        portable.add(*s.assertions())
        (out/'formula.smt2').write_text(portable.sexpr()+'\n(check-sat)\n')
    # Independent positive row rescaling makes the three minima equal;
    # subsequent common scaling makes any finite selected strict margins >=1.
    bound=math.isqrt(8**9)
    delta=z3.RealVal(1)/bound
    def pos(v):
        if args.bounded_representative:return v>=delta
        return v>0 if args.fixed_minima else v>=1
    if args.fixed_minima:
        s.add(*[c[i][i]==1 for i in range(3)])
    else:
        s.add(c[0][0]==c[1][1],c[1][1]==c[2][2])
        s.add(c[0][0]>=1)
    for i in range(3):
        s.add(*[pos(c[i][g]-c[i][i]) for g in range(8) if g!=i])
        if args.bounded_representative:
            s.add(*[c[i][g]<=bound for g in range(8) if g!=i])
    s.add(pos(c[0][2]-c[0][1]))
    free=list(range(7,2,-1))
    s.add(*[pos(c[0][b]-c[0][a]) for a,b in zip(free,free[1:])])
    # After equalising positive minima, choose row 0 to have the smallest
    # prefix total. A generic perturbation can make the two comparisons
    # strict. The remaining swap of rows/minimum-columns 1 and 2 still
    # supplies c01<c02. All these finitely many margins scale together.
    # The representative bound only supplies margins for within-row forms.
    # The two comparisons between row totals remain strictly positive.
    def cross_pos(v):return v>0 if args.fixed_minima else v>=1
    s.add(cross_pos(z3.Sum(c[1])-z3.Sum(c[0])),
          cross_pos(z3.Sum(c[2])-z3.Sum(c[0])))
    seen=set()
    known_regions=[]
    history=[]
    background=canonical_background()
    lower=[[int(g==j) for g in range(8)] for j in (3,1,2)] if args.restricted_ninth else None
    def add_region(region):
        key=tuple((p['row'],tuple(p['coeffs'])) for p in region)
        if key in seen:return False
        seen.add(key)
        known_regions.append(region)
        values=[z3.Sum(*[q*v for q,v in zip(p['coeffs'],c[p['row']]) if q]) for p in region]
        if args.bounded_representative:
            s.add(z3.Or(*[v<=-delta for v in values]))
        else:
            s.add(z3.Or(*[v<0 if args.fixed_minima else v<=-1 for v in values]))
        return True
    first_step=0
    if args.resume:
        for file in sorted(out.glob('region_*.json')):
            old=json.loads(file.read_text())
            previous_lower=old.get('extension_domain_lower',[[0]*8 for _ in range(3)])
            if args.restricted_ninth:
                assert all(all(u<=v for u,v in zip(a,b)) for a,b in zip(previous_lower,lower))
            else:
                assert previous_lower==[[0]*8 for _ in range(3)]
            if old.get('domain_inequalities')!=background:
                old['domain_inequalities']=background
                reduce_region(old)
                old['compression_replay']=verify_certificate(old['prefix'],old)
                old['independent_replay']=independent_verify(old)
                file.write_text(json.dumps(serial(old),indent=2)+'\n')
            add_region(old['region'])
            first_step=max(first_step,int(file.stem.split('_')[1])+1)
        print(json.dumps({'stage':'resumed','unique_regions':len(seen),'next_step':first_step}),flush=True)
        run_record.update(resumed_regions=len(seen),next_step=first_step)
        save_run()
        if (out/'history.json').exists():
            history=json.loads((out/'history.json').read_text())
    (out/'config.json').write_text(json.dumps(vars(args),indent=2)+'\n')
    result=None
    for step in range(first_step,args.max_steps):
        if time.monotonic()-t0>=args.deadline:
            result={'status':'unknown','reason':'wall-clock deadline','steps':step}
            break
        ts=time.monotonic();status=s.check()
        entry={'step':step,'prefix_solver_status':str(status),'check_seconds':time.monotonic()-ts}
        if status!=z3.sat:
            result={'status':str(status),'reason':s.reason_unknown() if status==z3.unknown else None,'steps':step}
            history.append(entry)
            print(json.dumps(entry),flush=True)
            break
        mod=s.model()
        rows=[[Fraction(str(mod.eval(v,model_completion=True))) for v in row] for row in c]
        denominator=math.lcm(*(v.denominator for row in rows for v in row))
        rows=[[int(v*denominator) for v in row] for row in rows]
        base_rows=[list(row) for row in rows]
        # Avoid subset-sum equality walls while keeping every earlier
        # strict failed-region comparison. Original costs are integers;
        # multiplication gives the perturbation an explicit margin budget.
        factor=1000*5**8
        rows=[[v*factor+(0 if g==i else 5**g) for g,v in enumerate(row)]
              for i,row in enumerate(rows)]
        assert rows[0][0]==rows[1][1]==rows[2][2]>=1
        assert all(sum(q*v for q,v in zip(b['coeffs'],rows[b['row']]))>=1
                   for b in background)
        assert sum(rows[0])<sum(rows[1]) and sum(rows[0])<sum(rows[2])
        assert all(any(sum(q*v for q,v in zip(p['coeffs'],rows[p['row']]))<=-1
                       for p in reg) for reg in known_regions)
        to=time.monotonic()
        ans=analyse_prefix(rows,timeout_ms=args.oracle_timeout*1000,minimise=True,
                           domain_inequalities=background,extension_domain_lower=lower)
        entry.update(oracle_status=ans['status'],oracle_seconds=time.monotonic()-to,
                     largest_cost=max(v for row in rows for v in row))
        if ans['status']=='covered':
            receipt=verify_certificate(rows,ans)
            ans['prefix']=rows
            ans['replay']=receipt
            ans['independent_replay']=independent_verify(ans)
            ans['step']=step
            # The oracle may use a perturbed point outside the bounded box.
            # Its weak sufficient region must also contain the original
            # exact SMT point, so learning removes that point as intended.
            assert all(sum(q*v for q,v in zip(p['coeffs'],base_rows[p['row']]))>=0
                       for p in ans['region'])
            ans['unperturbed_prefix']=base_rows
            ans['unperturbed_prefix_in_region']=True
            (out/f'region_{step:05d}.json').write_text(json.dumps(serial(ans),indent=2)+'\n')
            assert add_region(ans['region']),'oracle repeated an excluded region'
            entry.update(region_premises=len(ans['region']),cover_boxes=len(ans['cover']),
                         cumulative_regions=len(seen))
        else:
            ans['prefix']=rows
            (out/'oracle_stop.json').write_text(json.dumps(serial(ans),indent=2)+'\n')
            result={'status':ans['status'],'steps':step,'note':'uncovered must be independently verified on all 19683 labelled allocations'}
        history.append(entry)
        run_record['last_completed_step']=step
        (out/'history.json').write_text(json.dumps(history,indent=2)+'\n')
        if step%10==0 or result:
            save_formula()
            save_run()
        print(json.dumps(entry),flush=True)
        if result:break
    if result is None:
        result={'status':'unknown','reason':'maximum step count','steps':len(seen)}
    result.update(elapsed_seconds=time.monotonic()-t0,statistics=str(s.statistics()))
    save_formula()
    (out/'history.json').write_text(json.dumps(history,indent=2)+'\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    run_record.update(status='finished',ended_utc=datetime.now(timezone.utc).isoformat(),
                      result=result)
    save_run()
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
