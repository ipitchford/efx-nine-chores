# A smaller integer bound obtained by treating each valuation row separately

**Status.** The argument below proves a finite representative bound. It does not prove EFX existence, provide a counterexample, or report an exhaustive search of the resulting domain. The determinant method is standard, and no priority claim is made. This argument was independently scrutinized in this research session; it is not a proof-assistant formalization.

For nine chores the bound is **11,585 for every integer cost entry**. The three integer row minima may differ. This removes the coupling responsible for the larger bound in [finite_integer_bound.md](finite_integer_bound.md), whose stronger common-minimum conclusion remains valid.

## Theorem

Let there be three agents and \(m\ge4\) chores. Costs are nonnegative and additive. A complete allocation is EFX when
\[
c_i(A_i\setminus\{g\})\le c_i(A_j)
\quad\text{for every }i\ne j\text{ and every }g\in A_i,
\]
including owned chores of zero cost.

If an instance has no complete EFX allocation, then there is another such instance whose costs are positive integers satisfying
\[
1\le c_i(g)\le
B_m:=\left\lfloor (m-1)^{m/2}\right\rfloor
=\left\lfloor\sqrt{(m-1)^m}\right\rfloor
\qquad(i=0,1,2;\ g=0,\ldots,m-1).
\]
The integer representative can preserve the complete strict item order of every row of any fixed positive, rowwise-distinct counterexample.

In particular, for \(m=9\),
\[
\boxed{B_9=\left\lfloor 8^{9/2}\right\rfloor=11\,585.}
\]

No condition that the three integer row minima coincide is asserted or needed.

## Proof

### 1. Choose a positive counterexample with distinct costs in each row

Suppose a nonnegative instance is a counterexample. For each complete allocation, select one of its strictly failed EFX comparisons. There are only \(3^m\) complete allocations, so only finitely many selected strict inequalities.

A sufficiently small perturbation of the cost matrix preserves every selected positive failure margin. The perturbation can make all entries positive and avoid every equality between two entries of the same row. We may therefore start from a positive counterexample whose item costs in each row have a complete strict order.

This argument uses the literal deletion predicate. It does not omit zero-cost deletions at the original instance.

### 2. Separate the selected failure constraints by their evaluating agent

Consider the allocations for which all three bundles are nonempty. For every such allocation \(A\), fix one failed comparison and record its evaluating agent \(i(A)\), comparison agent \(j(A)\ne i(A)\), and removed chore \(g(A)\in A_{i(A)}\):
\[
c_{i(A)}(A_{i(A)}\setminus\{g(A)\})
-c_{i(A)}(A_{j(A)})>0.
\]

This inequality uses **only row \(i(A)\)**. In particular, the cost of the other agent's bundle is evaluated using \(c_{i(A)}\), not using that other agent's row.

For each agent \(i\), form a strict homogeneous system \(A_i x>0\) in \(m\) variables. Include:

1. Every selected failure whose evaluating agent is \(i\).
2. Every coordinate positivity condition \(x_g>0\).
3. The complete strict item order of the original row \(i\). Its adjacent inequalities suffice to impose that order.

The original row satisfies this system, so it is feasible. If an agent was assigned no selected failures, its positivity and order constraints still form a feasible system.

Every coefficient belongs to \(\{-1,0,1\}\). In a selected failure, the two compared item sets are disjoint, and, writing \(k\) for the third agent, the coefficient support has size
\[
|A_i|-1+|A_j|
=m-|A_k|-1\le m-2.
\]
Positivity rows have support one and order rows have support two. Because \(m\ge4\), every row of \(A_i\) therefore has support at most \(m-2\).

### 3. Find a bounded integer representative for each row independently

Fix \(i\). Since the finite system \(A_i x>0\) is feasible, dilating a feasible row by a sufficiently large positive factor yields
\[
P_i:=\{x\in\mathbb R^m:A_i x\ge\mathbf1\}\ne\varnothing.
\]
This dilation can be chosen separately for each agent. Positivity constraints are included, hence every \(x\in P_i\) satisfies \(x_g\ge1\).

The polyhedron \(P_i\) has a vertex. Indeed, minimize \(\sum_g x_g\). The sublevel set through any feasible point is nonempty, closed, and bounded because every coordinate is at least one. The minimum is attained, and its minimizing face is a nonempty compact polytope. A vertex of that face is also a vertex of \(P_i\).

At such a vertex \(v_i\), choose \(m\) linearly independent active constraints. Their integer coefficient matrix \(D_i\) is nonsingular and satisfies
\[
D_i v_i=\mathbf1.
\]
For coordinate \(g\), let \(D_{i,g}\) be \(D_i\) with column \(g\) replaced by ones. Cramer's rule gives
\[
(v_i)_g=\frac{\det D_{i,g}}{\det D_i}.
\]

