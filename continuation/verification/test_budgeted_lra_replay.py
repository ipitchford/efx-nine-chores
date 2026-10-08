#!/usr/bin/env python3
"""Tiny fresh-replay/relocation/failure controls of the resource-only driver."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    root = Path(__file__).resolve().parent
    output = root / 'budgeted_replay_controls'
    assert not output.exists()
    initial = output / 'initial'
    capture = initial / 'capture'
    capture.mkdir(parents=True)
    (initial / 'input.smt2').write_text(
        '(set-logic QF_LRA)\n(declare-fun x () Real)\n'
        '(assert (> x 0))\n(assert (< x 0))\n(check-sat)\n')
    input_digest = digest(initial / 'input.smt2')
    (capture / 'atoms.jsonl').write_text(
        '{"id":2,"affine_le_zero":[1,0]}\n{"id":3,"affine_le_zero":[-1,0]}\n')
    (capture / 'input_clauses.jsonl').write_text(
        '{"source_assertion":-1,"clause":[1]}\n'
        '{"source_assertion":0,"clause":[-2]}\n'
        '{"source_assertion":1,"clause":[-3]}\n')
    (capture / 'theory_clauses.jsonl').write_text('{"clause":[2,3]}\n')
    put(capture / 'metadata.json', dict(variables=['x'], true_atom=1, assertions=2,
                                      input_sha256=input_digest))
    historical = '/deliberately/unavailable/original/budgeted-replay/input.smt2'
    put(capture / 'receipt.json', dict(
        status='SYNTHETIC_ORCHESTRATION_CONTROL_NOT_AN_ECONOMICS_RESULT',
        input=historical, input_sha256=input_digest, finished_at_utc='synthetic_control',
        unique_atoms=2, unique_theory_clauses=1,
        files={name: dict(sha256=digest(capture / name), bytes=(capture / name).stat().st_size)
               for name in ['atoms.jsonl', 'input_clauses.jsonl', 'theory_clauses.jsonl']}))
    (initial / 'trace.jsonl').write_text(
        '{"kind":"axiom","id":2,"source":"input","source_index":1,"clause":[-2]}\n'
        '{"kind":"axiom","id":3,"source":"input","source_index":2,"clause":[-3]}\n'
        '{"kind":"axiom","id":4,"source":"theory","source_index":0,"clause":[2,3]}\n'
        '{"kind":"rup","id":5,"clause":[],"reasons":[2,3,4]}\n')
    (initial / 'farkas.jsonl').write_text(
        '{"clause_index":0,"clause":[2,3],"weights":[[0,"1"],[1,"1"]]}\n')
    (initial / 'missing_farkas.jsonl').write_text('')
    put(initial / 'selected.json', [0])
    relocated = output / 'unrelated_extracted_bundle'
    payload = relocated / 'payload'
    shutil.copytree(initial, payload)
    shutil.rmtree(initial)
    verifier = relocated / 'verifier'
    verifier.mkdir()
    sources = ['lra_certificate_common.py', 'check_lra_capture.py', 'check_lra_rup.py',
               'check_lra_farkas.py', 'check_lra_certificate.py',
               'bind_completed_lra_checks.py', 'run_lra_with_budget.py']
    for name in sources:
        shutil.copyfile(root / name, verifier / name)
    command = [sys.executable, 'verifier/run_lra_with_budget.py', '--stage', 'all',
               '--memory-mib', '1600', '--input', 'payload/input.smt2',
               '--expected-sha256', input_digest, '--capture', str(payload / 'capture'),
               '--trace', 'payload/trace.jsonl', '--certificates', str(payload / 'farkas.jsonl'),
               '--selected-indices', 'payload/selected.json', '--out-directory', 'fresh_replay']

    def run(argv):
        return subprocess.run(argv, cwd=relocated, capture_output=True, text=True, timeout=20)

    result = run(command)
    assert result.returncode == 0, result.stdout + result.stderr
    complete = relocated / 'fresh_replay/complete_verification.json'
    proof = json.loads(complete.read_text())
    assert proof['status'] == 'PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE'
    assert proof['input_sha256'] == input_digest
    assert proof['selected_theory_clauses'] == proof['derived_rup_clauses'] == 1
    for name in ['input_binding.json', 'rup_verification.json', 'arithmetic_verification.json']:
        stage = json.loads((complete.parent / name).read_text())
        assert stage['address_space_cap_mib'] == (None if sys.platform == 'darwin' else 1600)
        assert stage['address_space_cap_enforced'] == (sys.platform != 'darwin')
        assert stage['orchestration_driver_sha256'] == digest(root / 'run_lra_with_budget.py')
        assert stage['mathematical_checking_function_unchanged'] is True
    first_hash = digest(complete)
    repeat = run(command)
    assert repeat.returncode != 0 and digest(complete) == first_hash
    assert 'new output directory' in repeat.stderr
    missing = list(command)
    missing[missing.index('--certificates') + 1] = str(payload / 'missing_farkas.jsonl')
    missing[-1] = 'missing_coverage'
    result = run(missing)
    assert result.returncode != 0 and 'certificate coverage incomplete' in result.stderr
    assert not (relocated / 'missing_coverage/complete_verification.json').exists()
    wrong = list(command)
    wrong[wrong.index('--expected-sha256') + 1] = '0' * 64
    wrong[-1] = 'wrong_input'
    result = run(wrong)
    assert result.returncode != 0 and 'frozen original input changed' in result.stderr
    assert not (relocated / 'wrong_input').exists()
    assert not initial.exists()
    assert json.loads((payload / 'capture/receipt.json').read_text())['input'] == historical
    report = dict(
        status='PASS_BUDGETED_REPLAY_ORCHESTRATION_AND_RELOCATION_CONTROLS',
        control_count=4,
        controls=['complete fresh three-stage replay after relocation',
                  'existing complete output cannot be overwritten',
                  'missing arithmetic coverage cannot produce a combined PASS',
                  'wrong original input cannot create replay outputs'],
        memory_budget_mib=1600, mathematical_checking_functions_unchanged=True,
        original_location_deleted=True, mixed_relative_and_absolute_paths_checked=True,
        stale_historical_absolute_path_preserved_and_not_required=True,
        solver_invoked=False, large_completed_certificates_replayed=False,
        fixture_scope='Tiny synthetic contradiction, not an economics result',
        fixture_input_sha256=input_digest, fixture_complete_receipt_sha256=first_hash,
        checker_sources_sha256={name: digest(root / name) for name in sources},
        control_source_sha256=digest(__file__),
        completed_at_utc=datetime.now(timezone.utc).isoformat())
    put(root / 'budgeted_replay_controls.json', report)
    print(report['status'], report['control_count'])


if __name__ == '__main__':
    main()
