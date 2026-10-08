# Ancillary proof record: prescribed envy-freeness and three-agent chores

**Research date: 7 October 2026.**

**Scope.** The unrestricted question whether every three-agent, nine-chore instance admits a complete EFX allocation remains unresolved in this record. The results below concern a stronger auxiliary property, exact obstructions to that property, and reductions which must retain their stated premises. None of them substitutes for a proof or counterexample to the main nine-chore statement.

The minimum-insertion argument refines the argument of Kobayashi, Mahara, and Sakamoto (2023, Lemma 4.2). Priority for that refinement is not claimed. The eight-chore EFX theorem used in the conditional nine-chore reduction is Zhang (2026, version 2, Theorem 2).

## 1. Definitions and the auxiliary property

Let \(N=\{0,\ldots,n-1\}\) be the agents and \(M\) a finite set of chores. Each agent has a nonnegative additive cost function
\[
c_i(S)=\sum_{g\in S}c_{ig},\qquad c_{ig}\ge0.
\]
A complete allocation \(A=(A_i)_{i\in N}\) is a labelled partition of \(M\); empty bundles are permitted. It is **EFX** if
\[
c_i(A_i\setminus\{g\})\le c_i(A_j)
\quad
\text{for every }i,j\in N\text{ and every }g\in A_i.
\]
The quantifier includes owned chores of cost zero. For a nonempty bundle define
\[
r_i(S)=c_i(S)-\min_{g\in S}c_{ig},
\qquad r_i(\varnothing)=0.
\]
Thus EFX is equivalent to \(r_i(A_i)\le c_i(A_j)\) for all \(i,j\). An empty owner's original deletion condition is vacuous, and the residual convention gives the same result because all comparison costs are nonnegative.

An agent \(p\) is **ordinarily envy-free** in \(A\) if
\[
c_p(A_p)\le c_p(A_j)\qquad(j\in N).
\]
Ordinary envy-freeness implies that agent's EFX inequalities, but it is stronger.

For three agents write \(P_m\) for the statement:

> For every nonnegative additive cost matrix on \(m\) chores, and any prescribed agent \(p\), a complete EFX allocation exists in which \(p\) is ordinarily envy-free.

Agent symmetry lets an encoding prescribe agent 0. It must still establish the property for every cost matrix. A counterexample to \(P_m\) need not be a counterexample to ordinary EFX existence.

### Zero rows

For three agents and \(m\ge3\), every instance with a zero row satisfies \(P_m\).

If the prescribed agent has the zero row, allocate all chores to that agent. Its total and residual are zero. The other agents own empty bundles, so their deletion conditions are vacuous.

Otherwise choose a zero-cost agent \(z\ne p\). Give \(p\) one of its cheapest chores \(g\), give the remaining agent a different singleton, and give all remaining chores to \(z\). Both other bundles are nonempty because \(m\ge3\). Each therefore costs \(p\) at least \(c_p(g)\); consequently \(p\) is ordinarily envy-free. The other nonzero agent owns a singleton and has residual zero. Agent \(z\)'s residual is zero regardless of its bundle size. All EFX inequalities hold, including removal of any zero-cost owned chore.

### Scaling and genericity

Multiplying one row by a positive constant preserves all its ordinary-EF and EFX comparisons. Nonzero rows may therefore be normalised to have total one.

For fixed \(m\), failure of \(P_m\) is open in cost space. Each of the finitely many allocations fails through at least one strict linear inequality: an ordinary-envy inequality for the prescribed agent, or an EFX inequality for another agent. Choose one strict witness for each allocation. A sufficiently small perturbation preserves all these finitely many positive margins. Such a perturbation can make every cost positive and avoid every within-row equality hyperplane.

Consequently, to exclude counterexamples it is sufficient to exclude strictly positive, rowwise distinct counterexamples, after separately handling any structural cases omitted from an encoding. This is a strict-witness reduction; a strict canonical cone is not asserted to contain its tie boundaries.

## 2. Minimum insertion preserving a prescribed envy-free agent

### Theorem 1

