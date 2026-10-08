#!/usr/bin/env python3
"""Propose an exact original-assertion subset using Z3 assumption tracking.

The emitted subset is for independent cvc5 and external-checker replay. This
selector is neither an external proof checker nor the final proof certificate.
It copies source assertion commands verbatim; a selector mistake cannot add
an assumption that was not present in the original input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

import z3

from extract_z3_core import sha256, source_commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=360)
    parser.add_argument('--address-space-mib', type=int, default=1800)
    parser.add_argument('--arith', type=int, default=2)
    args = parser.parse_args()
    if args.timeout <= 0 or args.address_space_mib <= 0:
        parser.error('resource limits must be positive')
    old_soft, old_hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = args.address_space_mib << 20
    if old_hard != resource.RLIM_INFINITY:
        cap = min(cap, old_hard)
    resource.setrlimit(resource.RLIMIT_AS, (cap, old_hard))
    started = time.perf_counter()
    commands = list(source_commands(args.input.read_bytes()))
    raw_assertions = [raw for raw, command in commands if command[0] == 'assert']
    allowed = {'set-logic', 'set-info', 'declare-fun', 'declare-const', 'assert', 'check-sat', 'exit'}
    if any(command[0] not in allowed for _, command in commands):
        raise ValueError('selector requires a static declaration/assertion input')
    assertions = list(z3.parse_smt2_file(str(args.input)))
    if len(assertions) != len(raw_assertions):
        raise ValueError('source/parser assertion counts disagree')
    solver = z3.SolverFor('QF_LRA')
    solver.set(timeout=int(args.timeout * 1000), unsat_core=True, random_seed=0)
    solver.set('arith.solver', args.arith)
    names = [z3.Bool(f'core_selector_{index:05d}') for index in range(len(assertions))]
    if b'core_selector_' in args.input.read_bytes():
        raise ValueError('reserved tracking prefix appears in original input')
    for assertion, name in zip(assertions, names):
        solver.assert_and_track(assertion, name)
    checked = time.perf_counter()
    result = solver.check()
    finished = time.perf_counter()
    report = {
        'result': str(result), 'solver': 'Z3 ' + z3.get_version_string(),
        'input': str(args.input.resolve()), 'input_sha256': sha256(args.input),
        'assertions': len(assertions), 'timeout_s': args.timeout,
        'address_space_limit_mib': args.address_space_mib,
        'arith_solver': args.arith,
        'parse_s': round(checked - started, 6), 'check_s': round(finished - checked, 6),
        'scope': 'Exact original assertion subset proposed for independent replay; no external proof check here.',
    }
    if result == z3.unsat:
        selected_names = {str(name) for name in solver.unsat_core()}
        index = {str(name): i for i, name in enumerate(names)}
        if not selected_names.issubset(index):
            raise ValueError('unknown assumption in returned core')
        selected = sorted(index[name] for name in selected_names)
        keep = set(selected)
        output = []
        cursor = 0
        for raw, command in commands:
            if command[0] == 'assert':
                if cursor in keep:
                    output.append(raw)
                cursor += 1
            elif command[0] not in {'check-sat', 'exit'}:
                output.append(raw)
        output.append(b'(check-sat)')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(b'\n'.join(output) + b'\n')
        report.update({
            'selected_assertions': len(selected), 'original_assertion_indices': selected,
            'output': str(args.output.resolve()), 'output_sha256': sha256(args.output),
            'output_assertions': 'verbatim subset of original commands',
            'independent_replay': 'pending',
        })
    elif result == z3.unknown:
        report['reason_unknown'] = solver.reason_unknown()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report, indent=2) + '\n'
    args.report.write_text(serialized)
    print(serialized, end='')
    return 0 if result == z3.unsat else 2


if __name__ == '__main__':
    raise SystemExit(main())
