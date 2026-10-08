# Bounded object and prior-art check for the cardinality cut

7 October 2026.

## Frozen object

For one nonnegative additive cost row on `r>=4` chores, the claim is:

`exists a two-way EFX partition with both cardinalities >=2`

if and only if

`2 max(c)+min(c)<=sum(c)`.

The three-agent use gives a protected bundle `S` to one agent and performs a
decreasing-order greedy two-way EFX split of its complement for a cutter,
with the other agent choosing its cheaper bundle. Protection is by the
sum of the two cheapest outside costs, rather than by the cheapest outside
cost alone. The earlier residual bounds are unchanged.

## Identity boundary

This is a cardinality refinement of ordinary two-way EFX partitioning and
cut-and-choose. It is not a new fairness notion, not a proof of all
three-agent nine-chore instances, and not a result about approximate EFX.
Descending least-load insertion is the familiar construction; only the
exact condition preventing a final singleton is isolated here.

## Searches and inspected sources

The existing project inspected Kobayashi, Mahara, and Sakamoto,
*EFX Allocations for Indivisible Chores: Matching-Based Approach*, including
the two-direction EFX and matching insertion arguments, and Zhang's
*EFX Allocations for Three Agents and Seven or Eight Chores*, version 2.
This continuation reread their relevant local text sections.

Public searches included the following formula/structure aliases:

- `"EFX" "chores" "singleton" "two" partition cardinality greedy`
- `"EFX" "2" "maximum" "minimum" "two agents" chores`
- `"EFX" "chores" "at least two" "greedy"`
- `"EFX" "2" "max" "min" "partition" "chores"`
- `"EFX" "chores" "singleton bundles" partition`

These surfaced the already identified matching and approximation papers,
plus Hosseini et al., *To EFX OR to MMS, That is the Question*,
arXiv:2608.10397 (2026), which has a threshold-preserving two-bundle EFX
subroutine. Primary arXiv retrieval of that paper's version 2 failed in
this session, so it was not used as proof support or assessed for exact
overlap. A search snippet is insufficient to certify object identity.

## Disposition

No absolute priority or novelty claim is made. The result is recorded as
a direct elementary refinement of the known greedy two-way EFX method,
with a complete self-contained proof and a finite exact implementation
check. The bounded search did not establish whether the exact
`2max+min<=total` characterisation already appears explicitly elsewhere.

No release should describe it as an unrestricted nine-chore existence
theorem or as independently established publication priority.
