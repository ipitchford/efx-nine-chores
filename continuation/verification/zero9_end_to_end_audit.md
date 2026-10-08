# End-to-end audit of the full nine-chore UNSAT result

**Conclusion.** No missing mathematical hypothesis was identified in the chain from an arbitrary nonnegative additive nine-chore counterexample to the exact formula that returned UNSAT. Conditional on the soundness of that recorded UNSAT verdict and the cited eight-chore existence theorem, the chain proves complete EFX existence for three agents and nine chores. The decisive run did not generate a proof object, so independently checking the UNSAT derivation remains a separate unresolved obligation. This is not a claim that an external certificate has already passed.

The input is `continuation/exact_search/zero_minimum9_reference_strict.smt2`, SHA-256:

```
65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b
```

Z3 returned `unsat` after **591.6702368799997 seconds** in the recorded check. The supervisor observed normal exit with code zero. The mathematical result was recorded explicitly before any post-processing; it was not inferred from an exit code, timeout, lost process, or missing output. Proof generation was disabled, and the receipt states that no independently checked proof exists. The exact run and the earlier complete independent formula audit are bound in `zero9_end_to_end_binding.json`.

## 1. Target and exact failure predicates

Let the three agents be (0,1,2), and let the nine chores be (0,\ldots,8). Costs are arbitrary nonnegative reals, additive within each evaluating row. A complete labelled allocation is a partition (A=(A_0,A_1,A_2)); empty bundles are allowed. EFX requires

\[
c_i(A_i\setminus\{g\})\le c_i(A_j)
\quad(i\ne j,\ g\in A_i).
\]

The deletion quantifier includes an owned chore of zero cost. Both sides use the evaluating agent's row. For a nonempty bundle (S), define

\[
r_i(S)=c_i(S)-\min_{g\in S}c_i(g),
\]

and set (r_i(\varnothing)=0). Nonnegativity makes the residual formulation equivalent to the literal definition even for empty owned bundles. A failure is a **strictly positive** linear form

\[
F_{A,i,j,g}(C)=\sum_{h\in A_i\setminus\{g\}}c_{ih}
              -\sum_{h\in A_j}c_{ih}>0.
\]

Comparisons with (j=i) cannot fail, since removing a nonnegative-cost chore cannot increase its bundle's cost.

## 2. Strict positive counterexamples suffice

Suppose an arbitrary nonnegative matrix has no EFX allocation. There are only (3^9=19,683) complete labelled allocations. Choose one strictly failed literal for each allocation. All those strict inequalities hold on a sufficiently small open neighborhood of the matrix, because there are finitely many continuous linear forms and their chosen margins are positive.

That neighborhood contains a matrix with every entry positive and with all entries within each row distinct: first move slightly into the positive orthant and then avoid the finitely many equality hyperplanes. Every selected failure persists, so the new matrix is still a counterexample. This handles boundary zeros without assuming that the original matrix had positive rows or unique minima. It is an existence reduction, not an assertion that every perturbation works.

## 3. A shared minimum is impossible in a positive counterexample

The required external mathematical baseline is Zhang's eight-chore EFX theorem, stated for nonnegative additive costs with the same literal deletion convention. Its Theorem 2 and Definition 1 are in [arXiv:2609.10585v2](https://arxiv.org/html/2609.10585v2). For the present argument only its restriction to positive costs is needed.

The insertion fact used with that theorem is the following: if a chore (e) is globally cheapest for two of the three agents, any EFX allocation of the other chores can be extended, with possible reassignment of bundles, to an EFX allocation including (e). This is the three-agent instance of Kobayashi–Mahara–Sakamoto's insertion argument, Lemma 4.2 in [arXiv:2305.04168](https://arxiv.org/abs/2305.04168). A direct argument confirms that no identical-ordering hypothesis is needed here.

