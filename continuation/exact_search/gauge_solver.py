#!/usr/bin/env python3
"""Gauge all three positive pinned minima together, then use unit margins.

Every row can first be scaled independently to make its positive pinned
minimum equal to one. A common positive dilation then makes every strict
atom selected by the finite Boolean formula have margin at least one.
Thus equal *free* minima plus unit margins preserve satisfiability of the
homogeneous strict formula. They do not bound integer or rational costs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
import z3
from strict_lra import build
from compute_cegis import integer_rows, partitions, evaluate_efx


def transform(expression, substitutions, cache):
    old = expression.get_id()
    if old in cache:
        return cache[old]
    if z3.is_and(expression):
        result = z3.And(*(transform(a, substitutions, cache) for a in expression.children()))
    elif z3.is_or(expression):
        result = z3.Or(*(transform(a, substitutions, cache) for a in expression.children()))
    elif expression.decl().kind() == z3.Z3_OP_GT:
        lhs, rhs = [z3.substitute(a, *substitutions) for a in expression.children()]
        result = lhs-rhs >= 1
    elif expression.decl().kind() == z3.Z3_OP_LT:
        lhs, rhs = [z3.substitute(a, *substitutions) for a in expression.children()]
        result = rhs-lhs >= 1
    else:
        result = z3.substitute(expression, *substitutions)
    cache[old] = result
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--m', type=int, default=9)
    p.add_argument('--timeout', type=int, default=600)
    p.add_argument('--arith', type=int, default=2)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--cap-mib', type=int, default=2450)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--cuts', choices=['none','single','pairs'], default='none')
    p.add_argument('--no-gauge', action='store_true')
    p.add_argument('--fixed-min', action='store_true', help='fix every row minimum to one; requires --strict')
    p.add_argument('--rowtotal-least', action='store_true', help='choose row0 to have least total after minimum normalisation')
    p.add_argument('--strict', action='store_true')
    p.add_argument('--rank-case', type=int, nargs=2)
    args = p.parse_args()
    limit = args.cap_mib << 20
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    original, c, info = build(args.m, timeout=args.timeout, arith=args.arith,
                             all_trims=False, row_symmetry=True,
                             rank_case=args.rank_case,
                             dominance=bool(args.rank_case), cuts=args.cuts)
    if args.fixed_min:
        if not args.strict:
            p.error('--fixed-min requires --strict; a fixed scale cannot support unit failure margins')
        substitutions = [(c[i][i], z3.RealVal(1)) for i in range(3)]
    else:
        substitutions = [] if args.no_gauge else [(c[1][1], c[0][0]), (c[2][2], c[0][0])]
    s = z3.SolverFor('QF_LRA')
    s.set(timeout=args.timeout*1000, random_seed=args.seed)
    s.set('arith.solver', args.arith)
    cache = {}
    for a in original.assertions():
        s.add(z3.substitute(a, *substitutions) if args.strict else transform(a, substitutions, cache))
    del original
    c = [[z3.substitute(x, *substitutions) for x in row] for row in c]
    if args.rowtotal_least:
        s.add(z3.Sum(c[0]) <= z3.Sum(c[1]), z3.Sum(c[0]) <= z3.Sum(c[2]))
    text = s.to_smt2()
    args.out.with_suffix('.smt2').write_text(text)
    built = time.monotonic()
    info.update(solver='z3-'+z3.get_version_string(), method='common-minimum gauge',
                assertions=len(s.assertions()), rowtotal_least=args.rowtotal_least,
                common_minimum=not args.no_gauge, fixed_minimum=args.fixed_min, unit_margin=not args.strict,
                args={k: str(v) if isinstance(v, Path) else v for k,v in vars(args).items()},
                build_seconds=built-start,
                formula_sha256=hashlib.sha256(text.encode()).hexdigest())
    print(json.dumps({'stage':'built',**info}), flush=True)
    status = s.check()
    info.update(status=str(status), check_seconds=time.monotonic()-built,
                statistics=str(s.statistics()), max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if status == z3.sat:
        rows = integer_rows(s.model(), c)
        good = evaluate_efx(rows, list(partitions(args.m)), args.m)
        info.update(rows=rows, full_exact_nonempty_efx_count=len(good), efx_allocations=good)
    elif status == z3.unknown:
        info['reason_unknown'] = s.reason_unknown()
    args.out.with_suffix('.json').write_text(json.dumps(info, indent=2)+'\n')
    print(json.dumps(info), flush=True)


if __name__ == '__main__':
    main()
