# Allocation-core minimization and batched region learning

This note proves the additional inference rules used by
`row_elimination_cegis_batched.py`. It does not assert that the regions cover
the complete canonical domain. The ordinary nine-chore EFX question remains
unresolved unless a separate global coverage proof or an exactly verified
counterexample is obtained.

## 1. A certified allocation core gives a sufficient region

Let \(D_0\) be the fixed canonical domain of the first agent's costs. For a
complete labelled allocation \(A\), let \(G_i(A)\) denote all of agent \(i\)'s
literal EFX inequalities for that allocation:

\[
c_i(A_i\setminus\{g\})\le c_i(A_j)
\qquad(g\in A_i,\ j\ne i).
\]

A finite set \(K\) of allocations is a first-row covering core when

\[
D_0\subseteq\bigcup_{A\in K}G_0(A).
\]

Define its region in the other two cost rows by

\[
R_K=\bigcap_{A\in K}\bigl(G_1(A)\cap G_2(A)\bigr).
\]

For every pair of rows in \(R_K\), and for every first row in \(D_0\), at least
one allocation in \(K\) is EFX for all three agents. Indeed, the core property
selects an allocation satisfying agent 0, while every allocation in the core
satisfies agents 1 and 2 throughout \(R_K\). Consequently, a canonical
counterexample must lie outside every such certified region.

The regions are intersections of homogeneous linear halfspaces. Recorded
coefficient-dominance certificates justify removing redundant halfspaces
under the other agents' pinned-minimum domains; the compression does not
change the region within those domains.

## 2. Smaller covering cores produce broader regions

Suppose \(K'\subseteq K\), and \(K'\) is itself a certified first-row covering
core. Then

\[
R_K\subseteq R_{K'}.
\]

Every EFX inequality attached to an allocation in \(K'\) already occurs among
the inequalities for \(K\). Thus membership in the original region implies
membership in the smaller core's region. A certificate for \(K'\), together
with exact allocation-set inclusion, also proves the original core's local
guarantee. The original certificate need not be expanded into all its own
failure branches.

If exclusions of both regions occur in the outer formula, the exclusion of
\(R_K\) is redundant: the complement of \(R_{K'}\) is contained in the
complement of \(R_K\). This justifies retaining inclusion-minimal allocation
cores on restart. The restart manifest preserves the omitted source, the
retained source, and their allocation IDs, so each inclusion can be checked
directly.

For a fallback core returned by an inner solver, deletion minimization tests

\[
D_0\ \wedge\ \bigwedge_{A\in K'}\neg G_0(A).
\]

An UNSAT result permits that smaller core to be retained. An unknown result
does not permit a deletion. The subsequently generated exact rational
alternative certificate proves the retained core independently of the
minimization solver.

## 3. Several verified regions may be learned from one model

Let \(K_1,\ldots,K_b\) be covering cores whose other-row regions contain the
current sampled pair of cost rows. Every exclusion \(\neg R_{K_j}\) is valid
for a counterexample, so all \(b\) exclusions may be added simultaneously.
Each core keeps its own literal formula, exact certificate, region record,
and file hash. Batch selection has no role in the soundness argument.

There is a second conservative redundancy rule. Let \(P_K\) be the set of
retained linear predicates defining a region. If
\(P_{K_1}\subseteq P_{K_2}\), then
\(R_{K_2}\subseteq R_{K_1}\). Therefore the second, narrower region can be
omitted when the first is already selected. Equality of the predicate sets
also permits deduplication. The implementation uses this literal set test;
it does not assume that all semantic containments have been found.

Choosing small predicate sets and diverse regions is a search heuristic.
Neither the number of learned regions nor the number of sampled models
measures the fraction of the unbounded domain already covered.

## 4. Exact generic perturbation preserves the sampled model's exclusions

The outer domain contains separate homogeneous row predicates. Clear the
denominators in each model row to obtain a positive integer vector \(c\).
Keep the pinned minimum's perturbation equal to zero; assign the eight
remaining coordinates the directions
\(1,3,\ldots,3^7\), whose sum is \(3280\). Set

\[
c'=3281c+d.
\]

Every literal EFX comparison has coefficients in \(\{-1,0,1\}\). For any
such coefficient vector \(v\),

\[
|v\cdot d|\le3280.
\]

Thus a nonzero integer value of \(v\cdot c\) keeps its sign after the
perturbation. In particular, the strictly positive predicate witnessing
failure of each previously excluded region remains strictly positive.
The new sample therefore remains outside every previously learned region.

The perturbation also makes all subset sums distinct. If a difference of
two subset sums was already nonzero, sign preservation applies. If its old
value was zero, its nonminimum directions give a nonzero balanced ternary
sum unless all their coefficients vanish. In that last case only the pinned
positive cost could remain, which cannot have had value zero. Hence every
nontrivial subset-sum difference becomes nonzero.

Pinned-minimum inequalities remain strict. Independently normalizing the
new rows back to minimum one preserves all their homogeneous predicates.
This argument introduces no numerical upper bound; a separately bounded
search would need to check that its perturbation also stays inside its own
stated domain.

## 5. What would finish the argument

A certified contradiction of the complete outer formula would prove that
every canonical pair of remaining rows lies in a verified sufficient
region. Combined with the established canonical reduction, this would
settle the nine-chore existence question. A finite list of locally valid
regions, without that global contradiction, does not do so. A solver
timeout, interruption, or ordinary deadline is not a mathematical verdict.
