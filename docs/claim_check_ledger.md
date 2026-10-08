# Claim-to-check ledger

**Updated: 8 October 2026.** T9 now has a complete independently checked computer-assisted proof, with its current certificate and target binding recorded below. The authoritative status remains attached to an exact claim and object: historical unsuccessful attempts and earlier partial receipts are not rewritten. Files ending in `_positional_deprecated.json` are explicitly unbound historical receipts.

Status vocabulary: **checked finite refutation** means a complete independent proof replay bound to the exact input (historical certificates use Ethos; the new exact-Farkas/RUP route must pass every stage); **proved reduction** means the supplied written mathematical argument, without proof-assistant formalization; **exact solver result** means a solver verdict without the full external certificate route; **finite audit** means the stated finite comparison or enumeration; **unresolved** is not a theorem.

| ID | Claim | Evidence and dependency | Status / allowed conclusion |
|---|---|---|---|
| T9 | Every nonnegative additive three-agent nine-chore instance admits complete literal EFX, including deletion of owned zero-cost chores | `target.yaml`; `continuation/verification/zero9_complete_lra_certificate.json`; `zero9_full_target_binding.json`; full written reduction in `zero9_end_to_end_audit.md` | **Proved by an independently checked computer-assisted argument.** All 19,683 allocations are accounted for. Handwritten reductions, the stated smaller-case theorem, and checker/runtime dependencies remain explicit. |
| D1 | The literal own-chore deletion predicate matches the intended definition | Exact formula in `target.yaml`; 290,400 comparisons and zero-trim mutation in `results/encoding_audit9.json` | **Finite audit plus displayed definition.** Tests are not an all-input encoder proof. |
| R1 | Positive row scaling and simultaneous row/column relabellings preserve the problem | Homogeneity and bijections of complete allocations | **Proved elementary reduction.** Zero rows require separate handling. |
| R2 | Strict generic costs suffice for existence | Finite strict-failure margins; explicit prior perturbation in Yin–Mehta Lemma 2.1 | **Proved reduction; prior collision.** No novelty claimed. |
| R3 | An ordinary shared-minimum chore can be inserted after solving the smaller instance | Full cycle/path proof in `continuation/verification/zero9_end_to_end_audit.md`; KMS and Zhang attribution retained | **Attributed proved reduction.** The separately checked residual completes the other branch; no P8 or D8 strengthening is needed. |
| R4 | Fixed-rank trimming and dominance simplifications preserve the failure predicate on their stated domain | `work/structural_rank_audit.md`; 236,196 finite checks in `work/structural_rank_audit.json` | **Written argument plus finite audit.** No assertion that the rank cases have all been refuted. |
| O7F | The exact ordinary seven-chore strict/disjoint-minimum residual formula is UNSAT | `results/root7_pruned.smt2`; CPC object; corrected `results/root7_ethos.json` | **Checked finite refutation**, bound to input hash `7855d423…11bea`. |
| O7 | Ordinary EFX exists through seven chores | O7F; KMS six-chore existence and insertion; R1–R3 | **Known literature result with a new checked residual replay.** Distinguish the replay from historical novelty. |
| O8F | The exact ordinary eight-chore residual formula is UNSAT | Z3 `results/root8_pruned.json`, 68.53 seconds; native proof retained | **Exact solver result.** cvc5 full attempt was killed; an externally checked local refutation was not obtained. |
| O8 | Ordinary EFX exists through eight chores | Zhang v2 ordinary eight-chore theorem; the later Z8F/Z8E exact LRA proof supplies a retained alternative | **Prior theorem, with a separately checked local proof chain.** The successful local certificate is the exact Farkas/RUP proof, while the earlier CPC attempt remains unsuccessful. |
| P6F | The prescribed-agent six-chore normalized nonnegative formula is UNSAT | `work/structural_designated_m6.standard.smt2`; corrected `results/designated6_ethos.json` | **Checked finite refutation**, bound to input hash `bf24e507…50c4b2`. |
| PD | The frozen P6/P7 formulas contain exactly the specified domain and failure clauses | `work/structural_prescribed_formula_audit.json`: exact coefficient and domain matching for all 729/1,806 allocation clauses; separate 10,140 literal point checks in `results/designated_semantic_audit.json` | **Exact structural audit plus finite sanity checks.** Independent of the generators; depends on audit/parser correctness. |
| P6 | Every six-chore instance has complete EFX with any prescribed agent ordinarily envy-free | P6F; unit-row/zero-row handling and column symmetry; generator's literal failure clause | **Computer-assisted result conditional on the explicit semantic reductions**, with the finite refutation externally checked. |
| PR | Insertion of a chore cheapest for the two other agents preserves the prescribed agent's envy-freeness | `work/structural_lemmas.md`, Lemma 5; attributed extension of KMS cycle/path proof | **Proved reduction.** No new general matching principle claimed. |
| P7F | The prescribed-agent seven-chore residual is UNSAT | `work/structural_designated_reduced_m7_seed0.json`: Z3 UNSAT 99.72 seconds; `results/designated7_core_select.json`: tracked-core Z3 UNSAT 125.17 seconds | **Exact solver results; no external certificate obtained.** Full-input cvc5 exhausted memory; the subsequent core attempt exited 139 without a verdict or proof. |
| P7 | Prescribed-agent property holds through seven chores | P6, PR, P7F, genericity and residual symmetry | **Computer-assisted conclusion relying on the stated Z3 verdict.** It has not completed the external certificate route; do not describe it as externally certified. |
| NP8 | The prescribed-agent property fails at eight chores | Exact positive matrix and all 6,561 allocations in `results/p8_obstruction_verified.json`; 36 EFX allocations, ordinary-EF counts `(0,31,31)` | **Exact finite obstruction.** Agent 0 is never ordinarily envy-free in an EFX allocation. Ordinary EFX itself does exist. |
| SHARP | Seven/eight is the exact prescribed-agent threshold | P7 and NP8 | **Candidate theorem with a solver-trust dependency at P7.** The requested external certificate route remains incomplete. NP8 alone supplies only the upper obstruction. |
| NEXT | \(P_m\) would imply ordinary EFX at \(m+1\) | Remove a cheapest chore for the prescribed agent, solve \(P_m\), reinsert into its envy-free bundle; `work/structural_lemmas.md`, Corollary 6 | **Proved implication.** Since \(P_8\) fails, this unrestricted route does not prove T9. |
| D8 | Prescribed-agent property at eight chores with all three minima distinct | `results/D8_root.json`: UNKNOWN after 903.68 seconds | **Unresolved.** Domain restriction and any bridge to nine chores must be accounted for separately. |
| CUT | Protected-singleton/pair conditions guarantee EFX | `work/structural_lemmas.md`, Theorems 3–4, elementary decreasing-order split proof | **Proved sufficient cases.** Their negations are necessary search cuts, not full coverage. |
| CORE | A selected exact assertion subset can support a smaller proof | `src/extract_z3_core.py` / `src/select_z3_core.py` copy original assertion commands verbatim | **Reduction of checking input only.** UNSAT must subsequently be established for that subset. |
| CHECK | The successful external receipts enforce original assumptions and global false | Corrected stdin adapter, exact duplicate-declaration reuse, four passing controls in `results/checker_controls.json` | **Checked boundary behavior.** CPC calculus/checker soundness remain explicit premises. |
| NOV | No prior prescribed-agent threshold or later nine-chore resolution was found | `novelty_report.md`; `novelty_designated_addendum.md`, primary-source/version/query log | **Bounded search conclusion only.** No absolute priority claim. |

