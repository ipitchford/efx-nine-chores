#!/usr/bin/env python3
"""Extract source assertions referenced by `asserted` leaves of a Z3 proof.

This does NOT verify a Z3 proof or establish unsatisfiability. It only selects an
exact subset of assertions from the original SMT-LIB file. All extracted leaves
must match those source assertions after let expansion and rational-literal
normalisation. The output copies the selected ORIGINAL assertion commands.
An independent solver/proof checker must subsequently establish UNSAT.

The large proof is memory-mapped. Only alias spans and formula nodes reachable
from `asserted` leaves are retained; proof-rule subtrees are not interpreted.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import mmap
from pathlib import Path
import re
import sys
import time


TOKEN = re.compile(r';[^\n]*|\(|\)|[^\s()]+')
ALIASES = re.compile(rb'\((a!\d+)\s+')
ASSERTED = re.compile(rb'\(asserted\s+')
PARENS = re.compile(rb'[()]')
ATOM_END = re.compile(rb'[\s()]')
NUMBER = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:/\d+)?$')
FORMULA_OPERATORS = {"+", "-", "*", "/", "<", "<=", ">", ">=", "=", "or", "and", "not", "=>", "ite", "to_real", "distinct"}


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse(text: str):
    """Small strict S-expression parser for this project's unquoted QF_LRA."""
    if '"' in text or '|' in text:
        raise ValueError("quoted strings/symbols are outside this extractor's scope")
    stack: list[list] = []
    roots = []
    for match in TOKEN.finditer(text):
        token = match.group()
        if token.startswith(';'):
            continue
        if token == '(':
            stack.append([])
        elif token == ')':
            if not stack:
                raise ValueError("unbalanced closing parenthesis")
            term = tuple(stack.pop())
            if stack:
                stack[-1].append(term)
            else:
                roots.append(term)
        elif stack:
            stack[-1].append(token)
        else:
            roots.append(token)
    if stack or len(roots) != 1:
        raise ValueError("expected exactly one balanced expression")
    return roots[0]


def expression_end(data, start: int) -> int:
    """Find one expression end; generated inputs contain no quoted syntax."""
    if data[start] != ord('('):
        match = ATOM_END.search(data, start)
        return match.start() if match else len(data)
    depth = 0
    for match in PARENS.finditer(data, start):
        depth += 1 if match.group() == b'(' else -1
        if depth == 0:
            return match.end()
    raise ValueError("unbalanced expression in proof/input")


def canonical(term, bindings=None, resolve_alias=None):
    bindings = {} if bindings is None else bindings
    if isinstance(term, str):
        if term in bindings:
            return bindings[term]
        if resolve_alias is not None and re.fullmatch(r'a!\d+', term):
            return resolve_alias(term)
        if NUMBER.fullmatch(term):
            number = Fraction(term)
            return ("rational", number.numerator, number.denominator)
        return term
    if not term:
        return ()
    if term[0] == 'let':
        if len(term) != 3:
            raise ValueError("malformed let")
        new = dict(bindings)
        for binding in term[1]:
            if len(binding) != 2 or not isinstance(binding[0], str):
                raise ValueError("malformed let binding")
            new[binding[0]] = canonical(binding[1], bindings, resolve_alias)
        return canonical(term[2], new, resolve_alias)
    if term[0] not in FORMULA_OPERATORS:
        raise ValueError(f"unexpected formula operator {term[0]!r}")
    return (term[0], *(canonical(child, bindings, resolve_alias) for child in term[1:]))


def linear(term):
    """Exact affine coefficient map; the empty variable name is the constant."""
    if isinstance(term, str):
        if term in {'true', 'false'}:
            raise ValueError("Boolean atom used as a number")
        return {term: Fraction(1)}
    if term[0] == 'rational':
        return {'': Fraction(term[1], term[2])}
    operator, *children = term
    if operator == 'to_real' and len(children) == 1:
        return linear(children[0])
    if operator in {'+', '-'}:
        answer = {}
        for index, child in enumerate(children):
            factor = -1 if operator == '-' and (len(children) == 1 or index > 0) else 1
            for variable, value in linear(child).items():
                answer[variable] = answer.get(variable, Fraction(0)) + factor * value
        return {variable: value for variable, value in answer.items() if value}
    if operator == '*':
        factor = Fraction(1)
        affine = None
        for child in children:
            value = linear(child)
            if all(variable == '' for variable in value):
                factor *= value.get('', Fraction(0))
            elif affine is None:
                affine = value
            else:
                raise ValueError("nonlinear multiplication")
        return {variable: factor * value for variable, value in (affine or {'': Fraction(1)}).items() if factor * value}
    if operator == '/' and len(children) == 2:
        denominator = linear(children[1])
        if any(variable for variable in denominator):
            raise ValueError("nonconstant denominator")
        divisor = denominator.get('', Fraction(0))
        if not divisor:
            raise ValueError("zero denominator")
        return {variable: value / divisor for variable, value in linear(children[0]).items() if value}
    raise ValueError(f"unsupported arithmetic operator {operator!r}")


def relation(kind, coefficients):
    coefficients = {variable: value for variable, value in coefficients.items() if value}
    if not any(variable for variable in coefficients):
        value = coefficients.get('', Fraction(0))
        return ('true' if {'strict': value > 0, 'weak': value >= 0, 'equal': value == 0}[kind] else 'false')
    ordered = sorted(coefficients.items())
    scale = abs(ordered[0][1])
    if kind == 'equal' and ordered[0][1] < 0:
        scale = -scale
    return (kind, tuple((variable, (value / scale).numerator, (value / scale).denominator) for variable, value in ordered))


