#!/usr/bin/env python3
"""Small producer controls replayed by the separate stdlib hint checker."""
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'continuation/verification'))
from check_lra_rup import propagate_check


def main():
    exe = Path(__file__).with_name('rup_dependency_producer')
    results = []
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        for n in range(2, 7):
            capture = base / ('capture' + str(n))
            capture.mkdir()
            # The complete family forbids each Boolean assignment. Resolution
            # eliminates one variable at a time; each resolvent must be RUP.
            axioms = [sorted(s * (i + 2) for i, s in enumerate(signs))
                      for signs in itertools.product((-1, 1), repeat=n)]
            steps = [axioms[0]]  # exact duplicate case
            for k in range(n - 1, 0, -1):
                steps.extend(sorted(s * (i + 2) for i, s in enumerate(signs))
                             for signs in itertools.product((-1, 1), repeat=k))
            steps.append([])
            inputs = [[1], None] + axioms[:len(axioms)//2]
            theories = axioms[len(axioms)//2:]
            for name, clauses in [('input_clauses', inputs), ('theory_clauses', theories), ('rup_clauses', steps)]:
                (capture / (name + '.jsonl')).write_text(''.join(json.dumps({'clause': c}) + '\n' for c in clauses))
            out = base / ('out' + str(n))
            result = subprocess.run([str(exe), str(capture), str(out)], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, result.stderr
            known = {}
            for line in (out / 'trimmed_trace.jsonl').read_text().splitlines():
                record = json.loads(line)
                if record['kind'] == 'rup':
                    propagate_check(record['clause'], record['reasons'], known)
                else:
                    actual = (inputs if record['source'] == 'input' else theories)[record['source_index']]
                    assert record['clause'] == actual
                known[record['id']] = record['clause']
            assert record['clause'] == [] and record['kind'] == 'rup'
            results.append(dict(variables=n, status='PASS_INDEPENDENT_HINT_REPLAY', trace_records=len(known)))
        bad = base / 'bad'
        bad.mkdir()
        (bad / 'input_clauses.jsonl').write_text('{"clause":[1]}\n{"clause":[2,3]}\n')
        (bad / 'theory_clauses.jsonl').write_text('')
        (bad / 'rup_clauses.jsonl').write_text('{"clause":[2]}\n')
        rejected = subprocess.run([str(exe), str(bad), str(base / 'bad_out')], capture_output=True, text=True, timeout=10)
        assert rejected.returncode == 2 and 'RUP failed at source index 0' in rejected.stderr
        results.append(dict(status='PASS_NON_RUP_REJECTED'))
    report = dict(status='PASS_PRODUCER_CONTROLS', cases=results,
        producer_cpp_sha256=hashlib.sha256(exe.with_suffix('.cpp').read_bytes()).hexdigest(),
        producer_executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        checker_source_sha256=hashlib.sha256((ROOT / 'continuation/verification/check_lra_rup.py').read_bytes()).hexdigest())
    Path(__file__).with_name('rup_dependency_producer_controls.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
