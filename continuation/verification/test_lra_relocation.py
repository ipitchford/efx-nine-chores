#!/usr/bin/env python3
"""Relocate a tiny complete LRA proof and replay copied verifier sources.

This is a portability control, not an economics result. No large proof or
solver is run. Historical absolute paths are deliberately inaccessible.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def h(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    root = Path(__file__).resolve().parent
    sources = ['lra_certificate_common.py', 'check_lra_capture.py',
               'check_lra_rup.py', 'check_lra_farkas.py', 'check_lra_certificate.py']
    with tempfile.TemporaryDirectory(prefix='efx_relocation_') as temp:
        temp = Path(temp)
        original = temp / 'initial'
        original.mkdir()
        capture = original / 'capture'
        capture.mkdir()
        input_path = original / 'input.smt2'
        input_path.write_text('(set-logic QF_LRA)\n(declare-fun x () Real)\n(assert (> x 0))\n(assert (< x 0))\n(check-sat)\n')
        digest = h(input_path)
        (capture / 'atoms.jsonl').write_text('{"id":2,"affine_le_zero":[1,0]}\n{"id":3,"affine_le_zero":[-1,0]}\n')
        (capture / 'input_clauses.jsonl').write_text('{"source_assertion":-1,"clause":[1]}\n{"source_assertion":0,"clause":[-2]}\n{"source_assertion":1,"clause":[-3]}\n')
        (capture / 'theory_clauses.jsonl').write_text('{"clause":[2,3]}\n')
        put(capture / 'metadata.json', {'variables': ['x'], 'true_atom': 1,
                                      'assertions': 2, 'input_sha256': digest})
        historical = '/deliberately/absent/original/evidence-release/input.smt2'
        put(capture / 'receipt.json', {
            'status': 'SYNTHETIC_PORTABILITY_FIXTURE_NOT_AN_ECONOMICS_RESULT',
            'input': historical, 'input_sha256': digest,
            'finished_at_utc': 'synthetic_control', 'unique_atoms': 2,
            'unique_theory_clauses': 1,
            'files': {name: {'sha256': h(capture / name), 'bytes': (capture / name).stat().st_size}
                      for name in ['atoms.jsonl', 'input_clauses.jsonl', 'theory_clauses.jsonl']}})
        (original / 'trace.jsonl').write_text(
            '{"kind":"axiom","id":2,"source":"input","source_index":1,"clause":[-2]}\n'
            '{"kind":"axiom","id":3,"source":"input","source_index":2,"clause":[-3]}\n'
            '{"kind":"axiom","id":4,"source":"theory","source_index":0,"clause":[2,3]}\n'
            '{"kind":"rup","id":5,"clause":[],"reasons":[2,3,4]}\n')
        (original / 'farkas.jsonl').write_text('{"clause_index":0,"clause":[2,3],"weights":[[0,"1"],[1,"1"]]}\n')
        put(original / 'selected.json', [0])
        relocated = temp / 'unrelated_extracted_bundle'
        relocated.mkdir()
        payload = relocated / 'payload'
        shutil.copytree(original, payload)
        shutil.rmtree(original)
        verifier = relocated / 'verifier'
        verifier.mkdir()
        for name in sources:
            shutil.copyfile(root / name, verifier / name)
        command = [sys.executable, 'verifier/check_lra_certificate.py',
                   '--input', 'payload/input.smt2', '--expected-sha256', digest,
                   '--capture', str(payload / 'capture'),
                   '--trace', 'payload/trace.jsonl',
                   '--certificates', str(payload / 'farkas.jsonl'),
                   '--selected-indices', 'payload/selected.json',
                   '--out-directory', 'fresh_replay']
        result = subprocess.run(command, cwd=relocated, capture_output=True, text=True,
                                check=False, timeout=20)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        receipt = json.loads((relocated / 'fresh_replay/complete_verification.json').read_text())
        assert receipt['status'] == 'PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE'
        assert receipt['input_sha256'] == digest and receipt['selected_theory_clauses'] == 1
        assert receipt['derived_rup_clauses'] == 1 and not original.exists()
        assert json.loads((payload / 'capture/receipt.json').read_text())['input'] == historical
        report = {'status': 'PASS_COMPLETE_LRA_REPLAY_AFTER_RELOCATION',
                  'fixture_scope': 'Tiny synthetic arithmetic/Boolean proof; not an economics result',
                  'all_three_independent_stages_executed': True,
                  'mixed_relative_and_absolute_explicit_paths_accepted': True,
                  'original_location_deleted_before_replay': True,
                  'historical_absolute_input_path_unavailable_and_preserved': historical,
                  'historical_path_not_required_for_checking': True,
                  'solver_invoked': False, 'large_certificates_replayed': False,
                  'fixture_input_sha256': digest,
                  'fixture_complete_receipt_sha256': h(relocated / 'fresh_replay/complete_verification.json'),
                  'checker_sources_sha256': {name: h(root / name) for name in sources},
                  'relocation_test_source_sha256': h(__file__),
                  'completed_at_utc': datetime.now(timezone.utc).isoformat()}
    put(root / 'lra_relocation_control.json', report)
    print(report['status'])


if __name__ == '__main__':
    main()
