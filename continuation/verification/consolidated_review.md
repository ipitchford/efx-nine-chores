# Consolidated independent review of the nine-chore continuation

**The full nine-chore target is proved by an independently checked computer-assisted argument.** The complete exact LRA refutation, full written target reduction, and current release binding have passed. Every nonnegative additive three-agent nine-chore instance has a complete literal EFX allocation, including the deletion of owned zero-cost chores. The current completion is recorded in Section 13 and [zero9_full_target_binding.json](zero9_full_target_binding.json).

The complete eight-chore exact LRA certificate supplies the retained alternative baseline. The nine-chore proof independently checks original CNF and affine atoms, all 172,146 Boolean derivations and 8,088,323 ordered reasons, and exact Farkas certificates for all 370,780 admitted theory axioms. No producer verdict or callback assumption is a checking premise. All recorded production and checking subprocesses are terminal. Earlier sections and receipts preserve the successive historical scopes; they do not supersede this current completion.

Review updated on 8 October 2026. The earlier positive-minimum release boundary comprises **1,956 prefix-extension regions**, a **6,309-assertion two-row input** with **2,005 distinct nonordinal cores**, and the complete **18,177-assertion zero-minimum nine-chore input**. Its portable certificate phase finished at **21:55:09 UTC** and its zero-formula phase at **22:05:17 UTC on 7 October**, both against the same historical immutable release index. These remain completed standard-library checks, with exact rational arithmetic and no solver invocation. The new full-target index is separate and retains their exact historical identities where needed.

The strongest finite reduction now gives one zero in each row and all other costs positive integers at most **2,566**. Lifting those zeros gives a positive integer counterexample, if any exists, with common minimum one and even nonminimum costs at most **5,132**. The primitive-Cramer refinement is documented in Section 9; the earlier 3,831/7,662 reductions remain valid and their formulas stay unchanged. The earlier **11,585** positive-row bound and the formulas that used it remain valid and unchanged. These are complete reductions of the search domain, not completed searches; see Sections 3.6–3.7.

## 1. Target and inspection boundary

The target, frozen in [target.yaml](../../target.yaml), is:

> For every nonnegative additive cost matrix \(C\in\mathbb R_{\ge0}^{3\times9}\), there is a complete allocation \(A=(A_0,A_1,A_2)\) such that, for every agent \(i\), every other agent \(j\), and **every owned chore** \(g\in A_i\),
> \[
> c_i(A_i\setminus\{g\})\le c_i(A_j).
> \]

Every chore is assigned once, empty bundles are permitted, and the deletion quantifier includes zero-cost owned chores. The stronger requirement that a prescribed agent be ordinarily envy-free is a separate target; its eight-chore obstructions do not refute this target.

The Proof Digest informal track applies. The objects checked here are handwritten reductions, exact rational or integer certificate identities, finite Boolean coverage, and the correspondence between those certificates and particular SMT assertions. No proof-assistant development, theorem elaboration, transitive axiom audit, or end-to-end formalization is present.

This resumed review read the preserved audit programs and receipts; the extension-method, finite-bound, first-row-elimination, cardinality, and structural-limitations notes; the repaired row-core checker and its generator; and the paired-seed checker and enumeration interface. The preceding independent audit's inspected files are identified in [inspected_source_manifest.json](inspected_source_manifest.json). Their nine hashes matched at the 20:45:48 UTC resumption boundary. The search runner was subsequently extended to use more source regions and paired seeds; the current review binds the actual frozen assertions independently of that runner. The three checkers used for the latest audit have their own hashes in its receipt. This is not a complete source audit of Z3, cvc5, Python, or the earlier research package. The prior literature and smaller externally checked refutations in [the earlier verification record](../../docs/VERIFICATION.md) were not re-researched or replayed in this resumed pass.

## 2. Evidence preserved and reproduced

The resumed pass first checked the byte identity of completed evidence without repeating its mathematical tests. All 1,010 listed source/certificate entries matched: 641 prefix certificates, 169 row-core certificate files, 191 compressed-region records, and nine implementation/document sources. Six separately bound snapshot and seed files also matched. The hash replay took 0.089 seconds and peaked at 13,496 KiB RSS under Python 3.12.14. A hash match establishes continuity of evidence, not mathematical validity by itself. The subsequent computations addressed new evidence: 341 frozen cores, 51 more cores in a later immutable checkpoint, 1,048 paired seeds, and the complete corresponding outer assertion set.

The earlier completed, bounded checks are preserved as historical evidence:

| Check | Precisely recorded coverage | Result and resource use | Evidence |
|---|---|---|---|
| Prefix extension certificates and static SMT correspondence | 641 certificates: 300 for all nonnegative ninth columns and 341 for columns above the recorded linear lower bounds | Passed; 5.838 s; 52,172 KiB peak RSS | [prefix_snapshot_audit.json](prefix_snapshot_audit.json) |
| Boolean refutation checker controls | 17,522 Boolean systems compared against exhaustive truth tables; at most 12 recursion states per archived prefix certificate | Passed within the prefix audit | Same receipt |
| Literal support and finite-bound arithmetic | All 18,150 surjective allocations; 326,700 literal comparisons; maximum support seven; exact integer square-root bound | Passed within the prefix audit | Same receipt |
| Canonical deletion sanity checks | 10,000 exact integer samples, including 9,970 with strict minimizing scores | Passed; these samples supplement the general argument | Same receipt |
| Row-core alternatives and source binding | 169 certificate files: 60 legacy and 109 version 2; 24,416 checked branch records, maximum 8,192 in one certificate | Passed after type repair; 7.504 s; 60,656 KiB peak RSS | [row_core_audit.json](row_core_audit.json) |
| Ordinal singleton seeds, compression, and outer assertion binding | 3,238 seeds, each checked on all 28 allowed full first-row orders; 109 resumed regions; 191 new compressed records | Passed for the stated layers; 2.420 s; 166,788 KiB peak RSS | [row_compression_audit.json](row_compression_audit.json) |
| Additional frozen cores and exact source/compression binding | 284 compressed cores and 57 resumed cores; 3,752 exhaustive branch records, maximum 256 per core | Passed; generation 20.672 s; independent audit 1.181 s and 16,460 KiB peak RSS | [frozen_row_core_audit.json](frozen_row_core_audit.json) |
| Complete outer input frozen at the 20:54 checkpoint | 18 domain assertions plus 4,787 learned clauses; 1,048 paired certificates with 4,192 branches; 51 additional cores with 728 branches; all 450 prior core guarantees carried forward by hash | Passed; 51-core generation 3.783 s; independent final audit 3.420 s and 154,508 KiB peak RSS | [outer_resumed2_checkpoint1_audit.json](outer_resumed2_checkpoint1_audit.json) |