Let \(n\ge2\). Suppose \(A=(A_i)_{i\in N}\) is an EFX allocation of \(R\), and prescribed agent \(p\) is ordinarily envy-free. Let \(e\notin R\) satisfy
\[
c_i(e)\le c_i(h)
\quad
\text{for every }i\ne p\text{ and every }h\in R.
\]
Then \(R\cup\{e\}\) admits an EFX allocation in which \(p\) remains ordinarily envy-free.

This includes zero costs and empty bundles.

### Proof

For every \(i\ne p\), choose a minimum-cost bundle in the current partition, and draw an arc from \(i\) to that bundle's current owner. Agent \(p\) has no outgoing arc.

First suppose the resulting directed graph contains a cycle. The cycle excludes \(p\). Rotate its bundles so that every cycle agent receives the minimum-cost bundle to which its arc points. Those agents are now ordinarily envy-free in the unchanged collection of bundles, and every other agent retains its EFX bundle. Choose one cycle agent \(i\) and add \(e\) to its new bundle \(B\). The hypothesis on \(e\) gives
\[
r_i(B\cup\{e\})=c_i(B).
\]
This identity also holds when \(B\) is empty, since the new bundle is a singleton and both sides are zero. Because \(B\) was minimum-cost for \(i\), its old total is at most every other bundle's cost. Agent \(i\) is therefore EFX after insertion. Every other agent keeps its assigned bundle while a different bundle weakly increases in cost, so remains EFX. Agent \(p\) retained its old minimum-cost bundle and remains ordinarily envy-free.

Now suppose the graph is acyclic. Every vertex other than \(p\) has one outgoing arc, so every directed path terminates at \(p\). Add \(e\) to \(A_p\). If this augmented bundle is still minimum-cost for \(p\), the existing assignment has the required properties: \(p\) is ordinarily envy-free and the other agents' comparisons only improve.

Otherwise choose a minimum-cost bundle \(A_j\) for \(p\) in the augmented partition. Here \(j\ne p\), so \(A_j\) is unchanged. Follow the directed path
\[
j=i_1\longrightarrow i_2\longrightarrow\cdots
\longrightarrow i_t\longrightarrow p.
\]
Give \(A_j\) to \(p\). For \(s<t\), give original \(A_{i_{s+1}}\) to agent \(i_s\). Give \(A_p\cup\{e\}\) to \(i_t\). All agents outside the path retain their bundles.

Agent \(p\) now receives a minimum-cost bundle in the augmented partition. Each intermediate path agent receives one of its original minimum-cost bundles, whose total is at most the cost of every original bundle. The collection changed only by adding a nonnegative-cost chore to \(A_p\), so these intermediate agents are ordinarily envy-free, hence EFX. The last agent \(i_t\) regarded original \(A_p\) as minimum-cost. Its new residual equals \(c_{i_t}(A_p)\), by the displayed identity, and is therefore at most every other bundle's cost. This reasoning covers empty original \(A_p\) as well. Agents outside the path retain EFX because their own bundles are unchanged and another bundle only increased.

All required inequalities hold. \(\square\)

**Relation to the source argument.** Kobayashi–Mahara–Sakamoto's cycle/path proof preserves an EFX matching after insertion of a chore cheapest for all but one agent. The refinement above maintains an additional invariant for the exceptional agent. In the acyclic case, rerouting is performed whenever that agent loses ordinary envy-freeness, even if it remains EFX.

**Finite implementation check.** The independent integer implementation in [structural_insert_check.py](../work/structural_insert_check.py) checked all 512 binary \(3\times3\) matrices, all 4,032 initial allocations satisfying the prescribed property, and all 9,846 admissible binary insertions. All tests passed. Both cycle lengths, both nontrivial path lengths, and the unchanged-assignment branch occurred. This tests the implementation; the preceding argument supplies the general proof.

## 3. How \(P_6\) reduces \(P_7\)

### Proposition 2: the shared-minimum case

Assume \(P_{m-1}\). In a three-agent \(m\)-chore instance, suppose the two agents other than prescribed \(p\) share a cheapest chore \(e\). Delete \(e\), apply \(P_{m-1}\), and use Theorem 1 to reinsert it. Hence the instance satisfies the prescribed property.

