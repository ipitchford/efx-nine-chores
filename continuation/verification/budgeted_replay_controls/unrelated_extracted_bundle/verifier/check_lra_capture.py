#!/usr/bin/env python3
"""Independently bind an LRA capture to original SMT assertions, using stdlib.

PASS establishes syntax, exact affine atom interpretation, and original CNF.
It does not establish that captured theory clauses are valid or Boolean UNSAT.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import resource
import time

from lra_certificate_common import (LinearReader, atomic_json, capture_files,
    commands, json_file, json_lines, read_atoms, require, sha256, validate_clause)


def check(input_path, expected, capture):
    digest = sha256(input_path)
    require(digest == expected, 'frozen input hash mismatch')
    receipt, bindings = capture_files(capture)
    metadata = json_file(capture / 'metadata.json')
    require(receipt['input_sha256'] == digest == metadata['input_sha256'], 'capture input binding mismatch')
    require(type(metadata.get('true_atom')) is int and metadata['true_atom'] == 1, 'truth atom mismatch')
    names, assertion_count = [], 0
    logic_count = check_count = 0
    for command in commands(input_path):
        op = command[0]
        if op == 'declare-fun':
            require(assertion_count == check_count == 0, 'late declaration')
            require(len(command) == 4 and command[2:] == [[], 'Real'], 'unsupported declaration')
            require(type(command[1]) is str and command[1] not in names, 'duplicate declaration')
            names.append(command[1])
        elif op == 'assert':
            require(len(command) == 2 and check_count == 0, 'malformed or late assertion')
            assertion_count += 1
        elif op == 'set-logic':
            require(command == ['set-logic', 'QF_LRA'], 'unexpected logic')
            logic_count += 1
        elif op == 'check-sat':
            require(command == ['check-sat'], 'malformed check')
            check_count += 1
        else:
            raise ValueError('unsupported original command: ' + op)
    require(logic_count == check_count == 1, 'logic/check multiplicity')
    require(sorted(names) == metadata['variables'], 'declared variables do not match capture order')
    require(type(metadata['assertions']) is int and assertion_count == metadata['assertions'], 'assertion count mismatch')
    atoms = read_atoms(capture / 'atoms.jsonl', len(names) + 1)
    maximum = len(atoms) + 1
    reader = LinearReader(metadata['variables'], atoms)
    source_records = iter(json_lines(capture / 'input_clauses.jsonl'))
    truth_record = next(source_records, None)
    require(truth_record == {'source_assertion': -1, 'clause': [1]}, 'missing truth unit')
    require(type(truth_record['source_assertion']) is int and
            type(truth_record['clause'][0]) is int, 'noninteger truth record')
    input_nonnull, input_literals, null_inputs = 1, 1, 0
    index = 0
    for command in commands(input_path):
        if command[0] != 'assert':
            continue
        expected_clause = reader.clause(command[1])
        record = next(source_records, None)
        require(type(record) is dict and set(record) == {'source_assertion', 'clause'}, 'bad input record')
        require(type(record['source_assertion']) is int and record['source_assertion'] == index, 'input assertion order mismatch')
        require(record['clause'] == expected_clause, f'original clause differs at assertion {index}')
        if expected_clause is None:
            null_inputs += 1
        else:
            validate_clause(record['clause'], maximum)
            input_nonnull += 1
            input_literals += len(expected_clause)
        index += 1
    require(next(source_records, None) is None, 'extra input records')
    theory_count = theory_literals = 0
    for record in json_lines(capture / 'theory_clauses.jsonl'):
        require(set(record) == {'clause'}, 'bad theory record')
        clause = validate_clause(record['clause'], maximum)
        theory_count += 1
        theory_literals += len(clause)
    rup_count = rup_literals = 0
    if (capture / 'rup_clauses.jsonl').exists():
        for record in json_lines(capture / 'rup_clauses.jsonl'):
            require(set(record) == {'clause'}, 'bad RUP record')
            clause = validate_clause(record['clause'], maximum)
            rup_count += 1
            rup_literals += len(clause)
    require(receipt.get('unique_atoms') == len(atoms), 'reported atom count mismatch')
    require(receipt.get('unique_theory_clauses') == theory_count, 'reported theory count mismatch')
    return dict(status='PASS_ORIGINAL_INPUT_CNF_AND_AFFINE_ATOM_BINDING',
                input=str(input_path.resolve()), input_sha256=digest,
                capture=str(capture.resolve()), captured_files_sha256=bindings,
                variables=len(names), atom_count=len(atoms), original_assertions=assertion_count,
                original_atom_count=len(reader.used_atoms), original_clause_records=assertion_count + 1,
                original_nonnull_clauses=input_nonnull, original_tautological_assertions=null_inputs,
                original_literal_positions=input_literals,
                theory_clauses=theory_count, theory_literal_positions=theory_literals,
                rup_clauses=rup_count, rup_literal_positions=rup_literals,
                callback_assumptions_admitted=False, theory_validity_checked=False,
                boolean_unsat_checked=False, independent_unsat_certificate_complete=False,
                captured_solver_verdict=receipt.get('solver_verdict'),
                captured_solver_verdict_is_not_a_checking_premise=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (480 << 20,) * 2)
    started = time.monotonic()
    report = check(args.input, args.expected_sha256, args.capture)
    report.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=time.monotonic() - started,
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  checker_sha256=sha256(__file__),
                  common_sha256=sha256(Path(__file__).with_name('lra_certificate_common.py')))
    atomic_json(args.out, report)
    print(report['status'], report['original_assertions'], report['atom_count'],
          report['theory_clauses'], report['rup_clauses'])


if __name__ == '__main__':
    main()