The legacy and version 2 core files overlap. They certify **109 distinct resumed cores**, not 169 distinct regions. The branch-record total likewise counts both formats where both were retained.

The 20:54 checkpoint uses **501 distinct nonordinal core allocation sets**: the original 109 plus 284, 57, and 51 additional cores. Their version 2 certificates contain 5,616 exhaustive branch records in total. The 1,048 paired seeds add 4,192 branch records. These historical counts exclude the 60 duplicate legacy certificate files.

The original bounded audit commands, run from the package root, are:

    python3 continuation/verification/audit_prefix_snapshot.py
    python3 continuation/verification/audit_row_cores.py
    python3 continuation/verification/audit_row_compression.py
    python3 continuation/verification/audit_frozen_row_cores.py
    python3 continuation/verification/audit_outer_resumed2_checkpoint1.py

Each audit program sets a 480 MiB address-space limit and a 29-second alarm. Certificate generation was separately guarded by 480 MiB and a 27-second alarm; both generation batches completed with exit zero. The first three audit programs take snapshots of live source directories when invoked, so rerunning them after growth may change their evidence set. The last two audit programs use explicitly frozen inputs. Preserved receipts and hashes identify every run. No audit command here establishes a global solver verdict.

### 2.1 Final frozen release evidence

The explicit [release_certificate_index.json](release_certificate_index.json) names the valid certificates and every source or input needed by its replay. Invalid mutation fixtures are excluded. Its SHA-256 is `a3c55d0a8a1b6d60d03d56aff7cb0f57266899e4347a4b4f40d9df87c07d6edf`.

| Final check | Precisely checked objects | Completed result |
|---|---|---|
| Bounded prefix input | 1,956 certificates; 52 domain assertions; 1,956 exact region-complement clauses; 2,008 assertions altogether | All passed in the portable replay; 13.750 s |
| Positive-minimum two-row input | 18 domain assertions; 3,238 singleton guarantees; 1,048 static pair guarantees; 2,005 distinct nonordinal cores; 6,309 assertions altogether | All local certificates, original/reduced-core subset implications, source hashes, compression witnesses, and the ordered assertion sequence passed; 13.535 s |
| Zero-minimum full nine-chore input | 21 free real declarations; 27 domain assertions; 18,150 allocation clauses; all 191,104 retained literal positions | Every serialized affine failure form and clause reconstructed independently; 4.650 s in the portable zero-formula replay |
| Release binding | 1,956 prefix certificate entries, 2,005 row-certificate entries, and 8,245 bound files | The same hashes passed in both replay phases |

The final prefix family comprises **300** guarantees for every nonnegative ninth column and **1,656** guarantees for ninth columns above the recorded canonical lower bounds. All 255 regions added by the bounded run were also checked to contain their original, unperturbed SMT point. The arithmetic checker verified 106,116 conic identities and the Boolean checker visited 5,281 states across this family. Counts of regions, identities, and states measure the recorded evidence; they do not measure the fraction of the domain covered.

The final two-row input has **6,291 learned clauses**. Its 2,005 nonordinal cores comprise 827 archived exact cores, 1,088 direct pairs, 20 directly reduced cores, one larger historical core justified by an exact reduced-subset implication, and 69 direct fallback cores. The complete replay rechecked the registry of 889 historical version 2 certificates with 11,212 branch records, all singleton and static-pair guarantees, reduced-core/subset and resumption-pruning implications, 4,832 direct pair branches, and 1,144 direct fallback branches. The registry includes historical proofs retained for provenance even when a stronger region replaced them in the final input. Its branch count is therefore not a count of distinct final clauses. The 130,333 raw region atoms and 59,064 retained atoms were bound to the literal allocation predicates and their exact compression witnesses.

The successful phase receipts are [release_replay_final_certificates/release_replay.json](release_replay_final_certificates/release_replay.json) and [release_replay_final_zero_formula/release_replay.json](release_replay_final_zero_formula/release_replay.json). Together they cover every phase of the portable command `python continuation/verification/release_replay.py --phase all`. The later phase did not rerun the unchanged certificate audit. No package installation, network access, or solver is needed for this replay; a Unix-like Python runtime is used for the resource and alarm guards.

### 2.2 Later static audits and a concrete noncoverage witness

The positive lifting corollary also has independently reconstructed serialized formulas. The eight-chore calibration has 21 free real variables, 47 domain assertions, 5,796 allocation clauses, and 54,360 retained literal positions. The nine-chore formula has 24 free real variables, 54 domain assertions, 18,150 allocation clauses, and 191,104 retained literal positions. Both audits passed, in 1.652 and 6.219 seconds respectively, using only standard-library exact arithmetic. Their [eight-chore](lifted8_formula_audit.json) and [nine-chore](lifted9_formula_audit.json) receipts bind every assertion to the fixed-minimum-one bounds and unit failure margins. These are complete static checks; no solver was called by either audit.

The verified finite row guarantees transfer to a zero first-row minimum by closedness, while the other two rows can each be normalized by a positive reference entry. A fresh two-row input therefore has 14 free variables, 14 positive-domain assertions, and the same 6,291 exclusions. [zero_outer_audit.json](zero_outer_audit.json) independently reconstructed all 6,305 assertions and all 59,064 retained literal positions, binding 633 source files in 4.254 seconds. It explicitly checks that the old minimum-one equations were replaced rather than incorrectly subjected to zero substitution.

That zero-minimum outer formula subsequently returned SAT. Its exact model satisfies every serialized assertion, as recorded in [run1_model_verification.json](../structural_nine/zero_outer/run1_model_verification.json). Raising each zero minimum to \(1/304\) and scaling both rows by 304 produces these positive integer rows:

| Evaluating row | Chore 1 | Chore 2 | Chore 3 | Chore 4 | Chore 5 | Chore 6 | Chore 7 | Chore 8 | Chore 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Agent 1 in the zero-based code | 304 | 1 | 8 | 1524 | 860 | 882 | 216 | 84 | 120 |
| Agent 2 in the zero-based code | 304 | 6 | 1 | 1002 | 726 | 902 | 228 | 36 | 56 |

[verify_positive_outer_witness.py](verify_positive_outer_witness.py) independently evaluated all **6,309** assertions of the original positive-minimum final input at these rows. Every domain assertion and every one of the 6,291 exclusions passed. The smallest, over exclusions, of their maximum satisfied strict-atom margin is **one**. The [receipt](positive_outer_noncoverage_witness.json) proves that this particular finite region family **does not cover its two-row domain**. No first row is supplied, so this witness is not a three-agent EFX counterexample. Additional regions are required before this family can support a global proof.

The completed evidence, later proof/source files, and a merely prepared CPC configuration are jointly hash-bound in [release_completion_audit.json](release_completion_audit.json). Its 8,333 file bindings passed without repeating the underlying successful mathematical checks. The CPC controls are explicitly synthetic I/O and failure-injection checks; no real solver or external proof checker was invoked by them.

