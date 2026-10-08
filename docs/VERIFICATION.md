# Verification and reproducibility record

**The full nine-chore target now has a complete independently checked computer-assisted proof.** Updated 8 October 2026. The current certificate is `continuation/verification/zero9_complete_lra_certificate.json`, with the separate mathematical correspondence in `zero9_full_target_binding.json`. Section 15 records the completed nine-chore checks. Earlier sections preserve successive historical results, including the input-bound ordinary-seven and prescribed-agent-six certificates; their old scopes do not replace the current completion.

**Proof Digest track: I (informal mathematical reductions with exact computational certificates).** The inspected corpus consists of the frozen target, cited sections of the primary papers, the current predecessor solver, this project's listed encoders and reductions, exact run receipts, proof exporters/adapters, checker boundary controls, and the relevant pinned Ethos parsing/reference call sites. This is not a complete source audit of either solver or checker. The full development has not been formalized in Lean, Rocq or another proof assistant; theorem elaboration, compilation, transitive axiom inventories and admission scans for such a development are **not applicable**. A subset of nine-chore rank cases was tested; no complete rank-case refutation is claimed. Input/proof hashes are listed below and in the machine receipts.

## 1. Exact mathematical scope

The requested statement is that every nonnegative additive cost matrix \(C\in\mathbb R_{\ge0}^{3\times9}\) admits a complete labelled allocation \(A\) with

\[
\sum_{h\in A_i\setminus\{g\}}C_{ih}
\le \sum_{h\in A_j}C_{ih}
\qquad(i\ne j,\;g\in A_i).
\]

An owned zero-cost chore remains in the deletion quantifier. All costs of both bundles in one comparison use the evaluating agent's row. The target permits empty bundles and does not permit disposal, fractional assignment or approximation. It is frozen in `target.yaml`.

The ancillary property \(P_m\) additionally requires a **prescribed** agent, fixed as agent 0 by symmetry, to be ordinarily envy-free: \(c_0(A_0)\le c_0(A_1),c_0(A_2)\). Its designated-agent EFX inequalities are then automatic. Consequently each complete allocation fails this stronger property exactly when one of the two ordinary envy inequalities for agent 0 or one of the EFX inequalities for agents 1 and 2 fails strictly.

## 2. What the finite formulas cover

| Input | Variables / assertions | Exact scope of the formula |
|---|---:|---|
| `results/root7_pruned.smt2` | 21 / 1,849 | Ordinary EFX, strictly positive costs, distinct pinned cheapest chores for all three agents, residual column/agent symmetries; 1,806 nonempty allocation clauses. No row-sum normalization. |
| `results/root8_pruned.smt2` | 24 / 5,846 | Corresponding ordinary eight-chore disjoint-minimum residual; 5,796 nonempty allocation clauses. |
| `work/structural_designated_m6.standard.smt2` | 18 / 755 | Prescribed-agent property at six chores; nonnegative entries, unit row totals, lexicographically sorted columns, all \(3^6=729\) allocation clauses, including empty bundles. |
| `work/structural_designated_reduced_m7_seed0.standard.smt2` | 21 / 1,847 | Prescribed-agent property at seven chores on the strict positive residual where the two nondesignated agents have distinct pinned cheapest chores; 1,806 nonempty allocation clauses. |

Unsatisfiability of a residual formula is only the finite part of an existence proof. The following mathematical reductions supply its coverage.

