#!/usr/bin/env python3
"""Bind completed immutable nine-chore evidence and write a portable release index.

This does not repeat mathematical certificate checks. It refuses to write a
completion note, full-target receipt, replay command, or PASS index unless the
completed independent certificate and every previously checked byte agree.
All command-line relative paths are interpreted relative to the project root.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shlex

from lra_certificate_common import atomic_json, capture_files, json_file, require, sha256

ROOT = Path(__file__).resolve().parents[2]
VER = ROOT / 'continuation/verification'
EXPECTED = '65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b'
COMPLETE = 'PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE'


def inside(value):
    path = Path(value)
    path = (path if path.is_absolute() else ROOT / path).resolve()
    path.relative_to(ROOT)
    return path


def relative(path):
    return inside(path).relative_to(ROOT).as_posix()


def text_atomic(path, text):
    path = inside(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(text)
    temporary.replace(path)


def check_complete(receipt, expected):
    require(receipt['status'] == COMPLETE, 'complete independent certificate is absent')
    require(receipt['input_sha256'] == expected, 'wrong mathematical input')
    for key in ('original_smt_reconstructed', 'exact_affine_atoms_checked',
                'boolean_rup_refutation_checked', 'all_admitted_theory_axioms_checked'):
        require(receipt[key] is True, 'incomplete proof stage: ' + key)
    require(receipt['callback_assumptions_admitted'] is False, 'unsupported callback assumption')
    require(receipt['producer_solver_verdict_trusted'] is False, 'producer verdict trusted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', default='continuation/verification/zero9_complete_lra_certificate.json')
    parser.add_argument('--input', default='continuation/exact_search/zero_minimum9_reference_strict.smt2')
    parser.add_argument('--capture', required=True)
    parser.add_argument('--trace', required=True)
    parser.add_argument('--certificates', required=True)
    parser.add_argument('--selected-indices', required=True)
    parser.add_argument('--binding', default='continuation/verification/zero9_minimal_capture_input_binding.json')
    parser.add_argument('--rup-verification', required=True)
    parser.add_argument('--arithmetic-verification', required=True)
    parser.add_argument('--extra-artifact', action='append', default=[],
                        help='Additional sealed producer/provenance/arithmetic-part artifact to retain')
    parser.add_argument('--out', default='continuation/verification/nine_release_index.json')
    args = parser.parse_args()
    fields = ('certificate', 'input', 'capture', 'trace', 'certificates', 'selected_indices',
              'binding', 'rup_verification', 'arithmetic_verification', 'out')
    for key in fields:
        setattr(args, key, inside(getattr(args, key)))

    proof = json_file(args.certificate)
    check_complete(proof, EXPECTED)
    require(sha256(args.input) == EXPECTED, 'frozen nine-chore input changed')
    files = {}
    external_sources = {
        'kms': dict(title='EFX Allocations for Indivisible Chores: Matching-Based Approach',
                    url='https://arxiv.org/abs/2305.04168v1',
                    pdf_url='https://arxiv.org/pdf/2305.04168v1',
                    historical_files_sha256={}, required_for_certificate_replay=False,
                    redistributed_full_source=False),
        'zhang': dict(title='EFX Allocations for Three Agents and Seven or Eight Chores, version 2',
                      url='https://arxiv.org/abs/2609.10585v2',
                      pdf_url='https://arxiv.org/pdf/2609.10585v2',
                      historical_files_sha256={}, required_for_certificate_replay=False,
                      redistributed_full_source=False)}
    external_paths = {
        'sources/kms_2305_04168.pdf': 'kms', 'work/kms.txt': 'kms',
        'sources/zhang_2609_10585v2.pdf': 'zhang', 'work/zhang_v2.txt': 'zhang'}

    def add(path, expected=None):
        path = inside(path)
        require(path.is_file(), 'missing release file: ' + relative(path))
        digest = sha256(path)
        if expected is not None:
            require(digest == expected, 'changed checked file: ' + relative(path))
        key = relative(path)
        require(key not in files or files[key] == digest, 'inconsistent file binding')
        files[key] = digest
        return digest

    def carry_historical(path, digest):
        key = relative(path)
        if key in external_paths:
            # These are cited sources, not redistributed replay inputs. Preserve
            # the inspection identity from the immutable historical receipt.
            if inside(path).is_file():
                require(sha256(inside(path)) == digest, 'changed available cited-source bytes')
            external_sources[external_paths[key]]['historical_files_sha256'][key] = digest
        else:
            add(path, digest)

    add(args.input, EXPECTED)
    add(args.certificate)
    capture_receipt, capture_hashes = capture_files(args.capture)
    require(capture_hashes == proof['captured_files_sha256'], 'capture differs from completed proof')
    for name, digest in capture_hashes.items():
        add(args.capture / name, digest)
    capture_provenance = None
    capture_provenance_path = args.capture.parent / 'provenance_manifest.json'
    omitted_raw_callback_streams = capture_receipt.get('omitted_raw_callback_streams', {})
    require(set(omitted_raw_callback_streams) <= {'rup_clauses.jsonl', 'assumptions.jsonl'},
            'unsupported omitted source stream')
    if omitted_raw_callback_streams:
        provenance = json_file(capture_provenance_path)
        require(provenance['status'] == 'SEALED_MINIMAL_REPLAY_CAPTURE_PREPARATION_ONLY',
                'minimal capture provenance is absent')
        require(provenance['derived_capture_files_sha256'] == capture_hashes,
                'minimal capture differs from its preparation')
        require(provenance['source_indices_unchanged'] is True and
                provenance['original_files_modified'] is False,
                'minimal capture changed source indices or historical files')
        require(provenance['omitted_raw_callback_streams'] == omitted_raw_callback_streams,
                'inconsistent raw-stream omission inventory')
        for name, digest in provenance['copied_source_files_sha256'].items():
            require(capture_hashes[name] == digest, 'copied source stream differs')
        add(capture_provenance_path)
        add(args.capture.parent / provenance['preserved_source_receipt'],
            provenance['source_capture_files_sha256']['receipt.json'])
        add(args.capture.parent / provenance['preserved_source_binding'],
            provenance['source_input_binding_sha256'])
        add(VER / 'prepare_minimal_lra_capture.py', provenance['preparation_source_sha256'])
        capture_provenance = relative(capture_provenance_path)
    add(args.trace, proof['trace_sha256'])
    add(args.certificates, proof['certificate_sha256'])
    add(args.selected_indices, proof['selected_indices_sha256'])
    stage_paths = (args.binding, args.rup_verification, args.arithmetic_verification)
    require(sorted(add(path) for path in stage_paths) ==
            sorted(proof['stage_receipts_sha256'].values()), 'different completed stage receipts')
    for path in stage_paths:
        stage = json_file(path)
        if 'orchestration_driver' in stage:
            require(stage['orchestration_driver'] == 'run_lra_with_budget.py' and
                    stage['mathematical_checking_function_unchanged'] is True,
                    'unexpected independent-stage orchestration')
            add(VER / 'run_lra_with_budget.py', stage['orchestration_driver_sha256'])
    add(VER / 'run_lra_with_budget.py')
    orchestration_review = json_file(VER / 'nine_replay_orchestration_review.json')
    require(orchestration_review['status'] == 'PASS_ROOT_ORCHESTRATION_SOURCE_REVIEW',
            'resource-wrapper source review is absent')
    add(VER / 'run_lra_with_budget.py', orchestration_review['driver_sha256'])
    add(VER / 'nine_replay_orchestration_review.json')
    orchestration_controls = json_file(VER / 'budgeted_replay_controls.json')
    require(orchestration_controls['status'] ==
            'PASS_BUDGETED_REPLAY_ORCHESTRATION_AND_RELOCATION_CONTROLS',
            'resource-wrapper controls are absent')
    for name, digest in orchestration_controls['checker_sources_sha256'].items():
        add(VER / name, digest)
    add(VER / 'test_budgeted_lra_replay.py', orchestration_controls['control_source_sha256'])
    add(VER / 'budgeted_replay_controls.json')
    for name, digest in proof['checker_sources_sha256'].items():
        add(VER / name, digest)

    historical = json_file(VER / 'zero9_end_to_end_binding.json')
    require(historical['status'] == 'PASS_END_TO_END_INPUT_BINDING_AND_OMITTED_ALLOCATION_COVERAGE',
            'end-to-end mathematical binding is absent')
    require(historical['input_sha256'] == EXPECTED, 'end-to-end input differs')
    require((historical['free_real_variables'], historical['domain_assertions'],
             historical['surjective_allocation_clauses'], historical['omitted_empty_bundle_allocations_checked'],
             historical['complete_labelled_allocations_accounted_for']) == (21, 27, 18150, 1533, 19683),
            'unexpected target coverage')
    add(VER / 'zero9_end_to_end_binding.json')
    for path, digest in historical['bound_files'].items():
        carry_historical(path, digest)
    formula = json_file(VER / 'release_replay_final_zero_formula/zero_minimum9_formula_audit.json')
    require(formula['status'] == 'PASS_ALL_SERIALIZED_ZERO_MINIMUM_CLAUSES_RECONSTRUCTED_WITH_STDLIB',
            'full allocation-formula audit is absent')
    require((formula['input_sha256'], formula['allocation_clauses'], formula['domain_assertions'],
             formula['literal_positions_checked'], formula['pinned_zero_deletion_positions_reconstructed']) ==
            (EXPECTED, 18150, 27, 191104, 34776), 'formula audit does not match target')

    baseline = json_file(VER / 'zero8_full_target_binding.json')
    require(baseline['status'] == 'PASS_ORDINARY_EIGHT_CHORE_INPUT_AND_COMPLETED_CERTIFICATE_BINDING',
            'current ordinary eight-chore baseline binding is absent')
    require(baseline['independent_residual_unsat_certificate_complete'] is True, 'eight proof incomplete')
    add(VER / 'zero8_full_target_binding.json')
    for path, digest in baseline['files_sha256'].items():
        carry_historical(path, digest)
    inventory = json_file(VER / 'baseline_dependency_inventory.json')
    for path, digest in inventory['files_sha256'].items():
        carry_historical(path, digest)

    eight = json_file(VER / 'zero8_complete_lra_certificate.json')
    check_complete(eight, baseline['input_sha256'])
    eight_capture = ROOT / 'continuation/exact_search/zero8_clause_capture_composed1/capture'
    for name, digest in eight['captured_files_sha256'].items():
        add(eight_capture / name, digest)
    add('continuation/exact_search/zero8_rup_trim1/trimmed_trace.jsonl', eight['trace_sha256'])
    add('continuation/exact_search/zero8_rup_trim1/selected_theory_indices.json', eight['selected_indices_sha256'])
    add('continuation/exact_search/zero8_selected_farkas_composed1/arithmetic_certificates.jsonl',
        eight['certificate_sha256'])
    for name, digest in eight['checker_sources_sha256'].items():
        add(VER / name, digest)
    eight_stages = [VER / name for name in ('zero8_capture_composed1_input_binding.json',
                                          'zero8_rup_trim1_independent.json',
                                          'zero8_selected_farkas_independent.json')]
    require(sorted(add(path) for path in eight_stages) == sorted(eight['stage_receipts_sha256'].values()),
            'changed eight-chore stage receipts')
    for path in ('continuation/exact_search/zero8_clause_capture_composed1/provenance_manifest.json',
                 'continuation/exact_search/zero8_selected_farkas_composed1/preparation.json',
                 'continuation/verification/lra_checker_negative_controls.json',
                 'continuation/verification/lra_relocation_control.json',
                 'continuation/verification/test_lra_certificate_checkers.py',
                 'continuation/verification/test_lra_relocation.py',
                 'continuation/verification/build_nine_release_index.py'):
        add(path)
    finite = json_file(VER / 'primitive_cramer_bound_audit.json')
    require(finite['status'] == 'PASS_PRIMITIVE_CRAMER_BOUND_ARITHMETIC_AND_SMALL_DIMENSION_CONTROLS',
            'primitive-Cramer bound review is absent')
    add(VER / 'primitive_cramer_bound_audit.json')
    for name, digest in finite['files_sha256'].items():
        add(VER / name, digest)
    constructive = json_file(VER / 'constructive_solver_independent_review.json')
    require(constructive['status'] == 'PASS_CONSTRUCTIVE_SOLVER_INDEPENDENT_EXACT_CHECKS',
            'constructive solver review is absent')
    add('src/solve_efx9.py', constructive['source_sha256'])
    add(VER / 'constructive_solver_independent_review.json')
    add(VER / 'constructive_solver_review.md')
    for name, digest in constructive['files_sha256'].items():
        add(name, digest)
    for path in args.extra_artifact:
        require(relative(path) not in external_paths, 'cited full sources cannot be extra replay artifacts')
        add(path)

    # No generated completion artifact is written before all existing bindings pass.
    note = VER / 'zero9_full_target_completion.md'
    text_atomic(note, '''# Completion of the ordinary nine-chore EFX target

The independently checked exact certificate in `zero9_complete_lra_certificate.json`
refutes the frozen unbounded nine-chore formula with SHA-256
`65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b`.
Original SMT/affine reconstruction, the Boolean refutation, and complete exact
arithmetic coverage for every admitted theory axiom have all passed. Neither a
producer UNSAT label nor a callback assumption is a proof premise.

The complete written reduction is preserved in `zero9_end_to_end_audit.md`.
Its historical receipt was made before certificate completion and retains that
earlier status. This successor binds the same reviewed mathematics to the new
completed certificate; it does not edit or reinterpret the earlier receipt.

A nonnegative counterexample would admit a positive rowwise generic perturbation
because all chosen allocation failures are strict. If two agents share their
cheapest chore, the full shared-minimum insertion lemma and ordinary eight-chore
existence exclude a counterexample. Hence the unique minimum chores are distinct.
Lowering those minima to zero preserves every owned maximum-deletion residual
and only lowers comparison totals, so nonexistence persists. Simultaneous agent
and chore relabelling, the row-zero cross-minimum order, free-column sorting, and
independent positive reference scaling yield the exact 21-variable domain.

The existing full literal audit covers all 27 domain assertions and 18,150
surjective-allocation clauses, including owned zero-cost deletions. The separate
checked witness table covers every one of the 1,533 omitted empty-bundle
allocations. Thus all 19,683 complete labelled allocations are accounted for.
The independently checked refutation contradicts the existence of this canonical
counterexample. Every three-agent, nine-chore instance with arbitrary nonnegative
additive real costs therefore admits a complete literal EFX allocation.

The primary smaller-case premise may be Zhang's cited ordinary eight-chore
theorem. A separately retained alternative uses the cited six-chore theorem of
Kobayashi, Mahara, and Sakamoto, the input-bound seven-chore CPC/Ethos certificate,
and the independently checked ordinary eight-chore LRA residual, with the written
genericity and shared-minimum insertion arguments at each step. The current
eight-chore completion is `zero8_full_target_binding.json`; the earlier baseline
inventory remains unchanged as a historical checkpoint.

The retrieved source papers and their full extracted texts are not required
archive members. Their URLs and inspected-byte hashes are preserved separately
as external-source provenance; the cited theorems remain explicit mathematical
dependencies. None of these full sources is needed to execute certificate replay.

The handwritten reductions, the stated smaller-case theorem, the exact checking
calculus, and the checker implementation/runtime remain explicit trust boundaries.
This is an independently checked computer-assisted proof, not a proof-assistant
formalization. No P8/D8 strengthening, finite integer bound, regional exclusion
family, later minimum-preference symmetry, or producer correctness is required.
''')
    add(note)
    target_path = VER / 'zero9_full_target_binding.json'
    target = dict(status='PASS_ORDINARY_NINE_CHORE_INPUT_AND_COMPLETED_CERTIFICATE_BINDING',
                  input_sha256=EXPECTED, independent_residual_unsat_certificate_complete=True,
                  original_domain='arbitrary_nonnegative_additive_real_costs_for_three_agents_and_nine_chores',
                  zero_cost_owned_deletions_included=True, empty_bundles_allowed=True,
                  free_real_variables=21, domain_assertions=27, surjective_allocations_checked=18150,
                  omitted_allocations_independently_witnessed=1533, complete_allocations_accounted_for=19683,
                  strongest_literal_positions_checked=191104, pinned_zero_deletion_positions_checked=34776,
                  ordinary_eight_baseline='Zhang v2 Theorem 2, cited; or the retained checked seven/eight chain from the cited six theorem',
                  alternative_eight_baseline_complete=True, handwritten_reductions_remain_explicit_premises=True,
                  P8_or_D8_required=False, finite_integer_bound_required=False,
                  producer_solver_verdict_trusted=False, historical_receipts_modified=False,
                  completed_proofs_repeated_in_this_binding_step=False,
                  files_sha256=dict(sorted(files.items())), external_sources=external_sources,
                  completed_at_utc=datetime.now(timezone.utc).isoformat())
    atomic_json(target_path, target)
    add(target_path)

    command_path = ROOT / 'docs/zero9_replay_command.txt'
    command_args = [('stage', 'all'), ('memory-mib', '1600'),
                    ('input', args.input), ('expected-sha256', EXPECTED), ('capture', args.capture),
                    ('trace', args.trace), ('certificates', args.certificates),
                    ('selected-indices', args.selected_indices), ('out-directory', 'replay_results/zero9_fresh')]
    lines = ['python3 continuation/verification/run_lra_with_budget.py \\']
    for position, (key, value) in enumerate(command_args):
        shown = relative(value) if isinstance(value, Path) else value
        suffix = ' \\' if position < len(command_args) - 1 else ''
        lines.append('  --' + key + ' ' + shlex.quote(shown) + suffix)
    text_atomic(command_path, '\n'.join(lines) + '\n')
    add(command_path)

    index = dict(status='PASS_COMPLETE_NINE_CHORE_RELEASE_BINDING', input_sha256=EXPECTED,
                 accepted_capture=relative(args.capture),
                 capture_provenance=capture_provenance,
                 omitted_raw_callback_streams=omitted_raw_callback_streams,
                 replay_driver='continuation/verification/run_lra_with_budget.py',
                 replay_memory_mib=1600,
                 complete_certificate=relative(args.certificate), full_target_binding=relative(target_path),
                 replay_command=relative(command_path), completed_proofs_repeated=False,
                 relative_paths_are_from_project_root=True,
                 files_sha256=dict(sorted(files.items())), external_sources=external_sources,
                 file_count=len(files),
                 total_bound_bytes=sum((ROOT / path).stat().st_size for path in files),
                 completed_at_utc=datetime.now(timezone.utc).isoformat())
    atomic_json(args.out, index)
    print(index['status'], index['file_count'], index['total_bound_bytes'])


if __name__ == '__main__':
    main()
