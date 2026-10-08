# Structural lemmas for three-agent additive chore EFX

Working note; 7 October 2026. These are proved below without relying on an SMT solver. Their novelty has not been established. The target is EFX after deleting **every** owned chore, including one of cost zero.

Write `c_i(S)` for additive nonnegative costs and `r_i(S)=c_i(S)-min_{g in S}c_i(g)` for nonempty `S`, with `r_i(empty)=0`.

## Lemma 1: an EFX split for one cost function

Any finite chore set `R` has a partition into two bundles `(B,D)` for which both bundles are EFX according to a given additive nonnegative cost function `c`: `r(B)<=c(D)` and `r(D)<=c(B)`.

Proof. Order the chores by weakly decreasing `c`-cost. Starting with two empty bundles, place each chore in a currently least-cost bundle. If a final bundle `B` is nonempty, let `g` be the last chore placed in it. The ordering ensures `c(g)=min_{h in B}c(h)`, including when that minimum is zero. Immediately before `g` was inserted, `c(B\{g})` was at most the then-current cost of the other bundle. The other bundle's cost cannot subsequently decrease. Hence `r(B)=c(B\{g})<=c(D)` at termination. The same argument applies to `D`; an empty bundle has residual zero. QED.

When `|R|>=2`, the split can be chosen with both bundles nonempty: during the greedy procedure, break ties in favour of an empty bundle. The first two chores then go to different bundles unless the second-empty bundle ceased to be cheapest, which cannot occur while it still has cost zero.

## Lemma 2: residual bound for a two-way EFX split

Let `R=B disjoint-union D`, with both `B,D` nonempty, and suppose both bundles are EFX for cost function `c`. Put `T=c(R)` and `d=min_{g in R}c(g)`. Then

`max(r(B),r(D)) <= (T-d)/2 <= T/2`.

Proof. Relabel so `c(B)>=c(D)` and put `b=min_B c`, `e=min_D c`. From `c(B)-b<=c(D)` we obtain `2r(B)=2c(B)-2b <= T-b <= T-d`. Also `2r(D)=2c(D)-2e <= T-2e <= T-d`, since `e>=d>=0`. These inequalities include equality and zero costs. QED.

If a chooser receives a cheapest bundle of an arbitrary two-way partition of `R`, its residual is at most `T/2-d` (provided both bundles are nonempty), since its total cost is at most `T/2` and its cheapest owned chore has cost at least `d`.

## Theorem 3: common large singleton

For three agents and any `m>=3`, suppose there is a chore `g` and distinct agents `p,q` such that

`3c_p(g) >= c_p(M)` and `3c_q(g) >= c_q(M)`.

Then a complete EFX allocation exists.

Proof. Give `g` to the third agent `k`, who is automatically EFX because its residual is zero. Agent `p` applies Lemma 1 to `R=M\{g}`, producing `(B,D)`. Agent `q` receives a least-cost bundle according to `c_q`; agent `p` receives the other bundle. Agent `p` is EFX relative to the other member of `(B,D)` by construction. Its residual is at most `c_p(R)/2` by Lemma 2 (the weaker bound also holds if a bundle is empty). The hypothesis gives `c_p(R)/2<=c_p(g)`, so it is also EFX relative to `{g}`. Agent `q` does not envy the other bundle at all. Its residual is at most its owned total, at most `c_q(R)/2<=c_q(g)`, so it is EFX relative to `{g}` as well. QED.

Thus, under row-total-one normalisation, any counterexample must satisfy, for every chore `g` and every pair `p<q`,

`c_p(g)<1/3 OR c_q(g)<1/3`.

## Theorem 4: a protected bundle and a two-way split

Let `S` be a nonempty proper subset of `M`, put `R=M\S`, and assume `|R|>=2`. Choose an agent `k` to own `S`, and let `p,q` be the others. Suppose

1. `r_k(S) <= min_{g in R}c_k(g)`;
2. `3c_p(S)+d_p >= c_p(M)`, where `d_p=min_{g in R}c_p(g)`;
3. `3c_q(S)+2d_q >= c_q(M)`, where `d_q=min_{g in R}c_q(g)`.

Then a complete EFX allocation exists. Conditions 2 and 3 may instead hold with `p,q` interchanged.

Proof. Agent `p` cuts `R` into two nonempty bundles using Lemma 1; agent `q` takes a least-cost bundle and agent `p` receives the remaining one. Agent `p`'s residual is at most `(c_p(R)-d_p)/2` by Lemma 2, at most `c_p(S)` by condition 2. Agent `q`'s residual is at most `c_q(R)/2-d_q`, at most `c_q(S)` by condition 3. The cutter is EFX within `R` and the chooser has no envy within `R`. For agent `k`, each other bundle contains a chore of `R`; its cost according to `k` is therefore at least `min_R c_k >= r_k(S)`. Thus all six inter-agent EFX comparisons hold. QED.

