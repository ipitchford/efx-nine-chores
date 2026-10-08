#!/usr/bin/env python3
"""Complete finite-domain CP-SAT translation of the common-minimum formula.

The default bound is derived in finite_integer_bound.md. Reified atoms use
only the sound implication b -> inequality; all clauses are positive ORs,
so this is equisatisfiable. Every SAT candidate is checked literally over
all3**m complete allocations. UNSAT here is a solver result, not an
externally checked proof certificate.
"""
import argparse
import hashlib
import itertools
import json
from math import isqrt
from pathlib import Path
import resource
import sys
import time

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
sys.path.insert(0,str(HERE/'ortools_runtime'))
sys.path.insert(0,str(PROJECT/'src'))
import ortools
from ortools.sat.python import cp_model
import z3
from efx_exact import efx


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path)
    ap.add_argument('--m',type=int,choices=[8,9],required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--timeout',type=float,default=180)
    ap.add_argument('--workers',type=int,default=1)
    ap.add_argument('--cap-mib',type=int,default=1800)
    ap.add_argument('--bound',type=int)
    ap.add_argument('--all-different',action='store_true')
    ap.add_argument('--rowtotal-least',action='store_true')
    ap.add_argument('--linearization',type=int,choices=[0,1,2],default=1)
    args=ap.parse_args()
    cap=args.cap_mib<<20
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();m=args.m;d=3*m-2
    derived=isqrt((m-1)**d)
    bound=derived if args.bound is None else args.bound
    assert 1<=bound<=10**15
    complete=bound>=derived
    model=cp_model.CpModel()
    names=['c_0_0']+[f'c_{i}_{g}' for i in range(3) for g in range(m) if g!=i]
    assert len(names)==d and len(set(names))==d
    variables={name:model.new_int_var(1,bound,name) for name in names}
    rows=[[variables['c_0_0' if g==i else f'c_{i}_{g}'] for g in range(m)] for i in range(3)]
    expressions=z3.parse_smt2_file(str(args.input))
    seen=set();cache={}
    def linear(e):
        key=e.get_id()
        if key in cache:return cache[key]
        result={};constant=0
        if z3.is_rational_value(e):
            if e.denominator_as_long()!=1:raise ValueError('noninteger input coefficient')
            constant=e.numerator_as_long()
        elif z3.is_const(e) and e.decl().kind()==z3.Z3_OP_UNINTERPRETED:
            name=str(e)
            if name not in variables:raise ValueError('input not a free-common-minimum formula: '+name)
            seen.add(name);result[name]=1
        elif z3.is_add(e) or z3.is_sub(e):
            for k,a in enumerate(e.children()):
                sub,c=linear(a);sgn=-1 if z3.is_sub(e) and k else 1
                constant+=sgn*c
                for name,v in sub.items():result[name]=result.get(name,0)+sgn*v
        elif z3.is_mul(e):
            coefficient=1;nonconstant=[]
            for a in e.children():
                if z3.is_rational_value(a):
                    assert a.denominator_as_long()==1
                    coefficient*=a.numerator_as_long()
                else:nonconstant.append(a)
            assert len(nonconstant)<=1
            if nonconstant:
                sub,c=linear(nonconstant[0]);result={k:coefficient*v for k,v in sub.items()};constant=coefficient*c
            else:constant=coefficient
        elif e.decl().kind()==z3.Z3_OP_UMINUS:
            sub,c=linear(e.arg(0));result={k:-v for k,v in sub.items()};constant=-c
        else:raise ValueError('unsupported linear input '+str(e))
        result={k:v for k,v in result.items() if v}
        cache[key]=(result,constant)
        return result,constant
    def inequality(a):
        op=a.decl().kind()
        if op not in (z3.Z3_OP_GE,z3.Z3_OP_GT,z3.Z3_OP_LE,z3.Z3_OP_LT):
            raise ValueError('unsupported atom '+str(a))
        left,cl=linear(a.arg(0));right,cr=linear(a.arg(1))
        coeff=left.copy()
        for name,v in right.items():coeff[name]=coeff.get(name,0)-v
        constant=cl-cr
        if op in (z3.Z3_OP_LE,z3.Z3_OP_LT):
            coeff={k:-v for k,v in coeff.items()};constant=-constant
        rhs=-constant+(1 if op in (z3.Z3_OP_LT,z3.Z3_OP_GT) else 0)
        return tuple(sorted((k,v) for k,v in coeff.items() if v)),rhs
    atoms={};clauses=0;domains=0
    def expression(coeff):return sum(v*variables[k] for k,v in coeff)
    for a in expressions:
        if z3.is_or(a):
            literals=[]
            for atom in a.children():
                key=inequality(atom)
                if key not in atoms:
                    indicator=model.new_bool_var(f'failure_{len(atoms)}')
                    model.add(expression(key[0])>=key[1]).only_enforce_if(indicator)
                    atoms[key]=indicator
                literals.append(atoms[key])
            model.add_bool_or(literals);clauses+=1
        else:
            coeff,rhs=inequality(a);model.add(expression(coeff)>=rhs);domains+=1
    assert seen==set(names)
    assert clauses==3**m-3*2**m+3
    if args.all_different:
        for row in rows:model.add_all_different(row)
    if args.rowtotal_least:
        model.add(sum(rows[0])<=sum(rows[1]));model.add(sum(rows[0])<=sum(rows[2]))
    model_file=args.out.with_suffix('.pbtxt')
    model.export_to_file(str(model_file))
    validation=model.validate()
    if validation:raise ValueError(validation)
    built=time.monotonic()
    record=dict(solver='OR-Tools CP-SAT '+ortools.__version__,m=m,free_cost_variables=d,
                input=str(args.input.resolve()),input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                model_file=str(model_file.resolve()),model_sha256=hashlib.sha256(model_file.read_bytes()).hexdigest(),
                derived_complete_bound=derived,search_bound=bound,complete_bound=complete,
                allocation_clauses=clauses,domain_assertions=domains,shared_atoms=len(atoms),
                all_different=args.all_different,rowtotal_least=args.rowtotal_least,
                workers=args.workers,linearization=args.linearization,cap_mib=args.cap_mib,
                build_seconds=built-started,proof_status='no external proof certificate')
    record['memory_before_search']={k:v.strip() for k,v in (line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line) if k in ('VmRSS','VmSize','VmPeak')}
    args.out.with_suffix('.json').write_text(json.dumps(dict(stage='built; search pending',**record),indent=2)+'\n')
    print(json.dumps(dict(stage='built',**record)),flush=True)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.timeout
    solver.parameters.num_workers=args.workers
    solver.parameters.linearization_level=args.linearization
    solver.parameters.log_search_progress=True
    solver.parameters.log_to_stdout=False
    with args.out.with_suffix('.log').open('w') as log:
        def logging(line):
            log.write(line+'\n');log.flush()
        solver.log_callback=logging
        try:
            status=solver.solve(model)
        except Exception as error:
            record.update(status='NATIVE_EXCEPTION_NO_VERDICT',exception=type(error).__name__+': '+str(error),
                          check_seconds=time.monotonic()-built,
                          max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          conclusion='NO_RESULT')
            args.out.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
            print(json.dumps(record),flush=True)
            return
    record.update(status=solver.status_name(status),check_seconds=time.monotonic()-built,
                  response_statistics=solver.response_stats(),
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        costs=[[int(solver.value(v)) for v in row] for row in rows]
        good=[list(a) for a in itertools.product(range(3),repeat=m) if efx(costs,a)]
        record.update(rows=costs,literal_complete_allocations_checked=3**m,literal_efx_count=len(good),literal_efx_allocations=good)
        record['conclusion']='EXACT_COUNTEREXAMPLE' if not good else 'ENCODER_OR_SOLVER_MISMATCH'
    elif status==cp_model.INFEASIBLE:
        record['conclusion']='UNSAT_COMPLETE_DERIVED_BOUND' if complete else 'UNSAT_RESTRICTED_BOUND_ONLY'
    else:record['conclusion']='NO_RESULT'
    args.out.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record),flush=True)


if __name__=='__main__':main()