## Exact evidence that must accompany successful machine claims

For O7F retain the original SMT input, `certificates/root7_cvc5.cpc`, `results/root7_cvc5.json`, and corrected `results/root7_ethos.json`. For P6F retain the standardized SMT input, original/standardization receipt, `certificates/designated6_cvc5.cpc`, `results/designated6_cvc5.json`, and corrected `results/designated6_ethos.json`. Retain the pinned signature files, checker build receipt, adapter and boundary controls for both. Exact object hashes and replay commands appear in `docs/VERIFICATION.md`.

The proof object alone does not establish that the generator expresses the allocation theorem. Conversely, an exact finite semantic audit does not prove the SMT formula unsatisfiable. The complete mathematical claim needs both the semantic reductions and the finite refutation.

## Negative-result ledger

| Receipt | Recorded failure | Consequence |
|---|---|---|
| `results/root9_pruned_termination.json` | Exit 137 / killed without verdict | No conclusion about T9. |
| `results/root9_unit_cuts_termination.json` | Exit 137 / killed without verdict | No conclusion about T9. |
| `results/root9_cuts.json` | UNKNOWN / timeout | No conclusion about T9. |
| `results/rank9_6_7.json` | UNKNOWN / timeout | No completed branch proof or full rank cover. |
| `results/second_min_cases/summary.json` | All 14 restricted graph/rank cases returned UNKNOWN after 45-second solver budgets | No decided case and no completed full case cover. |
| `results/D8_root.json` | UNKNOWN / timeout | No theorem for the distinct-minimum prescribed-agent eight-chore target. |
| `work/compute_deleted_min9_full/stop_receipt.json` | UNKNOWN after 1,200.416110 seconds | No conclusion from the simultaneous deletion target. |
| `work/compute_designated8_allmin/stop_receipt.json` | Total search budget reached; interrupted without conclusion after 137 partial SAT models | Neither a distinct-minimum P8 counterexample nor an existence proof. |
| `work/compute_run_summary.json` and the seven other `compute_*/stop_receipt.json` records it identifies | Earlier incremental searches interrupted without conclusion | Partial-formula SAT entries do not establish counterexamples to a complete existence statement. |
| `results/root8_cvc5.json` | Killed without verdict | No externally checked local eight-chore certificate from this attempt. |
| `results/designated7_cvc5.json` | Memory exhaustion without verdict | No external P7 certificate from that attempt. |
| `results/designated7_core_cvc5.json` | Exit 139, no diagnostic, verdict or certificate; cause not established | No external P7 certificate from the final core attempt. The unsuccessful cap-change request is separately recorded. |
| `results/root7_ethos_positional_deprecated.json`; `results/designated6_ethos_positional_deprecated.json` | Original-assumption binding was not enforced in positional-file mode | Superseded by corrected stdin-mode receipts; never cite the deprecated verdict as a bound verification. |

