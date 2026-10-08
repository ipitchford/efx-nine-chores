#!/usr/bin/env python3
"""Bounded supervisor for the existing exact row-elimination search.

The mathematical worker is unchanged. Receipts distinguish an interrupted
process, a timed-out process, and a solver's own terminal verdict.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path, action='append', required=True)
    parser.add_argument('--pair-batch', type=int, default=4)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--hard-seconds', type=int, default=650)
    parser.add_argument('--memory-mib', type=int, default=1450)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    project = root.parent.parent
    out = args.out.resolve()
    assert not out.exists(), 'Use a new output directory to preserve prior receipts'
    out.mkdir(parents=True)
    resumes = [path.resolve() for path in args.resume]
    previous = sorted({f for resume in resumes for f in (resume / 'regions').glob('*.json')})
    assert previous, 'No completed source regions'
    for path in previous:
        data = json.loads(path.read_text())
        inner = path.parent.parent / 'inner' / path.with_suffix('.smt2').name
        assert digest(inner) == data['core_sha256']
    for resume in resumes:
        if (resume / 'summary.json').exists() or not (resume / 'heartbeat.json').exists():
            continue
        completed=sorted((resume / 'regions').glob('*.json'))
        observation = {
            'status': 'interrupted_without_terminal_verdict',
            'observed_utc': utc(),
            'completed_region_files': len(completed),
            'last_completed_region': completed[-1].name,
            'last_heartbeat': json.loads((resume / 'heartbeat.json').read_text()),
            'evidence': 'Completed artifacts remain; no terminal summary exists. No solver verdict is inferred.',
        }
        atomic_json(resume / 'interruption_observation.json', observation)
    worker = args.worker.resolve() if args.worker else root / 'row_elimination_cegis_batched.py'
    command = [sys.executable, '-u', str(worker),
               '--out', str(out), '--seconds', str(args.seconds),
               '--iterations', '10000', '--memory-mib', str(args.memory_mib),
               '--outer-timeout', '90000', '--inner-timeout', '15000',
               '--seed-robust', '--compress', '--generic-model', '--prune-resume-cores',
               '--order', 'descending', '--pair-batch', str(args.pair_batch),
               '--pair-seeds', str(root / 'pair_seeds_all.json'),
               '--pair-index', str(root / 'full_pair_census' / 'accepted_pairs.bin'),
               '--pair-scores', str(root / 'full_pair_census' / 'pair_region_scores.bin')]
    for resume in resumes:
        command.extend(['--resume', str(resume)])
    inputs = [worker, root / 'exact_pair_core.py',
              root / 'verify_pair_seeds.py', root.parent / 'verify_row_cores.py',
              Path(__file__).resolve(),
              root / 'pair_seeds_all.json',
              root / 'full_pair_census' / 'accepted_pairs.bin',
              root / 'full_pair_census' / 'pair_region_scores.bin']
    input_hashes = {str(path): digest(path) for path in inputs}
    snapshot = out / 'source_snapshot'
    snapshot.mkdir()
    for path in inputs[:5]:
        shutil.copy2(path, snapshot / path.name)
    started = time.monotonic()
    launch = dict(status='launch_prepared', created_utc=utc(), command=command,
                  seconds=args.seconds, hard_seconds=args.hard_seconds,
                  memory_mib=args.memory_mib, resume=[str(path) for path in resumes],
                  directly_resumed_regions=len(previous), input_sha256=input_hashes,
                  mathematical_domain='Unchanged fixed distinct minima and descending free first-row order; no numerical upper bound added.')
    atomic_json(out / 'startup_receipt.json', launch)
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    supervisor_termination = 'child_completed'
    with (out / 'worker.log').open('w') as log:
        child = subprocess.Popen(command, cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT)
        launch.update(status='launched', child_namespace_pid=child.pid, launched_utc=utc())
        atomic_json(out / 'startup_receipt.json', launch)
        try:
            while child.poll() is None:
                elapsed = time.monotonic() - started
                atomic_json(out / 'supervisor_heartbeat.json', dict(
                    utc=utc(), elapsed=elapsed, child_namespace_pid=child.pid,
                    status='running', hard_seconds=args.hard_seconds))
                if elapsed >= args.hard_seconds:
                    supervisor_termination = 'hard_supervisor_timeout'
                    child.terminate()
                    try:
                        child.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=3)
                    break
                try:
                    child.wait(timeout=min(10, args.hard_seconds - elapsed))
                except subprocess.TimeoutExpired:
                    pass
        except BaseException as error:
            supervisor_termination = 'supervisor_interrupted_' + type(error).__name__
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=3)
            raise
        finally:
            summary_file = out / 'summary.json'
            summary = json.loads(summary_file.read_text()) if summary_file.exists() else None
            terminal = dict(
                status=supervisor_termination, utc=utc(), elapsed=time.monotonic()-started,
                child_returncode=child.poll(), worker_summary=summary,
                completed_region_files=len(list((out / 'regions').glob('*.json'))),
                input_hashes_unchanged=all(digest(path) == input_hashes[str(path)] for path in inputs),
                mathematical_verdict=(summary['termination'] if summary else 'none_returned'))
            atomic_json(out / 'terminal_receipt.json', terminal)
            print(json.dumps(terminal), flush=True)


if __name__ == '__main__':
    main()