## 3. Reductions whose mathematical scope is justified

### 3.1 Positive generic counterexamples suffice

If an instance has no EFX allocation, each of finitely many complete allocations has a strictly positive failed comparison. Select one failure for each allocation. A sufficiently small perturbation preserves all selected margins and can make all costs positive and all costs within each row distinct. Positive independent row scaling preserves the comparisons.

In a positive nine-chore instance, an allocation with an empty bundle cannot be EFX: one of the other two bundles has at least two chores, so its positive residual exceeds the empty bundle's zero cost. Thus a search after the genericity reduction may omit nonsurjective allocations. It may not use that omission directly on arbitrary matrices with zeros.

The distinct-minimum canonicalization additionally invokes the earlier eight-chore existence theorem and shared-minimum insertion lemma. Those dependencies are stated in [the ancillary proofs](../../docs/ancillary_proofs.md) and inherited from the earlier review. Neither the prefix route nor the first-row-elimination route requires the unresolved prescribed-agent hypothesis \(D_8\).

### 3.2 A fixed allocation gives an exact extension box

Write \(x_i\) for agent \(i\)'s cost of the ninth chore. Every literal EFX comparison expands to \(q(C_i)+s x_i\le0\), where \(s\in\{-1,0,1\}\). Therefore its feasible extension set is a closed axis-aligned box, subject to constant prefix conditions. Every original trim is represented, including deleting a zero-cost chore.

Failure of every selected allocation is a conjunction of disjunctions of strict upper or lower endpoint violations. The certificate records exact incompatibilities between those violations. Its Boolean checker exhausts the possible selections; its arithmetic checker reconstructs the literal coefficient vectors and checks all required nonnegative rational identities. The implication is valid throughout the certified region, not just at the sampled prefix.

Every restricted certificate in the final family is valid on the common canonical ninth-column domain
\[
x_0\ge c_{03},\qquad x_1\ge c_{11},\qquad x_2\ge c_{22}.
\]
The 300 unrestricted certificates remain valid on this smaller domain as well. Erasing the restricted domain is not legitimate and was rejected by a mutation check.

The simultaneous deletion reduction is sound: after normalizing minima, let \(F\) be the six nonminimum chores and choose \(i\) minimizing \(T_i-\max_{g\in F}c_i(g)\). Delete a maximizing free chore \(e\) in that row. For every \(j\),
\[
T_j-c_j(e)\ \ge\ T_j-\max_{g\in F}c_j(g)\
\ge\ T_i-\max_{g\in F}c_i(g).
\]
Thus the selected row has least prefix total, while the removed free chore is at least as costly to that row as any remaining free chore. The generic perturbation makes the canonical comparisons strict when needed. This argument, not the 10,000 samples alone, justifies the restricted extension domain. See [extension_method.md](../extension_geometry/extension_method.md), Sections 1–4 and 6.

### 3.3 The first-row elimination implication is valid

The domain is a product \(D_0\times D_{12}\). The first row has minimum one in column 0, has \(c_{01}<c_{02}\), and orders the six free columns decreasingly. The other two rows have minimum one in their respective pinned columns. This route imposes no cross-row total ordering.

For a finite allocation set \(K\), suppose the first-row domain cannot make every allocation in \(K\) fail agent 0's EFX conditions. If both other rows satisfy their EFX conditions for every allocation in \(K\), some allocation in \(K\) is EFX for all three rows. This is a quantified implication over the entire allowed first row, as proved in [row_elimination_proof.md](../structural_nine/row_elimination_proof.md).

Each nonordinal core certificate expands the conjunction of allocation-failure disjunctions into every distinct selection of strict failure rows. For every selection, it supplies a nonzero nonnegative rational combination of the strict domain/failure rows equal to the zero coefficient vector. If all those strict inequalities held, that combination would be positive and zero simultaneously. Exhausting the selections proves the required inner unsatisfiability. The reconstructed coefficients and nonnegative weights are exact.

Version 2 keeps only deletions of potentially cheapest owned items under the first-row partial order. This is sound because deleting the cheapest owned item produces the largest residual. The checker verifies that every omitted item is strictly above a retained possible minimum and checks the resulting complete failure clauses.

### 3.4 Singleton and paired seeds have direct guarantees

There are 28 full first-row orders compatible with the partial order: choose the two ordered positions of columns 1 and 2 among eight nonminimum positions. For each order, deleting agent 0's cheapest owned item leaves a residual that must be dominated by both comparison bundles.

The audit checks all upper-rank threshold counts. These inequalities express an injection matching every residual chore to a weakly more expensive comparison chore. Summing those costs proves the residual comparison for every positive valuation respecting that order. The empty residual also passes. Thus all 3,238 audited singleton seeds have direct first-row guarantees; they do not depend on an inner solver's UNSAT verdict.

The **1,048 paired seeds** use a different exact argument on the same first-row cone. Each allocation gives columns 0, 1, and 2 to their respective agents. Because agent 0 owns its global minimum, deleting column 0 is its strongest EFX deletion test, leaving two possible failure inequalities. For a pair of allocations there are four combinations of these failures.

The nine independent positive gap coordinates are \(c_{00}\), \(c_{01}-c_{00}\), \(c_{02}-c_{01}\), \(c_{08}-c_{00}\), and the five successive gaps from \(c_{08}\) up to \(c_{03}\). For each of the four combinations, the certificate expresses zero as a nonnegative rational combination of the two failure forms and coordinate gap forms, with positive total weight on the failure forms. If both failures held, this expression would be positive, a contradiction. Reconstructing all allocation coefficients and checking all 4,192 identities proves that one allocation in each pair satisfies agent 0 on every allowed first row. This is an exact cone argument, rather than a claim that one fixed allocation works for every valuation in a full order.

The paired checker rejected five targeted mutations: an omitted failure combination, a negative weight, zero weights on both failure forms, a floating-point rational numerator, and an incorrect allocation ID. The audit establishes the validity of the archived pairs; it does not claim that these pairs alone cover the other-row domain.

### 3.5 Compressed other-row regions are equivalent on the stated domain

The raw conditions are reconstructed directly from every owned-item deletion for agents 1 and 2. Conditions with no positive coefficient are valid for every nonnegative row and may be omitted. Every retained atom is itself a raw atom.