Before upgrading any unresolved row, record the exact new input/proof hashes, complete successful checker receipt, any assertion-subset relationship, and all domain-reduction dependencies. Worker state is recorded separately in [CONTINUATION_STATUS.json](CONTINUATION_STATUS.json); the historical receipts above do not establish that later continuation workers have ended. A release title or abstract must not turn an ancillary result, a successful calibration, or an unfinished computation into a solution of T9.

## Continuation claim ledger

The earlier rows retain their original object-specific meaning. The following entries record the continuation's local guarantees and reductions. The final full nine-chore certificate is recorded separately at the end of this ledger; its completion does not change the coverage status of an older regional relaxation.

| ID | Claim | Evidence and dependency | Status / allowed conclusion |
|---|---|---|---|
| Z0 | Lowering one globally cheapest cost in each row to zero preserves the absence of EFX allocations | `continuation/exact_search/zero_minimum_reduction.md`; independent residual argument in `continuation/verification/zero_minimum_independent_review.md` | **Proved reduction.** Maximum owned-deletion residuals are unchanged and target sums weakly decrease; owned-zero deletions remain included. |
| Z3831 | Any nine-chore counterexample has a representative with one zero in each row and positive integer other costs at most 3,831 | Z0, finite strict-failure perturbation, eight-dimensional independent row systems, Cramer's rule and \(|\det D_g|^2\le7\cdot8^7\) | **Proved finite-domain reduction.** No exhaustive search of the domain has been completed. Distinct canonical zero positions additionally use R3 and O8. |
| L7662 | Any nine-chore counterexample has positive integer costs with common minimum one and even other costs at most 7,662 | Raise the zeros in Z3831 to one half, preserve each chosen integer failure margin, then double | **Proved finite-domain reduction.** Nonminimum costs lie in \(\{2,4,\ldots,7662\}\); no universal existence result follows from the bound alone. |
| ZF9 | The full 21-variable zero-minimum formula faithfully expresses the canonical counterexample question | `continuation/verification/zero_minimum9_formula_audit.json` and the portable zero-formula replay: all 18,177 assertions and 191,104 literal positions reconstructed | **Complete static formula audit.** The later Z9F certificate independently refutes this exact unbounded input. |
| LF9 | The full 24-variable positive lifted formula faithfully uses the 7,662 upper bound and unit failure margins | `continuation/verification/lifted9_formula_audit.json`: 54 domain assertions plus all 18,150 allocation clauses | **Complete static formula audit.** Real variables need not be even or integer; the forward implication is supplied by L7662, while a satisfying real matrix would be a strict counterexample. No solve is claimed for this input. |
| PR1956 | Every final prefix certificate guarantees EFX throughout its recorded ninth-column domain | `continuation/verification/release_replay_final_certificates/bounded_prefix_snapshot_audit.json`: 1,956 certificates and all 2,008 assertions | **Exact local guarantees and input binding.** 300 are unrestricted, 1,656 use recorded lower bounds. Global prefix coverage is unresolved. |
| RR6291 | Every region used in the final positive-minimum two-row input has a valid first-row guarantee and faithful other-row predicates | `continuation/verification/release_replay_final_certificates/row_snapshot_audit.json`: 3,238 singletons, 1,048 static pairs, 2,005 distinct cores; all 6,309 assertions matched | **Exact local guarantees and complete input binding.** This does not assert coverage. |
| NC6291 | The finite family in RR6291 does not cover its complete canonical two-row domain | `continuation/verification/positive_outer_noncoverage_witness.json`: exact positive integer rows satisfy every one of the 6,309 outer assertions, with minimum exclusion margin one | **Exact noncoverage witness.** Additional regions are required. It supplies no first row and is not a three-agent counterexample to T9. |
| ZR14 | The finite row guarantees transfer to a zero first-row minimum, with independently normalized references in the other two rows | `continuation/structural_nine/zero_outer/transfer_proof.md`; `continuation/verification/zero_outer_audit.json` reconstructs all 6,305 assertions | **Proved transfer and complete static audit.** Its checked SAT model is an outer candidate only. |
| CR | All explicitly indexed local certificates and final region/input correspondences can be replayed without an SMT solver | `continuation/verification/release_certificate_index.json`; two successful `release_replay.py` phases; `release_completion_audit.json` binds later source and audit evidence | **Completed standard-library exact replay and hash binding.** No global theorem or proof-assistant formalization is implied. |
| CPCP | A verdict-preserving CPC producer and exact-input replay configuration have been prepared | `continuation/exact_search/zero9_cpc_prepared_config.json`; synthetic I/O/failure-injection receipt explicitly has `real_solver_invoked=false` | **Prepared artifacts and synthetic controls only.** This is not an actual solver result or externally checked proof. Any real zero8/zero9 attempt needs its own terminal receipts. |

