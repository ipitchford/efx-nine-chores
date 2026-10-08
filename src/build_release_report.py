#!/usr/bin/env python3
"""Build the theorem manuscript; final output requires the checked nine proof.

--draft writes only a clearly marked temporary preview. It cannot overwrite
the final report. Exact proof and input identities are checked before release.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from solve_efx9 import atomic_write

ROOT = Path(__file__).resolve().parents[1]
VER = ROOT / 'continuation/verification'
INPUT_SHA = '65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def sealed_copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=target.name + '.', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as output, source.open('rb') as stream:
            shutil.copyfileobj(stream, output, 1 << 20)
            output.flush()
            os.fsync(output.fileno())
        if sha(Path(temporary)) != sha(source):
            raise AssertionError('temporary PDF differs from rendered output')
        os.replace(temporary, target)
        dfd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft', action='store_true')
    parser.add_argument('--certificate', type=Path, default=VER / 'zero9_complete_lra_certificate.json')
    parser.add_argument('--replay-command', type=Path, default=ROOT / 'docs/zero9_replay_command.txt')
    args = parser.parse_args()
    args.certificate = args.certificate.resolve()
    args.replay_command = args.replay_command.resolve()
    data = {}
    if args.certificate.exists():
        data = json.loads(args.certificate.read_text())
    passed = data.get('status') == 'PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE'
    if not args.draft:
        if not passed:
            raise SystemExit('Final manuscript blocked: complete independent nine-chore certificate required.')
        if data.get('input_sha256') != INPUT_SHA:
            raise SystemExit('Final manuscript blocked: proof has a different input identity.')
        for key in ['original_smt_reconstructed', 'exact_affine_atoms_checked',
                    'boolean_rup_refutation_checked', 'all_admitted_theory_axioms_checked']:
            if data.get(key) is not True:
                raise SystemExit('Final manuscript blocked: ' + key)
        if data.get('callback_assumptions_admitted') is not False:
            raise SystemExit('Final manuscript blocked: unsupported axiom provenance.')
        if data.get('producer_solver_verdict_trusted') is not False:
            raise SystemExit('Final manuscript blocked: independent proof required.')
        if sha(ROOT / 'continuation/exact_search/zero_minimum9_reference_strict.smt2') != INPUT_SHA:
            raise SystemExit('Final manuscript blocked: input bytes changed.')
        if not args.replay_command.is_file():
            raise SystemExit('Final manuscript blocked: concrete replay command is missing.')
        index_path = VER / 'nine_release_index.json'
        if not index_path.is_file():
            raise SystemExit('Final manuscript blocked: complete release binding is missing.')
        index = json.loads(index_path.read_text())
        if index.get('status') != 'PASS_COMPLETE_NINE_CHORE_RELEASE_BINDING':
            raise SystemExit('Final manuscript blocked: release binding is not complete.')
        indexed = index.get('files_sha256')
        if not isinstance(indexed, dict) or not indexed:
            raise SystemExit('Final manuscript blocked: no proof-object file identities.')
        try:
            receipt_relative = str(args.certificate.relative_to(ROOT))
        except ValueError:
            raise SystemExit('Final manuscript blocked: the selected receipt is outside the indexed package.')
        if indexed.get(receipt_relative) != sha(args.certificate):
            raise SystemExit('Final manuscript blocked: selected proof receipt is not the indexed completed object.')
        for relative, expected in indexed.items():
            path = ROOT / relative
            if not path.is_file() or sha(path) != expected:
                raise SystemExit('Final manuscript blocked: indexed proof bytes differ: ' + relative)

    working = ROOT / 'tmp/pdfs' / ('release_draft' if args.draft else 'release_final')
    working.mkdir(parents=True, exist_ok=True)
    status = ('DRAFT: nine-chore independent refutation still pending; theorem wording below is provisional.'
              if args.draft else 'COMPLETE: independently checked exact nine-chore UNSAT certificate.')
    fmt = lambda key: f'{data[key]:,}' if passed and key in data else 'Pending'
    command = (args.replay_command.read_text().strip() if args.replay_command.is_file()
               else '# Final concrete replay paths will be inserted after the complete certificate passes.')
    replacements = {
        'DATE': datetime.now(timezone.utc).strftime('%-d %B %Y'),
        'MAIN_STATUS_TEXT': status,
        'CERTIFICATE_STATUS_PARAGRAPH': (
            'The complete independent replay passed original-input reconstruction, the final Boolean '
            'contradiction, and exact arithmetic validation of every admitted theory axiom. The following '
            'counts describe the proof actually checked.' if passed and not args.draft else
            'The eight-chore certificate is complete. The nine-chore column remains provisional until '
            'its full independent Boolean and arithmetic replay finishes. A solver UNSAT result alone '
            'does not close this release gate.'),
        'N9_ORIGINAL_COUNT': fmt('selected_original_clauses'),
        'N9_THEORY_COUNT': fmt('selected_theory_clauses'),
        'N9_RUP_COUNT': fmt('derived_rup_clauses'),
        'N9_REASON_COUNT': fmt('ordered_reason_positions'),
        'N9_PROOF_RECEIPT_PATH': '`' + str(args.certificate.relative_to(ROOT)) + '`',
        'N9_REPLAY_COMMAND': command,
        'PRESS_DRAFT': (ROOT / 'docs/prospective_release_template.md').read_text().strip(),
    }
    content = (ROOT / 'docs/release_manuscript_template.md').read_text()
    for name, value in replacements.items():
        content = content.replace('{{' + name + '}}', value)
    if re.search(r'\{\{[A-Z0-9_]+\}\}', content):
        raise SystemExit('Unfilled release manuscript token')
    markdown_path = working / 'manuscript.md'
    atomic_write(markdown_path, content)
    intermediate_pdf = working / 'manuscript.pdf'
    run = subprocess.run([
        'pandoc', str(markdown_path), '--from=markdown+tex_math_dollars', '--standalone',
        '--number-sections', '--pdf-engine=xelatex', '--no-highlight',
        '--include-in-header=' + str(ROOT / 'src/release_header.tex'),
        '-V', 'documentclass=article', '-V', 'fontsize=11pt',
        '-V', 'geometry=a4paper,left=25mm,right=25mm,top=24mm,bottom=25mm',
        '-V', 'mainfont=Latin Modern Roman', '-V', 'sansfont=DejaVu Sans',
        '-V', 'monofont=DejaVu Sans Mono', '-V', 'monofontoptions=Scale=0.80',
        '-V', 'colorlinks=true', '-V', 'linkcolor=ReleaseTeal', '-V', 'urlcolor=ReleaseTeal',
        '-o', str(intermediate_pdf)
    ], capture_output=True, text=True, timeout=180)
    atomic_write(working / 'build.stdout', run.stdout)
    atomic_write(working / 'build.stderr', run.stderr)
    if run.returncode:
        raise SystemExit(run.stderr[-12000:])
    if args.draft:
        target = working / 'economics-problem-2-preview.pdf'
    else:
        target = ROOT / 'output/pdf/economics-problem-2-research-report.pdf'
        atomic_write(ROOT / 'docs/research_report.md', content)
        atomic_write(ROOT / 'docs/prospective_release.md', replacements['PRESS_DRAFT'] + '\n')
    sealed_copy(intermediate_pdf, target)
    receipt = {'status': 'DRAFT_RENDERED' if args.draft else 'FINAL_MANUSCRIPT_RENDERED_AND_SEALED',
               'pdf': str(target), 'bytes': target.stat().st_size, 'sha256': sha(target),
               'markdown_sha256': sha(markdown_path), 'source_sha256': sha(Path(__file__)),
               'proof_receipt_sha256': sha(args.certificate) if passed else None,
               'visual_review_required': True,
               'completed_at_utc': datetime.now(timezone.utc).isoformat()}
    atomic_write(working / 'build_receipt.json', json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