For a raw row vector \(a\) and its retained dominator \(b\), the certificate checks, with \(d=a-b\),
\[
\sum_g d_g\le0,\qquad d_g\le0\quad(g\ne i),
\]
where \(i\) is that agent's minimum column. Write \(c_i=t\mathbf1+s\), with \(t\ge0\), \(s_i=0\), and all other surpluses nonnegative. Then
\[
d\cdot c_i=t\sum_g d_g+\sum_{g\ne i}d_gs_g\le0.
\]
Consequently \(b\cdot c_i\le0\) implies \(a\cdot c_i\le0\). Since the retained atoms are a subset of the raw atoms, the conjunctions are equivalent on this domain. The optional zero dominator is covered by the same argument. The reasoning includes the weak boundary; the actual outer domain is stricter.

The final frozen outer audit checked **130,333 raw atoms and 59,064 retained atoms** across all 6,291 used regions. This validates compression and allocation identity. Compression alone does not prove a nonordinal core's first-row guarantee; the final input also has separate exact guarantees for every such core.

### 3.6 A smaller derived integer bound and its real normalization

The separate theorem [row_local_integer_bound.md](../exact_search/row_local_integer_bound.md) proves:
\[
B_9=\left\lfloor8^{9/2}\right\rfloor=\mathbf{11\,585}.
\]
If a nine-chore counterexample exists, one exists with all 27 costs positive integers at most this bound. The three integer row minima may differ.

The improvement is justified by the locality of every EFX comparison. Select one strictly failed comparison for each surjective allocation and assign it to its evaluating row. Even the cost of another agent's bundle is evaluated in that same row, so the constraints split into three independent systems with nine variables each. Include positivity and each row's complete strict item order. Every failure row has support at most seven; positivity and order rows have smaller support.

For each row separately, dilate to \(A_i x\ge\mathbf1\), minimize the sum of coordinates to obtain a vertex, and choose a nonsingular 9-by-9 active matrix. Replacing one column by ones gives squared row norms at most eight. Cramer's rule and Hadamard's inequality bound each integer numerator by \(\lfloor8^{9/2}\rfloor\). Clearing that row's determinant denominator preserves every selected failure assigned to it. Assembling the three replacement rows preserves every allocation's designated witness, regardless of how the other two rows changed. Positivity excludes EFX allocations with empty bundles.

For three agents and \(m\ge4\), the same proof gives \(\lfloor(m-1)^{m/2}\rfloor\). The lower limit on \(m\) makes the support-two order rows fit the uniform support bound \(m-2\). The exact arithmetic and continuity of the previous support audit are recorded in [row_local_integer_bound_check.json](row_local_integer_bound_check.json).

The earlier [common-minimum theorem](../exact_search/finite_integer_bound.md), with dimension 25 and bound \(194\,368\,031\,998\), remains true. It proves the additional requirement that the integer row minima share one value. That coupling is unnecessary for the smaller unrestricted integer search.

There is also a justified bounded **real** formulation. Normalize each integer row by its minimum \(a_i\in[1,B_9]\). Every cost is then at most \(B_9\), every pinned minimum is one, and each preserved strict row-local order or allocation-failure form has margin at least \(1/a_i\ge1/B_9\). Conversely, requiring one failed literal with margin at least \(1/B_9\) for every allocation makes a real model a counterexample. Thus this is an equivalence of existence questions, although it need not retain every original normalized model.

Multiplying this real formulation by \(B_9\) gives common minimum \(11,585\), upper cost bound \(B_9^2=134,212,225\), and unit row-local margins. These scaled variables need not be integers. Arbitrary cross-row total margins are not justified by this argument. No exhaustive integer search or UNSAT proof of either bounded real formulation is recorded here.

### 3.7 Zero minima, the 3,831 bound, and positive lifting

The stronger reduction is proved in [zero_minimum_reduction.md](../exact_search/zero_minimum_reduction.md) and independently reviewed in [zero_minimum_independent_review.md](zero_minimum_independent_review.md). In each evaluating row choose a globally cheapest chore and lower only its cost to zero. For every owned bundle, its maximum residual over allowed deletions is unchanged: if the selected chore belongs to the bundle, its sum and minimum decrease by the same amount; otherwise neither changes. Every comparison-bundle sum weakly decreases. Therefore every EFX allocation after lowering was already EFX before lowering, and a counterexample remains a counterexample. This argument uses deletion of owned zero-cost chores. It works with tied initial minima and does not require the three selected minima to be distinct.

After a strict positive perturbation, lowering leaves one zero and eight distinct positive costs in each row. A bundle with at least two chores has some deletion leaving positive residual, so an allocation with an empty bundle still fails when there are nine chores. For the canonical distinct pinned positions, retain the separate shared-minimum insertion reduction and known eight-chore theorem. The zero-minimum lemma itself has no dependency on that theorem.

Select a strict failure for each surjective allocation, divide those witnesses by their evaluating row, and include positivity and full strict order for the eight positive entries. Each coefficient row has support at most seven. Independently scale each finite strict system to \(Ax\ge\mathbf1\). Because the system includes \(x_g\ge1\), minimizing the coordinate sum gives a nonempty compact minimizing face and a vertex. At the vertex choose an invertible active integer matrix \(D\) of order eight. If \(D_g\) replaces column \(g\) by ones, every row of \(D_g\) has squared norm at most eight. Since column \(g\) of \(D\) is nonzero, at least one replacement row retains squared norm at most seven. Thus
\[
|\det D_g|^2\le7\cdot8^7=14,680,064,
\qquad
3831^2\le14,680,064<3832^2.
\]
Cramer's rule and multiplication by \(|\det D|\) give positive integers bounded by **3,831**, preserving every selected row-local witness. The three rows may be reconstructed independently. More generally the sufficient bound for three agents and \(m\ge4\) chores is
\[
Z_m=\left\lfloor\sqrt{(m-2)(m-1)^{m-2}}\right\rfloor,
\qquad Z_8=840,\quad Z_9=3831.
\]

For positive lifting, start from the zero-minimum integer representative and choose a strongest failed deletion comparison for each allocation. Its margin is an integer at least one. Raise every pinned zero to one half. Every maximum owned-deletion residual remains unchanged, while a target-bundle total rises by at most one half. Each designated failure remains at least one half. Multiplying by two gives a positive integer counterexample with pinned minima one, all other costs even and in \([2,7662]\), and designated failure margins at least one. Strict orders among nonminimum entries remain separated by at least two. This common-minimum representative is stronger than the earlier 11,585 independent-row bound; no old search input is retroactively changed.

For a smaller-dimensional real formula, independently normalize positive reference entries at columns \((1,0,0)\) to one while keeping the three minima zero. This leaves 21 free real variables. The prepared nine-chore formula imposes strict positivity and the canonical row-zero order, without numeric upper bounds or failure margins. The full serialized formula was independently reconstructed by [audit_zero_minimum_formula.py](audit_zero_minimum_formula.py): 27 domain assertions, 18,150 allocation clauses, and 191,104 retained literal positions, including 34,776 pinned-zero deletion positions. Its definition-sensitive mutation control confirms that omitting an owned-zero deletion changes a real allocation clause. These are semantic and arithmetic checks; they do not establish satisfiability or unsatisfiability.

