# Lowering each agent's cheapest chore to zero

**Status.** This is a complete reduction of the counterexample search, independently reviewed in this session. It does not settle nine-chore EFX existence. Earlier positive-minimum formulas, bounds, proofs, and receipts are unchanged. No novelty claim is made.

## 1. The zero-minimum lemma

Let costs be additive and nonnegative. For every agent \(i\), choose a globally cheapest chore \(e_i\). Form a new row \(d_i\) by replacing just \(c_i(e_i)\) with zero and keeping every other entry of that row unchanged. This operation is **not subtraction from the whole row**.

For a nonempty owned bundle \(S\), define its worst deletion residual by
\[
r_i^c(S)=\max_{g\in S}c_i(S\setminus\{g\})
=c_i(S)-\min_{g\in S}c_i(g).
\]
Set the residual of the empty bundle to zero. The literal EFX definition includes deletion of a zero-cost owned chore, so this formula also holds when the minimum is zero.

We have \(r_i^d(S)=r_i^c(S)\) for every bundle \(S\). If \(e_i\notin S\), no entry in \(S\) changes. If \(e_i\in S\), both its total and its minimum decrease by exactly \(c_i(e_i)\). This remains true when the original minimum is tied. Also \(d_i(T)\le c_i(T)\) for every comparison bundle \(T\).

Consequently, if an allocation \(A\) is EFX under \(d\), then for every \(i\ne j\),
\[
r_i^c(A_i)=r_i^d(A_i)\le d_i(A_j)\le c_i(A_j),
\]
so it is EFX under \(c\). Thus
\[
\boxed{\operatorname{EFX}(d)\subseteq\operatorname{EFX}(c).}
\]
Every counterexample remains a counterexample after this operation is applied independently to all rows. The three chosen minima need not be the same chore or distinct chores for this lemma.

## 2. Positive generic costs and distinct pinned zero minima

If a nonnegative instance is a counterexample, select one strictly failed literal EFX comparison for each of the finitely many complete allocations. A sufficiently small perturbation preserves every selected strict margin and makes each row positive with pairwise distinct entries. Apply the zero-minimum lemma to this perturbed counterexample. Each resulting row has exactly one zero; all its other costs remain positive and pairwise distinct.

The zero-minimum argument itself has no dependency on an eight-chore theorem. To restrict a nine-chore search to three **distinct** minimum chores, use the separately documented shared-minimum insertion reduction and the known eight-chore theorem. The same canonical reduction for an eight-chore calibration invokes the corresponding seven-chore baseline. These dependencies are recorded in [ancillary_proofs.md](../../docs/ancillary_proofs.md). They are not supplied by the present lemma.

After the usual permitted relabelings, pin the zero minima at \(c_i(i)=0\) for \(i=0,1,2\), require \(c_0(1)<c_0(2)\), and put the free columns \(3,\ldots,m-1\) in decreasing order in row zero. There is no comparison of totals between rows.

## 3. A search in only \(3(m-2)\) free real variables

Fix one positive reference entry in each row, for example reference columns \((1,0,0)\). Because these columns differ from the pinned zero minimum, their costs are positive. Independently divide each entire row by its reference cost. Positive row scaling preserves every EFX comparison. We may therefore require
\[
c_i(i)=0,\qquad c_0(1)=c_1(0)=c_2(0)=1.
\]

There are \(3(m-2)\) remaining real variables: **18 for eight chores and 21 for nine chores**. Every remaining off-minimum entry is strictly positive. The canonical row-zero inequalities remain strict. This normalization does not impose a common scale on distinct agents; each reference is set independently.

For every allocation with three nonempty bundles, require the disjunction of its strictly failed literal EFX comparisons. All coefficients remain linear because the six fixed values are constants. The existing minimum-trim pruning is valid: a worst deletion removes a cheapest owned chore, including the pinned zero when it belongs to the owned bundle. The frozen source allocation clauses are reused with exact substitutions, and the new domain is rebuilt explicitly.

An allocation with an empty bundle fails automatically when \(m\ge4\). At most two bundles receive the chores, so some owned bundle has at least two chores. Its owner's row has at most one zero, hence there is a deletion leaving a positive residual, which exceeds the empty bundle's cost. This argument asserts existence of a failing deletion; it does not assert that every deletion fails.

The resulting formula is equisatisfiable with the unrestricted counterexample question, conditional only on the separately stated canonical minimum-chore reduction. No finite bound or uniform positive failure margin is imposed on this strict real formula.

## 4. A smaller complete integer representative bound

For three agents and \(m\ge4\), a counterexample has a representative with one zero in each row and every other entry a positive integer at most
\[
\boxed{Z_m=\left\lfloor\sqrt{(m-2)(m-1)^{m-2}}\right\rfloor.}
\]
The positions of the zero minima and the complete strict order of the positive entries may be preserved from the zero-minimum counterexample above.

**Proof.** Select one strict failed deletion comparison for every allocation with three nonempty bundles. Group these inequalities by their evaluating agent. After its zero coordinate is removed, a row has \(d=m-1\) positive variables. Each selected failure has coefficients in \(\{-1,0,1\}\) and support at most \(m-2\): before deleting the zero coordinate, its support is
\[
|A_i|-1+|A_j|=m-|A_k|-1\le m-2.
\]
Removing a coordinate cannot increase support. Add positivity of every free coordinate and adjacent inequalities imposing the desired complete strict order. Their supports are one and two, also at most \(m-2\).

