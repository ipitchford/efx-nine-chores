# Ordinary eight-chore EFX: completed local computational proof

The exact zero-minimum eight-chore residual now has a complete independent computational refutation. `zero8_complete_lra_certificate.json` binds all three successful checks: the original SMT-to-affine-CNF reconstruction, the Boolean RUP refutation, and exact rational certificates for every admitted arithmetic theory clause. The independent checkers use only Python's standard library; they do not invoke a solver, trust a captured solver verdict, or admit callback assumptions.

The finite proof uses 898 original clauses and 27,637 independently valid arithmetic theory clauses. There are 10,845 derived RUP clauses and 405,499 ordered propagation reasons. Every proof clause lies in the dependency closure of the final empty clause. The original full input has 18 free variables, 23 domain assertions, and 5,796 allocation clauses. Its SHA-256 is `20d56e8ecd4bfad40ad5c7786c7865442c9961569dabb9e1a8dfe415b584c08f`.

## From arbitrary eight-chore instances to the checked residual

Suppose a nonnegative three-agent eight-chore instance had no complete EFX allocation. Choose a strictly failed literal deletion comparison for each of its finitely many complete allocations. A sufficiently small perturbation preserves all chosen failures while making all costs strictly positive and the entries within each row pairwise distinct.

If two agents had the same cheapest chore, delete that chore. The remaining seven-chore instance has ordinary EFX by the seven-chore baseline described below. The full shared-minimum insertion proof in `zero9_end_to_end_audit.md` applies at any cardinality: the chore is cheapest for two of the three agents, and the minimum-bundle cycle/path reassignment preserves EFX. It would extend the seven-chore allocation, a contradiction. Thus the three minima are distinct.

Label those chores 0, 1, and 2, with agent i's minimum at i. Choose the labels of agents/chores 1 and 2 so that agent 0 values chore 1 less than chore 2, and sort the remaining chores 3 through 7 by decreasing cost in row 0. Lower each row's single minimum to zero. The worst owned-chore deletion residual is unchanged, while each comparison-bundle total can only decrease. Every EFX allocation after lowering would therefore have been EFX before lowering; the absence of EFX persists. All other costs stay positive.

Finally divide each row by its positive reference cost at columns (1,0,0). The minima become zero and those reference costs become one. Positive row scaling preserves every EFX inequality, giving precisely the input's 18 free positive variables, c02>1, and the four row-zero order comparisons. There is no row-total coupling or finite cost bound.

The prior independent literal audit `zero_minimum8_formula_audit.json` reconstructed every one of the 5,796 surjective-allocation clauses and all 54,360 retained literal positions, including 10,836 pinned-zero deletion positions. The partial-order pruning retains an actually cheapest owned chore, so its disjunction is equivalent to failure of the complete literal EFX predicate. All 765 omitted allocations with an empty bundle fail automatically: some other agent owns at least two chores, and its row has at most one zero. Deleting a suitable owned chore leaves a positive-cost owned chore, whose residual exceeds the empty bundle's zero cost. `zero8_omitted_empty_allocation_witnesses.csv` supplies and independently checks an explicit such witness for each omitted allocation. All 6,561 complete allocations are accounted for.

Thus any original counterexample would satisfy the exact input now independently proved UNSAT. Ordinary complete EFX exists for three agents and eight chores, subject to the stated written reductions and baseline.

## Baseline and trust boundary

For ordinary seven chores, the package retains an input-bound Ethos-checked CPC refutation of the strict/disjoint-minimum residual: input `results/root7_pruned.smt2`, proof `certificates/root7_cvc5.cpc`, and corrected receipt `results/root7_ethos.json`. The earlier positional-mode receipt is deprecated. The genericity and symmetry reductions, plus shared-minimum insertion, extend the seven-chore residual to all nonnegative costs using the ordinary six-chore theorem.

That last baseline is Kobayashi–Mahara–Sakamoto, Theorem 3.1: EFX exists when the number of chores is at most twice the number of agents. At three agents it includes six chores. It is a cited mathematical theorem, with the primary source retained locally as `sources/kms_2305_04168.pdf`; no new proof-assistant formalization of it is claimed. The corresponding chain and unchanged prior certificate hashes are recorded in `baseline_dependency_note.md` and `baseline_dependency_inventory.json`.

This provides a locally checked alternative to citing Zhang's prior eight-chore theorem directly when reducing the main nine-chore problem. It is not a nine-chore proof by itself. The nine-chore residual requires its own complete independent certificate.

Two stream-integrity failures were rejected during preparation. The original eight-chore v3 capture had missing atom/input suffixes; the original arithmetic-certificate output had a missing final 237-record suffix. All rejected originals and rejection receipts were preserved. Separate derived artifacts reconstruct the static original-input streams and add only the missing arithmetic certificates. Independent input, Boolean, and arithmetic checks run on the resulting explicitly bound artifacts; no reconstructed file is attributed to an unchanged original producer run. The composed arithmetic file's hash exactly matches the original producer's intended complete hash. These failures do not become trusted assumptions of the proof.