The bound 11,585 and its earlier positive-row formulas remain valid as historical reductions. Their stronger successors do not retroactively change those inputs. An earlier nine-chore zero-minimum proof-enabled attempt returned **UNKNOWN / out of memory**; the positive lifted eight-chore calibration returned **UNKNOWN / timeout**. Their exact receipts and later outcomes are listed in `CONTINUATION_STATUS.json`. An intended timeout is not an observed terminal outcome, and a lost worker receives no inferred mathematical verdict.

## Full-target UNSAT checkpoint

| ID | Claim or observation | Evidence | Status |
|---|---|---|---|
| Z9U | The exact full zero-minimum nine-chore input is UNSAT | `continuation/exact_search/zero_minimum9_reference_noproof_run1.json`; SHA-256 `65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b` | **Exact solver result**, 591.67023688 seconds, normal exit; proof output disabled. |
| Z9E | Every original counterexample yields a model of that input | `continuation/verification/zero9_end_to_end_audit.md` and `zero9_end_to_end_binding.json` | **Written proof plus exact binding.** Full insertion lemma included; 18,150 explicit surjective clauses plus 1,533 independently witnessed omitted allocations. Uses ordinary eight-chore existence, without P8 or D8. |
| LRA100 | The new arithmetic checker validates a spread of 100 captured real theory clauses | `continuation/verification/zero8_capture_v2_spread_farkas.json` | **Exact arithmetic precheck**, distinct from complete selected-theory coverage for a Boolean refutation. |
| LRAC | The new exact LRA/RUP checkers reject targeted unsound mutations | `continuation/verification/lra_checker_negative_controls.json` | **41 focused controls passed**; no solver called and no target theorem inferred from controls. |

The direct full-nine CPC attempt and the eight-chore Boolean CPC attempt both terminated with native allocation failures before any durable verdict/proof. Those attempts did not discharge the independent proof obligation. The later exact arithmetic-lemma plus ordered-RUP certificate Z9F now does so, without changing the earlier failure receipts.

## Primitive-Cramer representative refinement