Each row of \(D_i\) has squared Euclidean norm at most \(m-2\). Replacing one coefficient in \(\{-1,0,1\}\) by 1 increases that squared norm by at most one: changing \(-1\) or \(+1\) leaves its square unchanged, and changing 0 adds one. Therefore every row of \(D_{i,g}\) has squared norm at most \(m-1\). Hadamard's inequality yields
\[
|\det D_{i,g}|\le(\sqrt{m-1})^m=(m-1)^{m/2}.
\]

Set
\[
q_i:=|\det D_i|\in\mathbb Z_{>0},
\qquad y_i:=q_i v_i.
\]
Every coordinate of \(y_i\) is an integer. Since \((v_i)_g\ge1\), it is positive, and Cramer's formula gives
\[
1\le (y_i)_g
=|\det D_{i,g}|
\le B_m.
\]
Furthermore,
\[
A_i y_i=q_i A_i v_i
\ge q_i\mathbf1\ge\mathbf1.
\]
Thus \(y_i\) preserves every selected strict failure assigned to row \(i\), all positivity conditions, and the entire strict item order.

Repeat this construction independently for all three agents. The denominators \(q_i\), and the resulting integer minima, are allowed to differ.

### 4. Assemble the three rows

Use \(y_0,y_1,y_2\) as the three rows of the new instance. For any allocation with three nonempty bundles, its selected failure was assigned to one definite agent \(i(A)\). That inequality is among the constraints of \(A_{i(A)}\), so it still has positive margin in the assembled instance. Replacing the other two rows cannot affect it.

An allocation with an empty bundle also cannot be EFX. With \(m\ge4\) chores assigned among at most two remaining bundles, one bundle contains at least two chores. After deleting any one of its chores, its owner's residual cost is positive, while the empty comparison bundle costs zero. This supplies a strict EFX failure.

Consequently every complete allocation fails EFX, and all three rows have positive integer entries at most \(B_m\). Their prescribed strict item orders are preserved. This proves the theorem. \(\square\)

## Nine-chore arithmetic and comparison with the earlier bound

The numerical bound can be checked without floating-point arithmetic:
\[
11\,585^2=134\,212\,225
\le8^9=134\,217\,728
<134\,235\,396=11\,586^2.
\]

| Representative requirement | Active linear system dimension | Sufficient bound on every integer entry |
|---|---:|---:|
| Three integer row minima forced to share one value | \(3\cdot9-2=25\) | \(194\,368\,031\,998\) |
| Each valuation row represented independently | \(9\) for each of three systems | **\(11\,585\)** |

The earlier theorem has a stronger normalization requirement. It remains true. The smaller bound suffices for an uncoupled integer search because EFX failures are entirely local to their evaluating rows.

For illustration, the general formula gives:

| Number of chores \(m\) | \(B_m\) |
|---:|---:|
| 4 | 9 |
| 5 | 32 |
| 6 | 125 |
| 7 | 529 |
| 8 | 2,401 |
| 9 | 11,585 |
| 10 | 59,049 |

For at most three chores, assigning at most one chore per agent directly gives an EFX allocation; no counterexample bound is needed.

### The same bound argument for more agents

For \(n\ge2\) agents and \(m\ge n+1\) chores, the identical proof gives
\[
B_{n,m}=\left\lfloor(m-n+2)^{m/2}\right\rfloor.
\]
In a surjective allocation, the \(n-2\) other bundles contain at least \(n-2\) chores, so a selected failure has support at most \(m-n+1\). This is at least two, so it also bounds the order rows' support. Every row is still an independent system in \(m\) variables; the Cramer replacement norm bound is \(m-n+2\). A positive allocation with an empty bundle has some other bundle of size at least two when \(m\ge n+1\), so the final empty-bundle argument also applies. No common integer minimum is required, and no additional search or novelty claim accompanies this observation.

## Consequence for an exact search

The unrestricted three-agent nine-chore question is equivalent to whether a counterexample exists with **27 integer variables**, one per cost entry, all in \([1,11585]\). A faithful UNSAT proof for this bounded domain would suffice to exclude every nonnegative counterexample. A SAT result must still be checked literally over every complete allocation.

The bounded encoding must permit the three row minima to differ. Merely changing the old common-minimum encoder's upper bound to 11,585 would impose an additional condition that this smaller-bound theorem does not justify.