Label the two agents for whom (e) is cheapest as 1 and 2. From each of these agents draw an arc to the owner of one of its minimum-cost old bundles. Agent 0 has no outgoing arc. If there is a directed cycle, rotate the bundles around that cycle so that every cycle agent receives a minimum-cost bundle. Add (e) to one cycle agent's new bundle (B). Its new maximum deletion residual is (c_i(B)), because (e) is cheapest, and that old bundle total was at most every other old bundle total. The identity also holds when (B) was empty. Thus the recipient is EFX; all other agents retain EFX because bundle reassignment gave changed agents minimum-cost bundles and only one comparison bundle subsequently increased.

If the graph is acyclic, all directed paths end at agent 0. First add (e) to agent 0's bundle. If that agent remains EFX, the allocation is complete. Otherwise one of its minimum-cost bundles in the augmented collection is an unchanged bundle (A_j), with (j\ne0): the augmented owned bundle cannot be minimum-cost if its deletion residual exceeds another bundle's total. Follow the path from (j) to 0. Give (A_j) to agent 0, move each intermediate path agent to the old minimum-cost bundle named by its arc, and give the augmented old bundle (A_0\cup\{e\}) to the last path agent. Agent 0 and the intermediate agents receive minimum-cost bundles in the augmented collection. The last agent regarded old (A_0) as minimum-cost, and its new residual is exactly that old total. Agents outside the path retain their bundles while the collection changes only by adding a nonnegative chore. All EFX inequalities therefore hold. Empty bundles and ties in chosen minimum bundles cause no exception.

Now, if a positive nine-chore counterexample had a shared cheapest chore, delete it, apply the eight-chore theorem, and apply this insertion fact. That would produce an EFX allocation, a contradiction. Consequently the positive generic counterexample has **three distinct unique minimum chores**. This reduction is applied before lowering minima to zero; it does not require an unstated zero-domain version of any source theorem.

## 4. Lower each selected minimum to zero

For each row (i), let (e_i) be its unique global minimum. Replace only (c_i(e_i)) by zero, leaving every other cost unchanged. If (e_i\notin S), the owned residual (r_i(S)) does not change. If (e_i\in S), the bundle sum and its minimum decrease by the same quantity, so the residual again does not change. Every target-bundle sum weakly decreases. Hence

\[
\operatorname{EFX}(C^{\mathrm{lowered}})
\subseteq \operatorname{EFX}(C).
\]

The lowered matrix is therefore still a counterexample. It has exactly one zero in each row, at the three distinct minimum chores; every other entry remains positive and rowwise distinct. This is a coordinatewise minimum operation, not subtraction of a constant from every entry in a row.

## 5. Canonical labels and positive reference normalization

Relabel the three distinct minimum chores as (0,1,2), with chore (i) the zero minimum for agent (i). Choose any agent to carry label 0. If necessary, swap agents 1 and 2 together with their minimum-chore labels, so that (c_{01}<c_{02}). The two costs are distinct and positive by construction. Sort the remaining six chore columns in decreasing order of agent 0's costs, obtaining

\[
c_{03}>c_{04}>c_{05}>c_{06}>c_{07}>c_{08}>0.
\]

These are simultaneous relabellings of agents and chores, so they give bijections of complete allocations and preserve the problem.

The entries (c_{01},c_{10},c_{20}) are all positive: none is its row's zero minimum. Divide row 0 by (c_{01}), row 1 by (c_{10}), and row 2 by (c_{20}). Positive independent row scaling preserves every EFX comparison because both sides use the same row. Thus one may impose

\[
c_{00}=c_{11}=c_{22}=0,
\qquad c_{01}=c_{10}=c_{20}=1.
\]

There remain exactly **21 free real variables**. The formula's domain consists of their 21 strict positivity assertions, (c_{02}>1), and the five strict successive free-column order comparisons: **27 assertions**. The six fixed values are substituted as constants, not declared as extra variables. The formula imposes no upper cost bound, no integrality, no comparison between row totals, no prescribed-agent envy-freeness, no second-minimum assumption, and no additional graph symmetry. The 3,831/7,662 bounds and subsequent proposed refinements are unnecessary for this UNSAT implication.

