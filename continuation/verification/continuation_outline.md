# Outline of the nine-chore continuation

## Statement

The intended theorem is that every nonnegative additive three-agent cost matrix on nine indivisible chores admits a complete EFX allocation, including removal of every owned zero-cost chore in the EFX test. **That theorem has not been proved or refuted by this continuation.**

The proved objects are reductions and local certificate implications. This outline describes where a complete argument could close, and identifies the parts already checked. Details and the exact evidence boundary are in [consolidated_review.md](consolidated_review.md).

## Idea

A hypothetical counterexample can be made positive and generic, normalized by its row minima, and placed in a canonical domain. Two complementary approaches then eliminate variables. The prefix approach turns each full allocation into a box of ninth-column values and certifies regions of eight-column prefixes on which a finite set of boxes always covers the required extension domain. The first-row approach finds allocation sets such that some member must satisfy the entire first row, then records the other two rows' simultaneous EFX conditions as a sufficient region. Either approach still needs a complete certified cover of its outer domain. Accumulating local regions has not yet supplied that cover.

## Outline

1. **Reduce any counterexample to positive generic costs.** Keep one strict failure for each of finitely many allocations; a small positive perturbation preserves them. Scale rows independently and use the shared-minimum insertion reduction to reach distinct pinned minima. This is the canonical setup in the extension and first-row notes, with earlier theorem dependencies identified in the ancillary proofs. **Standard.**

2. **Choose a canonical extension if using the prefix route.** Among rows, minimize the full total minus the largest free chore, then delete a maximizing free chore in that row. The remaining prefix has least total in the chosen row, and its removed cost is at least the other free costs in that row. This permits the explicit lower bounds \(x_0\ge c_{03},x_1\ge c_{11},x_2\ge c_{22}\). Source: extension-method Section 6. **The point.**

3. **Translate every allocation into exact box conditions.** Each literal comparison has ninth-coordinate coefficient \(-1\), 0, or 1. The allocation's valid extension set is therefore a closed box, with constant prefix conditions. Source: extension-method Sections 1–2. **Routine.**

4. **Certify a symbolic box cover on a prefix region.** Exact endpoint incompatibilities make simultaneous failure of all selected allocations propositionally impossible. Nonnegative rational coefficient identities justify every compressed premise. The independent checker verifies literal deletions, identities, and exhaustive Boolean branching. There are 641 checked archived certificates, of which 341 have the explicit restricted extension domain. Source: extension-method Sections 2–3 and prefix audit receipt. **The point.**

5. **Alternatively, eliminate the entire first row.** For an allocation set \(K\), show that every allowed first row makes at least one member of \(K\) EFX for agent 0. Requiring every member of \(K\) to be EFX for agents 1 and 2 then produces a sufficient two-row region. Source: first-row-elimination note, “Allocation predicates and a sufficient region.” **The point.**

6. **Supply exact first-row guarantees.** For 3,238 singleton seeds, upper-rank threshold counts establish ordinal domination over all 28 allowed full orders. For 1,048 paired seeds, each of four joint failure possibilities has a nonnegative rational contradiction in the nine positive gap coordinates. For all 501 distinct nonordinal cores in the latest frozen checkpoint, every selection of strict failure rows has an exact nonnegative linear alternative. Every learned clause used in this checkpoint therefore has a checked first-row guarantee. Source: first-row-elimination note, core audit receipts, and the final outer checkpoint audit. **The point.**

7. **Compress each two-row region without changing its meaning.** A retained coefficient vector dominates a discarded vector whenever their difference has nonpositive total and nonpositive nonminimum coordinates. Decomposing the valuation into its minimum and nonnegative surpluses proves the implication. The retained conjunction is a subset of the original one, giving equivalence. Source: compression audit and consolidated-review Section 3.5. **Routine.**

8. **Close the outer coverage obligation.** The prefix outer formula excludes all certified prefix regions; the first-row outer formula excludes all certified two-row regions. A sound input-bound UNSAT proof, with every local premise certified, would close the corresponding canonical search. No such global proof is presently available. Source: both method notes' global search obligations. **Unresolved load-bearing step.**

9. **A separate route gives a much smaller sufficient finite domain.** Assign each selected failed comparison to its evaluating row. Each row is an independent nine-variable system with coefficient support at most seven. A vertex argument and Cramer's rule give positive integer representatives with every cost at most \(\lfloor8^{9/2}\rfloor=11,585\); their row minima may differ. Dividing by those minima gives a bounded real formulation with minima one, costs at most 11,585, and selected row-local failure margins at least \(1/11585\). Multiplication by 11,585 gives the equivalent real formulation with common minimum 11,585, upper bound 134,212,225, and unit margins. These complete search reductions have not been exhausted. Source: [row_local_integer_bound.md](../exact_search/row_local_integer_bound.md). **Standard method with a load-bearing row decomposition.**

## Components and reuse

The box certificate implication applies whenever an allocation predicate depends separately and linearly on each extension coordinate with coefficient in \(\{-1,0,1\}\). Its usefulness is broader than the sampled prefixes. The first-row implication uses only a product domain and a finite allocation family, so it is also reusable. The minimum-plus-surplus compression rule is a general elementary dominance certificate on a cone. The specialized integer bound provides a complete domain by preserving every allocation's chosen witness in its own row. The earlier larger bound remains valid when common integer minima are required; the determinant method itself is not presented as new.

## Prior work

The preceding package identifies the shared-minimum insertion argument, generic perturbation, and known eight-chore theorem in its primary-source record. The extension and finite-bound notes explicitly disclaim priority for standard certificate and determinant techniques. This resumed review did not repeat the literature search and makes no new novelty finding.

## Verification status

The preserved receipts establish exact local checks; the resumption hash audit confirms their historical inputs at its recorded time. The raw prefix snapshot's 24 nonstandard model-converter commands were removed in a portable copy with otherwise identical parsed assertions. The first-row checker was repaired to reject floating coefficient rows, which had allowed an adversarial underflow certificate; all legitimate archived certificate files passed the repaired checker and nine mutations failed. This resumed verification added 392 core certificates using the same unchanged exact checker and checked all 1,048 paired seeds, including five additional mutation controls.

The archived prefix formula has 31 base assertions and 641 certified region-complement clauses. The latest immutable row-elimination checkpoint, independently audited at 20:54:20 UTC on 7 October 2026, has exactly **18 base assertions and 4,787 learned clauses**: 3,238 singleton seeds, 1,048 paired seeds, and 501 distinct nonordinal core regions. All 92,003 raw other-row atoms compress soundly to 42,858 retained atoms, and every actual learned assertion is bound to its locally certified region. The 501 core certificates contain 5,616 exhaustive branch records; the paired seeds contain 4,192 more.

The frozen outer file has SHA-256 7580e516bbb0d3ae4a7098dfc35984acaa982ea4284b1fc5396596e63d74edbb. Later live search records are outside this audit. There is no unresolved local-certificate premise for this frozen formula, but its global coverage obligation remains unresolved. The audit did not run a solver or establish UNSAT, and no full counterexample has been certified.
