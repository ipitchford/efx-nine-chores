#!/usr/bin/env python3
"""Seal the complete checked research release and verify its written archive.

No external publication or upload is performed by this program.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

from solve_efx9 import atomic_write

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
ZIP = OUT / 'economics-problem-2-reproducibility.zip'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(relative):
    return json.loads((ROOT / relative).read_text())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index_path = 'continuation/verification/nine_release_index.json'
    index = read(index_path)
    if index.get('status') != 'PASS_COMPLETE_NINE_CHORE_RELEASE_BINDING':
        raise SystemExit('Complete checked nine-chore release binding required.')
    for relative, expected in index['files_sha256'].items():
        path = ROOT / relative
        if not path.is_file() or sha(path) != expected:
            raise SystemExit('Required proof object absent or changed: ' + relative)
    proof = read('continuation/verification/zero9_complete_lra_certificate.json')
    if proof.get('status') != 'PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE':
        raise SystemExit('Complete independent nine-chore certificate required.')
    continuation = read('docs/CONTINUATION_STATUS.json')
    if continuation.get('all_supervised_runs_terminal') is not True:
        raise SystemExit('Live supervised jobs must be completed or explicitly stopped before the final snapshot.')
    report = read('tmp/pdfs/release_final/build_receipt.json')
    pdf = ROOT / 'output/pdf/economics-problem-2-research-report.pdf'
    if report.get('status') != 'FINAL_MANUSCRIPT_RENDERED_AND_SEALED' or sha(pdf) != report['sha256']:
        raise SystemExit('Final theorem manuscript missing or changed.')
    visual = read('output/pdf/release_visual_review.json')
    if visual.get('status') != 'PASS_FINAL_PDF_VISUAL_REVIEW' or visual.get('pdf_sha256') != sha(pdf):
        raise SystemExit('Current final PDF must pass visual review.')

    # Preserve the original seven-chore certificate identities used by the
    # optional independent six -> seven -> eight -> nine baseline chain.
    root7 = read('results/root7_ethos.json')
    if (root7.get('result') != 'verified' or not root7.get('reference_binding')
            or not root7.get('requires_final_false_at_global_scope')):
        raise SystemExit('Corrected seven-chore reference-bound receipt required.')
    for relative, key in [('results/root7_pruned.smt2', 'input_sha256'),
                          ('certificates/root7_cvc5.cpc', 'proof_sha256')]:
        if sha(ROOT / relative) != root7[key]:
            raise SystemExit('Historical seven-chore proof identity changed.')

    command = (ROOT / 'docs/zero9_replay_command.txt').read_text().strip()
    replacements = {
        'N9_REPLAY_COMMAND': command,
        'N9_ORIGINAL_COUNT': f"{proof['selected_original_clauses']:,}",
        'N9_THEORY_COUNT': f"{proof['selected_theory_clauses']:,}",
        'N9_RUP_COUNT': f"{proof['derived_rup_clauses']:,}",
        'N9_REASON_COUNT': f"{proof['ordered_reason_positions']:,}",
    }
    readme = (ROOT / 'README.release.template.md').read_text()
    for name, value in replacements.items():
        readme = readme.replace('{{' + name + '}}', value)
    if re.search(r'\{\{[A-Z0-9_]+\}\}', readme):
        raise SystemExit('Unfilled README token')
    atomic_write(ROOT / 'README.md', readme)
    claims = {
        'updated_at_utc': datetime.now(timezone.utc).isoformat(),
        'main_target': 'Complete zero-inclusive EFX for arbitrary nonnegative additive three-agent nine-chore costs.',
        'main_target_status': 'PROVED_BY_WRITTEN_REDUCTION_AND_INDEPENDENT_EXACT_COMPUTATIONAL_CERTIFICATE',
        'main_certificate': 'continuation/verification/zero9_complete_lra_certificate.json',
        'main_release_binding': index_path,
        'main_input_sha256': proof['input_sha256'],
        'eight_baseline_certificate': 'continuation/verification/zero8_complete_lra_certificate.json',
        'baseline': 'Ordinary eight-chore existence; alternative checked seven/eight chain over the cited KMS six-chore theorem.',
        'no_prescribed_agent_strengthening_required': True,
        'all_19683_allocations_covered': True,
        'all_nonnegative_real_costs_covered': True,
        'proof_assistant_formalization': False,
        'external_publication_performed': False,
        'strongest_separate_integer_representative_bounds': {'one_zero_per_row': 2566, 'positive_common_minimum_one': 5132},
        'finite_integer_grid_used_by_main_refutation': False,
        'historical_regional_searches_used_as_main_premises': False,
        'constructive_finder': 'src/solve_efx9.py',
        'historical_attempts': 'docs/CONTINUATION_STATUS.json',
    }
    atomic_write(ROOT / 'docs/CLAIM_STATUS.json', json.dumps(claims, indent=2) + '\n')

    files = set()
    def add(path):
        if path.is_file() and not path.is_symlink():
            files.add(path)
    def glob(pattern):
        for path in ROOT.glob(pattern):
            add(path)
    for name in ['README.md', 'README.release.template.md', 'target.yaml',
                 'novelty_report.md', 'novelty_designated_addendum.md', 'proof_export_notes.md',
                 'requirements-solver.txt', 'requirements-report.txt', 'requirements-continuation.txt']:
        add(ROOT / name)
    for pattern in ['docs/*', 'src/*.py', 'src/*.tex', 'scripts/*.sh', 'examples/*.json']:
        glob(pattern)
    for extension in ['json', 'smt2', 'log', 'csv']:
        glob('results/**/*.' + extension)
    for name in ['root7_cvc5.cpc', 'designated6_cvc5.cpc']:
        add(ROOT / 'certificates' / name)
    add(ROOT / 'results/root8_pruned.z3proof')
    for extension in ['py', 'json', 'smt2', 'md', 'csv']:
        for pattern in ['work/structural_*.', 'work/compute_*.', 'work/compute_*/**/*.']:
            glob(pattern + extension)
    for extension in ['smt2', 'cpc', 'json']:
        glob('work/checker_controls/**/*.' + extension)
    glob('work/cvc5_signatures/proofs/eo/cpc/**/*.eo')
    for relative in ['work/cvc5_signatures/COPYING', 'work/cvc5_signatures/AUTHORS',
                     'work/ethos/COPYING', 'work/ethos/AUTHORS', 'work/ethos/licenses/lgpl-3.0.txt',
                     'replay/setup_checker_validation.json', 'replay/checker_controls.json']:
        add(ROOT / relative)
    add(pdf)
    add(ROOT / 'output/pdf/release_visual_review.json')
    allowed = {'.py', '.cpp', '.md', '.yaml', '.json', '.jsonl', '.smt2', '.log', '.csv',
               '.txt', '.bin', '.pbtxt', '.stdout', '.stderr', '.cnf', '.lrat', '.rup', '.cpc', '.tex'}
    for path in (ROOT / 'continuation').rglob('*'):
        relative = path.relative_to(ROOT / 'continuation')
        if any(part in {'ortools_runtime', 'yices', '__pycache__'} for part in relative.parts):
            continue
        if path.suffix in allowed:
            add(path)
    # Explicit proof-index membership wins over suffix selection. Runtime and
    # external source PDFs are not silently admitted through this mechanism.
    for relative in index['files_sha256']:
        add(ROOT / relative)
    add(ROOT / index_path)
    # Preserve every accepted proof object, while avoiding repeated copies of
    # growing, untrusted extraction checkpoints. Their identities remain in a
    # separate inventory; the complete proof and canonical capture are kept.
    omissions = []
    capture_relative = Path(index['accepted_capture'])
    if capture_relative.is_absolute() or '..' in capture_relative.parts:
        raise SystemExit('Accepted capture must be a safe project-relative path.')
    accepted_capture = ROOT / capture_relative
    historical_capture_dirs = {
        ROOT / 'continuation/exact_search/zero9_clause_capture_run1/capture',
        ROOT / 'continuation/exact_search/zero9_clause_capture_run1_durable_snapshot/capture',
    }
    preserved_rejected_originals = (
        'continuation/exact_search/zero8_clause_capture_run3/capture/',
        'continuation/exact_search/zero8_selected_farkas_run1/artifacts/',
    )
    source_extensions = {'.py', '.cpp', '.md', '.tex', '.sh', '.yaml', '.eo'}
    documentary_name = re.compile(
        r'receipt|terminal|verdict|status|manifest|audit|review|control|validation|'
        r'provenance|binding|preparation|completion|result', re.IGNORECASE)

    def keep_documentary_history(path, relative):
        # All proof-index members bypass this selection. Keep authoring and
        # checking sources, the current documents, and compact run records;
        # large intermediate searches are inventoried instead of duplicated.
        if path == pdf or relative == 'output/pdf/release_visual_review.json':
            return True
        if relative.split('/', 1)[0] in {'docs', 'src', 'scripts', 'examples'}:
            return True
        if path.suffix in source_extensions:
            return True
        if path.name in {'COPYING', 'AUTHORS', 'LICENSE', 'README'}:
            return True
        if relative.startswith(preserved_rejected_originals):
            return True
        if path.stat().st_size <= 512 * 1024:
            if path.suffix == '.txt':
                return True
            if path.suffix == '.json' and relative.startswith('continuation/verification/'):
                return True
            if (path.suffix in {'.json', '.log', '.stdout', '.stderr'}
                    and documentary_name.search(path.name)):
                return True
        return False

    for path in sorted(files):
        relative = str(path.relative_to(ROOT))
        if relative in index['files_sha256']:
            continue
        reason = None
        duplicate = None
        if path.name.startswith('candidate_justifications') and path.suffix == '.jsonl':
            reason = 'Intermediate untrusted extraction checkpoint; the complete accepted refutation is included.'
        elif path.parent in historical_capture_dirs and path.parent != accepted_capture and path.suffix == '.jsonl':
            canonical = accepted_capture / path.name
            if canonical in files and sha(path) == sha(canonical):
                reason = 'Identical to the accepted replay capture included in this archive.'
                duplicate = str(canonical.relative_to(ROOT))
            elif (not canonical.exists()
                  and path.name in {'rup_clauses.jsonl', 'assumptions.jsonl'}):
                reason = 'Historical solver callback stream; the accepted independent refutation is included and replay does not use this stream.'
        if reason is None and not keep_documentary_history(path, relative):
            reason = ('Historical research data outside the accepted release proof. '
                      'Its exact identity is retained here; all final proof and replay inputs are included.')
        if reason:
            item = {'path': relative, 'bytes': path.stat().st_size,
                    'sha256': sha(path), 'reason': reason}
            if duplicate:
                item['duplicate_of'] = duplicate
            omissions.append(item)
            files.remove(path)
    omission_path = ROOT / 'historical_file_omissions.json'
    atomic_write(omission_path, json.dumps({
        'scope': 'Distribution-only omissions of intermediate research data and duplicate captures; local research files are preserved.',
        'all_release_index_objects_included': True,
        'files': omissions,
    }, indent=2) + '\n')
    add(omission_path)
    entries = [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                'sha256': sha(path)} for path in sorted(files)]
    lookup = {entry['path']: entry['sha256'] for entry in entries}
    for relative, expected in index['files_sha256'].items():
        if lookup.get(relative) != expected:
            raise SystemExit('Proof changed before snapshot: ' + relative)
    manifest = {
        'scope': 'Complete current proof, source code, current documents, and selected historical run records; historical_file_omissions.json identifies omitted intermediate research data and duplicate captures. Platform runtimes, caches, unrequested external source copies, and self-manifests are excluded.',
        'central_result': 'Complete EFX existence for three agents and nine chores with arbitrary nonnegative additive costs, supported by a written reduction and independently checked exact UNSAT certificate.',
        'main_release_index_sha256': sha(ROOT / index_path),
        'files': entries,
    }
    atomic_write(ROOT / 'artifact_manifest.json', json.dumps(manifest, indent=2) + '\n')
    atomic_write(ROOT / 'MANIFEST.sha256', ''.join(e['sha256'] + '  ' + e['path'] + '\n' for e in entries))
    files.update({ROOT / 'artifact_manifest.json', ROOT / 'MANIFEST.sha256'})
    fd, temporary = tempfile.mkstemp(prefix=ZIP.stem + '.', suffix='.zip', dir=OUT)
    os.close(fd)
    temporary_path = Path(temporary)
    try:
        with zipfile.ZipFile(temporary_path, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=8, allowZip64=True) as archive:
            for path in sorted(files):
                archive.write(path, 'economics_problem2/' + str(path.relative_to(ROOT)))
        with temporary_path.open('rb') as stream:
            os.fsync(stream.fileno())
        os.replace(temporary_path, ZIP)
        dfd = os.open(OUT, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    print(json.dumps({'stage': 'ZIP_SEALED', 'bytes': ZIP.stat().st_size,
                      'payload_files': len(entries)}, sort_keys=True), flush=True)
    # A distinct process reopens the completed archive, verifies every member
    # hash and CRC, binds the proof index, and independently computes ZIP SHA.
    receipt_path = OUT / 'release_archive_integrity.json'
    run = subprocess.run([sys.executable, str(ROOT / 'src/verify_release_archive.py'),
                          str(ZIP), '--out', str(receipt_path)], cwd=ROOT,
                         capture_output=True, text=True, timeout=600)
    if run.returncode:
        raise SystemExit('Written archive verification failed:\n' + run.stderr[-8000:])
    checked = json.loads(receipt_path.read_text())
    if checked['archive_sha256'] != sha(ZIP):
        raise SystemExit('Archive bytes changed after fresh-process verification.')
    checked['builder_source_sha256'] = sha(Path(__file__))
    checked['built_at_utc'] = datetime.now(timezone.utc).isoformat()
    atomic_write(OUT / 'release_bundle_build_receipt.json', json.dumps(checked, indent=2) + '\n')
    print(json.dumps(checked, indent=2), flush=True)


if __name__ == '__main__':
    main()
