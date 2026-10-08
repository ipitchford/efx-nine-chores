# A complete partition-level factorization of allocation failure

**Status.** This is an exact alternative Boolean organization of the same EFX search. It has not been encoded for a solver or benchmarked. The newly reviewed zero-minimum normalization is the more immediate reduction because it already removes variables and has a successful eight-chore calibration.

There are 18,150 complete nine-chore allocations with three nonempty labeled bundles. Group the six possible assignments of any three nonempty unlabeled bundles to the three agents. This leaves **3,025 partitions**.

For a partition \(P=\{B_0,B_1,B_2\}\), let agent \(i\) accept bundle \(b\) when it is EFX for that agent against both other bundles:
\[
G_{ib}(P)\iff
c_i(B_b)-\min_{g\in B_b}c_i(g)
\le \min_{a\ne b}c_i(B_a).
\]
Let \(R_{ib}=\neg G_{ib}\). Every agent accepts at least one bundle: its bundle of minimum total cost is accepted because nonnegative costs make its deletion residual no larger than its total. This observation is valid with zero minima and literal zero deletion.

An assignment of these bundles is EFX exactly when the corresponding 3-by-3 acceptance graph has a perfect matching. For graphs whose three agent neighborhoods are nonempty, Hall's condition fails exactly in one of the following two ways:

1. One bundle is rejected by all three agents.
2. Two agents both accept only the same single bundle.

The corresponding no-allocation condition is
\[
\left(\bigvee_{b=0}^2\bigwedge_{i=0}^2R_{ib}\right)
\ \lor\ 
\left(\bigvee_{0\le i<j\le2}\ \bigvee_{b=0}^2
\bigwedge_{a\ne b}(R_{ia}\land R_{ja})\right).
\]
Indeed, a one-agent Hall obstruction is excluded by the nonempty-neighborhood fact. A two-agent obstruction has neighborhood of size at most one, hence exactly one. A three-agent obstruction leaves at least one bundle uncovered. These are all Hall subsets, so the condition is both necessary and sufficient.

Each rejection predicate depends on a single cost row and can reuse the existing trimmed-sum failure atoms. A SAT encoding could introduce one of at most twelve Hall-obstruction selectors per partition, with shared row-local rejection predicates. It could also state explicitly that every row has some accepted bundle. A singleton bundle is accepted by every agent, which simplifies the partitions containing singletons.

Completeness enters twice: enumerate **every** one of the 3,025 partitions, and encode the rejection predicates exactly, including every relevant minimum-deletion possibility. Choosing only selected partitions or only one type of Hall obstruction is incomplete. The existing six labeled-allocation clauses and the Hall condition are logically equivalent on actual cost matrices, but their proof-search behavior may differ.

The small audit in `hall_partition_factorization_audit.json` checks all \(7^3=343\) possible nonempty-neighborhood graphs, with zero mismatches, and independently counts the partitions by bundle shape. It supplies no evidence of faster solving. Introducing many shared rejection variables could outweigh the reduction in top-level disjunctions; a successful calibration and the same complete literal audit would be needed before relying on an implementation.

This factorization does not repair the previously incomplete protected-bundle construction, prescribe a second-cheapest chore to a particular agent, or turn partial row/prefix coverage into a global proof. Those failed shortcuts and open coverage obligations remain as documented elsewhere.