The simpler symmetric conditions `3c_p(S)>=c_p(M)` and `3c_q(S)>=c_q(M)` suffice. A useful special case chooses `S` to consist of the two cheapest chores for `k`: then condition 1 holds automatically, because `r_k(S)` is the larger of those two costs and is no larger than any cost outside `S`.

For `S={g}`, condition 1 always holds and the asymmetric refined condition becomes

`3c_p(g)+min_{h!=g}c_p(h)>=c_p(M)` and
`3c_q(g)+2min_{h!=g}c_q(h)>=c_q(M)`.

All these conditions work for arbitrarily many chores; they are sufficient cases, not a proof of the unrestricted nine-chore target.

## Lemma 5: inserting a minimum while preserving a designated envy-free agent

Let `(A_0,A_1,A_2)` be an EFX allocation of a chore set `R`, and suppose agent 0 is fully envy-free: `c_0(A_0)<=c_0(A_1),c_0(A_2)`. Let `e` be a new chore which is no more costly than **every** member of `R` according to each of agents 1 and 2. Then an EFX allocation of `R union {e}` exists in which agent 0 remains fully envy-free.

This strengthens the conclusion of Kobayashi–Mahara–Sakamoto (2023), Lemma 4.2, for this invariant. It is proved by the same directed-path argument, with the branch test strengthened from EFX to ordinary envy-freeness. Source inspected: <https://arxiv.org/pdf/2305.04168>, proof on PDF pages 10–11 (printed 10–11), especially the acyclic case. Novelty beyond that immediate strengthening is not claimed.

Proof. Regard the three bundles as fixed vertices numbered by their current owners. For each `i in {1,2}`, choose a bundle of minimum cost according to `i` and draw an arc from `i` to its current owner. Agent 0 has no outgoing arc.

If the directed graph has a cycle, that cycle uses only vertices 1 and 2. It is either a loop or the two-cycle. Reassign the bundles cyclically so every cycle agent receives the minimum bundle to which its arc points. All noncycle agents retain their bundles. Each changed assignment is EFX because a minimum-cost bundle is EFX; all unchanged assignments remain EFX because the collection of bundles is unchanged. Choose one cycle agent `i` and add `e` to its newly received bundle. For a nonempty old bundle, `e` is a cheapest owned chore after insertion, so its new residual equals its old total, which was no greater than either other bundle's cost. For an empty old bundle the new residual is zero. Thus `i` is EFX. Every other agent retains its owned bundle while another bundle gains a nonnegative-cost chore, so remains EFX. Agent 0 retained its own minimum bundle and only another bundle increased; therefore it remains fully envy-free.

Otherwise the directed graph is acyclic. Each of vertices 1 and 2 has an outgoing arc, so its unique directed path ends at vertex 0. First add `e` to `A_0`. If `A_0 union {e}` remains a minimum-cost bundle for agent 0, the existing assignment is EFX and agent 0 is envy-free: agents 1 and 2 retain owned bundles and see another bundle weakly increase; agent 0's envy-freeness implies its EFX condition.

If agent 0 is no longer envy-free, let `A_j`, `j!=0`, be one of its minimum-cost bundles in the augmented partition. Follow the chosen directed path `j=i_1 -> i_2 -> ... -> i_t -> 0`. Give `A_j` to agent 0; give original `A_{i_{s+1}}` to agent `i_s` for `s<t`; and give `A_0 union {e}` to agent `i_t`. All agents outside the path retain their original bundles.

Agent 0 now has a minimum-cost bundle and is envy-free. Every intermediate path agent receives an original minimum-cost bundle. Its residual is no greater than the minimum original bundle cost, which is no greater than the minimum new bundle cost because the only change in the collection of bundles is that `A_0` gained `e`. Thus it is EFX. The last path agent `i_t` regards original `A_0` as a minimum-cost bundle. If it was nonempty, the new residual after adding `e` is precisely `c_{i_t}(A_0)`, which was no greater than either other original bundle cost and hence no greater than either other new bundle cost. If original `A_0` was empty, the new bundle is a singleton and has residual zero. Unchanged agents remain EFX since their assigned bundles did not change and the only modified bundle increased. This completes all cases. QED.

The proof applies to any number of agents: let every nondesignated agent choose one minimum-cost bundle and use a directed cycle, or an acyclic directed path to the designated agent.

## Corollary 6: a stronger finite target that implies the next EFX case

Let `P(m)` be the assertion that every three-agent nonnegative additive instance with `m` chores has an EFX allocation in which a prescribed agent is fully envy-free. If `P(m)` holds, then every three-agent instance with `m+1` chores has an EFX allocation.

Proof. Pick a globally cheapest chore `e` for the prescribed agent and remove it. Obtain a `P(m)` allocation, then add `e` to that agent's own bundle. Its new residual equals its old total if its old bundle was nonempty, and is zero otherwise. Its former envy-freeness therefore supplies its new EFX inequalities. Every other agent retains its own bundle while another bundle increases, so its EFX inequalities remain valid. QED.

