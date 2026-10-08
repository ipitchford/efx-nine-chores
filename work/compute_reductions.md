# Exact reductions used by the CEGIS worker

These notes are subordinate to a proof of the shared-minimum insertion
reduction. They do not themselves settle the nine-chore theorem.

## Open counterexample set and dense generic reduction

For a labelled allocation A and ordered distinct agents i,j, every failure
comparison is the homogeneous linear form

    f(A,i,j,g;C) = sum_{h in A_i minus {g}} C[i,h]
                  - sum_{h in A_j} C[i,h],  g in A_i.

An allocation fails complete EFX iff at least one such form is strictly
positive. The set N of matrices for which every allocation fails is a finite
intersection of finite unions of open halfspaces. Thus N is open in the full
ambient real vector space, before imposing nonnegativity.

If N intersects the nonnegative cone, take a point in that intersection and
an ambient open ball contained in N. This ball contains a strictly positive
matrix avoiding every specified finite family of proper linear hyperplanes.
In particular its row entries may all be distinct, and its normalised row
minima may be distinct if desired. The hyperplanes defining distinct
normalised minima are polynomial equalities before normalisation; their
zero sets still have empty interior, and they are plain linear equalities
after normalising each positive row to sum one.

If every matrix with a cheapest chore shared by two agents is known to admit
EFX, the generic counterexample's three unique cheapest chores must be
distinct. Relabel these as chores 0,1,2 for agents 0,1,2. Relabel the six
remaining chores so that row 0 is strictly increasing on columns 3,...,8.
Interchanging agents 1,2 and their corresponding minimum columns, if
necessary, imposes C[0,1]<C[0,2]. If all rows sum to one, initially choosing
agent 0 with smallest normalised row minimum also permits C[0,0]<=C[1,1]
and C[0,0]<=C[2,2], without losing the residual 1/2 interchange.

## Unit margins without row normalisation

Any finite conjunction of disjunctions of homogeneous strict linear
inequalities, together with homogeneous strict linear side conditions, is
satisfiable iff the formula obtained by replacing every atomic inequality
L(C)>0 by L(C)>=1 is satisfiable. One implication is immediate. For the
other, choose one true atom from every satisfied disjunction and include all
strict side conditions. Their finitely many positive values have a positive
minimum epsilon. Replacing C by C/epsilon makes all selected atoms at least
one. (Replacing all atoms by unit-margin versions therefore still satisfies
each disjunction.)

The unit-margin formula must omit inhomogeneous normalisations such as row
sums equal to one or diagonal costs equal to one. Positive independent row
scaling is still available when converting exact solver models into
primitive integer rows for direct EFX enumeration: it preserves signs of
all allocation-failure comparisons. The converted model need not continue
to satisfy margins of size one; its EFX/non-EFX status is unchanged.

A compatible homogeneous gauge is available when the three minima are
pinned at the diagonal: impose C[0,0]=C[1,1]=C[2,2], leaving their common
value free. To justify this, first scale each positive row so that its
minimum equals one. All EFX and ordinary-EF comparison signs are preserved.
Then scale all rows together until every selected true strict atom and
strict side condition has value at least one. Their minima remain equal.
This gauge removes two independent scale degrees of freedom without
fixing the common minimum to one. It must not be combined with independent
row-sum normalisations, which would impose a second, unjustified gauge.

## Seed constraints from two singleton bundles

Assume row i has a unique minimum at chore i and m>=5. Choose distinct
x,y different from i. The allocation giving M minus {x,y} to agent i and
singletons x,y to the other agents is EFX iff

    S_i - C[i,x] - C[i,y] - C[i,i] <= min(C[i,x],C[i,y]),

where S_i is the row sum. Consequently every counterexample satisfies

    S_i - C[i,x] - C[i,y] - C[i,i] > C[i,x]
    OR
    S_i - C[i,x] - C[i,y] - C[i,i] > C[i,y].

For m=9 there are 3 * binomial(8,2) = 84 such row-local clauses. If one of
x,y equals i, the large bundle's trimmed cost exceeds the cost of that
minimum singleton, so the corresponding allocation always fails; no
additional constraint is needed. These are merely a compressed subset of
the complete allocation clauses, rather than an additional theorem about
the full nine-chore problem.

## CEGIS certificate semantics

At every satisfiable model, enumerate all allocations exactly after
converting rational rows to integers. Add the failure clause for every EFX
allocation found. A SAT model satisfying these clauses is only a candidate
until the complete exact enumeration returns zero EFX allocations. An UNSAT
result is sufficient even if only a strict subset of allocation-failure
clauses has been added, because every true counterexample must satisfy each
of them. A timeout or unknown result proves neither existence nor failure.
