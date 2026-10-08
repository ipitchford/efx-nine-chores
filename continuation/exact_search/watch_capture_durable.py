#!/usr/bin/env python3
"""Fsync observed capture files and preserve a separate terminal raw snapshot.

Opening a file and calling fsync does not flush the writer's userspace buffer.
This watcher never modifies original contents and makes no completeness claim.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import time


def utc():
    return datetime.now(timezone.utc)


def durable_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def fsync_existing(capture):
    paths = sorted(capture.glob('*.jsonl'))
    for path in paths:
        with path.open('rb') as stream:
            os.fsync(stream.fileno())
    return {path.name: path.stat().st_size for path in paths}


def copy_observed(path, target):
    digest = hashlib.sha256()
    total = lines = 0
    temp = target.with_suffix(target.suffix + '.tmp')
    with path.open('rb') as source, temp.open('wb') as dest:
        for chunk in iter(lambda: source.read(1 << 20), b''):
            digest.update(chunk)
            total += len(chunk)
            lines += chunk.count(b'\n')
            dest.write(chunk)
        dest.flush()
        os.fsync(dest.fileno())
    os.replace(temp, target)
    with target.open('rb') as stream:
        copied = hashlib.file_digest(stream, 'sha256').hexdigest()
    if copied != digest.hexdigest():
        raise RuntimeError('snapshot copy hash mismatch: ' + str(path))
    os.chmod(target, 0o444)
    return dict(bytes=total, sha256=copied, lines=lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--supervisor-started', type=Path, required=True)
    p.add_argument('--hard-seconds', type=int, required=True)
    p.add_argument('--cleanup-seconds', type=int, default=120)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started = json.loads(args.supervisor_started.read_text())
    deadline = datetime.fromisoformat(started['utc']) + timedelta(seconds=args.hard_seconds + args.cleanup_seconds)
    initial = dict(status='WATCHING_ONLY_NO_COMPLETENESS_CLAIM', started_at_utc=utc().isoformat(),
        absolute_deadline_utc=deadline.isoformat(), capture=str(args.capture.resolve()),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        action='fsync existing files without changing contents; snapshot only after terminal capture receipt',
        does_not_flush_writer_userspace_buffers=True)
    durable_json(args.out / 'started.json', initial)
    iterations = 0
    while utc() < deadline:
        sizes = fsync_existing(args.capture)
        iterations += 1
        try:
            receipt = json.loads((args.capture / 'receipt.json').read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            receipt = {}
        durable_json(args.out / 'heartbeat.json', dict(utc=utc().isoformat(), iterations=iterations,
            current_observed_sizes=sizes, capture_status=receipt.get('status')))
        if receipt.get('finished_at_utc') and 'files' in receipt:
            snapshot = args.out / 'capture'
            snapshot.mkdir()
            observations = {}
            for path in sorted(args.capture.iterdir()):
                if path.is_file() and path.suffix in ('.json', '.jsonl'):
                    observations[path.name] = copy_observed(path, snapshot / path.name)
            fd = os.open(snapshot, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            recorded_matches = {name: bool(name in observations and
                info['sha256'] == observations[name]['sha256'] and
                info['bytes'] == observations[name]['bytes'])
                for name, info in receipt['files'].items()}
            atoms = observations.get('atoms.jsonl', {}).get('lines')
            inputs = observations.get('input_clauses.jsonl', {}).get('lines')
            theories = observations.get('theory_clauses.jsonl', {}).get('lines')
            metadata = json.loads((snapshot / 'metadata.json').read_text())
            count_matches = dict(atoms=(atoms == receipt.get('unique_atoms')),
                original_input_records=(inputs == metadata.get('assertions', -2) + 1),
                theory_records=(theories == receipt.get('unique_theory_clauses')))
            result = dict(status='RAW_TERMINAL_SNAPSHOT_RECORDED_INDEPENDENT_CHECK_REQUIRED',
                completed_at_utc=utc().isoformat(), iterations=iterations,
                capture_snapshot=str(snapshot.resolve()), observations=observations,
                recorded_hashes_match=recorded_matches, count_matches=count_matches,
                all_observed_counts_and_recorded_hashes_match=all(recorded_matches.values()) and all(count_matches.values()),
                original_files_content_modified=False, independent_completeness_checked=False,
                note='Raw observations only; solver verdict and producer counters are not proof premises.')
            os.chmod(snapshot, 0o555)
            durable_json(args.out / 'snapshot_manifest.json', result)
            durable_json(args.out / 'terminal.json', result)
            print(json.dumps(result), flush=True)
            return
        time.sleep(min(5, max(0, (deadline - utc()).total_seconds())))
    result = dict(status='WATCH_DEADLINE_WITHOUT_TERMINAL_CAPTURE', completed_at_utc=utc().isoformat(),
        iterations=iterations, snapshot_created=False, original_files_content_modified=False)
    durable_json(args.out / 'terminal.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