This finite homogeneous row-local system \(Ax>0\) is feasible. Scale its row independently to obtain \(Ax\ge\mathbf1\). Positivity constraints imply \(x_g\ge1\), so minimizing the sum of coordinates over the feasible polyhedron has a nonempty compact minimizing face. A vertex of that face is a vertex of the polyhedron. Choose \(d\) independent active constraints and write \(Dv=\mathbf1\), with nonsingular integer \(D\).

For coordinate \(g\), replace column \(g\) by ones to obtain \(D_g\). Each row of \(D\) has squared norm at most \(m-2\). A replacement raises that squared norm by at most one, so every row of \(D_g\) has squared norm at most \(m-1\). Nonsingularity of \(D\) means its replaced column is nonzero in at least one row. In that row the replacement changes a coefficient of magnitude one to one, leaving its squared norm at most \(m-2\). Hence Hadamard's inequality gives
\[
|\det D_g|^2\le(m-2)(m-1)^{d-1}
=(m-2)(m-1)^{m-2}.
\]

Let \(q=|\det D|\ge1\) and \(y=qv\). Cramer's rule makes each coordinate of \(y\) an integer equal in magnitude to \(\det D_g\). Positivity gives \(1\le y_g\le Z_m\), and \(Ay\ge q\mathbf1\ge\mathbf1\). Thus every selected failure, positivity condition, and chosen order is preserved. Restore the zero coordinate and perform this construction independently for all three rows. Every nonempty-bundle allocation keeps its selected failure; every empty-bundle allocation fails by the argument above. This proves the bound. \(\square\)

For nine chores,
\[
3831^2=14\,676\,561\le7\cdot8^7=14\,680\,064
<14\,684\,224=3832^2.
\]
Thus \(Z_9=3831\). There are 24 positive integer cost variables, plus three fixed zero minima. Each cost fits in 12 bits. An entire row sums to at most \(8\cdot3831=30\,648<2^{15}\), so unsigned sums need 15 bits. This bit-width observation uses the fixed zero: the coarser bound \(9\cdot3831\) would not fit in 15 bits.

For eight chores, \(Z_8=\lfloor\sqrt{6\cdot7^6}\rfloor=840\). The strict reference-normalized real formulas do **not** impose integrality or these bounds. A later finite integer formula would keep the positive reference entries variable; integer rows need not have reference cost one.

## 5. Lifting to positive integer costs with common minimum exactly one

The zero-minimum representative implies a stronger positive-cost normalization than the earlier independent-row bound. For nine chores, a counterexample has a representative with
\[
\boxed{c_i(i)=1,\qquad c_i(g)\in\{2,4,\ldots,7662\}\quad(g\ne i).}
\]
All selected allocation failures may have integer margin at least one, and the canonical strict order may be retained. Distinct pinned minimum positions again invoke the separately stated canonical reduction.

**Proof.** Start with the zero-minimum integer representative \(z\), whose positive entries are at least one and at most 3831. For every surjective allocation, choose a strongest failed comparison: delete a cheapest owned chore. Its failure margin is a positive integer, hence at least one. Raise each row's single zero to \(1/2\), keeping the other entries unchanged, to obtain \(w\).

Every worst owned-bundle residual is unchanged. If the bundle excludes the former zero, no entry changes. If it includes that chore, the chore remains its unique cheapest entry because every other cost is at least one; its sum and minimum both increase by \(1/2\). A comparison bundle's cost increases by at most \(1/2\). Thus every selected failure has margin at least \(1-1/2=1/2\) under \(w\). Multiplying all rows by two produces positive integer costs with minimum exactly one, even nonminimum entries between two and 7662, and every selected failure margin at least one. Allocations with empty bundles continue to fail by positivity. \(\square\)

More generally the positive upper bound is \(2Z_m\): 1680 for eight chores and 7662 for nine. The lifting may be applied separately to independently scaled integer rows; it imposes the common minimum only after obtaining the zero-minimum representatives.

This also justifies an **existence-equivalent bounded real formula** with minima fixed to one, nonminimum costs in \([2,7662]\), retained canonical order gaps at least two, and at least one failed literal EFX comparison of margin at least one per surjective allocation. The real formula need not impose evenness or integrality: the forward implication supplies an even integer witness, while any real model still has strict failure for every allocation. It is not a claim that an arbitrary original counterexample already has these normalized gaps. No prior frozen input is modified by this corollary.

The lifting was independently reviewed in [zero_minimum_independent_review.md](../verification/zero_minimum_independent_review.md). The ongoing reference-normalized strict formula continues to use zero minima; it does not use this additional positive-cost corollary.

## 6. What remains to complete the search

The lemma, finite bound, and reference normalization are exact reductions. They do not show that the resulting counterexample formula is satisfiable or unsatisfiable. A SAT model must be converted to exact costs and replayed over all \(3^9=19,683\) complete allocations, explicitly including zero deletions. An UNSAT result must be paired with a faithful encoding argument and, for an independently checked computational proof, a checked proof object.

The finite literal and formula controls are recorded in `zero_minimum_reduction_audit.json` and `zero_minimum{8,9}_reference_semantic_audit.json`. They compare actual serialized clauses with a separate literal checker. Such finite audits supplement the mathematical argument; they do not replace it or exhaust the real-valued domain. Earlier searches using the 11,585 positive-cost bound remain exactly the searches their receipts describe.