### 3.8 Transferring finite row guarantees to a zero minimum

Every checked finite core guarantees that some allocation in its fixed finite list satisfies all of the first row's non-strict literal EFX inequalities on the positive canonical cone. Homogeneity extends the pinned-minimum-one slice to every positive minimum. At a boundary row with minimum zero and all other entries positive in the same partial order, raise only the zero to a sufficiently small positive \(\varepsilon\). Along a sequence \(\varepsilon\downarrow0\), one allocation in the finite list occurs infinitely often. Its finitely many non-strict linear EFX inequalities persist at the limit. This includes deletion of the owned zero. The argument is finite-union closedness, and it applies to singleton, pair, and larger cores.

The other-row compression identities already hold when the pinned minimum is merely nonnegative, so setting it to zero preserves those implications. Their positive reference entries may be scaled to one independently, leaving seven variables per row. [transfer_proof.md](../structural_nine/zero_outer/transfer_proof.md) records the full argument. Every canonical full counterexample must avoid every transferred sufficient region; the converse is not established. In fact Section 2.2 supplies an exact two-row assignment avoiding the present family without supplying a first row.

## 4. Verifier fault found and repaired

The prior row-core checker admitted JSON floating-point coefficient entries because ordinary numerical equality allowed a float row to match an intended integer row. A weight \(10^{-400}\), represented exactly as a rational, multiplied by a floating-point coefficient could underflow to floating zero. The checker could therefore accept a claimed zero linear combination that was not mathematically zero.

The preserved negative control [row_core_float_unsound_certificate.json](row_core_float_unsound_certificate.json) exploits this. Its historical [false-acceptance receipt](row_core_float_unsound_receipt.json) is evidence of the defect, **not a valid core certificate**. For its single allocation \((0,0,0,0,0,0,0,1,2)\), the admissible first row
\[
(1,2,3,9,8,7,6,5,4)
\]
has a strict EFX failure margin of 31, directly contradicting the purported universal first-row guarantee.

The repaired [verify_row_cores.py](../verify_row_cores.py) requires each coefficient to have the exact Python integer type before any identity check, and requires rational weights to be supplied as integer or string values. Domain rows, failure rows, reconstructed clauses, and other-agent rows pass through this validation. The checked source hash is:

    288607fc42e9027e53d36b2634df9e7e8cbd9270b18efabb18628b3ad1eda1e2

The repaired checker accepted all 169 earlier legitimate certificate files and rejected nine adversarial changes: the old underflow fixture, a missing branch, a negative weight, the all-zero alternative, a wrong allocation ID, a changed other-agent literal, floating failure coefficients, a floating weight, and an omitted possible-minimum trim. The first resumption additionally generated and independently verified 392 exact core certificates with that same unchanged checker. The final release replay includes the expanded exact certificate registry and every local guarantee actually used by the 6,309-assertion input, as counted in Section 2.1. This verification pass added certificates and audit programs; it did not change the already repaired core checker.

## 5. Exact assertion binding and its limits

| Preserved formula | Assertions whose meaning was checked | Remaining logical obligation |
|---|---|---|
| [prefix_v3_portable_snapshot.smt2](prefix_v3_portable_snapshot.smt2) | 31 canonical domain assertions and 641 exact complements of certified extension regions | A checked global UNSAT proof; none is supplied |
| [row_compressed_outer_snapshot.smt2](row_compressed_outer_snapshot.smt2) | 18 other-row domain assertions and 3,523 compressed region-complement clauses | A checked global outer UNSAT proof; its earlier inner-certificate gap is now closed |
| [outer_resumed2_checkpoint1/outer.smt2](outer_resumed2_checkpoint1/outer.smt2) | 18 domain assertions and **4,787** locally certified region-complement clauses, with exact assertion-by-assertion correspondence | A checked global outer UNSAT proof; no unverified local premise is used in this checkpoint |
| [prefix_bounded1_final/formula.smt2](prefix_bounded1_final/formula.smt2) | 52 bounded canonical assertions and **1,956** exact margin complements of certified regions | A checked global UNSAT proof of this necessary-condition relaxation |
| [row_elimination_batch1/outer_final.smt2](../structural_nine/row_elimination_batch1/outer_final.smt2) | 18 domain assertions and **6,291** locally guaranteed region exclusions, including all final source/subset/compression implications | This exact formula has a checked SAT model; additional sufficient regions are required |
| [zero_minimum9_reference_strict.smt2](../exact_search/zero_minimum9_reference_strict.smt2) | 27 domain assertions and every one of **18,150** surjective allocation-failure clauses after fixed-zero and fixed-reference substitution | A decisive exact solver result, followed by literal exhaustive SAT verification or an independently checked UNSAT proof |
| [zero_minimum_final_outer.smt2](../structural_nine/zero_outer/zero_minimum_final_outer.smt2) | 14 positive-domain assertions and all **6,291** transferred region exclusions | Exact outer SAT model checked; no first row and no main-target counterexample |
| [lifted9_common_minimum_unit_margin.smt2](../exact_search/lifted9_common_minimum_unit_margin.smt2) | 54 domain assertions and all **18,150** allocation clauses with unit failure margin; fixed minima one and other costs in \([2,7662]\) | Prepared and fully reconstructed, without a solver result |

The prefix raw snapshot contained 24 nonstandard Z3 model-converter commands. Their narrow metadata shape was checked, and the portable snapshot removes them. The parsed assertion/declaration/check-sat syntax trees are otherwise identical. This is a portability correction with preserved logical assertions; it is not a solver refutation.

The compressed outer snapshot contains the 3,238 ordinal singleton clauses, the 109 independently certified resumed-core clauses, and the first **176** new nonordinal clauses: \(3238+109+176=3523\). The saved compression audit inspected 191 new records because the live search had progressed beyond the moment the outer snapshot was copied. The audit explicitly checked that the outer clauses equal the corresponding prefix of the expected clause sequence.

Those 191 new input files were originally only hash-bound. The resumed verification closed that inner-certificate gap for **all 284** completed compressed cores, and then for 57 additional resumed cores. The frozen outer checkpoint subsequently added 51 more cores, which were also certified and independently checked.

The 20:54 checkpoint contains \(3238+450+1048+51=4787\) learned clauses. Its 450 resumed cores comprise the original 109, all 284 compressed cores, and all 57 first-resume cores. Every actual learned clause exactly equals the strict complement of its corresponding compressed region, and every such region now has an independently checked local guarantee. That historical file's SHA-256 is:

    7580e516bbb0d3ae4a7098dfc35984acaa982ea4284b1fc5396596e63d74edbb