Therefore, once \(P_6\) is available, a counterexample to \(P_7\) must have disjoint cheapest-chore sets for its two nonprescribed agents.

### Exact finite formulas

For allocation \(a\), let its bundles be \(A_0,A_1,A_2\). The exact assertion that it fails the prescribed-agent-0 property is
\[
\begin{split}
\operatorname{Bad}^{P}_a(C)={}&
\bigvee_{j=1,2}
 \bigl[c_0(A_0)>c_0(A_j)\bigr]\\
&{}\lor
\bigvee_{i=1,2}
\ \bigvee_{g\in A_i}
\ \bigvee_{j\ne i}
 \bigl[c_i(A_i\setminus\{g\})>c_i(A_j)\bigr].
\end{split}
\]
No trim is needed for agent 0 because its ordinary-EF inequalities are stronger than its EFX inequalities. Every trim for agents 1 and 2 remains quantified, including trims of zero-cost chores.

For \(P_6\), the formula imposes nonnegative entries, unit row totals, a weak lexicographic order on all six columns, and \(\operatorname{Bad}^{P}_a(C)\) for all \(3^6=729\) allocations. These give 755 assertions. The zero-row argument, row scaling and column relabelling show that unsatisfiability excludes every \(P_6\) counterexample.

For reduced \(P_7\), positivity and genericity permit unique minima for agents 1 and 2. Put their minima in columns 0 and 1 respectively. Swap these two agents and those pinned columns if necessary so that \(c_{00}<c_{01}\). Sort free columns 2 through 6 by row 0. Impose unit row totals and all allocation-failure clauses for nonempty allocations. There are
\[
3^7-3\cdot2^7+3=1,806
\]
such allocations, and 41 domain assertions, giving 1,847 assertions in total.

Omitting allocations with an empty bundle is valid here: with seven positive-cost chores and an empty bundle, some other agent owns at least two chores and has positive residual, which exceeds the empty bundle's zero cost.

Any hypothetical \(P_7\) counterexample either has a shared minimum for agents 1 and 2, handled by Proposition 2 and \(P_6\), or can be perturbed and relabelled into the reduced formula's domain. Thus unsatisfiability of that reduced formula, together with \(P_6\), proves \(P_7\).

### Verification status

| Assertion | Recorded evidence | Current qualification |
|---|---|---|
| Unrestricted \(P_6\) formula is unsatisfiable | Z3 returned UNSAT; cvc5 returned UNSAT and exported a CPC proof; Ethos accepted a reference-bound proof ending in false | The encoding/reduction argument remains part of the proof's trust boundary, as do the checker and supplied CPC rule signatures |
| Reduced \(P_7\) formula is unsatisfiable | Z3 returned UNSAT in about 100 seconds | An independently checked \(P_7\) certificate is not yet recorded here; the first full cvc5 attempt exhausted its imposed memory limit without a verdict |
| \(P_7\) follows from the preceding two formula claims | Complete mathematical reduction above | The reduction does not replace the outstanding \(P_7\) certificate work |

The portable \(P_6\) input has SHA-256
bf24e50713175ad01e2d15d51fe78121e5df0412cb7c5c6f445e56337350c4b2.
The portable reduced \(P_7\) input has SHA-256
662a176b1db574f79025586c78a1a3a835b445a85662aa365d6411b0763cda3d.

Relevant records are [the \(P_6\) Ethos receipt](../results/designated6_ethos.json), [the reduced \(P_7\) Z3 result](../work/structural_designated_reduced_m7_seed0.json), and [the initial \(P_7\) cvc5 no-verdict receipt](../results/designated7_cvc5.json). The portable syntax variants eliminate unary addition by the identity \((+x)=x\); corresponding assertions were checked to simplify to identical arithmetic abstract syntax trees. That syntax conversion does not add a mathematical premise.

An [independent formula audit](../work/structural_prescribed_formula_audit.py), with its [exact receipt](../work/structural_prescribed_formula_audit.json), parses these frozen portable inputs without importing either generator. It matches all 2,535 allocation clauses to the displayed failure predicate by comparing exact integer coefficient vectors, allowing only duplicate disjuncts, reversed strict-comparison orientation, and the constant false comparison of two empty sums. It also matches the 26 and 41 domain assertions to independently reconstructed canonical constraints. All checks passed.

