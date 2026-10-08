#!/usr/bin/env python3
"""Seal a fixed complete-line candidate prefix; never assert a refutation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path


def write(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--configuration', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--previous', type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    size = a.source.stat().st_size
    with a.source.open('rb') as stream:
        os.fsync(stream.fileno())
        data = stream.read(size)
    assert len(data) == size, 'source shrank during prefix read'
    end = data.rfind(b'\n') + 1
    complete = data[:end]
    records = []
    for line in complete.splitlines():
        record = json.loads(line)
        assert set(record) == {'kind', 'id', 'clause', 'reasons'} and record['kind'] == 'rup'
        assert type(record['id']) is int and record['id'] > 0
        assert type(record['clause']) is list and type(record['reasons']) is list
        assert all(type(i) is int and i > 0 for i in record['reasons'])
        records.append(record['id'])
    assert len(records) == len(set(records)), 'duplicate candidate IDs'
    previous_match = None
    if a.previous:
        previous_match = complete.startswith(a.previous.read_bytes())
    target = a.out / 'candidate_justifications.jsonl'
    write(target, complete)
    reread = target.read_bytes()
    assert reread == complete
    config = json.loads(a.configuration.read_text())
    manifest = dict(status='SEALED_UNTRUSTED_CANDIDATE_PREFIX_NOT_A_REFUTATION',
        created_at_utc=datetime.now(timezone.utc).isoformat(), source=str(a.source.resolve()),
        observed_source_bytes=size, sealed_complete_bytes=end,
        omitted_unterminated_bytes=size-end, complete_records=len(records),
        first_id=records[0] if records else None, last_id=records[-1] if records else None,
        candidate_sha256=hashlib.sha256(complete).hexdigest(),
        configuration_sha256=hashlib.sha256(a.configuration.read_bytes()).hexdigest(),
        source_bindings=config['bound_files'],
        previous_prefix=str(a.previous.resolve()) if a.previous else None,
        extends_previous_complete_prefix=previous_match,
        independent_hint_validation_complete=False, final_dependency_closure_complete=False)
    write(a.out / 'manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())
    for path in a.out.iterdir():
        os.chmod(path, 0o444)
    fd = os.open(a.out, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(a.out, 0o555)
    print(json.dumps({k: manifest[k] for k in ('status', 'complete_records', 'sealed_complete_bytes',
        'candidate_sha256', 'last_id', 'extends_previous_complete_prefix')}))


if __name__ == '__main__':
    main()
