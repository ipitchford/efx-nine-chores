# Exact generic sampling of the two outer rows

This changes only the sampled point used to discover the next sufficient
region. It does not add any assumption or restriction to the outer formula.

After clearing a row's denominators and dividing out its common integer
factor, let `R` be the resulting positive integer row. Its prescribed
minimum, in column `i`, is strictly smaller than all eight other entries.
Set `d_i=0` and assign `1,3,9,...,2187` to the other coordinates, in increasing
column order. Thus `sum(d)=3280`. Use the integer row

`R' = 3281 R + d`.

For every vector `q` with entries in `{-1,0,1}`, the perturbation satisfies
`|q.d|<=3280`. If `q.R` is nonzero, it is an integer of absolute value at
least one. Therefore `q.R'` has the same strict sign as `q.R`.

If `q.R=0` and `q` is nonzero, at least one nonminimum coefficient of `q`
is nonzero: a vector supported only on the positive minimum cannot have
zero dot product. The powers of three have no nonzero signed relation
with coefficients in `{-1,0,1}`. Indeed, the largest power in any proposed
relation exceeds the sum of all smaller powers. Consequently `q.d!=0`,
and the old tie becomes a strict inequality.

Every two distinct subset sums of `R'` are therefore distinct. Its pinned
minimum remains unique because the old positive minimum gaps are scaled
by 3281 and receive nonnegative increments. Dividing by the new minimum
restores the original normalization when needed.

Each EFX comparison is a difference of disjoint subset sums, so its
coefficient vector lies in `{-1,0,1}^9`. Every strictly positive EFX-failure
atom that was true at the old outer point remains true. In particular,
each previously asserted disjunctive region exclusion retains every
formerly true disjunct. The perturbed point is still outside every region
already excluded by the outer solver.

An inner core is subsequently constructed for the perturbed point and
archived with all original deletion inequalities. Its first-row guarantee
is proved over the same first-row domain as before. Thus generic sampling
changes neither the meaning of a learned region nor the final coverage
obligation. An unfinished outer search remains unfinished.

## On-demand ordinal pairs

The full binary pair census is a discovery aid. At a sampled two-row point,
the implementation marks all allocations satisfying both outer agents'
literal EFX conditions, then selects a pair whose two members are marked.
Precomputed exact compression sizes prioritize pairs with fewer sufficient
premises. A direct rational alternative is reconstructed for every branch
of that selected pair's first-row failure, and the separate stdlib checker
checks all branch identities before the pair supplies a region. If no pair
is available, the existing inner solver searches for a larger core or a
counterexample.

No correctness claim about every entry of the census is required for this
use: any incorrectly admitted selected entry is rejected by its freshly
constructed independent certificate check. The size score affects only
which candidate is attempted; it does not prove that candidate valid.

## Verification record

`on_demand_pair_validation.json` records a deterministic 500-pair sample
from the full census, all 3,148 associated failure branches, and 500 exact
compression-size recomputations. It also records exhaustive checks of the
6,561 signed direction vectors on eight coordinates and generic sampling
of all 878 integer rows in the completed second restart. These finite checks
support the implementation; the preceding inequalities give the general
sign-preservation argument.
