# Completion record

This records the completed parts of the research and verification deliverable. **The full nine-chore target is proved by an independently checked computer-assisted argument.** Every three-agent instance with arbitrary nonnegative additive real costs admits a complete EFX allocation, with every owned chore included in the deletion condition, including zero-cost chores. The complete exact certificate and the separately reviewed full-target reduction are bound in [zero9_full_target_binding.json](../continuation/verification/zero9_full_target_binding.json). All recorded search, proof-production, and independent-checking subprocesses are terminal; [CONTINUATION_STATUS.json](CONTINUATION_STATUS.json) preserves their individual outcomes. The handwritten reductions, cited smaller-case premises, and checker/runtime trust boundary remain explicit.

| Requirement | Status | Evidence / limit |
|---|---|---|
| Track, intended claim and requested scope recorded | Completed | Proof Digest informal track; exact target in `target.yaml` and memorandum Section 1. |
| User-specified scope retained | Completed | Complete nine-chore EFX, arbitrary nonnegative additive costs, owned zero-cost removals retained. No substitute claim is presented as a solution. |
| Original files preserved and inspection boundary recorded | Completed | Frozen SMT files and native working records are retained. The archive manifest identifies included bytes; source-paper URLs and hashes identify inspected external originals. |
| Scripts and inputs inspected before execution | Completed | Root and independent agents inspected the generators, literal predicates and checker wrappers. |
| Baseline reproduction and environment recorded | Completed | Successful smaller solver/calibration receipts; Python and solver pins; `docs/VERIFICATION.md`. |
| Main statement and load-bearing inferences inspected | Completed mathematical and certificate checks | The full nonnegative target implies the exact 21-variable input, whose original CNF/atoms, complete Boolean refutation, and all admitted arithmetic axioms are independently checked. |
| Finite checks distinguished from universal arguments | Completed | Per-claim scopes in the memorandum, verification record and ledger. |
| Independent derivations and actual independence described | Completed | Separate root, structural and computation implementations; the report-table audit independently reconstructs exact costs and extension bounds. |
| Formal statement/prose comparison | Not applicable as a proof-assistant check | No proof-assistant development. Exact SMT clauses receive a coefficient/specification audit; the handwritten interpretation remains separate. |
| Formal edits labelled accepted or unverified | Not applicable | No Lean/Rocq/Isabelle edits. CPC reference adaptation and deprecated receipts are documented. |
| Theorem axiom/dependency audit | Not applicable end to end | Explicit SMT checker/calculus/encoding trust boundary is given; no transitive proof-assistant axiom report is claimed. |
| Fifteen quality sub-scores or N/A entries | Historical ancillary review completed | `docs/proof_review.md`; these retained exposition scores do not measure the correctness or novelty of the completed main theorem. |
| Dimension means and justifications | Completed | `docs/proof_review.md`; scores do not measure correctness, novelty or publishability. |
| Outline and prior-work boundary | Completed | `docs/proof-outline.md`, novelty reports and primary references. |
| Before/after proof diagnostics | Not applicable | New informal record; no supplied formal proof was shortened. |
| Reproduction logs and remaining obligations | Completed | Exact static inputs, authoritative receipts and `CLAIM_STATUS.json`. |
| Full nine-chore proof or counterexample | **Completed independent computer-assisted existence proof** | `zero9_complete_lra_certificate.json` refutes the full canonical input, and `zero9_full_target_binding.json` links it to all 19,683 labelled allocations and the original nonnegative target. |
| Bounded conclusion and concrete sanity check | Completed | Eight-chore prescribed-agent obstruction; smaller checked refutations; uniform-nine count 1,680 and all-zero count 19,683. |

## Completed continuation evidence

