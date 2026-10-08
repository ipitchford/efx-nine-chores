# A sufficient EFX class using two chores in each of the other bundles

7 October 2026. These are elementary deductions from decreasing-order greedy
two-way partitioning. No claim of priority is made. The unrestricted
three-agent, nine-chore theorem remains unresolved.

For a nonempty set write `r_i(S)=c_i(S)-min_{g in S}c_i(g)`.

## Lemma 1: exactly when a two-way EFX split can avoid singleton bundles

Let `R` contain at least four chores, with a single nonnegative additive cost
function `c`. Put `T=c(R)`, `a=max_R c`, and `d=min_R c`. There is a partition
`R=B disjoint-union D` which is EFX in both directions and satisfies
`|B|>=2`, `|D|>=2` if and only if

`2a+d<=T`.

**Necessity.** A bundle containing a maximum-cost chore contains another
chore, whose cost is at least `d`. Removing a cheapest chore from that bundle
leaves cost at least `a`. Its opposite bundle therefore has cost at least `a`,
by EFX, but cost at most `T-a-d`. Thus `a<=T-a-d`.

**Sufficiency.** List chores in nonincreasing cost order and insert each into
a currently least-cost bundle, breaking cost ties in favour of smaller
cardinality. Both bundles are EFX: deleting the last inserted chore gives
its cost just before insertion, no greater than the other bundle's then
cost, which only increases thereafter. The last inserted chore is cheapest
in its final bundle, including when its cost is zero.

Suppose one final bundle were a singleton. If its chore was not inserted
first, the first bundle received the largest chore and, before the second
chore, either had positive cost (forcing the second into the empty bundle),
or both initial costs were zero and the tie rule did the same. Thereafter a
singleton containing a nonlargest chore cannot remain singleton while the
other bundle receives another chore: its total is no greater than the
other bundle's initial maximum, and a tie prefers its smaller cardinality.
Hence the singleton must contain the first, maximum-cost chore.

Immediately before the last insertion, the other bundle then contains all
chores except that maximum and the last, minimum-cost chore. Its cost is
`T-a-d>=a`. The greedy choice puts the last chore in the singleton: strict
inequality selects it by cost, and equality selects it by smaller
cardinality (the other bundle has at least two chores). This contradicts
its being a final singleton. Both cardinalities are at least two.

Equivalently, the singleton argument may be shortened as follows. If either
bundle is a final singleton, greedy least-cost choice forces that singleton
to contain a maximum-cost chore; the final insertion then contradicts
`T-a-d>=a` with the stipulated tie rule. The detailed argument above also
covers all-zero costs.

## Theorem 2: protected bundle with two chores in each comparison bundle

Let `S` be nonempty and let `R=M\S` have at least four chores. Choose owner
`k` for `S`, cutter `p`, and chooser `q`, the other two agents. Write
`d_i=min_R c_i` and let `ell_k` be the sum of the two cheapest costs of `R`
according to `k`. Suppose

1. `r_k(S)<=ell_k`;
2. `2max_R c_p+d_p<=c_p(R)`;
3. `3c_p(S)+d_p>=c_p(M)`;
4. `3c_q(S)+2d_q>=c_q(M)`.

Then an EFX allocation exists.

**Proof.** Apply Lemma 1 using the cutter's row to obtain two EFX bundles
`B,D` from `R`, each of cardinality at least two. The chooser takes its
cheaper bundle and the cutter receives the other. The cutter's residual
is at most `(c_p(R)-d_p)/2`, a consequence of the two-way EFX inequalities.
Condition 3 bounds this by `c_p(S)`. The chooser's total is at most
`c_q(R)/2`, and deleting its cheapest owned chore reduces that by at least
`d_q`; condition 4 therefore makes its residual at most `c_q(S)`. Thus
both are EFX relative to `S` and to each other. Each of their bundles
contains at least two chores from `R`, hence costs `k` at least `ell_k`.
Condition 1 proves the owner's EFX inequalities. All inequalities are weak,
so zero costs and ties are included.

The cutter and chooser roles may be interchanged if the corresponding
conditions hold.

## Corollary 3: three cheapest chores of one agent

For nine chores, take `S` to be the three cheapest chores for owner `k`.
Condition 1 then holds automatically: the owner's residual is the sum of
its second- and third-cheapest costs, each no greater than either of the
two cheapest remaining costs. Thus only the cutter's cardinality condition
and the two residual-budget conditions need checking.

This strictly enlarges the previously recorded sufficient constructions.
For identical unit costs on nine chores, choose any three chores for `S`.
The residual is 2, the two-cheapest remaining sum is 2, the cutter's
cardinality inequality is `3<=6`, and the two budget inequalities are
`10>=9` and `11>=9`. The earlier sufficient tests restricted to a singleton
or a pair fail their budget inequalities on this same instance.

## Scope and use in exact search

For a putative counterexample, negate the four conditions for every chosen
`(k,p,q,S)`. These are sound extra necessary constraints once `d_i`,
`max_R c_p`, and `ell_k` are represented exactly. Replacing an unknown
minimum by a lower bound is safe in the two budget conditions, but is
**not** safe in the cutter's cardinality condition: that condition requires
an upper bound on its minimum if an approximation is used.

The theorem does not assert that these constructions cover all matrices.
It does not establish the original nine-chore existence statement.
