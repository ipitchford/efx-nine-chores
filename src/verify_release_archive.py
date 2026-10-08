#!/usr/bin/env python3
"""Check every archived payload hash and CRC against the embedded manifest."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

from solve_efx9 import atomic_write


def verify(path):
    before = path.stat()
    prefix = 'economics_problem2/'
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate archive names')
        manifest = json.loads(archive.read(prefix + 'artifact_manifest.json'))
        entries = manifest['files']
        expected_names = {prefix + e['path'] for e in entries}
        expected_names.update({prefix + 'artifact_manifest.json', prefix + 'MANIFEST.sha256'})
        if set(names) != expected_names:
            raise ValueError('archive membership differs from manifest')
        expected_text = ''.join(e['sha256'] + '  ' + e['path'] + '\n' for e in entries)
        if archive.read(prefix + 'MANIFEST.sha256').decode() != expected_text:
            raise ValueError('text and JSON manifests disagree')
        checked = 0
        total = 0
        for entry in entries:
            relative = Path(entry['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('unsafe archive path')
            h = hashlib.sha256()
            size = 0
            # ZipExtFile validates the CRC when it reaches EOF.
            with archive.open(prefix + entry['path']) as stream:
                for block in iter(lambda: stream.read(1 << 20), b''):
                    h.update(block)
                    size += len(block)
            if size != entry['bytes'] or h.hexdigest() != entry['sha256']:
                raise ValueError('archived bytes differ: ' + entry['path'])
            checked += 1
            total += size
        index = json.loads(archive.read(prefix + 'continuation/verification/nine_release_index.json'))
        if index.get('status') != 'PASS_COMPLETE_NINE_CHORE_RELEASE_BINDING':
            raise ValueError('incomplete release proof binding')
        lookup = {e['path']: e['sha256'] for e in entries}
        for relative, expected in index['files_sha256'].items():
            if lookup.get(relative) != expected:
                raise ValueError('required proof object absent or changed: ' + relative)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('archive changed during verification')
    return {
        'status': 'PASS_ALL_ARCHIVE_PAYLOAD_HASHES_AND_CRCS',
        'archive': str(path.resolve()), 'archive_bytes': after.st_size,
        'archive_sha256': h.hexdigest(), 'payload_files_checked': checked,
        'archive_entries_checked': len(names), 'uncompressed_payload_bytes': total,
        'complete_nine_proof_index_bound': True,
        'crc_verified_for_every_entry': True,
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = verify(args.archive)
    if args.out:
        atomic_write(args.out, json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
