# Baseline dependencies for the nine-chore conclusion

**Status:** dependency audit, not a new solver or proof-checker run. Historical successful certificates are carried by their exact input/proof hashes. The full-nine independent certificate remains pending.

## Present route using the prior eight-chore theorem

The standalone nine-chore reduction uses ordinary EFX existence for eight chores only when a generic nine-chore counterexample would have two agents sharing a cheapest chore. Delete that chore, apply ordinary eight-chore existence, and use the fully written shared-minimum insertion argument to extend an EFX allocation. Therefore a counterexample has three distinct minima and enters the canonical residual formula.

The cited eight-chore baseline is Zhang, *EFX allocations for three agents and seven or eight chores*, version 2, Theorem 2 (local source `sources/zhang_2609_10585v2.pdf`). The paper uses the literal nonnegative definition, including every owned chore in the deletion quantifier. This route depends on a cited prior mathematical theorem; the existing local eight-chore solver verdicts alone have not been independently proof-checked. Neither P8 nor D8 is a premise.

## An alternative certificate chain if the new eight-chore replay completes

The eight-chore zero-minimum residual is a second, separate exact input. To conclude ordinary eight-chore existence from its independently checked UNSAT certificate, the shared-minimum cases reduce to ordinary seven-chore existence. The same perturbation, zero-minimum, scaling, and symmetry arguments apply with eight in place of nine. All 5,796 surjective allocations are encoded; all 765 omitted empty-bundle allocations fail because a row has only one zero and a nonempty owner can retain a positive chore after deletion.

Ordinary seven-chore existence has a previously checked residual in this package:

| Object | SHA-256 / recorded outcome |
|---|---|
| `results/root7_pruned.smt2` | `7855d4233735958aff2ffb1bb52a1aae9ff782ac16abf0550ba780e6ff211bea` |
| `certificates/root7_cvc5.cpc` | `62d8754d1e0f592a8c28b39d64de02d9579287d05b2346ff6e6349a6cb02961c` |
| Corrected `results/root7_ethos.json` | Ethos `correct`, exit 0, 26.973256 seconds; reference binding and final global false enforced |

The older positional-mode Ethos receipt is deprecated and is not used. The corrected replay streams the proof after loading the reference, preserving input binding. It checks the strict/disjoint-minimum seven-chore residual; the mathematical passage to all nonnegative seven-chore instances still uses genericity, symmetry, and insertion.

At seven chores, the insertion step invokes the ordinary six-chore theorem. Kobayashi–Mahara–Sakamoto, *EFX Allocations for Indivisible Chores: Matching-Based Approach*, Theorem 3.1, proves existence whenever the number of chores is at most twice the number of agents; for three agents this includes six chores. The full version is retained as `sources/kms_2305_04168.pdf`. Its definition on page 2 quantifies over every owned chore. Theorem 3.1 is a cited mathematical baseline, not a theorem newly established by a retained full formal certificate here.

Consequently the optional completed chain would be:

1. KMS's cited theorem supplies ordinary EFX through six chores.
2. The corrected input-bound ordinary-seven CPC replay, plus the written reductions and insertion, supplies ordinary EFX through seven chores.
3. A completed independent zero-eight Farkas/RUP replay, plus the eight-chore input/reduction audit, would supply ordinary EFX through eight chores.
4. A completed independent zero-nine Farkas/RUP replay, plus the standalone nine-chore input/reduction audit, would supply the requested nine-chore theorem.

At this checkpoint steps 3 and 4 have no completed combined independent receipt. A passing eight-chore calibration would close the computational part of step 3; it would not by itself close step 4. The entire chain still trusts the explicit handwritten reductions, parser/checker/runtime correctness, and the cited six-chore theorem. It is not a proof-assistant formalization.
