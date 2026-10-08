# Full ordinal pair census and its actual use

This is an exploratory enumeration and a search aid. It is not a global
nine-chore EFX proof. The on-demand search independently certifies each
selected pair before allowing it to exclude an outer-row region.

## Frozen objects

The first-row domain is the positive cone described by

`c00 > 0`, `c00 < c01 < c02`, and
`c00 < c08 < c07 < c06 < c05 < c04 < c03`.

The input generator enumerates all 18,150 allocations with three nonempty
bundles. It removes the 3,238 allocations whose first-row EFX conditions
hold throughout this cone; the removed allocation IDs match the existing
28-order injection census exactly. The remaining 14,912 allocations have
6,802 distinct feasible failure atoms after minimal-deletion reduction and
componentwise dominance in positive gap coordinates.

For a literal failure coefficient vector `q`, those coordinates are

`U = (sum(q), q1+q2, q2, sum(q3..q8), sum(q3..q7), ..., q3)`.

A failure atom is impossible if every coordinate of `U` is nonpositive.
For two individually feasible failure atoms `U,V`, simultaneous strict
failure is impossible exactly when nonnegative weights, not both zero,
give a nonpositive combination. Since neither atom alone is impossible,
both weights must be positive, and this reduces to finding `r>0` with
`rU+V<=0` componentwise. The implementation compares integer products when
intersecting the rational lower and upper bounds on `r`.

A pair of allocations covers the first row precisely when each cross-pair
of their possible failure atoms is impossible. The C++ census tested all
111,176,416 unordered pairs and recorded 2,113,668 accepted pairs. Its known
all-minima-owning subfamily contains exactly 1,048 pairs, matching the
separately constructed and independently checked earlier family.

These total counts are the result of the enumerator. The package does not
claim an independent certificate replay for every accepted pair.

## Files and encodings

- `input.txt` is the compact integer input. `input_index.json` records the
  allocations, literal coefficient vectors, transformed vectors, and the
  input hash.
- `accepted_pairs.bin` consists of repeated pairs of unsigned 32-bit
  little-endian allocation IDs. An allocation ID is its nine ownership
  digits interpreted in base three, with item 0 as the most significant
  digit.
- `pair_region_scores.bin` stores one unsigned byte per accepted pair:
  the number of maximal sufficient outer-row inequalities after exact
  cone dominance. This is a selection heuristic, not a validity certificate.
- `summary.json`, `run_receipt.json`, and the score receipts record the
  completed enumeration, resource bounds, runtimes, and relevant hashes.

The enumeration ran under a 300 MiB address-space cap and a 120-second
external limit. It completed in approximately 0.68 seconds with 8.4 MiB
reported maximum resident memory on this execution environment.

## Bounded pruning experiments

The following counts belong to explicitly limited pruning methods. They
do not establish feasibility of a surviving region.

| Stage | Removed at this stage | Remaining pairs |
|---|---:|---:|
| Full ordinal census | — | 2,113,668 |
| One/two-inequality certificate of weak outer-row infeasibility | 438,767 | 1,674,901 |
| Two-inequality certificate requiring a nontrivial subset equality | 11,394 | 1,663,507 |
| Outer premises imply an already retained robust-singleton region by exact cone dominance | 34,505 | 1,629,002 |

The equality-only filter is relevant to a generic search. It does not
discard those regions when making a claim about all boundary valuations.
The weak-infeasibility test looks for a nonnegative combination of outer
inequalities with nonnegative gap coefficients and at least one positive
coefficient. The equality-only case has an identically zero combination
and forces a nonzero EFX comparison to vanish.

The singleton-dominance test checks, for every target premise, whether one
of the pair's premises dominates it componentwise in the corresponding
positive minimum-gap cone. Its surviving pairs can still be dominated by
more general combinations or by other pair regions. The intermediate
binary survivor files and their receipts retain these experiments.

## On-demand use and proof boundary

The current driver does not insert two million region clauses. For each
exact generic outer-row sample, it marks allocations satisfying EFX for
both outer agents, intersects that mark with the pair table, and prioritizes
a compatible pair with the smallest precomputed premise count.

`exact_pair_core.py` then reconstructs every branch of first-row failure
for that one pair, derives a rational nonnegative linear alternative, and
passes the result directly to the separate stdlib-only
`verify_row_cores.py`. The region is added only after that check succeeds.
The certificate and its hash are saved alongside the learned region.
If the table supplies no compatible pair, the existing exact inner solver
remains available to find a larger core or a counterexample.

`on_demand_pair_validation.json` in the parent directory additionally
records 500 deterministic sampled pairs, all 3,148 of their failure
branches, and 500 independently recomputed scores. Each actual selected
pair receives its own fresh check regardless of this sample.

The ultimate proof obligation remains an independently supported UNSAT
result for the complete outer coverage formula, or an exact counterexample
checked against every allocation. None is asserted by this census.
