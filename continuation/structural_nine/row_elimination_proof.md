# Exact elimination of the first valuation row

7 October 2026. This is a complete reduction for a computational proof or
counterexample search. It does not assert that either has been obtained.

## Canonical product domain

Use the already proved genericity and shared-minimum reductions. A
hypothetical nine-chore counterexample can be positive with unique,
pairwise distinct minima pinned to columns0,1,2 for agents0,1,2. Independently
scale each row so its pinned minimum equals1. Relabel agents1 and2 together
with their minimum columns to ensure `c01<c02`, then sort free columns3–8
in descending cost order for row0. This yields a Cartesian domain

`D0 x D12`.

`D0` concerns only row0: pinned minimum1 in column0, every other entry
strictly larger, `c01<c02`, and `c08<c07<...<c03`. `D12` concerns only the
two other rows: pinned minimum1 in columns1 and2 respectively, with all
other entries strictly larger. No row-sum comparison is imposed.

## Allocation predicates and a sufficient region

For an allocation a and agent i let `Good_i(a)` be the conjunction of all
its EFX inequalities, including every owned-chore deletion. Let `Bad_i(a)`
be its exact strict negation.

Suppose a finite list K of allocations satisfies

`D0 AND (AND_{a in K} Bad_0(a)) = UNSAT`.

Define the two-row region

`R_K = AND_{a in K} [Good_1(a) AND Good_2(a)]`.

For any `(c1,c2)` in this region and any `c0` in D0, some a in K makes
agent0 EFX by the displayed UNSAT statement. The other two agents are EFX
on that same a by the definition of the region. Thus R_K is a sufficient
region for universal existence over the entire allowed first row.

Its strict complement is a single disjunction of linear inequalities:
some allocation in K, some agent1 or2, and some owned-chore deletion fails
against another bundle. Every deletion is retained, except comparisons
whose coefficient vectors contain no positive coefficient; these are
already true for every nonnegative row.

## Outer and inner searches

The outer solver seeks a two-row point in D12 outside every recorded R_K.
At a SAT outer point, fix the two rows exactly and enumerate all complete
allocations for which both those agents are EFX. On this filtered list F,
ask whether

`D0 AND (AND_{a in F} Bad_0(a))`

is satisfiable.

If SAT, its first-row model together with the fixed rows is a full
counterexample. Every allocation either fails one fixed row or belongs
to F and fails row0. The implementation independently checks all3^9
allocations before recording a counterexample.

If UNSAT, an UNSAT core of allocation clauses supplies a list K contained
in F and hence a sufficient region containing the sampled two-row point.
The archived input with only D0 and those core clauses makes this claim
reviewable and independently checkable. UNKNOWN supplies no region.

If the outer formula eventually becomes UNSAT, the recorded regions cover
D12. Together with their inner certificates and the canonical reduction,
this proves the unrestricted nine-chore result. A timeout or finite list
of regions does not prove coverage.

## Seeding by ordinally valid allocations

There are28 full row0 orderings consistent with D0: choose the two positions
of columns1 and2, in that order, among the eight nonminimum positions;
the six free columns retain their order.

For a fixed full order, remove the cheapest chore of agent0's bundle.
Its remaining sum is at most a comparison bundle's sum for every positive
valuation respecting the order if its chores can be injected into that
comparison bundle with each matched chore having weakly higher rank.
With both rank lists sorted decreasingly, this means the residual list
is no longer than the comparison list and is coordinatewise no larger.

Necessity follows by choosing costs almost constant below a threshold and
very large above it when this dominance fails. Sufficiency is immediate
by summing the matched inequalities and the comparison bundle's remaining
nonnegative costs. Strict inequalities in the domain are obtained by
arbitrarily small rank-dependent perturbations, so they do not alter this
criterion.

An allocation which passes for every one of the28 orders makes agent0
EFX throughout D0 and therefore gives a region with a singleton K. These
regions can seed the outer solver before any model is sampled. The current
enumeration records3,238 such labelled nonempty allocations. This count
is an implementation result; the injection test itself is the proof of
each region's first-row guarantee.

## Trust boundary

The reduction and ordinal injection argument are handwritten mathematics.
Raw Z3 UNSAT results remain exploratory until their archived inputs have
adequate independent proof certificates. An outer UNSAT would need a
certificate for the outer formula as well as every nonordinal inner core.
The two-row model and all archived regions use exact rational/integer
arithmetic; no numerical tolerance is used.
