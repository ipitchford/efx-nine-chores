#!/usr/bin/env python3
"""Capture exact arithmetic clauses without retaining Z3's native proof DAG.

This is an untrusted certificate producer. An independent checker must validate
every arithmetic lemma, bind the original clauses, and refute the resulting
Boolean formula. A captured solver verdict alone is not such a certificate.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import resource
import time
import z3


def atomic(path, obj):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2) + '\n')
    tmp.replace(path)


def utc():
    return datetime.now(timezone.utc).isoformat()


class Collector:
    def __init__(self, solver, directory, names):
        self.solver, self.directory, self.names = solver, directory, names
        self.index = {name: j for j, name in enumerate(names)}
        self.n = len(names)
        self.linear_cache = {}
        self.literal_cache = {}
        self.atoms = {}
        self.inputs = set()
        self.theories = set()
        self.assumptions = set()
        self.counts = Counter()
        self.errors = []
        self.files = {k: (directory / (k + '.jsonl')).open('w')
                      for k in ['atoms', 'input_clauses', 'theory_clauses', 'assumptions']}

    def write(self, kind, obj):
        self.files[kind].write(json.dumps(obj, separators=(',', ':')) + '\n')

    def affine(self, expr):
        ident = expr.get_id()
        if ident in self.linear_cache:
            return self.linear_cache[ident][1]
        out = [Fraction(0)] * (self.n + 1)
        if z3.is_rational_value(expr):
            out[-1] = Fraction(expr.numerator_as_long(), expr.denominator_as_long())
        elif z3.is_const(expr) and expr.decl().kind() == z3.Z3_OP_UNINTERPRETED:
            out[self.index[str(expr.decl().name())]] = 1
        else:
            kind = expr.decl().kind()
            parts = [self.affine(ch) for ch in expr.children()]
            if kind == z3.Z3_OP_ADD:
                out = [sum(values) for values in zip(*parts)]
            elif kind == z3.Z3_OP_SUB:
                out = [parts[0][j] - sum(p[j] for p in parts[1:]) for j in range(self.n + 1)]
            elif kind == z3.Z3_OP_UMINUS:
                out = [-v for v in parts[0]]
            elif kind == z3.Z3_OP_MUL:
                nonconstants = [p for p in parts if any(p[:-1])]
                if len(nonconstants) > 1:
                    raise ValueError('nonlinear multiplication')
                scale = math.prod(p[-1] for p in parts if not any(p[:-1]))
                if nonconstants:
                    out = [scale * v for v in nonconstants[0]]
                else:
                    out[-1] = scale
            elif kind == z3.Z3_OP_DIV and len(parts) == 2 and not any(parts[1][:-1]):
                out = [v / parts[1][-1] for v in parts[0]]
            else:
                raise ValueError('unsupported affine expression: ' + expr.sexpr())
        out = tuple(Fraction(v) for v in out)
        # Hold the AST reference as well, so native AST ids cannot be recycled.
        self.linear_cache[ident] = (expr, out)
        return out

    def literal(self, expr):
        ident = expr.get_id()
        if ident in self.literal_cache:
            return self.literal_cache[ident][1]
        if z3.is_true(expr):
            answer = 1
        elif z3.is_false(expr):
            answer = -1
        elif z3.is_not(expr):
            answer = -self.literal(expr.arg(0))
        else:
            kind = expr.decl().kind()
            if kind not in [z3.Z3_OP_LE, z3.Z3_OP_GE, z3.Z3_OP_LT, z3.Z3_OP_GT]:
                raise ValueError('unsupported literal: ' + expr.sexpr())
            left, right = self.affine(expr.arg(0)), self.affine(expr.arg(1))
            vector = [a - b for a, b in zip(left, right)]
            sign = 1
            if kind in [z3.Z3_OP_GE, z3.Z3_OP_LT]:
                vector = [-v for v in vector]
            if kind in [z3.Z3_OP_GT, z3.Z3_OP_LT]:
                sign = -1
            denominator = math.lcm(*(v.denominator for v in vector))
            vector = [int(v * denominator) for v in vector]
            divisor = math.gcd(*vector)
            if divisor:
                vector = [v // divisor for v in vector]
            if not any(vector[:-1]):
                answer = sign * (1 if vector[-1] <= 0 else -1)
            else:
                key = tuple(vector)
                if key not in self.atoms:
                    number = len(self.atoms) + 2
                    self.atoms[key] = number
                    self.write('atoms', {'id': number, 'affine_le_zero': vector})
                answer = sign * self.atoms[key]
        self.literal_cache[ident] = (expr, answer)
        return answer

    def clause(self, expressions):
        result = set(self.literal(e) for e in expressions)
        if 1 in result or any(-v in result for v in result):
            return None
        result.discard(-1)
        return tuple(sorted(result))

    def record_inputs(self, assertions):
        self.write('input_clauses', {'source_assertion': -1, 'clause': [1]})
        self.inputs.add((1,))
        for j, assertion in enumerate(assertions):
            children = assertion.children() if z3.is_or(assertion) else [assertion]
            clause = self.clause(children)
            self.write('input_clauses', {'source_assertion': j, 'clause': clause})
            if clause is not None:
                self.inputs.add(clause)

    def callback(self, proof, dependencies, clause):
        try:
            hint = str(proof.decl().name())
            self.counts[hint] += 1
            if hint in ['rup', 'del']:
                return
            canonical = self.clause(clause)
            if hint == 'assumption':
                if canonical not in self.assumptions:
                    self.assumptions.add(canonical)
                    self.write('assumptions', {'clause': canonical,
                        'exact_original_clause': canonical in self.inputs})
            elif hint == 'smt':
                if canonical is not None and canonical not in self.theories:
                    self.theories.add(canonical)
                    self.write('theory_clauses', {'clause': canonical})
            else:
                raise ValueError('unexpected proof hint: ' + proof.sexpr())
        except BaseException as error:
            self.errors.append(type(error).__name__ + ': ' + str(error))
            self.solver.interrupt()

    def close(self):
        for stream in self.files.values():
            stream.flush()
            stream.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--timeout', type=int, required=True)
    parser.add_argument('--cap-mib', type=int, required=True)
    args = parser.parse_args()
    cap = args.cap_mib << 20
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    args.out.mkdir(parents=True, exist_ok=False)
    data = args.input.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert digest == args.expected_sha256
    status = dict(status='starting', started_at_utc=utc(), input=str(args.input.resolve()),
                  input_sha256=digest, solver='z3-' + z3.get_version_string(),
                  solver_timeout_seconds=args.timeout, address_space_cap_mib=args.cap_mib,
                  native_proof_retention=False, independent_certificate_status='pending')
    atomic(args.out / 'receipt.json', status)
    started = time.monotonic()
    solver = z3.SolverFor('QF_LRA')
    solver.set(timeout=args.timeout * 1000, random_seed=0)
    solver.set('arith.solver', 2)
    solver.from_string(data.decode())
    assertions = list(solver.assertions())
    names = sorted({str(v) for a in assertions for v in z3.z3util.get_vars(a)})
    collector = Collector(solver, args.out, names)
    collector.record_inputs(assertions)
    atomic(args.out / 'metadata.json', {'variables': names, 'true_atom': 1,
                                      'assertions': len(assertions), 'input_sha256': digest})
    del data, assertions
    callback = z3.OnClause(solver, collector.callback)
    checked = time.monotonic()
    status.update(status='running', check_started_at_utc=utc(), setup_seconds=checked-started)
    atomic(args.out / 'receipt.json', status)
    print(json.dumps(status), flush=True)
    try:
        result = solver.check()
        status.update(solver_verdict=str(result), status=str(result), check_seconds=time.monotonic()-checked)
        if result == z3.unknown:
            status['reason_unknown'] = solver.reason_unknown()
        atomic(args.out / 'receipt.json', status)
    except BaseException as error:
        status.update(status='exception_without_verdict', exception=repr(error))
        raise
    finally:
        collector.close()
        status.update(finished_at_utc=utc(), elapsed_seconds=time.monotonic()-started,
                      max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      event_counts=dict(collector.counts), unique_atoms=len(collector.atoms),
                      unique_theory_clauses=len(collector.theories),
                      unmatched_assumption_clauses=sum(c is not None and c not in collector.inputs
                                                     for c in collector.assumptions),
                      callback_errors=collector.errors)
        status['files'] = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                                  'bytes': p.stat().st_size}
                           for p in args.out.glob('*.jsonl')}
        atomic(args.out / 'receipt.json', status)
        print(json.dumps(status), flush=True)
    if collector.errors:
        raise RuntimeError('callback capture failed; see receipt')


if __name__ == '__main__':
    main()
