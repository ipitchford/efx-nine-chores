# A derived finite integer bound for the nine-chore search

**Status.** This is a reduction of the unresolved nine-chore problem to a
finite domain. It is not an existence proof, a counterexample, or a report
that the finite domain has been exhausted. The determinant method is
standard; no novelty claim is made for that method or for its application
here. The specialised argument has been independently reviewed in this
research session; this is not a proof-assistant formalisation.

## Claim

A three-agent, nine-chore counterexample with nonnegative additive costs,
if one exists, has a counterexample representative whose costs are
**positive integers**, whose three row minima have a common value, and
whose every entry is at most

\[
B=\left\lfloor 8^{25/2}\right\rfloor
 =194\,368\,031\,998.
\]

The numerical bound does not require the minimum chores to be distinct.
For the nine-chore application, the known eight-chore theorem and the
matching insertion lemma exclude a counterexample in which two agents
share a cheapest chore. One may therefore additionally impose the
existing canonical labels: agent i has
chore i as its unique minimum; the six unpinned chores are sorted in
agent0's valuation; agent0 values pinned chore1 below pinned chore2; and
agent0 has the least total cost among the three rows after minimum
normalisation. These are relabellings of a bounded representative and do
not enlarge its entries.

## Proof

For each complete allocation of a hypothetical counterexample, select one
strict failed EFX comparison. A sufficiently small positive perturbation
preserves all these finitely many strict failures and makes every row's
item costs distinct. Thus a positive generic counterexample exists.

Let mu_i be the index of agent i's unique minimum, permitting the mu_i to
coincide. Scale row i by the reciprocal of that positive minimum. The row
minima are now all one. Independent positive row scaling preserves every
EFX comparison. In the canonical distinct-minimum case one simply has
mu_i=i after relabelling.

Use a single variable t for the three entries c_i(mu_i). The remaining 24 entries
are private variables, eight in each agent's row. There are therefore
d=25 variables. They are the coordinates of a vector x.

For each complete allocation with all three bundles nonempty, choose one
of the strict failures it has. Such a failure has the form

\[
 c_i(A_i\setminus\{g\})-c_i(A_j)>0.
\]

Its coefficient row has only entries in {-1,0,1}. Its nonzero support has
size

\[
 |A_i|-1+|A_j|=9-|A_k|-1\le7,
 \qquad \{i,j,k\}=\{0,1,2\}.
\]

The two compared sets are disjoint. Identifying the three pinned minima
with t does not merge two coefficients within this row: this comparison
uses only one agent's valuation, which contains the common-minimum
variable exactly once.

Add every coordinate positivity constraint, each strict pinned-minimum
inequality, and the complete strict order of all nine item costs in each
row of the chosen generic starting counterexample. The last conditions
ensure that any row selected later as row0 still has distinct free-item
costs. These order rows have at most two nonzero coefficients, also in
{-1,0,1}. Do **not** add comparisons between row totals at this stage; they
are imposed later by relabelling.

All these finitely many inequalities are strict, homogeneous and
simultaneously feasible. A common positive dilation therefore gives

\[
 P=\{x\in\mathbb R^{25}:Ax\ge\mathbf1\}\ne\varnothing,
\]

where A is an integer matrix and each row has at most seven nonzero
coefficients, each equal to +1 or -1. Coordinate positivity is included,
so every point of P satisfies x_l>=1 for each coordinate l.

The polyhedron P has a vertex. To see this without assuming boundedness
of P, minimise the sum of its coordinates. A nonempty sublevel set through
any feasible point is compact because every coordinate is at least one.
The optimum is therefore attained. The optimum face is a nonempty compact
polytope and has a vertex, which is also a vertex of P.

At such a vertex v, select 25 linearly independent active constraints.
Their coefficient matrix D is nonsingular and integer, and

\[
Dv=\mathbf1.
\]

For a coordinate l, write D_l for D with column l replaced by the vector
of ones. Cramer's rule gives

\[
 v_l=\frac{\det D_l}{\det D}.
\]

Replacing one coefficient by 1 raises a row's squared Euclidean norm by
at most one. Thus every row of D_l has squared norm at most eight.
Hadamard's determinant inequality yields

\[
 |\det D_l|\le(\sqrt8)^{25}=8^{25/2}.
\]

Let q=|det D|, a positive integer, and y=qv. Every coordinate y_l is an
integer (with the appropriate common sign of det D), and v_l>=1 implies
y_l>=q>=1. Moreover,

\[
 Ay\ge q\mathbf1\ge\mathbf1,
 \qquad
 1\le y_l=|\det D_l|\le B.
\]

Consequently y preserves the selected strict failure of every surjective
allocation, all strict minima, all positivity constraints, and the common
pinned minimum. An allocation with an empty bundle cannot be EFX for
positive nine-chore costs: with three agents and nine chores, one of the
remaining bundles has at least two chores, and its positive residual
exceeds the empty bundle's zero cost. Thus y is a counterexample over all
19683 complete allocations.

For the distinct-minimum canonical form, finally relabel the agent of
least row total as agent0.
Because all pinned minima are equal, this is also the agent of least total
after minimum normalisation. Relabel the pinned chores simultaneously,
order the two remaining agents/pinned chores so that c_01<c_02, and sort
the six unpinned chores by row0. Relabelling preserves positive integer
entries and their bound B. The row-total comparisons are weak: ties may
arise at the selected vertex. This proves the stated canonical version.

For the analogous distinct-minimum residual search with m chores, m>=4,
the same argument gives dimension 3m-2 and bound

\[
B_m=\left\lfloor(m-1)^{(3m-2)/2}\right\rfloor.
\]

For example, B_8=7^11=1,977,326,743. The theorem justifying any particular
minimum-index canonicalisation must still be stated separately.

## Consequence for exact finite search

The unrestricted nine-chore question is equivalent, under the preceding
genericity and shared-minimum reductions, to whether a counterexample
exists within 25 integer coordinates in [1,B] with a common pinned minimum.
Therefore an **exact UNSAT result on a faithfully encoded domain with this
derived B** is sufficient for the universal theorem. A run on a smaller
arbitrary bound is only a restricted search. SAT at either bound must be
checked literally over all complete allocations.

The interval [1,B] has not been exhausted in this work. The bound is far
too large to enumerate naively, but it permits a complete integer/SAT
encoding without imposing an unjustified empirical grid cutoff.

## Prior art and bounded search record

The use of determinants to bound small solutions of integer-coefficient
linear systems is classical. A primary source is:

von zur Gathen, J., & Sieveking, M. (1978). A bound on solutions of linear
integer equalities and inequalities. *Proceedings of the American
Mathematical Society, 72*(1), 155-158.
https://doi.org/10.1090/S0002-9939-1978-0500555-0

Author-hosted copy inspected via web retrieval:
https://vonzurgathen.online/old/files/gatsie78.pdf

Searches on2026-10-07 included `"EFX" "chores" "Hadamard"`,
`"EFX" "chores" "integer counterexample" bound`, and
`"linear inequalities" "rational solution" "Hadamard" bound determinant`.
They did not locate this exact EFX-specific numerical bound. This is not a
claim that no such bound has previously appeared. The proof above is
self-contained and specialises standard vertex, Cramer and Hadamard
arguments; its purpose is to justify a computational domain.