As a separate semantic check, the audit evaluates every stored allocation clause on seven exact matrices for each chore count: the all-zero matrix, identical unit rows, each possible position of a zero row, a matrix with zeros and ties, and a strictly positive matrix. These give 17,745 comparisons with a direct implementation of the full deletion predicate, with no discrepancy. Both positive fixtures additionally check all 381 omitted seven-chore empty-bundle allocations, which all fail. The zero and tie fixtures test the allocation clauses independently of domain membership; they are not claimed to satisfy the reduced formula's strict canonical constraints. These checks support encoding consistency but do not replace the universal mathematical reductions or the solver certificate.

For context, \(P_m\) for \(m\le5\) follows from an immediate refinement of Kobayashi–Mahara–Sakamoto's small-instance construction. For \(3\le m\le5\), their Claim 3.2 leaves a prescribed unprocessed agent with a singleton in an EFX allocation. Swap that singleton with one of the prescribed agent's minimum-cost bundles. The prescribed agent becomes ordinarily envy-free; the displaced agent receives a singleton and is EFX. Other bundle totals do not change. For \(m<3\), leave the prescribed agent empty and assign at most one chore to each other agent.

## 4. An exact eight-chore obstruction to prescribed envy-freeness

Consider the following strictly positive integer matrix:
\[
C=
\begin{pmatrix}
35&48&55&239&247&304&332&500\\
3&15&24&136&358&171&500&294\\
20&4&7&235&166&500&56&203
\end{pmatrix}.
\]
Its row totals are \(1760,1501,1191\), and every entry is at most 500.

### Proposition 3

This instance has 36 complete EFX allocations, but none makes agent 0 ordinarily envy-free. It is therefore a counterexample to \(P_8\), while satisfying ordinary EFX existence.

### Exact verification

All \(3^8=6,561\) labelled allocations were checked using integer arithmetic and the full deletion quantifier. The counts of EFX allocations in which agents 0, 1 and 2 respectively are ordinarily envy-free are
\[
(0,31,31).
\]
For every allocation, the stored failure certificate gives either a strict ordinary-envy witness for agent 0 or a strict EFX witness for agent 1 or 2. Every recorded failure margin is a positive integer; the minimum is 1.

This short standalone check reproduces the count:

~~~python
from itertools import product

C = [
    [35, 48, 55, 239, 247, 304, 332, 500],
    [3, 15, 24, 136, 358, 171, 500, 294],
    [20, 4, 7, 235, 166, 500, 56, 203],
]
efx_count = 0
prescribed_counts = [0, 0, 0]
for a in product(range(3), repeat=8):
    A = [[g for g in range(8) if a[g] == i] for i in range(3)]
    V = [[sum(C[i][g] for g in A[j]) for j in range(3)]
         for i in range(3)]
    efx = all(V[i][i] - C[i][g] <= V[i][j]
              for i in range(3) for g in A[i] for j in range(3))
    if efx:
        efx_count += 1
        for i in range(3):
            prescribed_counts[i] += all(V[i][i] <= V[i][j]
                                        for j in range(3))
assert efx_count == 36
assert prescribed_counts == [0, 31, 31]
~~~

The independently produced [verification record](../work/structural_p8_obstruction_500_verified.json) lists all EFX allocations. The [failure-witness file](../work/structural_p8_obstruction_500_witnesses.json) is indexed by the same lexicographic allocation order used above.

As a direct sanity check, the allocation
\[
A_0=\{4,5\},\qquad
A_1=\{0,1,2,3,7\},\qquad
A_2=\{6\}
\]
is EFX. Its own residuals are \(304,469,0\). The corresponding minima of the other two bundle costs are \(332,500,469\), respectively. Agent 0 nevertheless envies agent 2 because \(551>332\).

Agents 0 and 1 share their unique cheapest chore, column 0. Agent 2's unique minimum is column 1. This detail matters for the conditional reduction in Section 6.

### Every arbitrary ninth column extends this particular matrix

