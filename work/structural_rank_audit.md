# Audit of the rank and dominance encoding

Source under audit: `economics_problem2/src/strict_lra.py`, `build(..., rank_case=(r1,r2), all_trims=False, dominance=True, cuts='none')`, and its caller `rank_run.py`. The exact source hash and finite predicate checks are recorded separately in `structural_rank_audit.json`.

## Mathematical justification

All cost entries are strictly positive. Every agent i has unique cheapest chore i. When rank cases are used, row 0 has a complete strict item order. All compared sets are an agent's own bundle with one item removed and a different agent's bundle; hence they are disjoint.

`order_implies_less(L,R,i)` uses three sufficient tests for `c_i(L)<c_i(R)`:

1. L is empty and R nonempty. Positivity gives the strict inequality.
2. L is the singleton containing agent i's global minimum and R is nonempty. Because the sets are disjoint, every item in R is strictly dearer than that minimum. Positivity of extra items preserves strictness.
3. For row 0's full order, `|L|<=|R|` and the ranks of L sorted from greatest to least are each strictly less than the corresponding initial ranks of R sorted the same way. Match those pairs. Every matched item in L is strictly cheaper than its counterpart in R. Summing proves strict inequality; unmatched items in R have positive costs.

The test is sufficient, rather than necessary; missing an available comparison only enlarges the search formula. If `c_i(R)<c_i(L)`, the failure atom `c_i(L)>c_i(R)` is always true, so the entire allocation-failure disjunction is a tautology and may be dropped. If `c_i(L)<c_i(R)`, that failure atom is always false and may be dropped. This justifies `automatically_bad` and `dominated_atoms` in their respective directions.

For a fixed own bundle, the largest residual comes from removing a least-cost owned item. If an agent owns its pinned global minimum, only that trim is needed. Otherwise row 0's full order identifies the unique least-cost owned item, so only that trim is needed. Other agents retain all their trims when they do not own their global minimum. Thus `all_trims=False` preserves the exact allocation-failure predicate in the rank-case domain.

An empty bundle cannot occur in an EFX allocation of nine strictly positive chores among three agents. The remaining two agents jointly own nine chores, so one owns at least two. Its residual after deleting a cheapest owned chore is positive and exceeds the empty bundle's zero cost. Therefore omitting allocations with an empty bundle is sound.

## Why 28 cases cover the generic domain

For a potential nine-chore counterexample, the known eight-chore result and minimum-insertion lemma first rule out shared cheapest chores. Since each allocation has a strictly positive failure witness, a sufficiently small perturbation preserves failure for all finitely many allocations and makes all costs positive and rowwise distinct. Relabel the three distinct minima to columns 0,1,2 and their agents to 0,1,2.

Keep agent 0 fixed. Simultaneously swapping agents 1 and 2 and their pinned minimum columns preserves the allocation problem; use this swap to make `c_0(1)<c_0(2)`. Sort the six free chores by row 0's costs and label them in the `ordered` sequence used by the program (descending labels 8,...,3 by default, but increasing costs). The two pinned chores 1 and 2 occupy a unique pair of positions `0<=r1<r2<=7` among the eight nonminimum row-0 positions. There are `binom(8,2)=28` possibilities. The builder fills all remaining positions with the six free chores in their fixed order, then prepends chore 0.

Hence every generic disjoint-minimum counterexample lies, after permitted symmetries, in one of these 28 domains. Exact ties are handled by the initial strict-witness perturbation argument, not by pretending that the strict cones individually contain tie boundaries.

## Scope of the finite audit

The audit script does not reimplement the pruned formula and compare it with itself. It wraps the actual source solver to record each asserted allocation clause together with its current allocation. It decodes those actual returned arithmetic expressions into integer coefficient vectors. It then compares their truth values with an independent direct EFX calculation for all 19,683 allocations on three exact canonical matrices in each of four extreme/interior rank cases. Missing source clauses are treated as true, so both automatically bad allocations and omitted empty-bundle allocations are checked. Source counters must reconcile exactly with the recorded clauses and the number of empty allocations.

These finite checks detect implementation errors on the inspected matrices. The preceding argument supplies the universal justification for the reductions; the finite checks themselves are not a proof of the nine-chore existence theorem.
