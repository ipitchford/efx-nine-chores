# Two exact limits of the proposed structural reductions

7 October 2026. These are counterexamples to auxiliary proposals, not
counterexamples to EFX existence for nine chores.

## 1. The prescribed agent's second-cheapest chore is not forced

The proposed necessary condition for failure of prescribed-agent EFX was
that the prescribed agent's two cheapest chores must be the two minimum
chores of the other agents. It is false. Consider

```
 7 32 20  79  96 115 106 176
 3 15 24 136 358 171 500 294
20  4  7 235 166 500  56 203
```

All entries are positive. Agent0 has minimum column0 and second minimum
column2. The other agents' respective minima are columns0 and1. Exhaustive
integer verification of all6,561 allocations gives32 EFX allocations and
zero EFX allocations in which agent0 is ordinarily envy-free.

This matrix was found by fixing rows1 and2 of the prior P8 obstruction and
varying only row0. There are671 complete allocations for which agents1
and2 simultaneously satisfy EFX. The resulting eight-real-variable formula
returned SAT in approximately0.055 seconds. Every full allocation was then
checked with the literal deletion predicate. The exact record is
`frozen_others_second_2.json`.

This does not refute the separate D8 conjecture requiring three distinct
minimum chores: here agent0 and agent1 share their minimum.

## 2. The cardinality-aware protected-bundle construction is not exhaustive

Take identical rows

`(4,4,4,1,1,1,1,1,1)`.

There is no choice of owner, cutter, chooser, and protected set S of size
one through five satisfying all four premises of Theorem2 in
`cardinality_cut.md`.

To see this without a solver, write h for the number of4-cost chores in S
and l for its number of1-cost chores. If l<=4, at least two1-cost chores
remain outside, so the protection bound is2. A set containing both a4 and
a1 has residual at least4 and fails protection. A set containing two or
more4-cost chores also has residual at least4 and fails protection.
The remaining possibilities are a singleton4 (whose cutter budget is
`3*4+1=13<18`), or at most three1-cost chores (whose cutter budget is at
most10<18), or four1-cost chores (whose residual3 exceeds protection2).
The final possibility is five1-cost chores: their residual4 is protected
by the remaining1 and4, but their cutter budget is `3*5+1=16<18`.
Thus every possible S fails at least one premise.

Nevertheless the instance has EFX allocations: give every agent one4-cost
chore and two1-cost chores. Each bundle costs6 and has residual5. This
shape gives `3! * 6!/(2!^3)=540` labelled allocations. Another108 EFX
allocations give one agent two4-cost chores, one agent a4-cost chore and
a1-cost chore, and the third agent the other five1-cost chores. Their
bundle costs are8,5,5 and residuals4,4,4. The exhaustive total is648.

The failure is not due to ties or shared minima. The following strictly
positive, rowwise-distinct matrix has three distinct minimum chores and
still has no qualifying protected set S:

```
100 101 102 103 104 105 400 401 402
101 100 102 103 104 105 400 401 402
101 102 100 103 104 105 400 401 402
```

It likewise has648 EFX allocations, including all540 allocations obtained
by giving every agent one of the last three chores and two of the first
six. The exact direct checker in `structural_limitations_check.py` verifies
both the absence of the sufficient construction and all19,683 allocations
for each matrix.

### The next simple construction for this shape

Let H be three common heavy chores and L the other six. If, for every row,
all H-costs are at least all L-costs and

`max_H c_i + max_L c_i <= min_H c_i + 2min_L c_i`,

then every allocation with one H-chore and two L-chores per agent is EFX.
Its residual is at most the left side; each comparison bundle costs at
least the right side. The displayed perturbed matrix satisfies these
conditions with upper bound507 and lower bound600 in every row.

This is a straightforward sufficient family around an already tractable
bi-valued example, not a claim of a new general theorem. In the current
exact row-elimination approach, stronger useful certificates come directly
from allocations whose row0 inequalities follow from ordinal dominance.
