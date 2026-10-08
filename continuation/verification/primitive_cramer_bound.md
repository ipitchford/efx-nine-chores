# A primitive-Cramer refinement of the finite representative bound

**Status:** independently reviewed existence reduction. This result does not assert that the finite domain has been exhaustively searched. It is separate from the full zero-minimum strict-real formula, which imposes no numerical upper bound. Every previously frozen input and historical bound receipt remains unchanged. The argument uses classical vertex, Cramer, parity, and Hadamard methods; no novelty claim is made.

## Statement

For three agents and \(m\ge4\) chores, if a nonnegative additive-cost counterexample to complete EFX exists, there is a counterexample with one zero in each row and all other costs positive integers at most
\[
\boxed{Q_m=\left\lfloor\sqrt{(m-1)(m-2)^{m-2}}\right\rfloor.}
\]
The zero positions and any chosen strict order among each row's nonminimum costs can be preserved from a generic zero-minimum counterexample. In particular,
\[
Q_8=571,\qquad Q_9=2566.
\]
Raising each zero to one half and doubling then gives a positive integer counterexample with common row minimum exactly one and even nonminimum costs at most \(2Q_m\). For nine chores the latter bound is **5,132**.

The existence of a representative with pairwise distinct zero positions additionally uses the separately stated ordinary \((m-1)\)-chore baseline and the shared-minimum insertion lemma. The bound itself neither requires nor establishes that distinctness.

## 1. The row polyhedron

The preceding zero-minimum reduction in `continuation/exact_search/zero_minimum_reduction.md` shows that a counterexample can be made generic and then have exactly one globally cheapest entry in each row lowered to zero, preserving nonexistence. Literal EFX includes deletion of an owned zero-cost chore. Each resulting row has \(d=m-1\) positive free coordinates.

For every allocation into three nonempty bundles, choose one strictly failed owned-chore deletion comparison, and group the selected comparisons by their evaluating row. A selected comparison has coefficients in \(\{-1,0,1\}\). Before deleting the fixed zero coordinate, its support is
\[
|A_i|-1+|A_j|=m-|A_k|-1\le m-2=d-1.
\]
Add strict positivity and adjacent comparisons giving the selected complete order of the positive coordinates. These have support one and two, which are at most \(d-1\) because \(m\ge4\).

For each row the resulting finite homogeneous system \(Ax>0\) is feasible and can be scaled to \(Ax\ge\mathbf1\). The positivity rows imply \(x_j\ge1\). Minimizing \(\sum_jx_j\) has a nonempty compact minimizing face; an extreme point of that face is a vertex of the feasible polyhedron. Select \(d\) independent active constraints at a vertex \(v\), obtaining
\[
Dv=\mathbf1,
\]
where \(D\) is a nonsingular integer matrix whose rows have entries \(0,\pm1\) and support at most \(d-1\).

## 2. Divide all Cramer coordinates by their common divisor

Let
\[
\Delta=\det D,\qquad N_j=\det D_j,\qquad
 g=\gcd(|\Delta|,N_1,\ldots,N_d),
\]
where \(D_j\) replaces column \(j\) by ones. Define
\[
w_j=\frac{\operatorname{sgn}(\Delta)N_j}{g},\qquad
q=\frac{|\Delta|}{g}.
\]
Cramer's rule gives \(w=qv\). Because \(g\) divides the nonzero integer \(\Delta\), \(q\) is a positive integer, so
\[
Aw\ge q\mathbf1\ge\mathbf1.
\]
The coordinates \(w_j\) are positive integers and all selected failures and order constraints remain strict. Dividing only the numerator determinants by an arbitrary factor would be invalid; the same divisor of \(\Delta\) and every numerator is essential here.

## 3. A common power of two from the full rows

Fix a coordinate \(j\), and let \(f\) be the number of rows of \(D_j\) in which all \(d\) entries are nonzero. Each such row must have originated from a row of \(D\) whose \(j\)-th entry is zero and whose remaining \(d-1\) entries are all \(\pm1\): a row of \(D\) is forbidden to have full support.

Consider the \(d\times(d+1)\) augmented matrix \([D\mid\mathbf1]\). All these \(f\) rows have exactly the same pattern modulo two: zero in original column \(j\) and one in every other column, including the appended column. If \(f\ge1\), subtract one of these rows from each of the other \(f-1\) rows. All entries of those \(f-1\) resulting rows are even.

These elementary row operations preserve every maximal minor of the augmented matrix. Every maximal minor uses every row, so each is divisible by \(2^{f-1}\). Those \(d+1\) minors are, up to signs, precisely \(\Delta,N_1,\ldots,N_d\). Consequently
\[
2^{f-1}\mid g\qquad(f\ge1).
\]
This is a statement about their common divisor, not merely a separate divisibility statement for the single determinant \(N_j\).

## 4. Hadamard's inequality and the worst value of f

Every row of \(D_j\) has \(0,\pm1\) entries. Its \(f\) full rows have squared norm \(d\), and its other rows have squared norm at most \(d-1\). Hadamard's inequality therefore gives
\[
|N_j|^2\le d^f(d-1)^{d-f}.
\]
If \(f=0\), then \(g\ge1\) gives
\[
|N_j/g|^2\le(d-1)^d<d(d-1)^{d-1}.
\]
If \(f\ge1\), the common-divisor argument gives
\[
|N_j/g|^2\le\frac{d^f(d-1)^{d-f}}{4^{f-1}}.
\]
The ratio of the last bound at \(f+1\) to the bound at \(f\) is \(d/[4(d-1)]<1\) for \(d\ge3\). Hence the largest bound for \(f\ge1\) occurs at \(f=1\), where it is \(d(d-1)^{d-1}\). In either case,
\[
1\le w_j\le\left\lfloor\sqrt{d(d-1)^{d-1}}\right\rfloor=Q_m.
\]
Apply the construction separately to all three rows and restore their zero coordinates. Every surjective allocation retains its chosen strict failure. If an allocation has an empty bundle, another owner has at least two chores and at most one zero-cost chore, so some allowed deletion leaves a positive residual; that allocation also fails. This proves the statement.

## 5. Positive common-minimum lifting

In the integer zero-minimum representative, every strongest failed comparison has integer margin at least one. Raise each row's zero to one half. A worst owned-bundle deletion residual remains unchanged, because if the modified chore is owned, the bundle total and its minimum both rise by one half. A comparison-bundle cost rises by at most one half. Every chosen failure therefore still has margin at least one half. Doubling gives minimum one, even other costs in \(\{2,4,\ldots,2Q_m\}\), and failure margins at least one.

The exact arithmetic for the two relevant cardinalities is
\[
571^2=326041\le7\cdot6^6=326592<327184=572^2,
\]
\[
2566^2=6584356\le8\cdot7^7=6588344<6589489=2567^2.
\]
The earlier bounds 3,831/7,662 remain correct weaker reductions, and the previously solved unbounded reference-normalized input remains exactly the same mathematical object.
