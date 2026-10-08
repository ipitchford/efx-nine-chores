#!/usr/bin/env python3
"""Hash-only preflight of immutable release inputs already independently checked.

No new mathematical certificate is accepted here, and no nine-chore completion
object is written. The final trace, selection, and complete arithmetic coverage
remain separate required gates.
"""
from datetime import datetime, timezone
from pathlib import Path

from lra_certificate_common import atomic_json, capture_files, json_file, require, sha256

ROOT = Path(__file__).resolve().parents[2]
VER = ROOT / 'continuation/verification'
EXPECTED = '65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b'
EXTERNAL = {'sources/kms_2305_04168.pdf', 'work/kms.txt',
            'sources/zhang_2609_10585v2.pdf', 'work/zhang_v2.txt'}


def main():
    files, external = {}, {}

    def bind(path, expected=None):
        path = Path(path)
        path = (path if path.is_absolute() else ROOT / path).resolve()
        name = path.relative_to(ROOT).as_posix()
        if name in EXTERNAL:
            external[name] = expected
            return expected
        require(path.is_file(), 'missing static prerequisite: ' + name)
        actual = sha256(path)
        require(expected is None or actual == expected, 'changed static prerequisite: ' + name)
        files[name] = actual
        return actual

    old = json_file(VER / 'zero9_end_to_end_binding.json')
    require(old['status'] == 'PASS_END_TO_END_INPUT_BINDING_AND_OMITTED_ALLOCATION_COVERAGE', 'missing target correspondence')
    require(old['input_sha256'] == EXPECTED, 'different main input')
    bind(VER / 'zero9_end_to_end_binding.json')
    for path, digest in old['bound_files'].items():
        bind(path, digest)

    for filename, status in [
        ('zero8_full_target_binding.json', 'PASS_ORDINARY_EIGHT_CHORE_INPUT_AND_COMPLETED_CERTIFICATE_BINDING'),
        ('baseline_dependency_inventory.json', 'PASS_BASELINE_DEPENDENCY_INVENTORY_AND_UNCHANGED_SEVEN_CERTIFICATE_BINDING')]:
        report = json_file(VER / filename)
        require(report['status'] == status, 'missing baseline binding')
        bind(VER / filename)
        for path, digest in report['files_sha256'].items():
            bind(path, digest)

    eight = json_file(VER / 'zero8_complete_lra_certificate.json')
    require(eight['status'] == 'PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE', 'eight certificate incomplete')
    base8 = ROOT / 'continuation/exact_search/zero8_clause_capture_composed1/capture'
    for name, digest in eight['captured_files_sha256'].items():
        bind(base8 / name, digest)
    for name, digest in eight['checker_sources_sha256'].items():
        bind(VER / name, digest)
    for path, key in [
        ('continuation/exact_search/zero8_rup_trim1/trimmed_trace.jsonl', 'trace_sha256'),
        ('continuation/exact_search/zero8_rup_trim1/selected_theory_indices.json', 'selected_indices_sha256'),
        ('continuation/exact_search/zero8_selected_farkas_composed1/arithmetic_certificates.jsonl', 'certificate_sha256')]:
        bind(path, eight[key])
    stages = ['zero8_capture_composed1_input_binding.json', 'zero8_rup_trim1_independent.json',
              'zero8_selected_farkas_independent.json']
    require(sorted(bind(VER / name) for name in stages) == sorted(eight['stage_receipts_sha256'].values()),
            'changed eight stage receipt')

    nine = json_file(VER / 'zero9_capture_snapshot_input_binding.json')
    require(nine['status'] == 'PASS_ORIGINAL_INPUT_CNF_AND_AFFINE_ATOM_BINDING', 'nine capture binding absent')
    require(nine['input_sha256'] == EXPECTED, 'nine capture has different input')
    base9 = ROOT / 'continuation/exact_search/zero9_clause_capture_run1_durable_snapshot/capture'
    _, current = capture_files(base9)
    require(current == nine['captured_files_sha256'], 'nine capture changed')
    for name, digest in current.items():
        bind(base9 / name, digest)
    bind(VER / 'zero9_capture_snapshot_input_binding.json')
    bind(VER / 'check_lra_capture.py', nine['checker_sha256'])
    bind(VER / 'lra_certificate_common.py', nine['common_sha256'])
    for path in ['continuation/exact_search/zero8_clause_capture_composed1/provenance_manifest.json',
                 'continuation/exact_search/zero8_selected_farkas_composed1/preparation.json',
                 'continuation/exact_search/zero9_clause_capture_run1_durable_snapshot/snapshot_manifest.json',
                 'continuation/verification/build_nine_release_index.py',
                 'continuation/verification/lra_checker_negative_controls.json',
                 'continuation/verification/lra_relocation_control.json',
                 'continuation/verification/test_lra_certificate_checkers.py',
                 'continuation/verification/test_lra_relocation.py']:
        bind(path)
    report = dict(status='PASS_STATIC_NINE_RELEASE_PREREQUISITES',
                  input_sha256=EXPECTED, completed_mathematical_checks_repeated=False,
                  main_nine_certificate_accepted_here=False,
                  main_certificate_is_a_separate_final_gate=True,
                  final_required_objects=['frozen full RUP refutation and selected indices',
                                          'single exact complete selected arithmetic stream',
                                          'independent full Boolean and arithmetic receipts'],
                  files_sha256=dict(sorted(files.items())), file_count=len(files),
                  external_source_hashes_not_required_archive_members=external,
                  checker_source_sha256=sha256(__file__), completed_at_utc=datetime.now(timezone.utc).isoformat())
    atomic_json(VER / 'nine_release_static_preflight.json', report)
    print(report['status'], report['file_count'])


if __name__ == '__main__':
    main()
