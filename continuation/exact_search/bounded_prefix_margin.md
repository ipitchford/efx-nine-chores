# Bounded prefix search with exact margins

**Status.** This note justifies an additional restriction of the prefix search as a necessary condition for a full nine-chore counterexample. It does not assert a solver verdict or equivalence between the SAT status of two partial prefix searches.

Let \(B=11585\), \(\delta=1/B\), and fix a **finite** family of verified extension regions
\[
R_t(C)=\bigwedge_{q\in Q_t}q(C_{i(q)})\ge0.
\]
Each \(q\) is a homogeneous integer-coefficient form in one prefix row. The regions' recorded backgrounds are the weak row-local canonical inequalities, and their extension guarantees hold on the recorded ninth-column domain. The current family permits the common restricted domain
\[
x_0\ge c_{03},\qquad x_1\ge c_{11},\qquad x_2\ge c_{22}.
\]
No strict comparison between different row totals is an implicit premise of these local certificates.

## Proposition

If a nonnegative three-agent nine-chore counterexample exists, then there is an eight-column prefix satisfying all of the following:

1. The three pinned row minima equal one.
2. Every other prefix cost is at most \(B\) and exceeds its row minimum by at least \(\delta\).
3. \(c_{02}-c_{01}\ge\delta\), and \(c_{0g}-c_{0,g+1}\ge\delta\) for \(g=3,4,5,6\).
4. Row 0's prefix total is **strictly** smaller than each other prefix total. No \(\delta\) margin is required for these two comparisons.
5. For every region \(R_t\), at least one of its recorded premises satisfies
   \[
   q(C_{i(q)})\le-\delta.
   \]

The prefix extends to a positive nine-chore counterexample satisfying the stated ninth-column bounds.

## Proof

By the [independent-row integer bound](row_local_integer_bound.md), take a counterexample \(Z\) with distinct costs within every row and all entries integers in \([1,B]\). The separately justified shared-minimum reduction allows three distinct minimum chores. Let \(a_i\) be the integer minimum in row \(i\). Since that row contains nine distinct positive integers,
\[
a_i+8\le B,\qquad a_i\le B-8.
\]
Normalize row \(i\) by dividing by \(a_i\). Every cost is at most \(B\). Every strict within-row difference and every selected allocation-failure form, being an integer before division, now has magnitude at least
\[
\frac1{a_i}\ge\frac1{B-8}>\frac1B=\delta.
\]
This strict slack above \(\delta\) is essential.

Let \(F\) be the six chores other than the three minima, and let \(T_i\) denote the normalized full-row total. Choose a row minimizing \(T_i-\max_{g\in F}c_i(g)\), and delete a maximizing free chore \(e\) in that row. For every \(j\),
\[
T_j-c_j(e)\ge T_j-\max_{g\in F}c_j(g)
\ge T_i-\max_{g\in F}c_i(g).
\]
Thus the selected row has a weakly least prefix total, and its deleted chore is at least as costly as every remaining free chore. Relabel that row as row 0, order the other two pinned minima by its costs, and sort its five remaining free chores decreasingly.

The resulting prefix satisfies every weak background condition, and the full counterexample's deleted column belongs to every region's required extension domain. Consequently it lies outside every \(R_t\); otherwise that region's certificate would supply an EFX allocation of the full matrix. For each region choose a failed premise \(q_t\). Before row normalization its value is a negative integer, so
\[
q_t(C_{i(q_t)})\le-\frac1{a_{i(q_t)}}<-\delta.
\]

It remains to make the two prefix-total comparisons strict while retaining these margins. Subtract a common sufficiently small \(\varepsilon>0\) from **all eight nonminimum entries of full row 0**, including the deleted free chore. Leave its minimum and both other rows unchanged.

Exactly seven row-0 prefix entries change, so its prefix total falls by \(7\varepsilon\). Both previously weak total comparisons become strict. Differences between two nonminimum row-0 entries are unchanged; in particular the pinned-order comparison, the free-item order, and the deleted-largest-free relation are preserved. The minimum gaps decrease only by \(\varepsilon\), and upper cost bounds remain valid because costs decrease.

There are only finitely many selected allocation failures and selected region witnesses. They all initially have strict slack above the required \(\delta\) magnitude. For an explicit choice, put
\[
s=\frac1{B-8}-\frac1B>0.
\]
For each affected row-0 form \(h\), let \(L_h\) be the absolute sum of its coefficients on nonminimum coordinates. Include both the selected full-allocation failure forms and selected prefix-region witness forms, and set \(L=\max(1,\max_h L_h)\). Choosing
\[
0<\varepsilon<\frac{s}{2L}
\]
changes each such form by less than \(s/2\). It preserves every chosen EFX failure with margin at least \(\delta\), every chosen negative region witness at most \(-\delta\), and every minimum gap at least \(\delta\). All other-row forms are unchanged. Positivity still excludes EFX allocations with an empty bundle.

The modified full matrix remains a counterexample, and its prefix has all the claimed properties. \(\square\)

## Consequence and logical scope

The proposed bounded prefix formula has 52 base assertions: three fixed minima, 26 row-local canonical inequalities with margin \(\delta\), 21 nonminimum upper bounds, and two strictly positive cross-row total differences. Every learned exclusion is the disjunction of \(q\le-\delta\) over one certified weak region's premises.

A checked **UNSAT** proof for this bounded formula, together with the local region certificates and the reductions above, excludes a full nine-chore counterexample. A **SAT** prefix remains an input to the extension oracle. Its existence need not imply a full counterexample.

In particular, this argument does not claim that the old unbounded residual prefix formula is satisfiable exactly when the bounded residual formula is satisfiable. Both are relaxations of the full counterexample condition. If full nine-chore allocation-failure conditions and the deleted column are retained, the representative argument does give the corresponding equivalence of full-counterexample existence questions.

The proposition applies to each fixed finite valid region family. It need not preserve one particular original model, and it does not require a single perturbation to work uniformly for an infinite future family.

## Implementation review

The bounded-representative flag in the inspected prefix runner:

- requires fixed minima and the restricted ninth-column domain;
- computes \(\delta\) as an exact rational;
- uses \(\ge\delta\) for the 26 row-local gaps and \(\le-\delta\) for learned exclusions;
- adds the 21 nonminimum cost bounds;
- leaves both cross-row total differences strictly positive.

The runner may pass a separately perturbed integer prefix to the oracle. The oracle's new weak sufficient region is required, by an exact assertion, to contain the original SMT model after common denominator clearing. Homogeneity makes that membership equivalent to membership of the original normalized point. Thus leaving the bounded box during oracle sampling does not prevent the learned region from removing the actual current model.

This source inspection found no blocking discrepancy with the proposition. It did not launch the restart or run a global solver.