The numerical theorem itself does not require pairwise distinct minimum chores or any result for eight chores. If the known eight-chore theorem and shared-minimum insertion reduction are invoked separately, a nine-chore counterexample can additionally be assumed to have three distinct minimum chores. The preserved row orders allow them to be relabeled as columns 0, 1, and 2 for their respective agents, with \(c_{01}<c_{02}\) and the six free columns in decreasing order in row 0. These relabelings preserve integrality and the bound. No row-total comparison or equality between row minima is necessary.

The domain \([1,11585]^{27}\) has **not** been exhausted in this work. The bound remains a complete search reduction, not an existence proof.

## Corollary: a bounded real formula with fixed minima and uniform margins

Put \(B=11585\) and \(\delta=1/B\). Invoke the separately justified nine-chore reduction to positive counterexamples with three distinct minima, labeled as columns 0, 1, and 2 for their respective agents.

Then a nonnegative nine-chore counterexample exists **if and only if** there is a real matrix \(C\) satisfying all of the following:

1. \(c_i(i)=1\) for \(i=0,1,2\).
2. \(1+\delta\le c_i(g)\le B\) for every \(g\ne i\).
3. \(c_0(2)-c_0(1)\ge\delta\), and \(c_0(g)-c_0(g+1)\ge\delta\) for \(g=3,4,5,6,7\).
4. For every complete allocation with three nonempty bundles, at least one literal failure has margin at least \(\delta\):
   \[
   \bigvee_{\substack{i\ne j\\g\in A_i}}
   \left[
   c_i(A_i\setminus\{g\})-c_i(A_j)\ge\delta
   \right].
   \]

This is a bounded quantifier-free linear-real formula after enumerating allocations. There are no cross-row total comparisons among these conditions.

**Proof of the forward implication.** Apply the theorem to obtain integer rows \(z_i\in[1,B]^9\), retaining every selected allocation failure and strict item order. Make the permitted canonical relabelings. Let \(a_i=\min_g z_i(g)\), so \(a_i\) is an integer in \([1,B]\), and divide row \(i\) by \(a_i\).

The normalized minimum is one, and every normalized cost is at most \(B/a_i\le B\). Any retained strict minimum or order difference is an integer at least one before division, hence is at least \(1/a_i\ge1/B=\delta\) afterward. The same reasoning applies to each selected failed EFX form: its value is an integer at least one and the entire form belongs to a single row. Thus the normalized matrix satisfies every displayed requirement.

**Proof of the reverse implication.** A matrix satisfying the formula is a valid positive cost matrix. Every surjective allocation has a strictly positive failed EFX comparison because \(\delta>0\). Every nonsurjective allocation fails by the positive-cost empty-bundle argument. Thus the matrix is a counterexample. \(\square\)

The statement is an equivalence of **existence questions**. It does not assert that every original counterexample, merely normalized, already has margins at least \(\delta\) or entries at most \(B\). The theorem may first replace each entire valuation row while preserving the selected failures.

### Equivalent common-minimum-\(B\) formula

Multiplying every normalized entry by \(B\) gives an equivalent real formula with
\[
c_i(i)=B,\qquad
B+1\le c_i(g)\le B^2=134\,212\,225\quad(g\ne i),
\]
and with each canonical order difference and each chosen allocation-failure margin at least **one**.

These scaled variables are still real or rational. They are not automatically integers: the construction gives \(Bz_i(g)/a_i\), and \(a_i\) need not divide \(Bz_i(g)\). The theorem therefore justifies this uniform-margin **linear-real** encoding, as well as the earlier integer encoding with independently valued minima; it does not justify imposing integrality on the scaled formula without another argument.

The margin estimate applies to homogeneous integer-coefficient forms within one row. It does not provide a \(1/B\) lower bound for arbitrary differences between normalized totals of different rows. Such additional constraints require their own justification.

## Verification and prior-work boundary

The proof was independently reviewed from the original row-local EFX comparisons. The already completed literal audit covered all 18,150 surjective nine-chore allocations and all 326,700 deletion comparisons, with maximum coefficient support seven. That unchanged receipt is identified by hash in [row_local_integer_bound_check.json](../verification/row_local_integer_bound_check.json).

The new exact check computes the bound by integer square root, verifies its two neighboring squares, and checks illustrative replacement-row norms. Those arithmetic controls supplement the general proof above; they do not replace it or enumerate any cost domain. No solver was run for this review, and no proof-assistant theorem was compiled.

The method uses standard polyhedral vertex arguments, Cramer's rule, and Hadamard's determinant inequality. The earlier bound note records the project's relevant determinant-method reference and limited search. No new literature search or novelty claim is made for this sharper numerical specialization.
