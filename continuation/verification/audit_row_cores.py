"""Bounded adversarial replay of exact row-core certificates; no solver."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (480 * 1024**2,) * 2)
signal.alarm(29)
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CHECKER = ROOT / 'continuation/verify_row_cores.py'
START = time.monotonic()
checker_bytes = CHECKER.read_bytes()
spec = importlib.util.spec_from_file_location('row_core_checker', CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def reject(data):
    try:
        checker.verify(data)
    except (AssertionError, KeyError, IndexError, ValueError) as e:
        return type(e).__name__ + ': ' + str(e)
    raise AssertionError('Invalid mutation was accepted')


def main():
    records = []
    first = {}
    for dirname in ('row_core_certificates', 'row_core_certificates_v2'):
        for file in sorted((ROOT / 'continuation' / dirname).glob('[0-9]*.json')):
            data_bytes = file.read_bytes()
            data = json.loads(data_bytes)
            receipt = checker.verify(data)
            version = data.get('format_version', 1)
            first.setdefault(version, data)
            source = ROOT / 'continuation/structural_nine/row_elimination_seeded/regions' / file.name
            original = json.loads(source.read_text())
            assert data['core_allocations'] == original['core_allocations']
            assert data['core_allocation_ids'] == original['core_allocation_ids']
            assert data['other_region_atoms'] == original['region_atoms']
            assert data['source_core_sha256'] == original['core_sha256']
            inner = ROOT / 'continuation/structural_nine/row_elimination_seeded/inner' / file.with_suffix('.smt2').name
            assert sha(inner.read_bytes()) == data['source_core_sha256']
            records.append({'file': str(file.relative_to(ROOT)), 'sha256': sha(data_bytes),
                            'format_version': version, **receipt})
    mutations = {}
    old_false = json.loads((OUT / 'row_core_float_unsound_certificate.json').read_text())
    mutations['previously_accepted_float_underflow_certificate'] = reject(old_false)
    current = first[2]
    value = deepcopy(current)
    value['branches'].pop()
    mutations['missing_failure_branch'] = reject(value)
    value = deepcopy(current)
    value['branches'][0]['weights'][0] = '-1'
    mutations['negative_alternative_weight'] = reject(value)
    value = deepcopy(current)
    value['branches'][0]['weights'] = ['0'] * len(value['branches'][0]['weights'])
    mutations['zero_alternative_vector'] = reject(value)
    value = deepcopy(current)
    value['core_allocation_ids'][0] += 1
    mutations['wrong_allocation_id'] = reject(value)
    value = deepcopy(current)
    value['other_region_atoms'][0]['coefficients'][0] += 1
    mutations['changed_other_agent_literal'] = reject(value)
    value = deepcopy(current)
    value['branches'][0]['failure_rows'][0] = [float(x) for x in value['branches'][0]['failure_rows'][0]]
    mutations['float_failure_coefficients'] = reject(value)
    value = deepcopy(current)
    value['branches'][0]['weights'][0] = 0.0
    mutations['float_alternative_weights'] = reject(value)
    value = deepcopy(current)
    value['failure_clauses'][0].pop()
    mutations['omit_potential_minimum_trim'] = reject(value)
    assert CHECKER.read_bytes() == checker_bytes, 'Checker changed during replay'
    report = {'status': 'PASS_AFTER_EXACT_TYPE_REPAIR_NOT_GLOBAL_COVERAGE',
              'python': sys.version, 'checker_sha256': sha(checker_bytes),
              'elapsed_seconds': time.monotonic() - START,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'certificates_verified': len(records),
              'format_counts': {str(v): sum(r['format_version'] == v for r in records) for v in (1, 2)},
              'failure_branches_verified': sum(r['exhaustive_failure_branches'] for r in records),
              'max_failure_branches': max(r['exhaustive_failure_branches'] for r in records),
              'source_binding': 'Every allocation, ID, other-row predicate list, and source core hash matched the original seeded record.',
              'mutations_rejected': mutations, 'receipts': records}
    (OUT / 'row_core_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'receipts'}, indent=2))


if __name__ == '__main__':
    main()
