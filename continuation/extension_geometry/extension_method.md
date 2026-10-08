# Exact extension regions for the three-agent, nine-chore problem

## Scope

This is a computational reformulation and certificate method. It is not a
universal nine-chore existence proof. Such a proof would additionally require
a globally checked statement that the certified regions cover the appropriate
canonical space of eight-chore prefixes. No priority claim is made for the
general ideas of counterexample-guided refinement, interval covers, or linear
redundancy certificates.

The implementation is `extension_oracle.py`. The independent checker is
`verify_extension_certificate.py`, which uses only the Python standard
library and does not import the oracle or any solver.

By default the extension variable ranges over the entire nonnegative
orthant. The optional `extension_domain_lower` records three nonnegative
coefficient vectors b_i and restricts the guarantee to x_i >= b_i(C_i).
The result and verification receipt state that conditional scope explicitly.

## 1. Exact box geometry

Fix a nonnegative three-agent cost matrix C on eight chores, and write
x = (x_0,x_1,x_2) for the costs of a ninth chore e. For a complete allocation
A of all nine chores, put B_i = A_i minus e, and let k own e. For any agent i,
owned chore g, and other agent j, its EFX comparison has the form

    q(C_i) + s x_i <= 0,

where q is an integer linear form in the eight prefix costs and
s belongs to {-1,0,1}. This follows directly by expanding
c_i(A_i minus g) - c_i(A_j). In particular, it includes the deletion of every
zero-cost owned chore.

For s=0, the comparison is a constant requirement on the prefix. For s=1,
it gives an upper bound x_i <= -q(C_i). For s=-1 it gives a lower bound
x_i >= q(C_i). Their intersection with the nonnegative orthant is therefore
a closed axis-aligned box, possibly empty or unbounded.

There is also a useful bundle interpretation. Put
r_i(B_i) = c_i(B_i) - min_{g in B_i} c_i(g) for nonempty B_i, with residual
zero for the empty bundle. If B_k is nonempty, the owner's requirements are

    c_k(B_k) <= min_{j != k} c_k(B_j),
    x_k <= min_{j != k} c_k(B_j) - r_k(B_k).

Thus the old owner must be ordinarily envy-free. If B_k is empty, its new
bundle is a singleton and there is no upper bound on x_k. For each nonowner
i, the comparison against the other nonowner j is the constant requirement

    r_i(B_i) <= c_i(B_j),

and the comparison against k is

    x_i >= r_i(B_i) - c_i(B_k).

The old prefix partition need not itself be EFX: a nonowner may envy B_k
until the extra chore increases that bundle's cost.

Enumerating all 3^8 old labelled partitions and each of three owners covers
exactly all 3^9 complete allocations. The oracle first finds a small cover
of the nonnegative orthant by their nonempty boxes. If no cover exists, it
returns an exact rational ninth column and checks the resulting full matrix
over all 19,683 complete labelled allocations.

## 2. Generalising a numerical cover to a linear region

Fix a selected collection of allocations whose numerical boxes cover the
orthant at the sampled prefix C. Keep all their constant requirements
q(C_i) <= 0. For each remaining comparison, the complement of its box has
one of the strict atoms

    x_i > U(C_i),        x_i < L(C_i).

Failure of one selected allocation is a disjunction of its strict atoms.
Failure of every selected allocation is the conjunction of those
disjunctions. No minimum-cost-item choice is frozen: every original trim
remains represented symbolically.

Two types of exact incompatibility suffice:

* The atom x_i < L(C_i) is impossible on x_i >= 0 whenever L(C_i) <= 0.
* The atoms x_i > U(C_i) and x_i < L(C_i) cannot both hold whenever
  U(C_i) >= L(C_i).

With a recorded extension lower bound x_i >= b_i(C_i), the first premise
is replaced by b_i(C_i) >= L(C_i). The default b_i=0 recovers the original
orthant argument. The independent checker verifies the exact coefficient
identity for this replacement, and rejects a tested certificate if its
required extension bounds are removed.

Each incompatibility is justified by a homogeneous, row-local linear
inequality in C. If a finite set of these incompatibilities makes the
allocation-failure clauses propositionally inconsistent, those linear
conditions, together with the constant EFX requirements, are a sufficient
region for extension. Every nonnegative prefix in the region has an EFX
allocation for every ninth column in the explicitly stated extension domain.

The Boolean inconsistency can be checked without an SMT solver. Maintain
the set of atoms blocked by unit incompatibilities and previously selected
atoms. Choose an unsatisfied allocation clause. Every possible still
unblocked atom in that clause must be selected in turn. If every branch
eventually reaches a clause with all its atoms blocked, the initial clause
system is inconsistent. Memoisation avoids repeated states. The independent
checker implements precisely this finite exhaustive recursion. For the
first 165 cached CEGIS regions, at most 12 states were needed per region.

Consequently, numeric box coverage is not merely sampled evidence: the
resulting symbolic region certificate has an exact logical implication
valid for every prefix satisfying its stated conditions, including all
boundary and zero-cost cases.

## 3. Exact linear compression

Many region conditions follow from the other conditions and C >= 0. For
each removed inequality q(C_i) >= 0, the certificate records an identity

    q = sum_j lambda_j r_j + sum_g mu_g e_g,

