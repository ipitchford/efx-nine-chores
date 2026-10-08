#!/usr/bin/env python3
"""Copy the unchanged source streams needed by the existing exact replay calculus.

This is an untrusted packaging operation. A new independent input/atom binding
must be run on its result. Original source files and historical receipts remain
untouched; no atom, source-clause index, or Boolean proof ID is remapped.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil

from lra_certificate_common import capture_files, json_file, require, sha256


def seal_copy(source, destination, expected):
    require(not destination.exists(), 'destination already exists: ' + str(destination))
    temporary = destination.with_suffix(destination.suffix + '.tmp')
    require(not temporary.exists(), 'temporary destination already exists')
    with Path(source).open('rb') as incoming, temporary.open('xb') as outgoing:
        shutil.copyfileobj(incoming, outgoing, length=1 << 20)
        outgoing.flush()
        os.fsync(outgoing.fileno())
    require(sha256(temporary) == expected, 'copied bytes differ')
    temporary.replace(destination)
    destination.chmod(0o444)
    require(sha256(destination) == expected, 'sealed copy read-back differs')


def seal_json(path, value):
    require(not path.exists(), 'JSON destination already exists')
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    path.chmod(0o444)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-binding', type=Path, required=True)
    parser.add_argument('--out-parent', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    source_binding = args.source_binding.resolve()
    output = args.out_parent.resolve()
    require(not output.exists(), 'output directory must be new')
    receipt, before = capture_files(source)
    binding = json_file(source_binding)
    require(binding['status'] == 'PASS_ORIGINAL_INPUT_CNF_AND_AFFINE_ATOM_BINDING',
            'source does not have the completed input/atom binding')
    require(binding['captured_files_sha256'] == before, 'source differs from its binding')
    metadata = json_file(source / 'metadata.json')
    require(binding['input_sha256'] == receipt['input_sha256'] == metadata['input_sha256'],
            'source input identity mismatch')
    selected = ('atoms.jsonl', 'input_clauses.jsonl', 'theory_clauses.jsonl', 'metadata.json')
    omitted = {name: receipt['files'][name] for name in ('rup_clauses.jsonl', 'assumptions.jsonl')
               if name in receipt['files']}
    capture = output / 'capture'
    capture.mkdir(parents=True)
    for name in selected:
        seal_copy(source / name, capture / name, before[name])
    seal_copy(source / 'receipt.json', output / 'source_capture_receipt.json', before['receipt.json'])
    source_binding_digest = sha256(source_binding)
    seal_copy(source_binding, output / 'source_capture_input_binding.json', source_binding_digest)
    finished = datetime.now(timezone.utc).isoformat()
    derived = dict(
        status='DERIVED_REPLAY_SOURCE_STREAMS_ONLY',
        finished_at_utc=finished,
        input_sha256=binding['input_sha256'],
        unique_atoms=binding['atom_count'],
        unique_theory_clauses=binding['theory_clauses'],
        solver_invoked=False,
        solver_verdict=None,
        source_solver_verdict=receipt.get('solver_verdict'),
        source_atom_and_clause_indices_unchanged=True,
        source_capture_receipt_sha256=before['receipt.json'],
        source_capture_input_binding_sha256=source_binding_digest,
        omitted_raw_callback_streams=omitted,
        omission_scope='Raw callback RUP and assumption logs are not axioms in the final hinted RUP/Farkas proof. All original CNF, oriented affine atoms, and theory-clause source indices are unchanged.',
        independent_input_atom_rebinding_required=True,
        independent_certificate_complete=False,
        files={name: dict(sha256=before[name], bytes=(capture / name).stat().st_size)
               for name in selected if name != 'metadata.json'})
    seal_json(capture / 'receipt.json', derived)
    _, derived_hashes = capture_files(capture)
    _, after = capture_files(source)
    require(before == after, 'source changed during packaging')
    require(sha256(source_binding) == source_binding_digest, 'source binding changed during packaging')
    provenance = dict(
        status='SEALED_MINIMAL_REPLAY_CAPTURE_PREPARATION_ONLY',
        source_capture=str(source), source_input_binding=str(source_binding),
        source_capture_files_sha256=before,
        source_input_binding_sha256=source_binding_digest,
        derived_capture='capture', derived_capture_files_sha256=derived_hashes,
        copied_source_files_sha256={name: before[name] for name in selected},
        preserved_source_receipt='source_capture_receipt.json',
        preserved_source_binding='source_capture_input_binding.json',
        omitted_raw_callback_streams=omitted,
        omitted_raw_bytes=sum(entry['bytes'] for entry in omitted.values()),
        source_indices_unchanged=True, original_files_modified=False,
        independent_math_acceptance_claimed=False, completed_at_utc=finished,
        preparation_source_sha256=sha256(__file__))
    seal_json(output / 'provenance_manifest.json', provenance)
    for directory in (capture, output):
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    print(provenance['status'], provenance['omitted_raw_bytes'])


if __name__ == '__main__':
    main()
