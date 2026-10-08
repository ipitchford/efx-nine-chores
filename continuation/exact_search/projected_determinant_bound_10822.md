# A separate projection refinement of the positive-row bound

**Status.** This note refines the nine-variable positive-row determinant estimate from 11,585 to **10,822**. The argument was independently reviewed in this session. All frozen formulas and completed runs using 11,585 are unchanged. The stronger zero-minimum reduction is documented separately in [zero_minimum_reduction.md](zero_minimum_reduction.md).

The row-local representative proof in [row_local_integer_bound.md](row_local_integer_bound.md) produces a nonsingular integer matrix \(D\in\{-1,0,1\}^{9\times9}\), each row of which has at most seven nonzero entries. A positive row vertex satisfies \(Dv=\mathbf1\). For a coordinate \(g\), let \(D_g\) replace column \(g\) of \(D\) with ones. Cramer's rule bounds the corresponding scaled integer coordinate by \(|\det D_g|\).

Permute columns to write \(D_g=[\mathbf1\ U]\), where \(U\) contains the eight unchanged columns. The original replaced column has a nonzero entry because \(D\) is nonsingular. Therefore the unchanged columns contain at most \(9\cdot7-1=62\) nonzeros, and
\[
\|U\|_F^2\le62.
\]
Let \(P=I-\mathbf1\mathbf1^\mathsf T/9\), the orthogonal projection onto the eight-dimensional subspace perpendicular to \(\mathbf1\). The Gram determinant identity, or an orthonormal change of basis with first vector \(\mathbf1/3\), gives
\[
\det(D_g)^2=9\det(U^\mathsf T P U).
\]
The latter Gram matrix is positive semidefinite. Its eight eigenvalues are nonnegative, so arithmetic–geometric mean yields
\[
\det(U^\mathsf T P U)
\le\left(\frac{\operatorname{tr}(U^\mathsf T P U)}8\right)^8
=\left(\frac{\|PU\|_F^2}8\right)^8
\le\left(\frac{62}8\right)^8.
\]
Taking square roots,
\[
|\det D_g|\le3\left(\frac{31}4\right)^4
=\frac{2\,770\,563}{256}
=10\,822+\frac{131}{256}.
\]
Since the determinant is an integer,
\[
\boxed{|\det D_g|\le10\,822.}
\]

The independent-row construction therefore gives positive integer representative costs at most 10,822 for any three-agent nine-chore counterexample, retaining the previously prescribed strict row orders. It imposes no equality between the three integer minima and uses no positivity assumption in the determinant estimate itself. Positivity enters the earlier vertex construction and its interpretation as costs.

The improvement is about 6.6 percent and leaves the original bit widths unchanged: 14-bit positive costs and 17-bit unrestricted nine-entry row sums. It offers no credible standalone prediction of faster nine-chore solving. The zero-minimum lemma subsequently removes an entire coordinate per row and gives a materially smaller complete bound; further numerical refinement of this nine-variable estimate has not been pursued.

Exact rational arithmetic, floor inequalities, and the dimension/support parameters are recorded in `projected_determinant_bound_10822_audit.json`. That receipt supplements the self-contained proof above; it is not an enumeration of all matrices or an EFX existence certificate.
