# Nine chores for three agents: complete EFX existence

## Current publication — 1.1.0-candidate

Anonymous · 8 October 2026 · DOI: **10.5281/zenodo.23234194**. Unrefereed candidate; no end-to-end formal verification or established external reproduction.

Read [AI_INDEX.md](AI_INDEX.md), [the revised manuscript](paper/manuscript.pdf), [assurance](ASSURANCE.md) and [review dispositions](REVIEW_RESPONSE.md). The authoritative accessible source is [docs/research_report.md](docs/research_report.md). The older report builders/templates below are historical and must not overwrite the revised paper.

For a Git checkout, first run `python3 publication/replay.py restore` to decompress the three large proof streams. The release ZIP already includes their uncompressed bytes. Then run `python3 publication/replay.py manifest`, `python3 publication/replay.py controls`, and `python3 publication/replay.py replay`. To test optimized Python, use `python3 -O publication/replay.py replay replay_results/zero9_optimized` with a different new output path. Source and mathematical inputs are hash-bound; a copied receipt is not a replay.

On Darwin, the portable driver explicitly records that the Linux-style address-space cap is not enforced. The old source index below binds the original pre-publication wrappers; the current MANIFEST.sha256 and publication records bind this revised package. The binder alone checks consistency of existing receipts, **not** proof execution. “Independent checking” below means separate from the producer, not independently authored second verification or an unaffiliated rerun.

## Original package description (historical pointers qualified above)

**Problem 2 has a positive answer.** Every nonnegative additive cost matrix for three agents and nine indivisible chores has a complete EFX allocation, with zero-cost owned chores included in the deletion quantifier and empty bundles allowed.

This package contains the written reductions, exact computational proof, independent checking programs, and a practical allocation finder. The final nine-chore certificate status is **PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE**. The complete release binding is `continuation/verification/nine_release_index.json`.

The current manuscript is `paper/manuscript.pdf`; its editable text is `docs/research_report.md`. Prospective editorial copy in `docs/prospective_release.md` is historical, not part of the revised scientific paper. No peer-review endorsement is asserted.

## Find an allocation for your costs

Python 3.10 or newer, standard library only:

```sh
python3 src/solve_efx9.py examples/costs9.json --out allocation.json
```

The input is a JSON object with a `costs` field containing three rows of nine nonnegative rational costs. Integer values, JSON decimal numbers, and fraction strings such as `"2/3"` are read exactly. The output numbers agents from 1 to 3 and chores from 1 to 9, specifies all three bundles, and gives all 18 original EFX deletion inequalities with exact slacks. The included example exercises deletion of an owned zero-cost chore.

The finder examines at most 19,683 assignments. It checks the returned allocation directly; it does not invoke a theorem prover or rely on the universal theorem to accept an allocation.

## Replay the complete nine-chore certificate

Run from the extracted package root, using a new output directory:

```sh
python3 continuation/verification/run_lra_with_budget.py \
  --stage all \
  --memory-mib 1600 \
  --input continuation/exact_search/zero_minimum9_reference_strict.smt2 \
  --expected-sha256 65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b \
  --capture continuation/exact_search/zero9_minimal_replay_capture1/capture \
  --trace continuation/exact_search/zero9_rup_source_cache_run1/trimmed_trace.jsonl \
  --certificates continuation/exact_search/zero9_selected_farkas_final1/arithmetic_certificates.jsonl \
  --selected-indices continuation/exact_search/zero9_rup_source_cache_run1/selected_theory_indices.json \
  --out-directory replay_results/zero9_fresh
```

The expected final status is `PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE`. This command checks the original SMT input and its exact affine atoms, the Boolean RUP refutation, and every arithmetic theory axiom used in the proof. It uses Python's standard library, including exact integers and `Fraction`. It does not invoke Z3, cvc5, SciPy, a compiler, or a proof producer. The recorded environment used Python 3.12.14; resource guards use the Unix `resource` module. The nine-chore replay command declares a 1,600 MiB address-space allowance and calls the independently reviewed checking functions unchanged.

The input SHA-256 is:

```text
65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b
```

The input has 21 real variables and 18,177 assertions: 27 domain assertions and one failure clause for each of the 18,150 allocations with three nonempty bundles. The written proof covers all 1,533 other allocations. Its input audit reconstructs 191,104 retained literal positions, including 34,776 owned-zero deletions.

The proof actually checked contains 4,550 selected original clauses, 370,780 exact arithmetic axioms, 172,146 derived RUP clauses, and 8,088,323 ordered propagation reasons. Complete hashes and per-stage receipts are in the release index and `continuation/verification/zero9_complete_lra_certificate.json`.

## The smaller-case baseline