There are exactly 18 real declarations and 18 domain assertions in each positive-minimum two-row snapshot: each of agents 1 and 2 has pinned minimum one and every other entry strictly above one. No additional constraint or nonstandard model-converter command is present. There is one check-sat command. The static audits establish the assertion correspondences without running that command. The later final frozen snapshots are now covered by their own complete audits in Section 2.1.

The final bounded-prefix input has SHA-256 `143c753bccaa2a5aca123ed0beb26fc97436b3862cf6ca2b23991a830581f8ac`; the final positive-minimum two-row input has SHA-256 `1fc2bec83744678c33126d36e26ea535ff31bab494e8a6c4f9ad662d46214ec4`; the full zero-minimum nine-chore input has SHA-256 `65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b`. The two-row input is a necessary-condition relaxation: a model outside the learned regions need not be a full counterexample. The same distinction applies to the bounded-prefix relaxation. Its 11,585 upper bounds and row-local margin \(1/11585\) follow from the separately proved bounded-prefix reduction, while its two cross-row total comparisons remain strictly positive without an imposed numerical margin. The full zero-minimum allocation formula, in contrast, expresses counterexample existence under the documented canonical reductions.

## 6. Claim/check ledger and remaining work

| Claim | Present status | What remains |
|---|---|---|
| Every certified prefix region guarantees EFX throughout its recorded ninth-column domain | Exact certificate checks passed for 1,956 archived regions | No further local obligation identified for those unchanged certificates |
| The 1,956 prefix regions cover the canonical prefix domain | **Unresolved** | A valid global refutation of their exact bounded complement, or a different complete cover |
| Every one of the 3,238 singleton seeds guarantees the first row | Direct ordinal verification passed over all 28 orders | No inner solver certificate is required for these singleton seeds |
| Every one of the 1,048 paired seeds guarantees the first row | 4,192 exact gap-alternative identities and all four failure branches per pair passed | No further local obligation identified for these unchanged pairs |
| The 2,005 distinct nonordinal cores in the final positive-minimum input guarantee the first row | Exact direct, historical, reduced-core and subset certificates passed and were source-bound | No further local obligation identified for these unchanged guarantees |
| All 6,291 exclusions in the final positive-minimum input have exact local guarantees and faithful compressed predicates | All 130,333 raw atoms and 59,064 retained atoms bound to literal allocation conditions; ordered assertions reconstructed | A future tail requires its own frozen binding before this count is extended |
| The 6,291 sufficient regions cover the complete canonical two-row domain | **False for this frozen family**: the exact positive integer witness satisfies every exclusion | Add valid sufficient regions covering the witness and any other uncovered points, then establish complete coverage; an UNSAT proof for this exact current input is impossible |
| Any counterexample has a positive integer representative with costs at most 11,585 | Independent row-wise vertex/determinant proof reviewed; exact bound/support arithmetic passed | The integer search must permit unequal minima; the domain has not been exhausted |
| Fixed-minimum-one real search with upper bound 11,585 and row-local margins at least \(1/11585\) is sufficient | Normalization corollary reviewed in both directions, with the stated canonical reduction | A faithful formula and checked global UNSAT proof; no cross-row total margin follows from this corollary |
| Lowering one global minimum to zero preserves the absence of EFX allocations | General residual argument reviewed, including tied minima and owned-zero deletions | None for this stated implication; it does not itself establish a counterexample |
| Any counterexample has a representative with one zero per row and all positive costs at most 3,831 | Independent eight-dimensional row systems, exact Cramer/Hadamard bound, and source proof reviewed | The finite domain has not been exhausted |
| Any counterexample has a positive integer representative with common minimum one and even other costs at most 7,662 | Half-unit lifting and designated failure margins reviewed | The finite domain has not been exhausted |
| The 21-variable zero-minimum formula faithfully expresses the canonical full counterexample question | All 18,177 serialized assertions and all retained literal positions reconstructed using exact standard-library arithmetic | A decisive exact result with the corresponding independent verification |
| An actual nine-chore counterexample exists | **None established by this continuation** | A full matrix passing literal exhaustive failure verification over all \(3^9=19,683\) allocations |
| Universal nine-chore EFX existence | **Completed later by the independent full-input proof in Section 13** | The earlier regional family is not the proof of global existence; the unbounded literal counterexample formula has its own complete refutation |

For the fully audited frozen prefix input, global coverage remains unresolved. For the positive-minimum row family, the exact witness now proves that more regions are needed: global coverage is false for the present finite family. Later live or merely prepared variants are separate evidence. A SAT model of a two-row or prefix relaxation is not a full EFX counterexample. Timeouts, interrupted runs, and a finite accumulation of regions supply no global existence result. A lost heartbeat or missing process produces no inferred timeout verdict; only an observed terminal receipt supports a completed-run outcome. The two exact structural counterexamples in [structural_limitations.md](../structural_nine/structural_limitations.md) concern proposed auxiliary reductions, not EFX existence; they must not be relabeled as main-target counterexamples.

## 7. Proof organization assessment

These scores assess the exposition and interfaces of the extension-method, finite-bound, and first-row-elimination reductions. They are not probabilities of correctness or scores for a completed nine-chore proof.

| Dimension | Three submetrics, on the 1–5 half-point scale | Mean |
|---|---|---:|
| Structure | Main argument as outline 4.0; meaningful complexity distribution 4.0; dependency clarity 4.0 | 4.00 |
| Signature quality | Natural statements 4.5; hypothesis economy 4.0; useful generality 4.0 | 4.17 |
| Step transparency | Local reasoning 4.5; explicit use of intermediate claims 4.0; controlled automation 4.0 | 4.17 |
| Reuse | Structural usefulness 4.5; applicability beyond the instance 4.0; absence of decorative helpers in the reviewed notes 4.0 | 4.17 |
| Human readability | Readable argument 4.0; mathematical naming/style 4.0; maintainability 4.0 | 4.00 |

The mean of all fifteen submetrics is **4.10**. The extension note separates box geometry, Boolean incompatibility, linear compression, and global coverage. The finite-bound note displays the dimension and support calculations where the numerical constant depends on them. The first-row note makes its product domain and quantified core implication explicit. Generality is adequate for the certificate methods, although several implementation-specific canonical choices remain local. The final two audits now take immutable input snapshots, resolving the moving-boundary weakness of the earlier live-directory audits; hashes preserve the distinction between historical and current claims.

## 8. Prior work, trust, and completion record

The finite-dimensional vertex/determinant method, nonnegative linear alternatives, ordinal domination, and counterexample-guided refinement are standard ingredients. This review makes no new priority claim. The finite-bound source note records its own limited literature search; the earlier package records the EFX primary sources and their verification. No new external literature search was performed in this resumed review.

