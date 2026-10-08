#!/usr/bin/env python3
"""Hash-bound command supervisor with a hard process-group deadline."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, obj):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2) + '\n')
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('configuration', type=Path)
    args = parser.parse_args()
    conf = json.loads(args.configuration.read_text())
    for name, digest in conf['bound_files'].items():
        assert sha(name) == digest
    out = Path(conf['supervisor_directory'])
    out.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    initial = dict(status='starting', utc=datetime.now(timezone.utc).isoformat(),
                   configuration_sha256=sha(args.configuration), configuration=conf)
    atomic(out / 'started.json', initial)
    def limits():
        cap = conf['address_space_mib'] * 2**20
        resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    killed = False
    with (out / 'worker.log').open('w') as log:
        child = subprocess.Popen(conf['argv'], cwd=conf['cwd'], stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True,
                                 preexec_fn=limits)
        try:
            while child.poll() is None:
                elapsed = time.monotonic() - began
                remaining = conf['hard_wall_seconds'] - elapsed
                if remaining <= 0:
                    killed = True
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                    break
                atomic(out / 'heartbeat.json', dict(utc=datetime.now(timezone.utc).isoformat(),
                                                   elapsed_seconds=elapsed, remaining_seconds=remaining))
                try:
                    child.wait(timeout=min(5, remaining))
                except subprocess.TimeoutExpired:
                    pass
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            raise
        finally:
            receipt = dict(status='hard_wall_timeout' if killed else 'child_completed',
                           returncode=child.poll(), elapsed_seconds=time.monotonic()-began,
                           utc=datetime.now(timezone.utc).isoformat(),
                           hard_killed=killed, configuration_sha256=sha(args.configuration),
                           bound_files_unchanged=all(sha(p) == h for p, h in conf['bound_files'].items()),
                           max_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
            atomic(out / 'terminal.json', receipt)
            print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
