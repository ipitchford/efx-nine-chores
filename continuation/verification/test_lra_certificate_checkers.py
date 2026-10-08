#!/usr/bin/env python3
"""Focused positive and adversarial controls for the independent checkers.

These controls exercise strict inequalities, rational underflow, atom direction,
and propagation soundness. They are not evidence about the economics target.
"""
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import tempfile

from check_lra_capture import check as check_capture
from check_lra_farkas import verify_weights
from check_lra_rup import propagate_check, check as check_rup
from lra_certificate_common import (LinearReader, atomic_json, json_loads,
                                   read_atoms, require, sha256)


def main():
    passed = []

    def accept(name, action):
        action()
        passed.append({'name': name, 'expected': 'accept', 'observed': 'accept'})

    def reject(name, action):
        try:
            action()
        except (ValueError, TypeError, ZeroDivisionError):
            passed.append({'name': name, 'expected': 'reject', 'observed': 'reject'})
        else:
            raise AssertionError('negative control accepted: ' + name)

    atoms = {2: [1, 0], 3: [-1, 0], 4: [1, -1], 5: [-1, 1]}
    reader = LinearReader(['x'], atoms)
    for operator, expected in [('<=', 2), ('>=', 3), ('>', -2), ('<', -3)]:
        accept('comparison_' + operator,
               lambda op=operator, value=expected: require(reader.literal([op, 'x', '0']) == value, 'wrong comparison'))
    accept('positive_scale', lambda: require(reader.literal(['<=', ['*', '2', 'x'], '0']) == 2, 'scale changed atom'))
    accept('negative_scale_preserves_orientation', lambda: require(reader.literal(['<=', ['*', '-2', 'x'], '0']) == 3, 'orientation flipped'))
    accept('exact_fraction_scale', lambda: require(reader.literal(['<=', ['/', 'x', '3'], '0']) == 2, 'fraction scale failed'))
    accept('strict_zero_is_false', lambda: require(reader.literal(['>', '0', '0']) == -1, 'strict zero'))
    accept('weak_zero_is_true', lambda: require(reader.literal(['>=', '0', '0']) == 1, 'weak zero'))
    accept('complementary_clause_is_true', lambda: require(reader.clause(['or', ['>', 'x', '0'], ['<=', 'x', '0']]) is None, 'complement'))
    accept('false_clause_is_empty', lambda: require(reader.clause(['or', 'false', 'false']) == [], 'false clause'))
    reject('equality_fail_closed', lambda: reader.literal(['=', 'x', '0']))
    reject('nonlinear_fail_closed', lambda: reader.literal(['<=', ['*', 'x', 'x'], '0']))
    reject('variable_denominator_fail_closed', lambda: reader.literal(['<=', ['/', '1', 'x'], '0']))
    reject('duplicate_json_key', lambda: json_loads('{"id":2,"id":3}'))
    accept('strict_zero_constant_farkas', lambda: verify_weights([2, 3], [[0, '1'], [1, '1']], atoms, 2))
    accept('weak_positive_constant_farkas', lambda: verify_weights([-5, -2], [[0, '1'], [1, '1']], atoms, 2))
    accept('strict_positive_constant_farkas', lambda: verify_weights([-2, 4], [[0, '1'], [1, '1']], atoms, 2))
    accept('arbitrarily_small_exact_positive_strict_weight',
           lambda: verify_weights([2, 3], [[0, '1e-400'], [1, '1e-400']], atoms, 2))
    reject('weak_zero_constant_not_a_contradiction', lambda: verify_weights([-3, -2], [[0, '1'], [1, '1']], atoms, 2))
    reject('negative_constant_not_a_contradiction', lambda: verify_weights([-4, 2], [[0, '1'], [1, '1']], atoms, 2))
    reject('zero_weights_not_a_contradiction', lambda: verify_weights([2, 3], [[0, '0'], [1, '0']], atoms, 2))
    reject('noncancelling_coefficients', lambda: verify_weights([2, 3], [[0, '1'], [1, '2']], atoms, 2))
    reject('negative_multiplier', lambda: verify_weights([2, 3], [[0, '-1'], [1, '-1']], atoms, 2))
    reject('floating_underflow_weight', lambda: verify_weights([2, 3], [[0, 1e-400], [1, 1e-400]], atoms, 2))
    reject('boolean_weight', lambda: verify_weights([2, 3], [[0, True], [1, True]], atoms, 2))
    reject('duplicate_weight_position', lambda: verify_weights([2, 3], [[0, '1'], [0, '1']], atoms, 2))
    reject('invalid_weight_position', lambda: verify_weights([2, 3], [[2, '1']], atoms, 2))
    known = {1: [2, 3], 2: [-2], 3: [-3]}
    accept('empty_clause_rup', lambda: propagate_check([], [2, 3, 1], known))
    accept('negated_goal_rup', lambda: propagate_check([3], [2, 1], known))
    reject('nonunit_reason', lambda: propagate_check([], [1], known))
    reject('satisfied_reason', lambda: propagate_check([3], [3, 2, 1], known))
    reject('unknown_reason', lambda: propagate_check([], [4], known))
    reject('nonconflicting_last_reason', lambda: propagate_check([], [2], known))
    reject('reason_after_conflict', lambda: propagate_check([], [2, 3, 1, 1], known))
    reject('boolean_reason_id', lambda: propagate_check([], [True], known))
    # Small original-input/axiom-provenance fixture, independent of target files.
    with tempfile.TemporaryDirectory(prefix='efx_lra_checker_controls_') as directory:
        directory = Path(directory)
        input_path = directory / 'input.smt2'
        input_path.write_text('(set-logic QF_LRA)\n(declare-fun x () Real)\n(assert (> x 0))\n(assert (<= x 0))\n(check-sat)\n')
        (directory / 'atoms.jsonl').write_text('{"id":2,"affine_le_zero":[1,0]}\n')
        (directory / 'input_clauses.jsonl').write_text('{"source_assertion":-1,"clause":[1]}\n{"source_assertion":0,"clause":[-2]}\n{"source_assertion":1,"clause":[2]}\n')
        for name in ['theory_clauses.jsonl', 'assumptions.jsonl']:
            (directory / name).write_text('')
        atomic_json(directory / 'metadata.json', {'variables': ['x'], 'true_atom': 1,
                    'assertions': 2, 'input_sha256': sha256(input_path)})
        atomic_json(directory / 'receipt.json', {'finished_at_utc': 'synthetic_control',
                    'input_sha256': sha256(input_path), 'unique_atoms': 1, 'unique_theory_clauses': 0,
                    'files': {name: {'sha256': sha256(directory / name), 'bytes': (directory / name).stat().st_size}
                              for name in ['atoms.jsonl', 'input_clauses.jsonl', 'theory_clauses.jsonl', 'assumptions.jsonl']}})
        binding = check_capture(input_path, sha256(input_path), directory)
        atomic_json(directory / 'binding.json', binding)
        atomic_json(directory / 'selected.json', [])
        trace_path = directory / 'trace.jsonl'
        trace = ('{"kind":"axiom","id":2,"source":"input","source_index":1,"clause":[-2]}\n'
                 '{"kind":"axiom","id":3,"source":"input","source_index":2,"clause":[2]}\n'
                 '{"kind":"rup","id":4,"clause":[],"reasons":[2,3]}\n')
        trace_path.write_text(trace)
        accept('input_bound_refutation_fixture', lambda: check_rup(directory, directory / 'binding.json', trace_path, directory / 'selected.json'))
        trace_path.write_text(trace.replace('"source_index":1', '"source_index":2', 1))
        reject('wrong_axiom_provenance', lambda: check_rup(directory, directory / 'binding.json', trace_path, directory / 'selected.json'))
        trace_path.write_text(trace.replace('"source":"input"', '"source":"assumption"', 1))
        reject('callback_assumption_injection', lambda: check_rup(directory, directory / 'binding.json', trace_path, directory / 'selected.json'))
        trace_path.write_text(trace.replace('"reasons":[2,3]', '"reasons":[4]'))
        reject('circular_reason_injection', lambda: check_rup(directory, directory / 'binding.json', trace_path, directory / 'selected.json'))
        (directory / 'atoms.jsonl').write_text('{"id":2,"affine_le_zero":[1.0,0]}\n')
        reject('floating_atom_coefficient', lambda: read_atoms(directory / 'atoms.jsonl', 2))
    root = Path(__file__).parent
    output = root / 'lra_checker_negative_controls.json'
    atomic_json(output, {'status': 'PASS_NEW_LRA_CHECKER_POSITIVE_AND_NEGATIVE_CONTROLS',
                        'control_count': len(passed), 'controls': passed,
                        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
                        'sources_sha256': {name: sha256(root / name) for name in [
                            'lra_certificate_common.py', 'check_lra_capture.py', 'check_lra_farkas.py',
                            'check_lra_rup.py', 'test_lra_certificate_checkers.py']},
                        'real_solver_invoked': False, 'main_target_proved': False})
    print('PASS', len(passed), 'focused controls')


if __name__ == '__main__':
    main()