Moreover, if `P(m-1)` holds, Lemma 5 reduces a potential counterexample to `P(m)` to the case where the **two nondesignated agents** have disjoint sets of cheapest chores.

### Zero rows and genericity for this target

For `m>=3`, if the designated row is zero, assign all chores to the designated agent and leave the other bundles empty. If a nondesignated row is zero, give the designated agent one of its own cheapest chores, give the other nondesignated agent any other singleton, and give all remaining chores to the zero-cost agent. The designated agent is envy-free because both other bundles are nonempty and each contains a chore of cost at least its chosen minimum. The zero-cost agent is EFX and the remaining singleton owner is EFX. Thus no zero row occurs in a counterexample.

For fixed finite `m`, failure of this target is open in the space of cost matrices: for each of finitely many allocations, some EFX inequality of a nondesignated agent or some ordinary envy inequality of the designated agent fails **strictly**. A sufficiently small common perturbation preserves a chosen strict witness for every allocation. Consequently, a counterexample can be made strictly positive with all costs in each row distinct, without introducing any newly acceptable allocation. Positive row scaling then gives unit row totals. This justifies exact open-domain encodings with unique pinned minima and strict column orders; it does not itself prove the target.

## Conditional Lemma 7: second-cheapest chores and two canonical patterns

**Unproved premise D(8):** every three-agent eight-chore instance whose three agents have pairwise disjoint cheapest-chore sets admits an EFX allocation with any prescribed agent fully envy-free. The unrestricted premise `P(8)` is false: the exact matrix in `structural_p8_obstruction_verified.json` has 36 EFX allocations and none with prescribed agent 0 envy-free. That matrix has a cheapest chore shared by agents 0 and 1, so it does not refute D(8). D(8) remains under investigation and must not be assumed in an unconditional theorem.

If D(8) holds, every nine-chore EFX counterexample can be perturbed to strictly positive, rowwise distinct costs and relabelled so each agent `i` has unique cheapest chore `i`, and its **second-cheapest** chore belongs to `{0,1,2}\{i}`.

Proof. First, a nine-chore counterexample cannot have a chore cheapest for two agents, by the known eight-chore EFX theorem and KMS insertion. The finite strict-witness argument permits a generic perturbation, and distinct minima can be relabelled to columns 0,1,2. Let `s_i` denote the second-cheapest chore for agent `i`. Delete chore `i`. For each other agent `j`, its unique minimum remains chore `j`. Agent `i`'s new unique minimum is `s_i`. If `s_i` were not one of the other two agents' minimum chores, the reduced eight-chore instance would have three distinct minima. D(8) would yield an EFX allocation in which `i` is fully envy-free. Reinserting chore `i` into that agent's bundle gives a nine-chore EFX allocation by Corollary 6, a contradiction. Thus `s_i` lies among the other two pinned minima. QED.

Draw an arc `i -> s_i` on vertices `{0,1,2}`. Each vertex has one outgoing arc and no loop. Consequently the graph has exactly one of two isomorphism types:

1. A directed three-cycle. Relabel it as `s_0=1, s_1=2, s_2=0`.
2. A directed two-cycle with the remaining vertex feeding into a cycle vertex. Relabel it as `s_0=1, s_1=0, s_2=0`: vertex 0 is the cycle vertex also receiving the tail, vertex 1 is its cycle partner, and vertex 2 is the tail.

These are exhaustive because a functional graph on three loop-free vertices must contain a cycle of length two or three; in the two-cycle case the remaining vertex has no permissible target outside that cycle. Simultaneous permutations of agents and their pinned minimum columns preserve the EFX question, so both relabellings are legitimate.

In both canonical patterns, chore 0 is row 0's cheapest and chore 1 its second-cheapest. Sort the six unpinned chores 3,...,8 by row 0. Chore 2 can then occupy any of seven positions among the seven chores after 0 and 1. Thus D(8), if proved, reduces the generic nine-chore counterexample problem to **14 canonical cones**: two graph patterns times seven row-0 positions for chore 2. Each cone additionally imposes the designated second-minimum inequalities in rows 1 and 2; those inequalities can make the reduction much stronger than the factor of two in the case count suggests.

## Rejected stronger route

The assertion that an EFX allocation can always be obtained from a three-way partition which is EFX for one agent in all three bundles is false already for seven chores. Exhaustive enumeration of 301 unlabelled nonempty partitions found the integer matrix

```
2325  38   37  14 30    1  65
  89  83   43 112 63 2205 256
  77 296 1140 347 48    0 433
```

has EFX allocations (30 partitions have an EFX perfect matching), but no partition simultaneously has an EFX perfect matching and an agent adjacent to all three bundles. This is a computational working observation; no independent packaged verification is yet included.
