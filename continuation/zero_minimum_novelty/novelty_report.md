# Novelty-gate addendum: lowering one cheapest chore to zero

**Search date:** 7 October2026.  
**Scope:** A bounded formula-level search after a structural simplification of the nine-chore investigation.  
**Intended contribution:** An explicit, independently checked search reduction and its computational artifacts. No priority claim is made.

## 1. Frozen statement and contribution boundary

The exact statement is in `target.yaml` and is proved in `../exact_search/zero_minimum_reduction.md`. For each row, zero one selected globally cheapest coordinate. Every owned bundle retains exactly the same worst-deletion residual. Every comparison-bundle cost can only decrease. Therefore an EFX allocation after the transformation was already EFX beforehand.

The statement concerns **every owned deletion, including a zero-cost chore**. It does not assert equality of allocation sets, does not subtract the minimum from the whole row, and does not solve the nine-chore question. The finite representative bound and its positive lifting are consequences of this normalization and standard linear-algebra arguments.

## 2. Normalization and fingerprints

| Object or phrase | Exact interpretation | Boundary |
|---|---|---|
| EFX for chores | `c_i(A_i\\{g}) <= c_i(A_j)` for every owned g | Includes owned zero-cost chores |
| Worst deletion residual | `r_i(S)=c_i(S)-min_{g in S}c_i(g)`; empty residual zero | Both sides use row i |
| Zeroing | Replace only `c_i(e_i)` by0 for a selected global minimum e_i | Other coordinates are unchanged |
| Projection within a fixed minimum cone | Diagonal matrix with one zero and all other diagonal entries one | The projection operator itself is elementary prior mathematics |
| Search normalization | After distinct pins, independently set off-minimum references `[1,0,0]` to1 |21 free real variables at m=9 |
| Integer representative | One zero and eight positive integers per row, each at most3831 | Not an exhausted search domain |
| Positive lift | Raise each zero to1/2, then multiply by2 | Common row minima1, other entries even and at most7662 |

Three exact projection matrices at sizes3,4,5 are in the target. Their rank and trace are m-1, determinant zero, and characteristic polynomial is `lambda*(lambda-1)^(m-1)`. They are idempotent and scale-equivariant. No new matrix, spectrum, kernel or cross-disciplinary identification is claimed.

Exact row examples, listing residuals in binary subset-mask order:

| Original row | Zeroed row | Residuals before and after |
|---|---|---|
| `(2,4,7)` | `(0,4,7)` | `(0,0,0,4,0,7,7,11)` |
| `(3,6,10)` | `(0,6,10)` | `(0,0,0,6,0,10,10,16)` |
| `(2,2,5)` | `(0,2,5)` | `(0,0,0,2,0,5,5,7)` |

The third example checks a tied original minimum. Exact controls elsewhere also include an already-zero row minimum and all511 nonempty bundle shapes of nine chores.

The sufficient zero-cost representative bounds for m=4,...,12 are `4,13,50,197,840,3831,18557,94868,509287`. This is an upper-bound sequence derived from a determinant estimate, not a proposed new enumerative sequence. No generating function or recurrence is asserted.

## 3. Search log and inspected source boundary

The web search was repeated after the zero-minimum simplification. Queries included:

1. `EFX chores "minimum" "zero" normalization`
2. `EFX chores lower cheapest chore cost zero residual`
3. `EFX additive chores "without loss of generality" "zero" minimum`
4. `chores EFX "cheapest" "zero" normalization additive`, restricted to arXiv
5. `EFX "c_i" "minimum" "zero" "lowering" chores`
6. `EFX chores "set" "cheapest chore" "0"`
7. `EFX chores "3831"`
8. `"4, 13, 50, 197, 840, 3831"`
9. `"EFX" "residual" "lower" "minimum" chores`
10. `"EFX" "cheapest" "set to zero"`
11. `"EFX" "minimum" "coordinate projection"`

The inspected primary-source boundary is:

- Xinkai Zhang, [EFX Allocations for Three Agents and Seven or Eight Chores, v2](https://arxiv.org/html/2609.10585v2). The definition/residual passage, row-scaling and shared-minimum reductions, and Section6 were inspected. Section6 leaves nine chores open in that source and records the shared-minimum reduction. This is attribution to that version, not proof that no later result exists anywhere.
- Kobayashi, Mahara and Sakamoto, [EFX Allocations for Indivisible Chores: Matching-Based Approach](https://doi.org/10.1016/j.tcs.2024.115010), with the [full preprint](https://arxiv.org/abs/2305.04168) inspected during the earlier investigation. Its insertion lemma and residual graph conditions remain prior dependencies. A new HTML request in this addendum returned an internal error; it supplied no new evidence.
- [Fairness criteria for allocating indivisible chores: connections and efficiencies](https://link.springer.com/article/10.1007/s10458-023-09618-5), Definition2.3 and the returned nearby proof passage. This uses a positive-cost-only deletion convention. It is a nearby definition, not an identity match to the commissioned zero-inclusive target.
- Christoforidis and Santorinaios, [On the Pursuit of EFX for Chores](https://www.ijcai.org/proceedings/2024/0300.pdf), the returned preliminary definitions and superadditive counterexample passage. Superadditive nonexistence is not an additive nine-chore result.
- The publisher result for [Polynomial-Time Algorithms for Fair Orientations of Chores](https://journals.sagepub.com/doi/10.3233/FAIA251225) explicitly distinguishes positive-only and zero-inclusive deletion variants. The orientation restriction is not the unrestricted allocation problem here.
- The classical determinant-method source remains von zur Gathen and Sieveking, [A bound on solutions of linear integer equalities and inequalities](https://doi.org/10.1090/S0002-9939-1978-0500555-0). Cramer's rule and Hadamard's inequality are not claimed as new.

Searches also returned secondary summaries about restricted additive costs, binary chores, and EFX orientations. These were used only to identify terminology and primary sources. Their summaries do not establish a collision or a new technical claim. The attempted HTML page for arXiv2606.08872v2 returned an internal error and was not counted as inspected full text.

## 4. Alias and missingness audit

The natural aliases are residual-preserving preprocessing, monotone tightening of bundle comparisons, allocation-set inclusion, counterexample-preserving coordinate projection, and a small integer representative for a sparse linear system. Probability and mathematical-physics searches have no load-bearing role: on a fixed minimum cone the map is simply an elementary deterministic projection, not a stochastic kernel or a new spectral object. No cross-disciplinary bridge is claimed.

The search covers indexed web passages and the identified primary sources, not every paper, language, unpublished note, book or repository. There was no dedicated comprehensive MathSciNet, zbMATH or OEIS database interrogation, and no author enquiry. An exact sequence search that does not identify a match cannot prove the bound or normalization is historically new. Different zero-cost conventions materially reduce the reliability of title-only matches.

## 5. Adjudication

| Contribution unit | Outcome | Permitted language |
|---|---|---|
| Elementary coordinate projection and determinant method | Known mathematics | Standard tools used in the derivation |
| Exact EFX zero-minimum normalization | **Bounded uncertainty** | Derived and independently checked here; no exact identity found in the inspected search boundary |
| Numeric bounds3831 and7662 | **Bounded uncertainty** | Sufficient bounds proved in the accompanying note; no priority claim |
| New strict formulas and semantic controls | Recorded computation/artifacts | Explicit inputs and exact finite audits, with their own actual run outcomes |
| Nine-chore universal existence | Unresolved by this addendum | No solution claim follows from a normalization or a finite bound |

**Decision: BOUNDED UNCERTAINTY.** The proof and computational work can proceed with explicit attribution to standard ingredients and without novelty language. A failed search is not evidence of first discovery. If a later full solution or a materially different structural identity is obtained, its exact statement and prior-art boundary need a fresh review.
