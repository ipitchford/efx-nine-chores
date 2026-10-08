#!/usr/bin/env python3
"""Backward-extraction controls with independent ordered-hint replay."""
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
    exe = Path(__file__).with_name('rup_dependency_producer_v5')
    results = []
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        def run(name, inputs, theories, steps):
            capture = base / name
            capture.mkdir()
            for field, clauses in [('input_clauses', inputs), ('theory_clauses', theories), ('rup_clauses', steps)]:
                (capture / (field + '.jsonl')).write_text(''.join(json.dumps({'clause': c}) + '\n' for c in clauses))
            out = base / (name + '_out')
            result = subprocess.run([str(exe), str(capture), str(out)], capture_output=True, text=True, timeout=10)
            return result, out
        for n in range(2, 7):
            axioms = [sorted(s * (i + 2) for i, s in enumerate(signs))
                      for signs in itertools.product((-1, 1), repeat=n)]
            steps = [axioms[0]]
            for k in range(n - 1, 0, -1):
                steps.extend(sorted(s * (i + 2) for i, s in enumerate(signs))
                             for signs in itertools.product((-1, 1), repeat=k))
            steps.append([])
            inputs = [[1], None] + axioms[:len(axioms)//2]
            theories = axioms[len(axioms)//2:]
            result, out = run('positive' + str(n), inputs, theories, steps)
            assert result.returncode == 0, result.stderr
            known = {}
            for line in (out / 'trimmed_trace.jsonl').read_text().splitlines():
                record = json.loads(line)
                if record['kind'] == 'rup':
                    assert all(i < record['id'] for i in record['reasons'])
                    propagate_check(record['clause'], record['reasons'], known)
                else:
                    actual = (inputs if record['source'] == 'input' else theories)[record['source_index']]
                    assert record['clause'] == actual
                known[record['id']] = record['clause']
            assert record['clause'] == [] and record['kind'] == 'rup'
            results.append(dict(variables=n, status='PASS_INDEPENDENT_HINT_REPLAY', trace_records=len(known)))
        negatives = [
            ('provisional_opposite_units', [[1]], [[2], [-2]]),
            ('future_binary_and_unit', [[1], [-2]], [[2], [2, 3], [-3]]),
            ('self_or_future_empty', [[1]], [[2], []]),
            ('satisfiable_complete_capture', [[1], [2, 3]], [[2]]),
        ]
        for name, inputs, steps in negatives:
            result, out = run(name, inputs, [], steps)
            assert result.returncode == 3, (name, result.stderr)
            report = json.loads((out / 'producer_result.json').read_text())
            assert report['status'] == 'UNTRUSTED_BACKWARD_EXTRACTION_INCOMPLETE_NO_REFUTATION'
            assert report['final_empty_id'] == 0
            assert not (out / 'trimmed_trace.jsonl').exists()
            results.append(dict(status='PASS_INVALID_PROVISIONAL_REFUTATION_REJECTED', control=name))
    report = dict(status='PASS_BACKWARD_PRODUCER_CONTROLS', cases=results,
        producer_cpp_sha256=hashlib.sha256(exe.with_suffix('.cpp').read_bytes()).hexdigest(),
        producer_executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        checker_source_sha256=hashlib.sha256((ROOT / 'continuation/verification/check_lra_rup.py').read_bytes()).hexdigest())
    Path(__file__).with_name('rup_dependency_producer_v5_controls.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