def negate(formula):
    if formula == 'true':
        return 'false'
    if formula == 'false':
        return 'true'
    if formula[0] in {'strict', 'weak'}:
        inverse = {variable: -Fraction(numerator, denominator) for variable, numerator, denominator in formula[1]}
        return relation('weak' if formula[0] == 'strict' else 'strict', inverse)
    if formula[0] == 'not':
        return formula[1]
    return ('not', formula)


def connective(operator, children):
    absorbing = 'true' if operator == 'or' else 'false'
    identity = 'false' if operator == 'or' else 'true'
    flattened = set()
    for child in children:
        if child == absorbing:
            return absorbing
        if child == identity:
            continue
        if isinstance(child, tuple) and child[0] == operator:
            flattened.update(child[1:])
        else:
            flattened.add(child)
    if not flattened:
        return identity
    if len(flattened) == 1:
        return next(iter(flattened))
    return (operator, *sorted(flattened, key=repr))


def semantic(term):
    """Linear normal form plus sound Boolean identity/AC normalisations."""
    if term in {'true', 'false'} if isinstance(term, str) else False:
        return term
    if isinstance(term, str):
        raise ValueError(f"unexpected free Boolean atom {term!r}")
    operator, *children = term
    if operator in {'or', 'and'}:
        return connective(operator, [semantic(child) for child in children])
    if operator == 'not' and len(children) == 1:
        return negate(semantic(children[0]))
    if operator == '=>' and len(children) == 2:
        return connective('or', [negate(semantic(children[0])), semantic(children[1])])
    if operator in {'<', '<=', '>', '>=', '='} and len(children) == 2:
        left, right = (linear(child) for child in children)
        coefficients = dict(left)
        for variable, value in right.items():
            coefficients[variable] = coefficients.get(variable, Fraction(0)) - value
        if operator in {'<', '<='}:
            coefficients = {variable: -value for variable, value in coefficients.items()}
        kind = 'equal' if operator == '=' else ('strict' if operator in {'<', '>'} else 'weak')
        return relation(kind, coefficients)
    raise ValueError(f"unsupported Boolean operator {operator!r}")


def source_commands(data: bytes):
    position = 0
    while position < len(data):
        if data[position:position + 1].isspace():
            position += 1
            continue
        if data[position] == ord(';'):
            following = data.find(b'\n', position)
            position = len(data) if following < 0 else following + 1
            continue
        if data[position] != ord('('):
            raise ValueError("unexpected top-level input syntax")
        end = expression_end(data, position)
        raw = data[position:end]
        yield raw, parse(raw.decode('utf-8'))
        position = end


def extract(args):
    started = time.perf_counter()
    declarations: list[bytes] = []
    assertions: list[bytes] = []
    source_index = {}
    for raw, command in source_commands(args.input.read_bytes()):
        if command[0] == 'assert':
            key = semantic(canonical(command[1]))
            source_index.setdefault(key, len(assertions))
            assertions.append(raw)
        elif command[0] in {'declare-fun', 'declare-const', 'set-logic', 'set-info'}:
            declarations.append(raw)
        elif command[0] not in {'check-sat', 'exit'}:
            raise ValueError(f"unsupported source command {command[0]!r}")

    with args.proof.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as proof:
        spans = {}
        for match in ALIASES.finditer(proof):
            name = match.group(1).decode('ascii')
            if name in spans:
                raise ValueError(f"repeated alias {name}; scope-aware fallback required")
            begin = match.end()
            spans[name] = (begin, expression_end(proof, begin))
        cache = {}
        pending = set()

        def resolve(name):
            if name in cache:
                return cache[name]
            if name in pending:
                raise ValueError(f"cyclic formula alias {name}")
            if name not in spans:
                raise ValueError(f"unbound formula alias {name}")
            pending.add(name)
            begin, end = spans[name]
            value = canonical(parse(proof[begin:end].decode('utf-8')), resolve_alias=resolve)
            pending.remove(name)
            cache[name] = value
            return value

        selected = set()
        leaf_count = 0
        for match in ASSERTED.finditer(proof):
            begin = match.end()
            end = expression_end(proof, begin)
            key = semantic(canonical(parse(proof[begin:end].decode('utf-8')), resolve_alias=resolve))
            if key not in source_index:
                raise ValueError(f"asserted leaf {leaf_count} does not match any original assertion: {repr(key)[:3000]}")
            selected.add(source_index[key])
            leaf_count += 1

    if not selected:
        raise ValueError("no source assertions were selected")
    output = b'\n'.join(declarations + [assertions[index] for index in sorted(selected)] + [b'(check-sat)']) + b'\n'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    return {
        "result": "source_subset_extracted",
        "unsatisfiability": "not_checked_by_this_script",
        "input": str(args.input.resolve()),
        "input_sha256": sha256(args.input),
        "z3_proof": str(args.proof.resolve()),
        "z3_proof_sha256": sha256(args.proof),
        "output": str(args.output.resolve()),
        "output_sha256": sha256(args.output),
        "source_assertions": len(assertions),
        "proof_aliases": len(spans),
        "resolved_formula_aliases": len(cache),
        "asserted_occurrences": leaf_count,
        "selected_assertions": len(selected),
        "source_assertion_indices": sorted(selected),
        "matching": "exact affine normal forms and Boolean AC/idempotence after let expansion",
        "output_commands": "verbatim original source assertion commands",
        "elapsed_s": round(time.perf_counter() - started, 6),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('proof', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        report, status = extract(args), 0
    except Exception as error:
        report, status = {"result": "error", "error": str(error)}, 2
    serialized = json.dumps(report, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding='utf-8')
    sys.stdout.write(serialized)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