The written nine-chore reduction uses ordinary EFX existence for eight chores when a chore is cheapest for two agents. The package includes an independently checked eight-chore residual and the corresponding full reduction. Replay it with:

```sh
python3 continuation/verification/check_lra_certificate.py \
  --input continuation/exact_search/zero_minimum8_reference_strict.smt2 \
  --expected-sha256 20d56e8ecd4bfad40ad5c7786c7865442c9961569dabb9e1a8dfe415b584c08f \
  --capture continuation/exact_search/zero8_clause_capture_composed1/capture \
  --trace continuation/exact_search/zero8_rup_trim1/trimmed_trace.jsonl \
  --certificates continuation/exact_search/zero8_selected_farkas_composed1/arithmetic_certificates.jsonl \
  --selected-indices continuation/exact_search/zero8_rup_trim1/selected_theory_indices.json \
  --out-directory replay_results/zero8_fresh
```

The accepted eight-chore proof contains 898 original clauses, 27,637 exact arithmetic axioms, 10,845 RUP derivations, and 405,499 propagation reasons. Its record is `zero8_complete_lra_certificate.json` and its full target correspondence is `zero8_full_target_completion.md`, both in `continuation/verification/`.

The smaller-case chain uses the previously checked seven-chore CPC proof and the cited six-chore theorem of Kobayashi, Mahara and Sakamoto. `docs/REPRODUCTION.md` gives the CPC/Ethos instructions and version pins. The theorem of Zhang for eight chores is also a cited baseline. No prescribed-agent EFX-plus-envy-freeness assumption is used.

## Proof and implementation boundaries

The checking calculus is exact affine arithmetic plus reverse unit propagation. An arithmetic axiom is accepted only after a nonnegative rational weighted sum yields a strict contradiction. A Boolean clause is accepted only after negating it and performing the recorded unit propagations against previously admitted clauses. Original axioms are reconstructed from the frozen input, and the final derived clause is empty. Solver callback assumptions are not admitted as new axioms.

The computational certificate is independently checked; it is not an end-to-end proof-assistant formalization. The written reductions, cited baseline, checker implementation and runtime remain explicit dependencies. The untrusted solver, C++ proof extraction and numerical multiplier search are unnecessary for replay correctness.

## File integrity and historical records

`artifact_manifest.json` and `MANIFEST.sha256` identify all included payload files. They exclude themselves to avoid self-reference. The ZIP build validates every manifest entry from the written archive, its CRCs, and a fresh-process read-back. `src/verify_release_archive.py` can repeat the archive integrity check.

Historical research notes, run outcomes, source code, and selected supporting artifacts are retained. `historical_file_omissions.json` identifies intermediate search inputs and data, candidate checkpoints, redundant capture copies, and historical solver callback streams omitted from this distribution, with their exact file identities. The accepted replay capture preserves the original input clauses, arithmetic atoms, and complete theory-clause source exactly. Its provenance records the complete original capture; the independent proof replay uses the final chronological RUP trace directly. Every accepted proof object listed in the release index is included. Some historical receipts and instructions refer to omitted intermediates; their original status statements describe those attempts. The current nine- and eight-chore replay commands above have all their proof inputs included. Accepted recovered eight-chore data have separate provenance and were completely checked; their rejected originals remain distinct and are also retained.

The secondary finite representative bound is 2,566 for positive integer entries in a row with one zero, or 5,132 for a positive representative with common minimum one. Its full determinant proof is `continuation/verification/primitive_cramer_bound.md`. The main refuted nine-chore formula is unbounded over real costs and does not use this numerical bound. Historical inputs keep the bounds with which they were actually run.

The old `src/build_report.py` and `src/build_bundle.py` are historical unresolved-result builders. The final manuscript and package use `src/build_release_report.py` and `src/build_release_bundle.py`, which refuse a final build without a complete checked nine-chore proof and matching file identities. Rebuilding the PDF additionally uses Pandoc, XeLaTeX and the fonts documented in `docs/REPRODUCTION.md`; none of those presentation dependencies is needed to check the theorem.

## Primary sources

- Zhang, *EFX Allocations for Three Agents and Seven or Eight Chores*, version 2: <https://arxiv.org/abs/2609.10585v2>.
- Kobayashi, Mahara and Sakamoto, *EFX Allocations for Indivisible Chores: Matching-Based Approach*: <https://doi.org/10.1016/j.tcs.2024.115010>; full preprint <https://arxiv.org/abs/2305.04168>.
- Z3 clause/proof logging documentation: <https://microsoft.github.io/z3guide/programming/Proof%20Logs/>.

The inspected prior version leaves nine chores open. The recorded literature search is bounded and is not a universal historical-priority determination.
