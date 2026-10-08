# Proof review appendix

**The listed finite checks reproduced; no proof of the unrestricted nine-chore claim is present.** This is a bounded internal review, dated 7 October 2026, using Proof Digest's informal track. It assesses the memorandum and ancillary arguments, not a purported solution of Problem 2.

## Inspection boundary and reproduction

The review read the full memorandum through [its builder](../src/build_report.py), [ancillary_proofs.md](ancillary_proofs.md), the literal finite checker, the P6/P7 formula audit, the current claim ledger, and the corrected Ethos wrapper and receipts. It checked the domains, prescribed-agent quantifier, zero-cost deletion convention, empty bundles, scaling, genericity, insertion proof, and conditional dependencies. The original report source was not edited by this review.

The following evidence has distinct scopes:

| Check | Outcome and boundary |
|---|---|
| Independent report arithmetic | **Passed.** [structural_report_check.py](../work/structural_report_check.py) reads the actual displayed table data without importing report/checker/solver implementations. It enumerates all 6,561 allocations, reproduces 36 EFX allocations and prescribed counts `(0,31,31)`, checks all ten agent-0 bundle groups and the direct witness, and derives the exact three extension regions. |
| Frozen P6/P7 clauses | **Passed.** [The formula audit](../work/structural_prescribed_formula_audit.json) matches all 729/1,806 allocation clauses and 26/41 domain assertions to independently reconstructed formulas. Its 17,745 literal point comparisons include zeros and ties; 762 additional empty-allocation checks use strictly positive costs. |
| External arithmetic refutations | **Receipts inspected; not rerun in this review.** Corrected P6 and ordinary-seven receipts require input binding and global false. The P7 selected-core replay remained pending at this review's cutoff. |
| Entire proof infrastructure / universal theorem | **Not fully inspected / not available.** No line-by-line manual review of every CPC inference, proof-assistant formalisation of the reductions, or completed nine-chore proof is claimed. |

From the project directory, `python work/structural_report_check.py` reproduced the report checks under Python 3.12.14, exit 0, in approximately 0.04 seconds. Its [receipt](../work/structural_report_check.json) records the inspected source hashes. Solver and external-checker versions and exact commands remain in [VERIFICATION.md](VERIFICATION.md); their reported timings were compared with the receipts, not replaced by this short audit's timing.

## Proof outline and concrete review findings

1. **Standard reduction — memorandum §2, ancillary §1.** Finitely many strict failure witnesses permit positive rational generic costs; row scaling and chore relabelling preserve the comparisons. Zero-domain omissions are justified through this argument.
2. **Computational step — memorandum §3, ancillary §3.** P6 follows from the nonnegative canonical input's checked refutation together with explicit zero-row handling. Zero padding legitimately gives every smaller cardinality: removing globally zero dummy chores changes neither bundle totals nor any residual obtained by deleting an original chore.
3. **Structural step — ancillary Theorem 1 and Proposition 2.** The cycle/path argument preserves a prescribed ordinarily envy-free agent. This handles the shared-minimum case for P7; the remaining exact formula has a separate certificate obligation. The proof also covers empty old bundles and ties.
4. **Exact obstruction and restricted extension — memorandum §§4–5.** Exhaustion refutes P8, while the three explicit allocations cover every appended nonnegative column for this particular matrix. All one-based chore labels, residuals and thresholds agree with direct calculation. This does not prove universal nine-chore existence.

One precision issue was flagged and corrected: “every atom is a strict linear inequality” now refers to **allocation-failure atoms**, since domain constraints can be weak inequalities or equalities. No other mathematical error was found within the inspected scope. KMS insertion and Zhang's ordinary-eight result are identified as prior work; this review makes no additional novelty determination.

## Exposition-quality rubric

Scores use the required 1–5 half-point scale. They evaluate the **available ancillary exposition only**. For the absent nine-chore proof, all fifteen sub-metrics, five dimension means, and overall mean are **N/A**. These scores are judgments about presentation and proof organisation, **not probabilities of correctness, novelty, or publishability**.

The informal mapping reads tactic transparency as inference transparency, broad-tactic control as control of computational closure, and Mathlib style as mathematical exposition conventions.

| Dimension | Sub-metric | Score |
|---|---|---:|
| Structure | `main_theorem_slimness` | 4.5 |
| Structure | `complexity_distribution` | 4.0 |
| Structure | `dependency_clarity` | 4.5 |
| Signature quality | `statement_naturalness` | 4.5 |
| Signature quality | `binder_economy` | 4.5 |
| Signature quality | `generality` | 4.5 |
| Step transparency | `tactic_transparency` | 4.0 |
| Step transparency | `explicit_lemma_use` | 4.5 |
| Step transparency | `broad_tactic_control` | 4.0 |
| Reuse | `helper_usefulness` | 4.5 |
| Reuse | `reuse_potential` | 4.5 |
| Reuse | `no_dead_helpers` | 4.5 |
| Human readability | `proof_readability` | 4.5 |
| Human readability | `mathlib_style` | 4.5 |
| Human readability | `maintainability` | 4.0 |

| Dimension | Mean | Concrete justification |
|---|---:|---|
| Structure | 4.33 | Memorandum §§2–5 separate the universal encoding, auxiliary induction, obstruction and fixed-family extension. Ancillary Propositions 2–4 expose dependencies; the large finite refutation remains a concentrated computational step. |
| Signature quality | 4.50 | Ancillary Theorem 1 supports any number of agents with precisely stated minimum assumptions. Pm fixes the agent in advance; Proposition 4 retains its unproved D8 premise. |
| Step transparency | 4.17 | The cycle/path proof explains the residual identity, and memorandum §5 displays every threshold. Exact solver inputs and receipts expose computational closure, though those refutations are not short human calculations. |
| Reuse | 4.50 | The insertion lemma drives the shared-minimum reduction, and the owner-insertion implication explains why P8 would suffice. Ancillary §5's merge counterexamples serve an explicit purpose in excluding invalid routes. |
| Human readability | 4.33 | The opening states the unresolved target; memorandum §§1 and 4 distinguish EFX from ordinary envy. Repeated status statements across the memorandum, ledger and ancillary record require coordinated maintenance. |
| **Overall** | **4.37** | Simple mean of all fifteen assessable ancillary scores: 65.5 / 15. |

## Remaining obligations and sanity check

The main nine-chore obligation remains entirely open in this package. Upgrading P7's certificate status requires a successful input-bound refutation of the selected core, its exact subset relationship to the original formula, and the written P6/insertion/genericity dependencies. The checked finite formulas still rely on the stated semantic reductions, parser/checker implementation and CPC calculus. Historical priority and release suitability require separate judgments.

The bounded conclusion is that the reviewed ancillary arguments and exact displayed calculations are consistent with their stated evidence. For a concrete sanity check, the memorandum's direct witness has own residuals `(548,307,166)` against other-bundle minima `(579,312,227)`, so it is EFX. Agent 0's total is nevertheless 583, greater than 579: the same witness does **not** satisfy the prescribed ordinary-EF requirement.


## Final certificate status

The final prescribed-agent seven-chore external proof attempt ended without a verdict or certificate (exit 139; cause not established). No cap change was applied and no further run was started. The Z3 UNSAT result and exact formula audits remain available, but independent external verification of that residual was not obtained. The original nine-chore target remains unresolved. See `VERIFICATION.md` and `CLAIM_STATUS.json` for the closed run ledger.
