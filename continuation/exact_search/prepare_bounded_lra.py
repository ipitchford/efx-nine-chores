#!/usr/bin/env python3
"""Prepare two exact bounded-LRA forms from the reviewed rowwise integer bound.

Fractional form: minimum=1, every strict atom becomes a >=1/B atom,
and every nonminimum cost is <=B. Unit form scales all costs by B:
minimum=B, margin=1, upper bound=B**2. This is an existence reduction,
not pointwise equivalence of arbitrary strict real-valued matrices.
No solver check is performed here.
"""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import isqrt
from pathlib import Path
import resource
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (1100 << 20, 1100 << 20))
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
import z3


def normalize(assertions, m, minimum, margin, upper):
    substitutions = [(z3.Real(f"c_{i}_{i}"), z3.RealVal(minimum)) for i in range(3)]
    atom_cache = {}; linear_cache = {}
    def affine(expression):
        key = expression.get_id()
        if key not in linear_cache: linear_cache[key] = z3.substitute(expression, *substitutions)
        return linear_cache[key]
    def transform(expression):
        key = expression.get_id()
        if key in atom_cache: return atom_cache[key]
        if z3.is_or(expression): result = z3.Or(*(transform(child) for child in expression.children()))
        elif z3.is_and(expression): result = z3.And(*(transform(child) for child in expression.children()))
        elif z3.is_gt(expression): result = affine(expression.arg(0)) - affine(expression.arg(1)) >= margin
        elif z3.is_lt(expression): result = affine(expression.arg(1)) - affine(expression.arg(0)) >= margin
        else: raise ValueError("Unexpected source assertion: " + str(expression))
        atom_cache[key] = result
        return result
    result = [transform(assertion) for assertion in assertions]
    result += [z3.Real(f"c_{i}_{g}") <= upper for i in range(3) for g in range(m) if g != i]
    return result


def scaling_audit(fractional, unit, bound):
    """Check every affine coefficient and Boolean connective under q=B*x."""
    affine_cache = {}; pair_cache = set(); atoms = 0
    def affine(expression):
        key = expression.get_id()
        if key in affine_cache: return affine_cache[key]
        coefficients = {}; constant = Fraction(0)
        if z3.is_rational_value(expression): constant = Fraction(expression.numerator_as_long(), expression.denominator_as_long())
        elif z3.is_const(expression) and expression.decl().kind() == z3.Z3_OP_UNINTERPRETED: coefficients[str(expression)] = Fraction(1)
        elif z3.is_add(expression) or z3.is_sub(expression):
            for k, child in enumerate(expression.children()):
                child_coeff, child_constant = affine(child)
                sign = -1 if z3.is_sub(expression) and k else 1
                constant += sign * child_constant
                for name, value in child_coeff.items(): coefficients[name] = coefficients.get(name, 0) + sign * value
        elif z3.is_div(expression):
            numerator_coeff, numerator_constant = affine(expression.arg(0))
            denominator_coeff, denominator_constant = affine(expression.arg(1))
            assert not denominator_coeff and denominator_constant != 0
            coefficients = {name: value / denominator_constant for name, value in numerator_coeff.items()}
            constant = numerator_constant / denominator_constant
        else: raise ValueError("Unsupported affine expression: " + str(expression))
        coefficients = {name: value for name, value in coefficients.items() if value}
        affine_cache[key] = coefficients, constant
        return coefficients, constant
    def row(expression):
        assert z3.is_ge(expression) or z3.is_le(expression)
        left, lc = affine(expression.arg(0)); right, rc = affine(expression.arg(1))
        coefficients = left.copy()
        for name, value in right.items(): coefficients[name] = coefficients.get(name, 0) - value
        constant = lc - rc
        if z3.is_le(expression): coefficients = {name: -value for name, value in coefficients.items()}; constant = -constant
        return {name: value for name, value in coefficients.items() if value}, constant
    def compare(a, b):
        nonlocal atoms
        key = a.get_id(), b.get_id()
        if key in pair_cache: return
        pair_cache.add(key)
        if z3.is_or(a) or z3.is_and(a):
            assert a.decl().kind() == b.decl().kind() and a.num_args() == b.num_args()
            for x, y in zip(a.children(), b.children()): compare(x, y)
        else:
            ac, ak = row(a); bc, bk = row(b)
            assert ac == bc and bk == bound * ak
            atoms += 1
    assert len(fractional) == len(unit)
    for a, b in zip(fractional, unit): compare(a, b)
    return atoms


def prepare(m):
    started = time.monotonic(); bound = isqrt((m-1)**m)
    source = PROJECT / f"results/root{m}_pruned.smt2"
    original = list(z3.parse_smt2_file(str(source)))
    fractional = normalize(original, m, 1, z3.RealVal(f"1/{bound}"), bound)
    unit = normalize(original, m, bound, z3.RealVal(1), bound**2)
    forms = []
    parsed_forms = []
    for name, assertions, minimum, margin, upper in (
            ("fractional", fractional, 1, f"1/{bound}", bound),
            ("unit", unit, bound, "1", bound**2)):
        path = HERE / f"bounded{m}_fixed_min_{name}.smt2"
        holder = z3.SolverFor("QF_LRA"); holder.add(*assertions)
        path.write_text(holder.to_smt2())
        parsed = list(z3.parse_smt2_file(str(path)))
        assert len(parsed) == len(assertions)
        assert all(z3.simplify(a).eq(z3.simplify(b)) for a, b in zip(assertions, parsed))
        parsed_forms.append(parsed)
        forms.append(dict(form=name, input=str(path), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          assertions=len(assertions), fixed_minimum=minimum, failure_margin=margin,
                          nonminimum_upper_bound=upper, free_variables=3*m-3,
                          allocation_clauses=3**m-3*2**m+3,
                          roundtrip_assertions="all exact simplified ASTs preserved; parser may represent rational literals as division nodes"))
    atom_count = scaling_audit(*parsed_forms, bound)
    receipt = dict(status="prepared_no_solver_call", m=m, integer_bound=bound,
                   source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   created_at_utc=datetime.now(timezone.utc).isoformat(),
                   reduction="Every bounded integer row a has minimum r>=1; a/r has cost<=B and each positive integer comparison gap becomes at least 1/r>=1/B. Each allocation retains a selected failed atom.",
                   pointwise_equivalence_claimed=False,
                   existence_equisatisfiability="conditional on the reviewed row-local integer-bound theorem and existing canonical reductions",
                   fractional_unit_scaling_audit="PASS", distinct_affine_atoms_checked=atom_count,
                   variable_change="q = B*x; all Boolean connectives and affine coefficient vectors checked",
                   forms=forms, elapsed_seconds=time.monotonic()-started,
                   max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    output = HERE / f"bounded{m}_fixed_min_preparation.json"
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    for dimension in (8, 9): prepare(dimension)