The counterexample to \(P_8\) does not become an ordinary nine-chore counterexample by appending any nonnegative column. Write the new costs as \((x_0,x_1,x_2)\), and call the new chore 8. The following three allocations cover every possible new column:

| Allocation | Agent 0's bundle | Agent 1's bundle | Agent 2's bundle | Sufficient condition |
|---|---|---|---|---|
| A | \(\{4,5\}\) | \(\{0,1,2,3,7\}\) | \(\{6,8\}\) | \(x_2\le469\) |
| B | \(\{3,4\}\) | \(\{5,8\}\) | \(\{0,1,2,6,7\}\) | \(x_1\le494\) |
| C | \(\{8\}\) | \(\{0,2,5,7\}\) | \(\{1,3,4,6\}\) | \(x_1\ge489,\ x_2\ge457\) |

For allocation A, agents 0 and 1 have residuals 304 and 469, while each relevant other-bundle cost is at least 332 and 500 respectively. Agent 2's residual is \(\max(56,x_2)\), and its two comparison costs are 666 and 469. This proves A under its stated condition.

For B, agents 0 and 2 have residuals 247 and 286, with comparison costs at least 304 and 401. Agent 1's residual is \(\max(171,x_1)\), and its two comparison costs are 494 and 836. This proves B.

For C, agent 0 is a singleton owner. Agents 1 and 2 have residuals 489 and 457; their other non-singleton comparison costs are 1009 and 730. Thus their comparisons with chore 8 require precisely the displayed lower bounds.

If neither A nor B applies, then \(x_2>469>457\) and \(x_1>494>489\), so C applies. This proves extension for all nonnegative \((x_0,x_1,x_2)\), including zeros and all equality boundaries. The [three-box certificate](../work/structural_extension_cover_500.json) also verifies these comparisons with exact arithmetic.

## 5. Two false marked-merge proposals

### 5.1 A specified chore need not have an envy-free owner

The assertion “every eight-chore instance and specified chore \(g\) admit an EFX allocation in which \(g\)'s owner is ordinarily envy-free” is false.

Take all three rows equal to
\[
(100,1,1,1,1,1,1,1)
\]
and specify the 100-cost chore. In every allocation its owner's cost is at least 100, while the other two bundles together cost at most 7. The owner therefore envies at least one other bundle. This obstruction does not concern EFX existence: give the 100-cost chore as a singleton and split the seven unit chores into bundles of sizes three and four.

### 5.2 Even choosing the merged pair freely is insufficient

A second proposal asks whether, in every nine-chore instance, some pair can be merged into one chore so that the resulting eight-chore instance has an EFX allocation with the merged chore's owner ordinarily envy-free. This is also false.

Take all three rows equal to
\[
(7,2,2,2,2,2,2,2,2).
\]
In any EFX allocation, the 7-cost chore must be a singleton. If its owner received even one other chore, its residual would be at least 7. Each other bundle, consisting only of 2-cost chores, would then need cost at least 8, requiring four small chores in each. That would leave no small chore for the 7-cost chore's owner, a contradiction.

The remaining eight small chores must split four and four. Indeed, if their bundle sizes are \(u,v\) with \(u+v=8\), EFX against the 7-cost singleton gives \(2(u-1)\le7\) and \(2(v-1)\le7\), hence \(u,v\le4\) and \(u=v=4\). Therefore every EFX allocation has costs \(7,8,8\), and its only ordinarily envy-free owner has the 7-cost singleton.

If any pair could be merged as proposed, split that merged chore back into its two original chores within the same owner's bundle. All three agents' bundle totals remain unchanged. The merged owner remains ordinarily envy-free and hence EFX; every other owner's EFX comparisons are unchanged. This would produce an ordinarily envy-free owner with at least two chores in the original nine-chore instance, contradicting the preceding classification.

Thus both marked-merge proposals fail through explicit positive-cost examples. Ordinary EFX existence holds in both examples.

## 6. A conditional disjoint-minimum route

Define the currently unproved statement \(D_8\):

> Every three-agent eight-chore instance with pairwise disjoint cheapest-chore sets admits an EFX allocation with any prescribed agent ordinarily envy-free.