* Positive independent scaling of each nonzero row preserves comparisons. Zero rows have direct allocations, detailed in `work/structural_lemmas.md`.
* Strict generic instances suffice: a hypothetical counterexample has a strict failed comparison for each of finitely many allocations, and a sufficiently small perturbation preserves all selected failures. Yin–Mehta give an explicit prior perturbation in Lemma 2.1 of [arXiv:2211.15836](https://arxiv.org/pdf/2211.15836).
* Simultaneous chore permutations and appropriate agent permutations preserve the allocation problem. They justify pinning distinct minima and sorting the remaining columns.
* For strictly positive costs and more than three chores, an EFX allocation cannot have an empty bundle: some other bundle has at least two chores, whose positive residual would exceed the empty bundle's zero cost. Thus the residual formulas may omit nonsurjective allocations. This omission is not used directly on arbitrary zero-cost instances.
* Ordinary shared-minimum cases reduce to the preceding cardinality by the insertion lemma of Kobayashi–Mahara–Sakamoto, Lemma 4.2 of [arXiv:2305.04168](https://arxiv.org/pdf/2305.04168). At nine chores Zhang v2 §6 already states this reduction. The ordinary seven-chore residual certificate, together with the known six-chore theorem, covers ordinary seven chores; the analogous eight-chore argument uses the seven-chore result.
* The prescribed-agent insertion variant is proved in `work/structural_lemmas.md`, Lemma 5. It preserves agent 0's ordinary envy-freeness when the inserted chore is cheapest for both other agents. This connects the full six-chore property to the residual seven-chore formula.

The handwritten reductions and the semantic interpretation of generated SMT-LIB are separate proof obligations from checking its unsatisfiability. None has been translated into a proof assistant in this package.

## 3. Authoritative successful external checks

Only the corrected **stdin-mode** Ethos receipts listed here establish refutations bound to their exact original inputs.

| Result | cvc5 result | External result | Authoritative receipts |
|---|---|---|---|
| Ordinary seven-chore residual | UNSAT, 8.710778 seconds; 94,014 CPC inference steps | Ethos `correct`, exit 0, 26.973256 seconds | `results/root7_cvc5.json`; `results/root7_ethos.json` |
| Full prescribed-agent six-chore formula | UNSAT, 94.634382 seconds; 857,855 CPC inference steps | Ethos `correct`, exit 0, 90.488245 seconds | `results/designated6_cvc5.json`; `results/designated6_ethos.json` |

Both CPC exports have zero reported trust/hole steps and no warning lines. The external checker used only the core CPC signature, enforced a final proof of false at global assumption scope, and bound all global proof assumptions to the reference input. Neither run emitted stderr. Runtime figures describe these executions, not reproducibility guarantees on different hardware or under different load.

| Object | SHA-256 |
|---|---|
| Ordinary seven-chore input | `7855d4233735958aff2ffb1bb52a1aae9ff782ac16abf0550ba780e6ff211bea` |
| `certificates/root7_cvc5.cpc` (6,515,732 bytes) | `62d8754d1e0f592a8c28b39d64de02d9579287d05b2346ff6e6349a6cb02961c` |
| Actual adapted root7 proof stream | `93d068f78b8e1c93363d101e8c34c6299088d007d196b12f95358495a575c910` |
| Prescribed-agent six-chore standardized input | `bf24e50713175ad01e2d15d51fe78121e5df0412cb7c5c6f445e56337350c4b2` |
| `certificates/designated6_cvc5.cpc` (70,716,103 bytes) | `71bfd7610a258a5dbdad262e32f121f15f12e2e865b90afc5e31c2a42c013e85` |
| Actual adapted designated6 proof stream | `23e9742e8802efe090fb78c1cdf39434f9a840cbe79b49f98a57d1fe15267cbd` |

The prescribed-agent standardized inputs remove only unary additions, using the identity \((+\;x)=x\), and add an explicit QF_LRA declaration. Originals were retained. `work/structural_standardise_receipt.json` records input/output hashes and identical simplified ASTs for all corresponding assertions. The certificate directly covers the standardized input; that syntax-conversion check is separately recorded.

## 4. Checker boundary, correction and controls

The solver is cvc5 1.4.1. Ethos was built from commit `08e4aa40c4f8a6e00833f10e8d8985777e424027`, as selected by cvc5's pinned helper. The CPC signatures come from the cvc5-1.4.1 checkout at commit `2b2e84419f70817ec919a784a48806e79f677240`. The checker binary SHA-256 is `11c3f0685eeac19c655f8305af4cb75fd775639ad9c27aa2e2ac9ca7df66de8b`. Build/dependency details are in `results/checker_build.json`; every signature-file hash is in each successful receipt.

**A material invocation error was found and corrected during verification.** In the pinned Ethos implementation, opening the proof as a positional file resets its reference-state flag. A `correct` verdict in that mode checked the derivation but did not establish the claimed link to the original assertions. Initial receipts were marked `derivation_checked_reference_binding_invalid` and archived with `_positional_deprecated` suffixes. They do not support a bound-proof claim.

`src/check_ethos.py` now streams the proof through stdin after loading the reference. Because Ethos creates fresh constants upon redeclaration, the adapter removes only initial, attribute-free Real declarations that exactly match constants already declared by the reference. It retains every proof definition, assumption and inference step, rejects unsupported command classes and additional includes, and records the streamed bytes' hash. The original CPC file and the checker binary remain unchanged.

`src/check_ethos_controls.py` exercises the boundary explicitly. `results/checker_controls.json` records all four passing controls: a valid refutation is accepted; removing a reference assertion causes rejection at the missing assumption; a non-refuting but valid prefix is accepted without the final-false requirement; the same prefix is rejected with that requirement. These controls demonstrate enforcement of those conditions; they are not a proof of checker soundness.

**Declared trust boundary:** Ethos checks applications of the supplied CPC rules. The soundness of that calculus, correctness of the checker and arithmetic/runtime implementation, parsing, and the mathematical correspondence between the frozen allocation problem and the SMT input remain premises. This is external SMT proof checking, not an end-to-end Lean formalization of the fair-division theorem. cvc5's internal proof check is an additional check, not the independent checker itself. The retained Alethe export for ordinary seven chores has not been externally checked.

## 5. Unsuccessful and unresolved runs

| Run | Recorded result | Meaning |
|---|---|---|
| Ordinary eight-chore residual, Z3 | UNSAT in 68.533468 seconds; native proof retained | Exact solver result; not an externally checked exported proof. `results/root8_pruned.json`. |
| Ordinary eight-chore cvc5 full input | Killed, exit 137, no verdict | No cvc5 UNSAT conclusion or certificate. `results/root8_cvc5.json`. A memory-guard process-exit record is not a solver verdict. |
| Eight-chore core selection from native proof | 934 of 5,846 original assertions copied verbatim | A smaller candidate input, not a proof result. `results/root8_core_extract.json`; independent replay was not performed. |
| Prescribed-agent seven-chore residual, Z3 | UNSAT in 99.720441 seconds | Exact solver result. `work/structural_designated_reduced_m7_seed0.json`. An external finite refutation was not obtained. |
| First full prescribed-agent seven-chore cvc5 attempt | `std::bad_alloc`, exit 134 under 1,800 MiB address-space cap, no verdict | No certificate. `results/designated7_cvc5.json`. |
| Prescribed-agent seven-chore core selection | First default-arithmetic attempt timed out; retry with the original arithmetic engine returned Z3 UNSAT in 125.169974 seconds and selected 853 of 1,847 assertions | `results/designated7_core_select.json`; core input hash `5694d8a839b41c29e18d72beec7dc5de83893d5ea8065bfb025755ac204fa15d`. This is the core selector's exact solver result, not an external proof check. |
| Prescribed-agent seven-chore core, cvc5 proof attempt | Exit 139 with no diagnostic, solver verdict or proof file; initial address-space cap 2,300 MiB and solver timeout 600 seconds | `results/designated7_core_cvc5.json`. No external certificate was obtained. A requested increase to 4,500 MiB could not be applied because the process was no longer found; `results/designated7_core_limit_change.json` records that no limit changed. The exit's cause was not established. No further proof attempt was started. |
| Nine-chore strict residual, baseline and unit-margin variants | Killed, exit 137, no verdict | `results/root9_pruned_termination.json`; `results/root9_unit_cuts_termination.json`. |
| Nine-chore residual with proved cuts | UNKNOWN, timeout after 1,807.949691 seconds | `results/root9_cuts.json`; does not decide the target. |
| Nine-chore rank case `(6,7)` | UNKNOWN, timeout after 183.254653 seconds | `results/rank9_6_7.json`; a single undecided branch supplies no case cover. |
| Stronger eight-chore target with all three minima distinct (`D8`) | UNKNOWN, timeout after 903.677793 seconds | `results/D8_root.json`; no conclusion about this restricted stronger target. |
| Nine-chore second-minimum graph/rank subcases | All 14 cases returned UNKNOWN with timeout, each with a 45-second solver budget | `results/second_min_cases/summary.json`: cycle and tail graphs, seven row-0 rank cones each. No case was decided, and these restricted tests do not establish a full case cover. |
| Three simultaneous deleted-minimum prescribed-agent obstructions | UNKNOWN, timeout after 1,200.416110 seconds on 17,388 clauses | `work/compute_deleted_min9_full/stop_receipt.json`; no logical verdict. |
| Distinct-minimum prescribed-agent eight-chore CEGIS search | Stopped without conclusion at its agreed total search budget; 1,223.37 seconds wall time, 137 completed partial SAT models | `work/compute_designated8_allmin/stop_receipt.json`; every tested model still had at least one designated-agent witness. Partial SAT models are not counterexamples. |

For selected assertion cores, the selector copies an exact subset of original assertions. A later independently checked refutation of that subset would refute the full input. The core selector itself is never treated as a proof checker. Failed runs must not be interpreted as evidence for the opposite solver answer. All computational workers have ended; this package leaves no background proof search running.

The final computation inventory is `work/compute_run_summary.json`. Seven earlier incremental searches also have explicit `INTERRUPTED_WITHOUT_CONCLUSION` stop receipts: `compute_cegis_a`, `compute_cegis_unit`, `compute_rank_0_1`, `compute_rank_0_1_noproof`, `compute_designated8`, `compute_designated8_neighbours`, and `compute_deleted_min9`, each under `work/<name>/stop_receipt.json`. These jobs were stopped or reallocated after retaining their exact clauses and models. Their intermediate SAT verdicts concern partial failure formulas, and the models still had fair allocations; they supply neither a full nine-chore counterexample nor a proof of existence. The separately verified P8 obstruction comes from the structural search and exhaustive enumeration, not from reinterpreting any unfinished CEGIS run.

## 6. Exact finite semantic and obstruction checks

For the frozen P6/P7 inputs, `work/structural_prescribed_formula_audit.py` independently decodes every inequality into its exact coefficient vector, compares every allocation clause with vectors built directly from the specification, and checks the canonical-domain assertions separately. The checker imports neither generator. Its inspected receipt, `work/structural_prescribed_formula_audit.json`, records exact matches for all 26/41 domain assertions and all 729/1,806 allocation clauses. This is a symbolic coefficient check of the frozen finite formulas, supplemented by 17,745 point evaluations; it is stronger than testing the formulas only at sampled cost matrices. It still depends on the audit code and parser and does not formalize the surrounding mathematical reductions.

The separately written literal audit `src/audit_designated_semantics.py` makes all EFX deletion comparisons for every agent and then the ordinary agent-0 comparisons, without importing either generator. It evaluates the stored clauses on four exact matrices per cardinality, including zero entries and rational costs. `results/designated_semantic_audit.json` records 10,140 matrix-allocation comparisons with no disagreement, reproducing uniform designated-agent counts of 90 at six chores and 420 at seven chores. Point tests outside a canonical domain check clause meaning, not the domain constraints.

`results/encoding_audit9.json` records 290,400 matrix-allocation comparisons: 16 exact matrices and all 18,150 nonempty labelled allocations per matrix, with zero disagreements. It also detects the deliberate zero-trim mutation and obtains the expected 1,680 allocations for uniform positive nine-chore costs. This is a finite semantic audit, not a formal proof that the generator is correct for every real input.

`work/structural_rank_audit.json` records 236,196 additional predicate comparisons on four representative rank cases and identifies all 28 canonical rank cases. The written ordering/dominance argument is in `work/structural_rank_audit.md`. The finite comparison checks do not establish UNSAT of those 28 cases.

The positive integer matrix in `results/p8_obstruction_verified.json` was exhaustively checked over all 6,561 eight-chore allocations. It has 36 ordinary EFX allocations, and the numbers also making agents 0, 1 and 2 ordinarily envy-free are `(0,31,31)`. It therefore refutes \(P_8\), not ordinary EFX. A later smaller matrix is retained separately; its exact verifier record must be used if that alternative is selected for publication.

## 7. Replaying the verified objects

From the project directory, with the pinned checker and signatures installed in the recorded locations, run:

```sh
python src/check_ethos_controls.py
python src/check_ethos.py results/root7_pruned.smt2 certificates/root7_cvc5.cpc --report replay_root7.json
python src/check_ethos.py work/structural_designated_m6.standard.smt2 certificates/designated6_cvc5.cpc --report replay_designated6.json
```

Both replay receipts must say `result: verified`, `reference_binding: true`, and `requires_final_false_at_global_scope: true`, and identify the stdin adaptation. The wrapper accepts only exit zero with final verdict `correct`, never `incomplete`. Checker/signature locations can be supplied using `--checker` and `--signatures` without altering the proof objects.

The corrected verification executions used working directory `/workspace/scratch/5abf44ff3fd9` and the following commands. Exact external executable arguments, versions, return codes and output are also stored in the corresponding receipts.

| Check | Exact wrapper command from that directory | Result / evidence |
|---|---|---|
| Ordinary seven-chore proof | `python economics_problem2/src/check_ethos.py economics_problem2/results/root7_pruned.smt2 economics_problem2/certificates/root7_cvc5.cpc --report economics_problem2/results/root7_ethos.json` | **Passed**, 26.973256 seconds, exit 0 and `correct`; corrected receipt. |
| Prescribed-agent six-chore proof | `python economics_problem2/src/check_ethos.py economics_problem2/work/structural_designated_m6.standard.smt2 economics_problem2/certificates/designated6_cvc5.cpc --report economics_problem2/results/designated6_ethos.json` | **Passed**, 90.488245 seconds, exit 0 and `correct`; corrected receipt. |
| Checker boundary controls | `python economics_problem2/src/check_ethos_controls.py` | **Passed**, all four expected outcomes in `results/checker_controls.json`. |
| Proof-assistant compilation/axiom audit | No such development supplied | **Not applicable** to track I. |

Re-solving is optional for replaying an existing proof. To regenerate a CPC object, use `src/check_cvc5.py` on the exact SMT input; it reads the static SMT-LIB independently of the generator and records its input hash. Then run the external checker separately. Detailed format/version choices and build notes are in `proof_export_notes.md`.

## 8. Literature and release scope

Zhang's inspected version 2, submitted 6 October 2026, proves ordinary EFX at seven/eight chores and explicitly leaves nine chores unresolved. The inspected artifact commit is `b5121a08f21f1d1a75353d9cad4932a92540de64` (5 October 2026). The primary-source novelty searches are frozen in `novelty_report.md` and `novelty_designated_addendum.md`. They cover indexed arXiv and selected journal/conference papers plus the public artifact history; they are not exhaustive historical-priority determinations.

No earlier prescribed-agent seven/eight boundary was found in the recorded searches. The closest KMS observation guarantees a minimum matched edge for **some** agent, which is not the prescribed-agent statement. A sharp seven/eight conclusion currently depends on trusting the exact P7 Z3 verdict; the independent certificate route did not close. The externally checked six-chore result and exact eight-chore obstruction therefore have stronger recorded verification than the seven-chore positive conclusion. Neither ancillary result settles the original nine-chore request.

## 9. Changes, remaining obligations and sanity check

Original SMT inputs and exported CPC objects were retained. The six-/seven-chore portable syntax conversion is recorded separately, and the checker adapter creates only a temporary stream with matching duplicate declarations removed. Deprecated positional-mode receipts remain marked unbound. The changes to input handling and proof streaming preserve every actual proof assumption and inference step; no theorem statement was weakened to obtain a successful result.

The central mathematical gap is the unrestricted nine-chore residual. A separate certificate gap remains for the prescribed-agent seven-chore residual. Resource-exhausted and timed-out runs are environment/search failures, not counterexamples. A broader historical-priority audit and end-to-end proof-assistant formalization are additional work, not accomplishments of this record.

The strongest current machine conclusion is the pair of input-bound finite refutations listed in §3, together with the exact eight-chore obstruction enumeration. As a concrete sanity check, uniform positive costs on nine chores produce exactly \(9!/(3!)^3=1680\) EFX allocations, reproduced by the finite audit. The zero-trim mutation control also fails as intended, confirming that the tested predicate includes zero-cost owned chores.

## 10. Continuation: finite bounds, exact local guarantees, and complete input audits

The preceding sections retain the original verification history. The completed continuation additionally supplies **1,956 exact prefix-extension guarantees**, a fully audited positive-minimum two-row input with **6,309 assertions**, and an independently reconstructed full zero-minimum nine-chore input. The original nine-chore existence problem remains unresolved. Completed local guarantees and faithful input formulas do not establish global coverage.

The strongest reviewed finite reduction is now:

> If a three-agent, nine-chore EFX counterexample exists, one exists with exactly one zero in each row and all other entries positive integers at most **3,831**. A positive integer counterexample then exists with common minimum **one** and every nonminimum entry even and at most **7,662**.

Lowering only a globally cheapest entry to zero leaves every maximum owned-deletion residual unchanged and weakly lowers every target-bundle sum. It therefore preserves the absence of EFX allocations. Each row then has eight positive variables. Independent row-local vertex systems, Cramer's rule, and Hadamard's inequality bound their integer representatives by \(\lfloor\sqrt{7\cdot8^7}\rfloor=3831\). Raising each zero to one half preserves a selected failure margin of at least one half; doubling gives the stated positive representative. The argument includes deletion of owned zero-cost chores. Canonical distinct zero positions additionally use the already documented shared-minimum insertion reduction and eight-chore theorem. The proof and independent review are in [zero_minimum_reduction.md](../continuation/exact_search/zero_minimum_reduction.md) and [zero_minimum_independent_review.md](../continuation/verification/zero_minimum_independent_review.md). No exhaustive search of this finite domain has been completed.

| Completed evidence | Exact scope |
|---|---|
| Final prefix snapshot | 1,956 certificates: 300 for all nonnegative ninth columns and 1,656 for columns above recorded linear lower bounds; 52 canonical bounded-domain assertions and 1,956 matching exclusion clauses |
| Final positive-minimum two-row snapshot | 18 domain assertions plus 6,291 exclusions: 3,238 singleton guarantees, 1,048 static paired guarantees, and 2,005 distinct nonordinal cores; all source, reduced-subset, compression, and ordered-input bindings checked |
| Full zero-minimum nine-chore formula | 21 free real variables, 27 domain assertions, 18,150 surjective allocation clauses, and all 191,104 retained literal positions reconstructed exactly; owned-zero deletions included |
| Portable release replay | An explicit index of valid certificates and 8,245 bound files; standard-library exact arithmetic, without solver imports or network access |

The portable certificate replay completed at 21:55:09 UTC on 7 October 2026; its missing zero-formula phase completed separately at 22:05:17 UTC against the identical index. The authoritative phase receipts are [release_replay_final_certificates/release_replay.json](../continuation/verification/release_replay_final_certificates/release_replay.json) and [release_replay_final_zero_formula/release_replay.json](../continuation/verification/release_replay_final_zero_formula/release_replay.json). They cover the complete command `python continuation/verification/release_replay.py --phase all`. The historical invalid floating-point fixture is excluded from the valid-certificate index. The repaired exact row-core checker remains unchanged.

See [consolidated_review.md](../continuation/verification/consolidated_review.md) for the full claim ledger, final input hashes, count boundaries, and trust assumptions. Actual solver outcomes are recorded separately in [CONTINUATION_STATUS.json](CONTINUATION_STATUS.json). A timeout, a lost worker, a merely prepared proof configuration, or a SAT model of a region-complement relaxation supplies no main-target verdict. The zeros/reference-normalized full allocation formula is a complete canonical counterexample formula; the prefix and two-row region formulas are necessary-condition relaxations.

The later zero-minimum outer input has also passed a complete 6,305-assertion audit and an exact SAT-model check. Lifting its two rows to positive integer costs yields an exact model of all 6,309 assertions in the original final positive-minimum outer input. [positive_outer_noncoverage_witness.json](../continuation/verification/positive_outer_noncoverage_witness.json) therefore proves that this particular **6,291-region family is incomplete**. It supplies no first row and is not a three-agent counterexample. A global refutation of that exact finite complement is impossible; more valid sufficient regions would be needed.

The positive lifted allocation formulas were independently reconstructed as well: all 5,843 eight-chore assertions and all 18,204 nine-chore assertions, with their exact bounds and unit failure margins. The [completion binding receipt](../continuation/verification/release_completion_audit.json) carries forward these successful new audits, the two portable replay phases, the reviewed zero-minimum and lifting proofs, and the prepared CPC configuration through 8,333 exact file bindings. It does not rerun or upgrade any mathematical claim merely because its file hash matches.

## 11. Full-target UNSAT checkpoint and exact proof route

The full zero-minimum nine-chore formula returned UNSAT in 591.67023688 seconds in `continuation/exact_search/zero_minimum9_reference_noproof_run1.json`. Proof output was disabled. The original full formula, rather than a region relaxation, was checked. `continuation/verification/zero9_end_to_end_audit.md` gives the full logical reduction and insertion lemma; `zero9_end_to_end_binding.json` binds the actual terminal run and accounts for every omitted empty-bundle allocation. This is an affirmative solver-supported result with an independent certificate still pending.

The new independent certificate entry point is `continuation/verification/check_lra_certificate.py`. It first reconstructs each original SMT assertion over explicitly interpreted primitive integer affine atoms, then verifies every hinted Boolean unit-propagation step, and finally verifies nonnegative exact rational Farkas weights for precisely the theory clauses admitted in that refutation. For a weighted sum of negated theory literals, all variable coefficients must cancel and the constant must be positive, or zero with positive weight on a strict premise. Callback assumptions are never admitted. A completed combined receipt alone may claim `PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE`; isolated input binding, sample arithmetic checks, and producer UNSAT verdicts cannot.

The new checkers passed 41 targeted positive/negative controls. A 100-clause spread from the real eight-chore capture passed independent exact arithmetic checking. These calibration receipts remain separate from a completed main proof.

## 12. Strongest finite bound: 2,566 / 5,132

`continuation/verification/primitive_cramer_bound.md` gives the independently reviewed common-divisor refinement. Its bound is `floor(sqrt((m-1)*(m-2)^(m-2)))`, equal to 2,566 at nine chores and 571 at eight. The positive common-minimum lifting bounds are 5,132 and 1,142. `primitive_cramer_bound_audit.json` records exact arithmetic and focused parity/divisibility controls. Every earlier 3,831/7,662 formula and receipt remains unchanged and valid; the full solved zero-minimum strict-real input has no finite upper bound.

## 13. Completed independent eight-chore proof

`continuation/verification/zero8_complete_lra_certificate.json` now records **PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE**. The original affine/CNF binding, all 10,845 Boolean RUP derivations, all 405,499 propagation reasons, and exact Farkas identities for all 27,637 selected theory axioms passed independent standard-library checking. The final proof uses 898 original clauses. Callback assumptions and producer solver verdicts are not checking premises.

The full mathematical correspondence is separately bound in `zero8_full_target_binding.json`: all 5,796 surjective allocations and all 765 omitted empty-bundle allocations are accounted for. `zero8_full_target_completion.md` explains the unchanged seven-chore checked residual and cited KMS six-chore baseline. This provides a locally checked eight-chore baseline for the nine-chore reduction; it does not supply the still-pending nine-chore refutation.

The original truncated v3 capture and truncated arithmetic output were rejected and preserved. Separately composed artifacts restore the static input/atom streams and the missing 237 arithmetic records, with explicit provenance and complete independent checks. The completed arithmetic file matches the original producer's intended full hash. The relocation control passed on a tiny full proof; the exact portable replay command is in Section 12 of `REPRODUCTION.md`.

## 14. Nine-chore source binding and minimal replay package

The full durable nine-chore capture independently passed original SMT/affine binding in `continuation/verification/zero9_capture_snapshot_input_binding.json`. This covers 18,177 original assertions, 18,066 interpreted atoms, every original clause record, and the syntax and terminal hashes of all 3,234,215 theory records and 2,480,762 raw RUP records. It establishes source identity and interpretation; it does not establish the theory axioms or the final contradiction.

The smaller final replay source is `continuation/exact_search/zero9_minimal_replay_capture1/capture`. The original atoms, CNF, all theory records, metadata, and every source index are unchanged. Only raw callback RUP/assumption logs are omitted; they are not premises of the final hinted proof. A new run of the unchanged input/atom checker passed on this derived package in `zero9_minimal_capture_input_binding.json`, and its preparation manifest preserves the full snapshot's identity and the omitted logs' hashes. The final trimmed trace and exact arithmetic certificates remain required separate proof objects. No nine-chore independent refutation is claimed by source binding alone.

## 15. Complete independent nine-chore certificate

`continuation/verification/zero9_complete_lra_certificate.json` records **PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE** for input SHA-256 `65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b`. All three independently completed stages share the same interpreted atoms, original source clauses, selected theory set, and actual proof bytes. Their successful receipts are composed by immutable hashes; the composition step does not repeat mathematical checks.

| Stage | Complete accepted scope | Receipt |
|---|---|---|
| Input and atom binding | All 18,177 original assertions and 18,066 primitive affine atoms, with the complete original CNF and theory source indexing | `zero9_minimal_capture_input_binding.json` |
| Boolean RUP proof | 4,550 original axioms, 370,780 theory axioms, 172,146 derived clauses, and 8,088,323 ordered reasons; exact dependency closure and final derived empty clause | `zero9_rup_source_cache_independent.json` |
| Exact arithmetic | All 370,780 selected theory clauses and 1,317,350 rational multiplier positions; 360,481 strict zero-constant and 10,299 positive-constant contradictions | `zero9_selected_farkas_independent.json` |
| Full problem correspondence | Every original nonnegative counterexample would give a model of the refuted input; all 18,150 explicit surjective and 1,533 omitted allocations accounted for | `zero9_full_target_binding.json` |

The arithmetic checker interprets a positive literal for an atom \(q\le0\) as having the negated strict premise \(-q<0\), and a negative literal as having the negated weak premise \(q\le0\). Every nonnegative weighted sum has exactly zero variable coefficients and a contradictory constant/sign condition. The Boolean checker uses only original clauses and these exactly covered theory axioms. Each RUP reason is an earlier checked clause, each nonfinal reason is unit under the current assignment, and the last reason is a conflict. No callback assumption, floating-point computation, or producer UNSAT label is admitted as a premise.

The RUP CLI's initial 700 MiB cap was insufficient and produced a preserved `MemoryError`, not a mathematical verdict. The accepted `run_lra_with_budget.py` driver calls the unchanged checking functions under a 1,600 MiB cap. RUP replay took 30.267 seconds with 902,792 KiB maximum resident memory; arithmetic replay took 82.486 seconds with 195,164 KiB. The wrapper's source review and four small relocation/failure controls passed. These figures describe the recorded execution, not guaranteed runtime or memory on another host.

The complete fresh command is `docs/zero9_replay_command.txt`, also displayed in Section 15 of `REPRODUCTION.md`. `nine_release_index.json` binds 96 immutable required files and explicitly names the accepted minimal capture. The written reductions and cited ordinary eight-chore theorem remain explicit mathematical premises; the retained checked seven/eight chain from the cited six-chore theorem is an alternative. The result is an independently checked computer-assisted proof, without a claim of end-to-end proof-assistant formalization.