## 6. All omitted empty-bundle allocations fail on this domain

There are

\[
3^9-3\cdot2^9+3=18,150
\]

surjective allocations, so exactly **1,533** complete allocations have an empty bundle. If an allocation has an empty bundle, at most two bundles contain the nine chores, so some owned bundle has at least two chores. Its evaluating row has at most one zero. Choose a positive-cost owned chore (h), and remove a different owned chore (g). The remaining owned cost is at least (c_i(h)>0), whereas the empty target bundle costs zero. Thus this literal EFX comparison fails.

This is a universal argument on the actual formula domain, not a claim about arbitrary zero-cost matrices. The accompanying omitted-allocation certificate explicitly lists such a combinatorial witness for every one of the 1,533 omitted assignments. No allocation is discarded because it lacks a convenient bundle size, except through this stated proof.

## 7. Retained deletion clauses express every allocation failure

For a fixed owned bundle, a largest deletion residual is obtained by removing a cheapest owned chore. It therefore suffices in a failure disjunction to retain every chore that could be cheapest under the imposed partial order. The pinned row minimum is cheaper than all other entries. In row 0 the only additional known relations are (c_{01}<c_{02}) and the free-column chain; the other two rows have no additional ordering restriction.

Every actual cheapest owned chore is retained. If a omitted chore were a strict failure witness, deleting a cheaper owned chore would give an even larger residual, so a retained cheapest deletion also fails. Conversely every retained literal is an original EFX comparison. Owned bundles of size at most one cannot fail, because their deletion residual is zero and every target total is nonnegative. In particular, when the pinned zero is owned, deleting it is retained; this is not the convention that skips zero-cost deletions.

For each of the 18,150 surjective allocations the serialized formula asserts the disjunction of these strictly failed literals, evaluated with the six fixed substitutions. `audit_zero_minimum_formula.py` reconstructs the clauses independently of the encoder using only the standard library and exact integer affine coefficients. Its completed audit checked every declaration, every domain assertion, all allocation clauses in enumeration order, and all **191,104** retained literal positions, including **34,776** pinned-zero deletion positions. Repeated copies of the same literal do not change a disjunction. No sampled matrix evaluation is substituted for this full syntactic and affine reconstruction.

## 8. The resulting implication and the remaining trust obligation

Let (F_9) be the exact hash-pinned formula. The preceding steps show that every arbitrary nonnegative additive nine-chore counterexample would produce a real model of (F_9). Conversely, a real model of (F_9) gives a nonnegative matrix with no successful surjective allocation by its clauses and no successful nonsurjective allocation by Section 6. With the stated eight-chore baseline and relabelling reduction, the existence questions are equivalent.

Consequently,

\[
F_9\text{ is unsatisfiable}
\quad\Longrightarrow\quad
\text{every nonnegative additive three-agent nine-chore instance has complete EFX.}
\]

The recorded Z3 result supplies an **exact solver-supported resolution of the full target**, subject to the solver's soundness. It is not merely a failed search for a counterexample, a finite integer-grid search, or a partial family of sufficient regions. The existing local-region noncoverage witness does not contradict it: that witness supplied only two evaluating rows and no full counterexample.

For independently checked computational evidence, the remaining task is to obtain a proof of false bound to this exact input and check the derivation with the intended calculus, original assumptions, and global scope. The proof-free Z3 receipt alone cannot supply that object. A rerun that times out, exhausts memory, or fails during export does not alter the recorded UNSAT result; it also does not complete the independent certificate obligation. Handwritten reductions, the cited eight-chore theorem, the parser/audit programs, and the eventual checker/calculus remain explicit dependencies rather than an end-to-end proof-assistant development.
