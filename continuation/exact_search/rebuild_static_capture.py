#!/usr/bin/env python3
"""Untrusted static reconstruction for a separate derived certificate package.

No solver check is called. The stdlib independent binder must separately verify
every reconstructed atom and original clause against the frozen SMT source.
The original callback capture is never modified.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import z3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def durable_json(path, value):
    with path.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--cross-check', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    assert sha(args.input) == args.expected_sha256
    args.out.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name('collect_lra_lemmas_v3.py')
    assert sha(source) == '87f3287f7763f0972e9da6ceb0e4947572c90f5c6755b7cd85815c85d42972fe'
    spec = importlib.util.spec_from_file_location('frozen_collector_v3', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    text = args.input.read_text()
    names = sorted(re.findall(r'^\(declare-fun (c_\d+_\d+) \(\) Real\)', text, re.M))
    solver = z3.SolverFor('QF_LRA')
    solver.from_string(text)
    assertions = list(solver.assertions())
    collector = module.Collector(solver, args.out, names)
    collector.record_inputs(assertions)
    collector.close()
    checks = {}
    for name in ('atoms.jsonl', 'input_clauses.jsonl'):
        rebuilt = (args.out / name).read_bytes()
        prior = (args.capture / name).read_bytes()
        cross = (args.cross_check / name).read_bytes()
        assert rebuilt == cross, 'reconstruction differs from complete cross-check: ' + name
        assert rebuilt.startswith(prior), 'surviving capture is not a reconstructed prefix: ' + name
        checks[name] = dict(reconstructed_sha256=sha(args.out / name),
            original_capture_sha256=sha(args.capture / name),
            complete_cross_check_sha256=sha(args.cross_check / name),
            original_bytes=len(prior), reconstructed_bytes=len(rebuilt),
            prefix_equal=True, complete_cross_check_equal=True)
    for name in ('theory_clauses.jsonl', 'rup_clauses.jsonl'):
        shutil.copyfile(args.capture / name, args.out / name)
    assert sha(args.out / 'theory_clauses.jsonl') == sha(args.cross_check / 'theory_clauses.jsonl')
    # Callback assumptions are not certificate premises.
    (args.out / 'assumptions.jsonl').unlink()
    metadata = dict(variables=names, true_atom=1, assertions=len(assertions), input_sha256=args.expected_sha256)
    durable_json(args.out / 'metadata.json', metadata)
    for path in args.out.glob('*.jsonl'):
        with path.open('rb') as stream:
            os.fsync(stream.fileno())
    now = datetime.now(timezone.utc).isoformat()
    original_receipt = json.loads((args.capture / 'receipt.json').read_text())
    files = {path.name: dict(sha256=sha(path), bytes=path.stat().st_size) for path in args.out.glob('*.jsonl')}
    receipt = dict(status='DERIVED_CAPTURE_STATIC_RECONSTRUCTION_NOT_A_SOLVER_RUN',
        finished_at_utc=now, input_sha256=args.expected_sha256,
        callback_errors=[], unique_atoms=len(collector.atoms),
        unique_theory_clauses=original_receipt['unique_theory_clauses'], files=files,
        independent_certificate_status='pending', solver_called=False,
        original_capture=str(args.capture.resolve()), original_receipt_sha256=sha(args.capture / 'receipt.json'))
    durable_json(args.out / 'receipt.json', receipt)
    manifest = dict(status='DERIVED_PACKAGE_REQUIRES_INDEPENDENT_SOURCE_AND_PROOF_REPLAY',
        created_at_utc=now, input=str(args.input.resolve()), input_sha256=args.expected_sha256,
        reconstruction_source_sha256=sha(Path(__file__)), frozen_normalizer_sha256=sha(source),
        original_capture=str(args.capture.resolve()), cross_check_capture=str(args.cross_check.resolve()),
        static_streams=checks, copied_streams={name: dict(source=str((args.capture / name).resolve()), sha256=sha(args.out / name))
            for name in ('theory_clauses.jsonl', 'rup_clauses.jsonl')},
        original_files_modified=False, independent_binding_pending=True,
        anomaly_cause='Unexplained missing terminal suffixes in original static streams; no writer collision identified in bounded source/path inspection.',
        no_solver_check_performed=True)
    durable_json(args.out.parent / 'provenance_manifest.json', manifest)
    print(json.dumps(dict(status=receipt['status'], atoms=len(collector.atoms), assertions=len(assertions), files=files)))


if __name__ == '__main__':
    main()
