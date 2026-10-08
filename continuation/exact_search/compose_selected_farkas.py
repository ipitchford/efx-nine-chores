#!/usr/bin/env python3
"""Durably merge sorted multiplier candidate streams without changing records.

This is a provenance/coverage producer, not the independent arithmetic checker.
Every part must already be closed and match its preparation manifest. The final
stream is separately checked by check_lra_farkas.py before proof acceptance.
"""
import argparse
import hashlib
import heapq
import json
import os
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    partial = path.with_suffix(path.suffix + '.partial')
    with partial.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    partial.replace(path)
    sync_directory(path.parent)


def records(path):
    previous = -1
    with path.open('rb') as stream:
        for raw in stream:
            record = json.loads(raw)
            index = record['clause_index']
            if type(index) is not int or index <= previous:
                raise ValueError('Part indices must be increasing and unique')
            previous = index
            if not raw.endswith(b'\n'):
                raise ValueError('Unsealed final line in a part')
            yield index, raw, record


def compose(capture, selected_path, parts, out, allow_unselected_records=False):
    if out.exists():
        raise ValueError('Use a fresh composition directory')
    selected = json.loads(selected_path.read_text())
    selected_hash = digest(selected_path)
    if (type(selected) is not list or any(type(x) is not int or x < 0 for x in selected)
            or selected != sorted(set(selected))):
        raise ValueError('Selection must be increasing unique nonnegative integers')
    receipt_path = capture / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    if not receipt.get('finished_at_utc') or receipt.get('callback_errors'):
        raise ValueError('Capture must be completed without callback errors')
    bindings = {name: digest(capture / name) for name in
                ('metadata.json', 'atoms.jsonl', 'input_clauses.jsonl', 'theory_clauses.jsonl')}
    for name in ('atoms.jsonl', 'input_clauses.jsonl', 'theory_clauses.jsonl'):
        if bindings[name] != receipt['files'][name]['sha256']:
            raise ValueError('Capture stream differs from terminal receipt')
    receipt_hash = digest(receipt_path)
    provenance = []
    iterators = []
    for part in parts:
        manifest_path = part / 'preparation.json'
        certificate = part / 'arithmetic_certificates.jsonl'
        manifest = json.loads(manifest_path.read_text())
        if manifest['capture_receipt_sha256'] != receipt_hash:
            raise ValueError('Part binds a different capture receipt')
        if {name: info['sha256'] for name, info in manifest['capture_bindings'].items()} != bindings:
            raise ValueError('Part binds different static capture streams')
        actual = digest(certificate)
        if actual != manifest['certificates_sha256']:
            raise ValueError('Part certificate hash differs from its manifest')
        provenance.append(dict(directory=str(part.resolve()),
            manifest_sha256=digest(manifest_path), certificates_sha256=actual,
            expected_records=manifest['certified_theory_clauses'], observed_records=0,
            retained_records=0, omitted_unselected_records=0))
        iterators.append(iter(records(certificate)))
    out.mkdir(parents=True)
    target = out / 'arithmetic_certificates.jsonl'
    partial = target.with_suffix('.jsonl.partial')
    heap = []
    for i, iterator in enumerate(iterators):
        item = next(iterator, None)
        if item is not None:
            heapq.heappush(heap, (item[0], i, item[1], item[2]))
    source = (json.loads(line)['clause'] for line in (capture / 'theory_clauses.jsonl').open())
    source_index, clause, count, previous_index = -1, None, 0, -1
    selected_set = set(selected)
    with partial.open('wb') as stream:
        while heap:
            index, part_index, raw, record = heapq.heappop(heap)
            if index <= previous_index:
                raise ValueError('Duplicate or disordered index across part streams')
            previous_index = index
            provenance[part_index]['observed_records'] += 1
            if index not in selected_set and allow_unselected_records:
                provenance[part_index]['omitted_unselected_records'] += 1
                item = next(iterators[part_index], None)
                if item is not None:
                    heapq.heappush(heap, (item[0], part_index, item[1], item[2]))
                continue
            if count >= len(selected) or index != selected[count]:
                raise ValueError('Duplicate, missing, or unselected certificate in merge')
            while source_index < index:
                clause = next(source)
                source_index += 1
            if record['clause'] != clause:
                raise ValueError('Certificate literal clause differs from frozen theory source')
            stream.write(raw)
            provenance[part_index]['retained_records'] += 1
            count += 1
            item = next(iterators[part_index], None)
            if item is not None:
                heapq.heappush(heap, (item[0], part_index, item[1], item[2]))
        if count != len(selected):
            raise ValueError('Merged certificate coverage is incomplete')
        if any(p['observed_records'] != p['expected_records'] for p in provenance):
            raise ValueError('Part count differs from its preparation manifest')
        stream.flush()
        os.fsync(stream.fileno())
    # Recheck source hashes before publishing the composed stream.
    for part, info in zip(parts, provenance):
        if (digest(part / 'arithmetic_certificates.jsonl') != info['certificates_sha256']
                or digest(part / 'preparation.json') != info['manifest_sha256']):
            raise ValueError('A part changed during composition')
    if (receipt_hash != digest(receipt_path) or selected_hash != digest(selected_path)
            or any(digest(capture / n) != h for n, h in bindings.items())):
        raise ValueError('Capture changed during composition')
    partial.replace(target)
    sync_directory(out)
    readback_count = sum(1 for _ in records(target))
    if readback_count != count:
        raise ValueError('Closed composed stream read-back count mismatch')
    manifest = dict(status='COMPLETE_COMPOSED_EXACT_MULTIPLIER_CANDIDATES',
        input_sha256=receipt['input_sha256'], capture_receipt_sha256=receipt_hash,
        capture_bindings={n: dict(path=str((capture/n).resolve()), sha256=h) for n, h in bindings.items()},
        selection=dict(path=str(selected_path.resolve()), sha256=selected_hash, records=len(selected)),
        parts=provenance, certificates_sha256=digest(target), certified_theory_clauses=count,
        read_back_count=readback_count, unchanged_record_bytes=True,
        unselected_record_filtering_enabled=allow_unselected_records,
        scope='Coverage and source-bound composition only. Independent exact arithmetic and RUP verification required.')
    atomic_json(out / 'preparation.json', manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--selected', type=Path, required=True)
    parser.add_argument('--part', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--allow-unselected-records', action='store_true',
                        help='Drop candidate records outside the final selected set, preserving omission counts')
    args = parser.parse_args()
    result = compose(args.capture, args.selected, args.part, args.out, args.allow_unselected_records)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