where every lambda_j and mu_g is a nonnegative rational, the r_j are retained
inequality coefficient vectors, and e_g is a coordinate unit vector.
The independent checker verifies every rational coefficient, its sign, and
the coefficient identity with Fraction arithmetic.

An optional canonical background can supply additional generators. In that
case the certificate explicitly records the background and the extension
guarantee is conditional on it. It does not silently upgrade a conditional
region to an unconditional one.

For one difficult saved prefix, its selected seven-allocation cover gave
121 distinct uncompressed conditions. Removing linear redundancies left
42 conditions. Using the 26 explicit weak canonical order conditions below
as background left 16. Both reductions have exact rational certificates.

## 4. Canonical space and the global proof obligation

A hypothetical nonnegative nine-chore counterexample can be perturbed to
have positive costs and unique minima, because each of finitely many
allocations has a strict failed inequality. Known eight-chore existence and
the shared-minimum insertion lemma handle the case in which two agents
share a minimum. Thus a hypothetical counterexample may be assumed to have
three distinct minimum chores.

Keep all three minimum chores in the eight-column prefix. Independently
scale each row so that its minimum is one. Within this slice, small
perturbations of nonminimum costs preserve every strict failed allocation
comparison and can separate the three prefix row totals. Choose the row
with the smallest prefix total as row 0. Label the other two rows and their
minimum columns so that c_01 < c_02. Sort the five free prefix columns so
that c_03 > c_04 > c_05 > c_06 > c_07.

The recorded weak row-local background consists of:

* c_ig - c_ii >= 0 for each i and g != i;
* c_02 - c_01 >= 0;
* c_0g - c_0,g+1 >= 0 for g = 3,4,5,6.

The global prefix solver additionally fixes equal positive minima and
requires row 0's prefix total to be strictly smaller than both others.
These latter cross-row conditions are not used implicitly in the region
certificates.

If R_t(C) is the conjunction for a certified extension region, a genuine
counterexample prefix must satisfy

    canonical_domain(C) and every t: not R_t(C).

Every failed R_t supplies a strict negative linear witness. All strict
domain and failure margins can be made at least one by one common positive
scaling, while keeping the common minimum free. Therefore the use of unit
margins does not impose a bounded-integer restriction.

An independently checked UNSAT proof of that global formula, together with
the canonical reduction and the independently checked region certificates,
would prove the universal nine-chore statement. A SAT model instead gives
another exact prefix to pass to the extension oracle. A timeout proves
neither result.

## 5. Perturbing solver models away from accidental equalities

The generated region vectors have coefficients in {-2,-1,0,1,2}. Clear
denominators in a prefix model, multiply its integer entries by
M = 1000 times 5^8, and add 5^g to each nonminimum entry c_ig, leaving c_ii
unchanged. Equal minima remain equal. A row-local linear form with the
stated coefficient range changes by less than 195,313, while any prior
nonzero integer margin was enlarged to at least M = 390,625,000.

Thus every previously selected strict comparison keeps its sign. For a
nonzero coefficient vector, a zero original value acquires a nonzero
perturbation: balanced base-5 uniqueness applies to its nonminimum
coordinates; a vector supported only at the minimum already has nonzero
value. This ensures that no generated nontrivial region facet passes
through the perturbed sample merely because the SMT model selected an
accidental sum equality.

The runner also checks its exact background inequalities, the two strict
prefix-total inequalities, and every previous region exclusion directly
after perturbation. These checks are part of the recorded computation.

## 6. A smaller canonical extension domain

The extension variable need not range over all of the nonnegative orthant
when searching only for canonical counterexamples. At least x_i >= c_ii is
necessary because each global row minimum remains in the prefix.

It is also possible simultaneously to require x_0 >= c_03 and to keep row
0's prefix total smallest. To see this, equalise all row minima in a full
nine-chore instance. Let F be the six chores other than the three pinned
minima, let T_i be each full row total, and choose an index i minimising

    T_i - max_{g in F} c_i(g).

Delete a free chore e attaining that row's maximum. For every j,

    T_j - c_j(e) >= T_j - max_{g in F} c_j(g)
                  >= T_i - max_{g in F} c_i(g).

Hence the chosen row has minimum prefix total and its deleted chore has
cost at least every remaining free prefix chore. Relabel it as row 0 and
sort the remaining free columns as above. Generic perturbation can make
the required canonical comparisons strict.

The oracle restricted to x_0 >= c_03, x_1 >= c_11, x_2 >= c_22 therefore
suffices for the main problem. This option is implemented; the default
remains unrestricted extension, so all previously generated certificates
keep their original scope. The bounds are recorded as the three unit
coefficient vectors at positions 3, 1, and 2 respectively. In the Boolean
certificate, impossibility of x_i < L is justified by the recorded lower
bound being at least L.

One canonical sample produced a two-allocation cover with seven returned
prefix conditions under this restricted extension domain. Its independent
standard-library checker passed, and a separate 27-variable direct formula
confirmed that the prefix domain, seven region conditions, ninth-column
bounds, and failure of both literal full EFX allocations are jointly
unsatisfiable. Removing the extension-bound record was deliberately tested
and correctly rejected by the independent checker. These are validations
of that conditional region, not a proof that all prefixes are covered.
