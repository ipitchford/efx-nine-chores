# Independent review: zero minima, finite bounds, and positive lifting

**The normalization and the bounds below are sound as counterexample-existence reductions. They do not establish either a counterexample or universal EFX existence.** This review concerns the literal requirement that every owned chore may be deleted, including a zero-cost chore. Its exact arithmetic and targeted semantic controls are recorded in [zero_minimum_normalization_audit.json](zero_minimum_normalization_audit.json).

## 1. Lowering one minimum coordinate in each row

For a nonempty owned bundle \(S\), the largest residual cost over all allowed deletions is
\[
W_i(S)=\max_{g\in S}c_i(S\setminus\{g\})
      =c_i(S)-\min_{g\in S}c_i(g).
\]
Let \(e_i\) be a global minimum of row \(i\). Replace only \(c_i(e_i)\) by zero, keeping the other entries unchanged. If \(e_i\notin S\), then \(W_i(S)\) is unchanged. If \(e_i\in S\), the bundle total and its minimum each decrease by exactly \(c_i(e_i)\), so \(W_i(S)\) is again unchanged. Every comparison-bundle total either stays unchanged or decreases. It follows that any allocation satisfying EFX after the replacement also satisfied EFX before it.

Consequently a counterexample remains a counterexample after the replacement. Applying this separately in each row is valid, because EFX comparisons by agent \(i\) use only row \(i\). Empty owned bundles contribute no deletion comparisons.

The usual finite-strict-failure perturbation first gives a positive counterexample whose costs within each row are all distinct. The replacement then leaves exactly one zero in each row and eight positive, mutually distinct other entries. A bundle with at least two chores has a deletion leaving positive cost when there is at most one zero in the evaluating row. For nine chores and three agents, an allocation with an empty bundle therefore fails EFX by comparison with that empty bundle. The finite search may restrict to surjective allocations.

The numerical bound itself does not require the three zero positions to be different. Using the canonical positions \(e_i=i\) additionally retains the existing distinct-minimum reduction, whose dependencies are the earlier eight-chore result and shared-minimum insertion lemma. Lowering the selected coordinates preserves those distinct positions.

## 2. An independent integer representative with bound 3,831

Select one strict failed comparison for every surjective allocation of a zero-minimum counterexample. Split the selected inequalities by their evaluating row. A row now has eight positive variables, with its one zero fixed. Include strict positivity and the complete strict order of its positive entries. These conditions are all homogeneous and row-local.

For a surjective allocation, a failed comparison has support at most
\[
|A_i|-1+|A_j|=9-|A_k|-1\le7.
\]
Fixing a zero coordinate can only decrease this support. Positivity and ordering rows have supports one and two. Thus every coefficient row has entries in \(\{-1,0,1\}\) and support at most seven.

Because the selected system is finite and strictly feasible, independently dilate each row so that every selected form is at least one. The polyhedron \(Ax\ge\mathbf1\) is nonempty and contains the constraints \(x_g\ge1\). Minimizing the sum of its coordinates gives a nonempty compact optimal face, hence a vertex. At that vertex choose an invertible active \(8\times8\) integer matrix \(D\).

For coordinate \(g\), Cramer's rule uses \(D_g\), obtained by replacing column \(g\) with ones. Since \(D\) is invertible, its original column \(g\) is nonzero in at least one row. In that row, replacing its \(\pm1\) by one leaves its squared norm at most seven. In each of the other seven rows the squared norm is at most eight. Hadamard's inequality therefore gives
\[
|\det D_g|^2\le7\cdot8^7=14,680,064.
\]
Multiplying the vertex by \(|\det D|\) yields a positive integer row with every chosen strict form still at least one and every coordinate at most
\[
B_9^0=\lfloor\sqrt{7\cdot8^7}\rfloor=\boxed{3831}.
\]
Indeed, \(3831^2=14,676,561\) and \(3832^2=14,684,224\). The rows may be cleared independently; every allocation retains its designated failure in its designated row. Reassembling the three rows gives the claimed zero-minimum integer counterexample.

For three agents and \(m\ge4\) chores the same calculation, with \(m-1\) positive variables and support at most \(m-2\), gives
\[
B_m^0=\left\lfloor\sqrt{(m-2)(m-1)^{m-2}}\right\rfloor.
\]
In particular \(B_8^0=840\). These bounds are derived sufficient bounds, not experimentally exhausted grids.

## 3. A formulation with 21 free real variables

With zeros canonically pinned at columns \(0,1,2\), columns \((1,0,0)\) give fixed positive reference entries for rows \((0,1,2)\). Divide each integer row by its reference entry \(a_i\in[1,B_9^0]\). The reference becomes one, every positive entry lies between \(1/B_9^0\) and \(B_9^0\), and every selected strict integer comparison or strict order gap becomes at least \(1/a_i\ge1/B_9^0\).

Thus a complete counterexample search can use three fixed zeros, three fixed positive references, and 21 remaining real variables, with a disjunction of margin-at-least-\(1/B_9^0\) failed comparisons for every surjective allocation. Any satisfying matrix is itself a counterexample; conversely a counterexample has such a representative under the stated canonicalization. This is an existence equivalence, not a claim that every original normalized matrix obeys the bounded margins.

An integer bit-vector formulation instead has 24 positive bounded entries and three fixed zeros. Twelve bits hold an entry at most 3,831. Fifteen unsigned bits hold any row subset sum because a row has only eight nonzero entries and
\[
8\cdot3831=30,648<2^{15}.
\]
The fixed-zero fact is essential when using that width. Costs must be extended to the sum width before addition, and all comparisons must use unsigned arithmetic.

## 4. Lifting to positive integer costs with common minimum one

Start from the bounded integer zero-minimum counterexample. For each allocation choose a failing agent and target for its largest owned-deletion residual. Its failure margin is an integer at least one. Raise each row's one zero to \(1/2\). Since all its other entries are at least one, its largest owned-deletion residual is unchanged: if the raised coordinate is owned, the owned minimum and total both rise by \(1/2\); otherwise neither changes. A target-bundle total increases by at most \(1/2\).

Each selected failure therefore remains at least \(1/2\). Multiplying all rows by two yields a positive integer counterexample with each pinned minimum exactly one, all nonminimum costs even and in \([2,7662]\), and all designated failure margins at least one. Nonminimum strict orders and the pinned positions are preserved.

This supplies a stronger common-minimum normalization than the earlier independent positive-row bound: counterexample existence implies a positive integer counterexample with common minimum one and maximum cost 7,662. The zero-minimum formulation still uses fewer free coordinates. Previously frozen searches with other bounds remain exactly as recorded.

## 5. Definition-sensitive controls and limits

The accompanying script checks all 511 nonempty owned-bundle shapes for each of three fixture rows, verifying that the maximum deletion residual is unchanged by lowering the minimum and is positive for every bundle of size at least two. It checks the bounds and bit widths using exact integers.

A separate fixture has one zero and eight distinct positive entries in each row and obeys the canonical first-row order. The allocation \((0,1,2,0,1,1,2,2,2)\) fails literal EFX only when agent zero deletes its owned zero: the two margins are 176 and 177. A deliberately incorrect predicate that skips owned zero-cost deletions accepts this allocation. The fixture is a regression control for the definition, not a matrix without any EFX allocation.

These finite controls support implementation review. The general arguments above justify the reductions. No solver result, exhaustive bounded search, universal EFX theorem, or main-target counterexample is supplied by this review.