Proposition 3 does not refute \(D_8\), because its agents 0 and 1 share a cheapest chore. No search timeout or absence of a counterexample establishes \(D_8\).

### Proposition 4, conditional on \(D_8\)

If \(D_8\) holds, every generic nine-chore counterexample can be relabelled so that agent \(i\)'s unique cheapest chore is \(i\), and its second-cheapest chore is one of the other two agents' minimum chores.

### Proof

Zhang's ordinary eight-chore EFX theorem and the KMS insertion lemma exclude a shared cheapest chore in a nine-chore counterexample. The strict-witness argument permits positive, rowwise distinct costs. Relabel the three distinct minima as chores 0, 1 and 2.

Let \(s_i\) be agent \(i\)'s second-cheapest chore and delete its cheapest chore \(i\). Each other agent \(j\)'s unique minimum remains chore \(j\). Agent \(i\)'s new minimum is \(s_i\).

If \(s_i\) were not one of the other two minimum chores, the reduced eight-chore instance would have three distinct minima. Under \(D_8\), it would admit an EFX allocation in which \(i\) is ordinarily envy-free. Add chore \(i\) to that agent's own bundle. Since it is globally cheapest for \(i\), the new residual equals that bundle's old total; ordinary envy-freeness therefore supplies the new EFX inequalities. Other agents keep their bundles while another bundle weakly increases. This contradicts a nine-chore counterexample. Hence \(s_i\) is one of the other two pinned minima. \(\square\)

Draw an arc \(i\to s_i\) on the three minimum-chore labels. Every vertex has one outgoing arc and no loop. Up to simultaneous agent and pinned-column relabelling, there are exactly two possibilities:
\[
(s_0,s_1,s_2)=(1,2,0)
\quad\text{or}\quad
(s_0,s_1,s_2)=(1,0,0).
\]
The first is a directed three-cycle. The second is a two-cycle with the remaining vertex feeding into a cycle vertex. This exhausts a loop-free functional graph on three vertices.

In either canonical pattern, chore 0 is row 0's minimum and chore 1 its second minimum. Sort the six free chores 3 through 8 by row 0. Chore 2 can occupy any of seven remaining positions. Consequently a proved \(D_8\) would reduce the generic nine-chore search to 14 cones: two directed patterns times seven positions, together with their specified second-minimum inequalities in rows 1 and 2.

This 14-cone reduction is conditional. It cannot be used to discard nine-chore cases until \(D_8\) is proved.

## Sources and verification boundary

### Mathematical sources

Kobayashi, Y., Mahara, R., & Sakamoto, S. (2023). *EFX allocations for indivisible chores: Matching-based approach*. arXiv. https://arxiv.org/abs/2305.04168  
Full-version numbering used here: Claim 3.2 and Lemma 4.2. https://arxiv.org/pdf/2305.04168

Zhang, X. (2026). *EFX allocations for three agents and seven or eight chores* (Version 2, 6 October 2026). arXiv. https://arxiv.org/abs/2609.10585v2  
Theorem 2 supplies ordinary eight-chore EFX existence; Section 6 leaves nine chores open. https://arxiv.org/html/2609.10585v2

### Local evidence

The exact counterexample and three-allocation extension cover use only the displayed integer matrix and finite arithmetic. Their verification does not require trusting a search solver. The positive finite formula results additionally require the logical translation into QF_LRA and the stated canonical-domain reductions. A checked proof establishes unsatisfiability of its referenced formula; it does not by itself establish that the formula represents the intended theorem.

The main nine-chore question remains unresolved by this record. The completed insertion proof, exact \(P_8\) refutation and marked-merge counterexamples remain valid regardless of how that main question is eventually resolved.


## Final certificate status

The final prescribed-agent seven-chore external proof attempt ended without a verdict or certificate (exit 139; cause not established). No cap change was applied and no further run was started. The Z3 UNSAT result and exact formula audits remain available, but independent external verification of that residual was not obtained. The original nine-chore target remains unresolved. See `VERIFICATION.md` and `CLAIM_STATUS.json` for the closed run ledger.