The certificate checkers are independent of the search oracles in the limited sense documented by their source: they reconstruct the literal allocation predicates and use standard-library exact arithmetic rather than import the solver encoders. The resumed pass combines a fresh source-and-receipt inspection, a hash replay, exact verification of new certificates, and complete binding of an immutable outer formula. It is not a proof-assistant verification or a replay of every prior run. Python's exact arithmetic implementation, the checker programs, parsing, and the handwritten mathematical reductions remain part of the trust boundary.

| Completion item | Status and scope |
|---|---|
| Target, track, original evidence, and inspection boundary | Recorded in Sections 1–2 and the manifests |
| Applicable mathematical identities and quantifier boundaries | Reviewed in Sections 3–5 |
| Completed finite checks and actual counts | Historical provenance retained; the final explicit certificate index, all local proofs and both complete region inputs replayed with exact arithmetic; every full zero-minimum input assertion reconstructed |
| Verifier changes and negative control | Documented in Section 4; exact core checker unchanged throughout the new checks |
| Fifteen submetrics and five dimension means | Included in Section 7 |
| Outline and prior-work boundary | [continuation_outline.md](continuation_outline.md) and Section 8 |
| Solver/global proof and formal trust audit | Full nine-chore obligations completed later in Section 13; proof-assistant audit not applicable |
| Later live or prepared searches | Explicitly outside the completed-evidence boundary unless separately recorded and audited |

**Strongest conclusion at that earlier checkpoint:** the completed release evidence contained 1,956 exact prefix-extension guarantees and a frozen positive-minimum two-row input whose 6,291 learned clauses all had exact local guarantees: 3,238 singleton seeds, 1,048 static paired seeds, and 2,005 distinct nonordinal cores. Every included assertion and compressed predicate was bound to those guarantees. Exact positive integer rows proved that the row family was incomplete. The full zero-minimum and positive-lifted allocation formulas had passed literal reconstruction, and the reviewed representative bounds were then 3,831 and 7,662. That checkpoint did not yet supply a universal nine-chore proof. Sections 9–13 record the stronger bound, completed baseline, and final independent proof without altering the earlier receipts.

## 8. Historical full-target UNSAT checkpoint

The frozen zero-minimum nine-chore input returned **UNSAT in 591.67023688 seconds** under Z3, with normal process termination and proof generation disabled. The receipt is [zero_minimum9_reference_noproof_run1.json](../exact_search/zero_minimum9_reference_noproof_run1.json). Its exact input SHA-256 is `65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b`. The input has no finite upper bound and no local-region cuts: it is the complete canonical counterexample formula previously reconstructed by the independent literal audit.

The [standalone end-to-end proof](zero9_end_to_end_audit.md) shows how any nonnegative counterexample first gives a strictly positive generic counterexample, why coincident cheapest chores are excluded using ordinary eight-chore EFX existence and the explicitly proved insertion lemma, why lowering each selected minimum to zero preserves nonexistence, and why the canonical relabeling and positive reference normalizations yield this precise input. The argument uses neither the prescribed-agent property P8 nor D8. It includes all owned-zero deletions. The [binding receipt](zero9_end_to_end_binding.json) independently witnesses every one of the **1,533 omitted empty-bundle allocations**, alongside the **18,150 explicitly encoded surjective allocations**. All **19,683** allocations are thus accounted for. No mathematical gap was identified in this reduction.

At that checkpoint, the original solver result supported an affirmative solution of the full target conditional on solver soundness and the cited ordinary eight-chore baseline. It had not yet become a completed independently checked computational proof; that later completion is recorded in Section 13. A direct full-nine CPC export attempt exhausted memory without a verdict/proof; an eight-chore Boolean-CPC calibration did likewise. The alternative proof route captures canonical affine atoms and arithmetic theory clauses, verifies selected clauses by exact mixed-strict Farkas multipliers, and checks an ordered Boolean RUP refutation using only the original clauses and those verified axioms. Callback assumptions are excluded.

The new standard-library capture checker independently bound all **5,819** original assertions and **5,746** affine atoms of the eight-chore calibration. A spread of **100** real theory clauses passed exact Farkas checking. **41** targeted controls passed, covering strict/weak boundaries, tiny exact weights, floating-point and Boolean value rejection, atom orientation, axiom provenance, and malformed propagation hints. These are completed checks of their stated finite scopes. They do not imply that the final selected theory set or a complete nine-chore refutation has passed. Current terminal and active attempts are recorded in [CONTINUATION_STATUS.json](../../docs/CONTINUATION_STATUS.json); no intended timeout is relabeled as an observed result.

## 9. Primitive-Cramer bound refinement

The separate [primitive-Cramer proof](primitive_cramer_bound.md) improves the sufficient representative bounds to **2,566** with one zero per row, and **5,132** after positive lifting with common minimum one. At a row vertex, divide the Cramer numerators and denominator by their common gcd. If the replaced-column matrix has \(f\) full rows, the corresponding augmented rows have one common parity pattern, so every maximal minor has a factor \(2^{f-1}\). Combining that common factor with Hadamard's inequality gives

\[
Q_m=\left\lfloor\sqrt{(m-1)(m-2)^{m-2}}\right\rfloor.
\]

The [arithmetic receipt](primitive_cramer_bound_audit.json) checks the integer square-root values and the comparison between all possible row counts, plus all 3,264 nonsingular admissible three-dimensional matrices as focused parity controls. The general theorem is supplied by the written argument, not inferred from those finite controls. This is an existence reduction; it does not change the unbounded strict-real formula that returned UNSAT, and it does not retroactively change the 7,662-bound positive lifted formula or any historical receipt.

## 10. Completed eight-chore independent certificate and portability

The eight-chore calibration has advanced to a complete independently checked computational proof: [zero8_complete_lra_certificate.json](zero8_complete_lra_certificate.json). All 27,637 selected theory clauses passed exact rational Farkas checking, and the previously completed 10,845-clause RUP refutation and original-input binding remain unchanged. The completed stages are bound to one input, one atom interpretation, one selected theory set, and the actual certificate bytes. No captured solver verdict or callback assumption is trusted.

The [full eight-chore target binding](zero8_full_target_binding.json) combines that finite refutation with the previously audited literal formula, explicit witnesses for all 765 omitted allocations, and the ordinary-seven checked residual/cited-six baseline chain. [zero8_full_target_completion.md](zero8_full_target_completion.md) supplies the complete correspondence. This closed a local eight-chore computational proof and validated the alternative baseline for the main nine-chore reduction. The nine-chore certificate was still pending at that checkpoint; Section 13 records its later completion.

