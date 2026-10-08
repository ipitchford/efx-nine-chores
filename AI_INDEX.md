# Agent-readable research index

## Claim, version and limits

Version 1.1.0-candidate, Anonymous, unrefereed. [Manuscript](docs/research_report.md) states Theorem 1: every three-agent, nine-chore nonnegative additive real-cost instance has a complete EFX allocation, including deletion of zero-cost owned chores. [Assurance](ASSURANCE.md) separates written reductions, exact computational refutation and unresolved review dimensions. [Review response](REVIEW_RESPONSE.md) records every supplied request and disposition.

## Essential nine-chore replay files

These paths are all present in the release ZIP. Large proof streams are release assets rather than Git history; download and extract the complete ZIP before replay.

* [Exact SMT input](continuation/exact_search/zero_minimum9_reference_strict.smt2): SHA-256 `65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b`.
* [Capture metadata](continuation/exact_search/zero9_minimal_replay_capture1/capture/metadata.json), [atoms](continuation/exact_search/zero9_minimal_replay_capture1/capture/atoms.jsonl), [original clauses](continuation/exact_search/zero9_minimal_replay_capture1/capture/input_clauses.jsonl), [theory clauses](continuation/exact_search/zero9_minimal_replay_capture1/capture/theory_clauses.jsonl), [capture binding](continuation/exact_search/zero9_minimal_replay_capture1/capture/receipt.json).
* [Trimmed RUP trace](continuation/exact_search/zero9_rup_source_cache_run1/trimmed_trace.jsonl), [selected theory indices](continuation/exact_search/zero9_rup_source_cache_run1/selected_theory_indices.json), [exact multipliers](continuation/exact_search/zero9_selected_farkas_final1/arithmetic_certificates.jsonl).
* [Fresh replay driver](continuation/verification/run_lra_with_budget.py), [input checker](continuation/verification/check_lra_capture.py), [Boolean checker](continuation/verification/check_lra_rup.py), [arithmetic checker](continuation/verification/check_lra_farkas.py), [common parser](continuation/verification/lra_certificate_common.py).

Run the complete command in manuscript §7 or README. Use a new output directory. Expected counts: 4,550 original axioms; 370,780 theory axioms; 172,146 RUP derivations; 8,088,323 reason positions. Standard-library Python only. On Darwin the requested address-space cap is explicitly not enforced. This is producer-coordinated internal replay, not external reproduction.

## Semantics, controls and practical use

* [Formula audit](continuation/verification/audit_zero_minimum_formula.py) reconstructs the allocation encoding. Its historical Linux wrapper has a resource limit; see publication controls for the portable audit route.
* [Zero-minimum proof](continuation/exact_search/zero_minimum_reduction.md) and manuscript Lemma 3 explain the semantic bridge.
* [Adversarial controls](continuation/verification/test_lra_certificate_checkers.py) reject wrong signs, noncancelling/negative/float multipliers, assumption injection and invalid/circular reasons.
* [Allocation finder](src/solve_efx9.py), [example](examples/costs9.json): `python3 src/solve_efx9.py examples/costs9.json --out allocation.json`. Returned inequalities are independently readable.
* [Finite bound](continuation/verification/primitive_cramer_bound.md) is supplementary; it does not limit the main real domain.

## Historical evidence versus current checking

[Original nine receipt](continuation/verification/zero9_complete_lra_certificate.json), [eight receipt](continuation/verification/zero8_complete_lra_certificate.json), and [original index](continuation/verification/nine_release_index.json) are historical. Original indexes may bind pre-publication wrapper sources: they are not current manifests. [Binder](continuation/verification/bind_completed_lra_checks.py) composes existing receipts only. Its PASS string must never be reported as fresh proof execution. Current publication checks and manifests explicitly bind the revised package.

## Licensing and further work

See [component licence map](LICENSES.md). Remaining directions: independently implemented verification, formalising the written reduction, or extending the chore count after a fresh prior-art check. Neither archival availability nor media changes raise the mathematical assurance level.
