# Transfer of the verified row cores to zero minima

The original first-row core guarantee was checked on the slice
\(c_{00}=1\), with every other entry greater than one,
\(c_{01}<c_{02}\), and \(c_{08}<c_{07}<\cdots<c_{03}\).
All EFX comparisons and all strict ordering conditions are homogeneous.
Positive rescaling therefore extends each guarantee to the cone with
\(c_{00}>0\), every other entry greater than \(c_{00}\), and the same
partial order.

Fix a finite covering core \(K\), and a boundary row with \(c_{00}=0\), all
other entries positive, and the required strict partial order. Replace only
\(c_{00}\) by a positive \(\varepsilon\) smaller than every other entry.
The perturbed row lies in the positive cone and thus admits an allocation
from \(K\) satisfying all of agent 0's literal EFX inequalities. Along any
sequence \(\varepsilon\downarrow0\), at least one allocation in the finite
set \(K\) occurs infinitely often. Its EFX inequalities are non-strict
linear inequalities, so they persist at the limit. Thus the same finite
core covers the boundary row. This is also the statement that a finite
union of closed EFX sets is closed.

This argument applies to the singleton cores, static pair cores, and every
exactly certified retained or newly learned core in the frozen final outer
formula. It includes deletions of the now zero-cost owned chore: the limit
uses every literal deletion inequality, rather than a positive-cost-only
variant of EFX.

For the other rows, the original raw region predicates are precisely their
literal EFX inequalities for all allocations in the core. The compression
rule is valid on the weak pinned-minimum cone. For two coefficient vectors
\(a,b\) in agent \(i\)'s row, its recorded certificate uses

\[
(a-b)\cdot c_i
=\left(\sum_g(a_g-b_g)\right)c_{ii}
 +\sum_{g\ne i}(a_g-b_g)(c_{ig}-c_{ii})\le0.
\]

Every multiplier on the right is nonpositive and every cost factor is
nonnegative. Setting \(c_{ii}=0\) therefore preserves the implication.
The compressed predicates continue to define the same sufficient regions
within the zero-minimum canonical domain.

In a generic canonical counterexample the three pinned minima are distinct
chores, and each row has a unique minimum. After the separate proved
minimum-lowering reduction, \(c_{11}=c_{22}=0\) while \(c_{10},c_{20}>0\).
Independent positive rescaling of rows 1 and 2 sets these two reference
entries to one. This leaves seven positive free entries per row, hence
fourteen free variables. The first row retains the partial order required
by its core guarantees after relabelling and the corresponding positive
rescaling.

The new formula consequently keeps every one of the 6,291 verified region
exclusions, substitutes
\(c_{11}=c_{22}=0\) and \(c_{10}=c_{20}=1\) in their literal predicates,
and replaces the old eighteen minimum-one domain assertions by fourteen
strict positivity assertions. Substituting zero into the old minimum-one
equalities would be invalid and is not the construction used.

Every canonical nine-chore counterexample yields a model of this new outer
formula. A certified refutation of that formula would therefore exclude
such counterexamples. A satisfying assignment supplies only two candidate
rows outside the currently proved sufficient regions; it does not supply a
three-agent counterexample.