| ID | Claim | Evidence | Status |
|---|---|---|---|
| Z2566 | Any nine-chore counterexample has a representative with one zero per row and positive integer other costs at most 2,566 | `continuation/verification/primitive_cramer_bound.md`; common divisor of all augmented maximal minors, exact parity factor, and Hadamard | **Proved reduction, independently reviewed.** Exact arithmetic and small-dimension controls in `primitive_cramer_bound_audit.json`. |
| L5132 | Any nine-chore counterexample has a positive integer representative with common minimum one and even nonminimum costs at most 5,132 | Z2566 followed by half-unit raising and doubling | **Proved reduction.** No finite search exhaustion is claimed. |

Z3831/L7662 and the earlier frozen inputs are unchanged valid weaker bounds. The full zero-minimum strict-real formula that returned UNSAT imposes none of these finite upper bounds.

## Complete eight-chore alternative baseline

| ID | Claim | Evidence | Status |
|---|---|---|---|
| Z8F | The exact 18-variable zero-minimum eight-chore residual is UNSAT | `continuation/verification/zero8_complete_lra_certificate.json` | **Checked finite refutation.** All original input/atom bindings, 27,637 exact Farkas axioms, 10,845 RUP derivations, and 405,499 reasons passed. No solver verdict trusted. |
| Z8E | Z8F supplies ordinary eight-chore existence using the checked seven-chore residual and cited six-chore theorem | `continuation/verification/zero8_full_target_completion.md` and `zero8_full_target_binding.json` | **Completed correspondence and certificate binding.** All 6,561 allocations accounted for; no P8 or D8 premise. |
| LPORT | The new complete certificate checker is portable after bundle extraction | `continuation/verification/lra_relocation_control.json` | **Full small-fixture relocation check passed.** Explicit relative/absolute paths work; historical absolute provenance paths are not required. |

Z8F is a new complete independent proof for a different exact input than the historical positive eight-chore O8F solver result. The known ordinary eight-chore theorem remains a prior literature result; this package now also has a locally checked alternative proof chain. It does not infer a nine-chore certificate from the eight-chore proof.

## Complete nine-chore proof and current release binding

| ID | Claim | Evidence | Status / allowed conclusion |
|---|---|---|---|
| Z9B | The final Boolean proof refutes selected original/theory clauses | `continuation/verification/zero9_rup_source_cache_independent.json` | **Checked finite Boolean refutation relative to the listed theory axioms.** All 172,146 derived clauses and 8,088,323 ordered reasons, original/theory provenance, final empty clause, and exact dependency closure passed. |
| Z9A | Every arithmetic theory axiom admitted by Z9B is valid | `continuation/verification/zero9_selected_farkas_independent.json` | **Complete exact arithmetic certificate.** All 370,780 selected clauses and 1,317,350 multiplier positions checked, with strict and weak inequalities handled exactly. |
| Z9F | The exact full unbounded nine-chore counterexample input is UNSAT | `continuation/verification/zero9_complete_lra_certificate.json` | **Complete independent exact LRA refutation.** Original input/atom reconstruction, Z9B and Z9A share the same hashes and exact selected set. No producer verdict or callback assumption is trusted. |
| Z9T | Z9F proves the original nonnegative nine-chore existence target | `continuation/verification/zero9_full_target_completion.md` and `zero9_full_target_binding.json` | **Completed mathematical correspondence.** Genericity, full insertion lemma, zero-minimum lowering, canonical normalization, every literal allocation clause, and all omitted allocations are accounted for. Uses the stated ordinary eight-chore premise. |
| Z9PORT | The full nine-chore certificate has a concrete portable replay command | `docs/zero9_replay_command.txt`; `continuation/verification/budgeted_replay_controls.json`; `nine_replay_orchestration_review.json` | **Reviewed resource-only wrapper and four successful small controls.** The unchanged mathematical functions run under an explicit 1,600 MiB cap. The earlier 700 MiB failure remains a resource failure. |
| Z9REL | The current release binds the complete proof and its mathematical dependencies | `continuation/verification/nine_release_index.json` | **PASS, 96 immutable required files.** Accepted minimal capture, trace, exact arithmetic stream, current target binding, smaller-case dependencies, trusted checker sources, and replay command are hash-bound. Full retrieved source papers are external provenance. |

These completed checks establish T9 as an independently checked computer-assisted theorem. They do not establish the separate prescribed-agent seven-chore certificate, prove coverage of the old regional relaxations, or make an absolute priority claim. Current presentation and archive manifests are separate from the immutable mathematical proof index.