Both detected file-integrity failures were rejected, preserved, and repaired only through separately documented derived artifacts. The original arithmetic file lacked its final 237 records; regenerating only that suffix produced a complete file whose hash exactly matches the original producer's intended full hash. All 27,637 identities were checked in the final composed file. The [relocation control](lra_relocation_control.json) additionally executed all three proof stages on a tiny certificate copied into a different directory, with the old location unavailable and a stale absolute provenance path preserved. The complete eight-chore replay command uses explicit relative or absolute paths and standard-library Python only.

## 11. Full-nine capture binding and final manuscript review

The complete, read-only nine-chore capture snapshot passed [original-input and atom binding](zero9_capture_snapshot_input_binding.json). The checker reconstructed the same 18,177 original assertions over 18,066 interpreted affine atoms, validated all 3,234,215 theory and 2,480,762 ordered RUP records, and checked every terminal hash and record count. This check establishes the source identity and interpretation of the proof material; it does not by itself establish the validity of a theory axiom or the final contradiction.

Two separate untrusted extraction variants passed new eight-chore Boolean calibrations using the unchanged independent RUP checker. The [cached-closure variant](zero8_rup_cached_calibration1_independent.json) had 27,488 theory axioms and 9,696 derived clauses; the [backward variant](zero8_rup_backward_calibration1_independent.json) had 28,037 theory axioms and 12,811 derived clauses. Each check verified earlier-clause propagation, original/theory provenance, exact selected-set equality, a final derived empty clause, and complete backward dependency closure. They are Boolean calibrations relative to selected theory axioms; no new arithmetic completion is inferred. The accepted full eight-chore certificate remains unchanged.

The [private manuscript review](release_manuscript_review.md) found no mathematical gap in the insertion cycle/path cases, canonical-domain counts, deletion pruning, alternative baseline chain, or primitive-Cramer bound. Every one of the worked example's 18 literal inequalities was recomputed exactly. The separate [constructive solver review](constructive_solver_review.md) verified exact input parsing, integer row scaling, subset residuals including zeros, exhaustive labelled assignments including empty bundles, and the returned literal certificate. These ancillary checks are separate from the completed nine-chore universal refutation in Section 13.

The release-index builder now binds the complete nine-chore proof, current full-target completion, and accepted alternative baseline. It wrote completion status only after every required certificate identity passed. Retrieved prior-work PDFs and their full extracted texts are external-source provenance, rather than required redistributed replay files. No historical input, proof, or receipt was altered by these checks.

## 12. Minimal replay capture with unchanged source indices

The separate [minimal-capture binding](zero9_minimal_capture_input_binding.json) passed the unchanged input/atom checker in 24.642 seconds. Its source is `continuation/exact_search/zero9_minimal_replay_capture1/capture`. All 18,066 atom records, 18,178 original-clause records, 3,234,215 theory records, and metadata are exact copies of the audited full snapshot. The source indices and later Boolean proof IDs are unchanged.

The raw callback RUP and assumption streams have no premise role in the final independently checked hinted proof. Omitting those two logs from this derived replay package removes 138,584,363 bytes; the original snapshot remains untouched. A sealed provenance manifest preserves all original and derived hashes, and copies of the historical source receipt and binding accompany the package. The final release index will expose this source as `accepted_capture` and explicitly inventory omitted raw streams. No trusted checker was changed, and no completed Boolean or arithmetic proof was repeated by this packaging step.

The updated release gate was tested with the real complete eight-chore certificate and correctly rejected it as the wrong nine-chore input without writing any completion artifact: [negative control](nine_release_minimal_capture_gate_negative_control.json). The final selected RUP refutation and exact arithmetic stream subsequently passed against this same minimal capture, as recorded next.

## 13. Complete independently checked nine-chore proof

The accepted combined receipt is [zero9_complete_lra_certificate.json](zero9_complete_lra_certificate.json), with status `PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE`. It binds the independently reconstructed original SMT/affine interpretation to one complete Boolean refutation and the exact same selected arithmetic axiom set. The stage receipts were composed by immutable content hashes after their successful checks, without unnecessarily replaying them.

The [Boolean receipt](zero9_rup_source_cache_independent.json) checks **4,550 original axioms**, **370,780 selected theory axioms**, **172,146 derived clauses**, and **8,088,323 ordered propagation reasons**. Each reason is an earlier checked clause, every propagation step is truly unit under the negated goal, and the final reason is a conflict. The last derived clause is empty, with ID **5,735,883**. Exact backward dependency closure and the selected theory index set both match. The check passed in **30.267 seconds**, using **902,792 KiB** maximum resident memory.

The [arithmetic receipt](zero9_selected_farkas_independent.json) checks every one of those **370,780** theory clauses and all **1,317,350** nonnegative exact rational multiplier positions. All weighted variable coefficients cancel. There are **360,481** contradictions with zero summed constant and a positive strict-premise weight, and **10,299** with positive summed constant. The checker used no floating-point arithmetic. It passed in **82.486 seconds**, using **195,164 KiB** maximum resident memory. The final exact arithmetic stream has SHA-256 `1158d4059ecb2ea0a0fce97a492e662a9b151b26f03fa33b6d839732d4d0e356`.

The original RUP CLI's **700 MiB** memory cap was insufficient; its `MemoryError` and exit 1 are preserved in [zero9_rup_700m_attempt1.json](zero9_rup_700m_attempt1.json), without a mathematical verdict. The accepted [resource wrapper](run_lra_with_budget.py) uses **1,600 MiB**, invokes the same checking functions unchanged, and delegates complete acceptance to the unchanged hash binder. Its [source review](nine_replay_orchestration_review.json) and [four tiny orchestration/relocation controls](budgeted_replay_controls.json) passed. Resource figures describe this execution, rather than a guarantee for every machine.

The [current full-target completion](zero9_full_target_completion.md) now joins the finite refutation to the unchanged handwritten reduction. A nonnegative counterexample would give a positive generic counterexample. The full shared-minimum insertion lemma, using ordinary eight-chore existence, rules out coincident unique minima. Lowering each row's minimum to zero and applying the audited relabeling and positive reference scaling gives the precise 21-variable domain. The complete literal formula audit and omitted-allocation witness table cover **all 19,683 labelled allocations**, including every owned-zero deletion. The checked refutation makes that counterexample impossible.

The [release index](nine_release_index.json) has status `PASS_COMPLETE_NINE_CHORE_RELEASE_BINDING` and binds **96** required files. It names the accepted minimal capture, final trace, final arithmetic stream, current mathematical completion, baseline dependencies, checker sources, and the [concrete replay command](../../docs/zero9_replay_command.txt). Obsolete candidate prefixes and intermediate arithmetic batches are not required proof inputs. Full retrieved papers are recorded separately as external sources. The original ordinary eight-chore theorem is the primary literature premise; the retained checked seven/eight chain from the cited six-chore theorem is an alternative. The handwritten mathematics and checker/runtime implementation remain explicit trust boundaries. No proof-assistant formalization or absolute priority claim is made.