| Requirement | Status | Evidence / limit |
|---|---|---|
| Strongest finite representative bounds | Proved reductions, independently reviewed | One zero per row and all other integer costs at most **2,566**; positive integer lifting with common minimum one and even nonminimum costs at most **5,132**. The primitive-Cramer refinement is separately proved; the earlier 3,831/7,662 inputs remain unchanged, and no finite domain is claimed exhausted. |
| Final prefix local guarantees | Completed exact replay | **1,956** certificates: 300 unrestricted and 1,656 with recorded ninth-column lower bounds; every assertion in the 2,008-assertion bounded-prefix input matched. Global coverage remains unresolved. |
| Final positive-minimum row local guarantees | Completed exact replay | **6,291** sufficient regions, including 2,005 distinct nonordinal cores; all 6,309 input assertions and source/subset/compression implications bound. |
| Coverage of that finite row family | Disproved for the frozen family | Exact positive integer rows satisfy all 6,309 outer assertions. More regions are required; no first row or three-agent EFX counterexample follows. |
| Complete zero-minimum full formula | Completed independent static audit | Every declaration and all 18,177 assertions, including 18,150 allocation clauses and 191,104 retained literal positions, reconstructed with standard-library exact arithmetic. |
| Positive lifted full formulas | Completed independent static audits | Eight-chore input: 5,843 assertions; nine-chore input: 18,204 assertions. Bounds, nonminimum orders, and unit failure margins matched exactly. A static audit supplies no solver verdict. |
| Zero-minimum outer transfer | Proved reduction and completed static audit | Finite-union closedness and weak-cone compression transfer all regions to a 14-variable, 6,305-assertion input. Its exact SAT model is only an outer candidate. |
| Portable verification and evidence preservation | Completed for the frozen scopes | The explicit release index, two successful replay phases, and later completion binding receipt preserve exact hashes; historical invalid mutation fixtures are excluded. |
| Prepared CPC workflow | Preparation and synthetic controls only unless superseded by a real receipt | Input, producer, adapter and signatures are pinned. Synthetic I/O or memory-failure injection is not a real solver/proof result. |
| Full nine-chore solution | **Completed** | The full independent arithmetic/Boolean certificate and the separately reviewed target reduction have passed and are bound in the current release index. |

The detailed boundaries are in [the consolidated review](../continuation/verification/consolidated_review.md), [VERIFICATION.md](VERIFICATION.md), and [the claim ledger](claim_check_ledger.md). The initial solver verdict remains historical evidence; the accepted proof now rests on the independent exact checks and the stated mathematical reduction, without trusting that verdict.

## Full-input UNSAT and independent-proof work

The initial exact terminal result is `continuation/exact_search/zero_minimum9_reference_noproof_run1.json`: Z3 returned **UNSAT in 591.67023688 seconds**, with proof output disabled. `continuation/verification/zero9_end_to_end_audit.md` supplies the full shared-minimum insertion argument and the complete reduction to this input; its historical `zero9_end_to_end_binding.json` binds that outcome and independently accounts for all 1,533 omitted empty-bundle allocations. Direct CPC export subsequently exhausted memory without a verdict or proof. The alternative arithmetic-lemma plus ordered-RUP route has now completed. The historical receipts retain their earlier status; the current successor is `zero9_full_target_binding.json`.

## Completed eight-chore baseline certificate

The full zero-minimum eight-chore residual has passed independent exact arithmetic and Boolean proof checking. `zero8_complete_lra_certificate.json` records all 27,637 admitted theory lemmas and all 10,845 RUP derivations as checked, with original-input and atom binding. `zero8_full_target_binding.json` supplies the separate mathematical scope, all 6,561 allocations, and the seven/six baseline chain. This is the retained alternative smaller-case premise for the completed nine-chore proof. The cited ordinary eight-chore theorem is the primary literature premise.

## Final nine-chore certificate completion — 8 October 2026

| Accepted component | Exact checked scope |
|---|---|
| Original formula and affine interpretation | 21 free real variables, 27 domain assertions, and all 18,150 surjective-allocation assertions; 18,066 primitive oriented affine atoms |
| Boolean refutation | 4,550 original axioms, 370,780 selected theory axioms, 172,146 derived clauses, and all 8,088,323 ordered propagation reasons; final derived empty clause and exact dependency closure |
| Arithmetic validity | All 370,780 selected clauses, using 1,317,350 exact rational multiplier positions; 360,481 strict zero-constant contradictions and 10,299 positive-constant contradictions |
| Original problem coverage | All 19,683 complete labelled allocations: 18,150 explicit surjective cases and 1,533 separately witnessed empty-bundle cases; owned-zero deletions retained |
| Portable release binding | `nine_release_index.json` binds 96 immutable proof, checker, reduction, baseline, and command files, with external-source provenance recorded separately |

The RUP check passed in 30.267 seconds with 902,792 KiB maximum resident memory; the exact arithmetic check passed in 82.486 seconds with 195,164 KiB maximum resident memory. These are observed resource figures, not runtime guarantees. The original 700 MiB RUP CLI exhausted its memory cap and produced no mathematical verdict. The accepted resource wrapper uses a stated 1,600 MiB cap and calls the same checking functions unchanged; its source review and four orchestration/relocation controls are retained.

The minimal replay capture omits only raw callback RUP and assumption logs, preserving every source atom and clause index. The final trimmed proof and complete selected arithmetic stream remain mandatory. [zero9_replay_command.txt](zero9_replay_command.txt) gives the complete fresh replay command. No solver, floating-point library, producer binary, or retrieved source paper is needed to run that exact replay. This is an independently checked computer-assisted proof with explicit mathematical dependencies, without a claim of proof-assistant formalization or absolute historical priority.
