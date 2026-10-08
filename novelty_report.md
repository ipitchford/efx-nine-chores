# Novelty-gate report: Three agents and nine additive chores

**Search date:** 7 October 2026.  
**Researcher/agent:** Literature and source-audit agent; no author attribution requested.  
**Corpus boundary:** The supplied problem statement; arXiv primary papers and their indexed full text; the public Zhang artifact and its GitHub commit history; selected primary journal/conference pages. Search results were inspected through the available web-search service. This is a bounded search, not an exhaustive historical-priority claim.  
**Intended contribution unit:** An existence theorem at exactly nine chores, or an exact counterexample. A separately checked computational proof is a distinct contribution unit.

## 1. Frozen claim

For every nonnegative real matrix \(C\in\mathbb R_{\ge0}^{3\times9}\), there is a complete labelled partition \((A_0,A_1,A_2)\) of \(\{0,\ldots,8\}\) satisfying

\[
\sum_{h\in A_i\setminus\{g\}}C_{ih}\leq\sum_{h\in A_j}C_{ih}
\quad(i\ne j,\;g\in A_i).
\]

Empty bundles are allowed. The removal quantifier includes owned chores of zero cost. The alternative successful outcome is a rational matrix for which all \(3^9\) labelled allocations fail this predicate.

Excluded targets include approximate fairness, EF1, tEFX, partial allocation or disposal, an arbitrary bound on integer costs, and a proof only for a prespecified bundle-size profile. An undecided solver run does not decide this statement.

**Permitted language before a successful proof:** “Zhang's inspected version 2 leaves the nine-chore case unresolved; no later resolution was found in this bounded search.”

## 2. Normalisation and translation table

| Source or alternative notation | Canonical form | Translation |
|---|---|---|
| Allocation vector \(a\in\{0,1,2\}^9\) | \(A_i=\{g:a_g=i\}\) | Bijective encoding of complete labelled partitions. |
| Trimmed own cost | \(c_i(A_i)-\min_{g\in A_i}c_{ig}\) | Equals the largest cost remaining after one own chore is removed; empty bundles are checked separately. |
| Costs or disutilities | Nonnegative additive row \(C_i\) | All comparisons use the evaluating agent's row, including the other bundle. |
| Agent labels \(1,2,3\) in KMS | Agent labels \(0,1,2\) | Simultaneous relabelling of rows and assigned bundles. |
| Unit row sums | Independent positive row scaling | Each comparison is homogeneous within one row. A zero row is handled by giving that agent all but two chores and the others one chore each. |
| Goods EFX | Different predicate | Goods remove an item from the envied bundle, so the three-agent goods theorem does not establish this target. |
| Positive-cost-only trim | Different allocation predicate on boundary instances | The frozen target explicitly keeps zero-cost owned chores; replacing its quantifier would require a separate argument. |

## 3. Fingerprints

The complete-allocation counts for \(m=3,\ldots,9\) are
\(27,81,243,729,2187,6561,19683\), with ordinary generating function \(1/(1-3t)\) when the sequence starts at \(m=0\). These elementary counts identify the encoding size, not a new enumerative object.

Exact small instances from `target.yaml` are consistent with the predicate:

| Matrix | EFX allocations | Reason |
|---|---:|---|
| Three rows, nine all-zero entries per row | 19,683 | Every comparison reads \(0\le0\). |
| Three rows, three unit entries per row | 6 | Each agent receives one chore. |
| Three rows, six unit entries per row | 90 | Each agent receives two chores: \(6!/(2!)^3\). |
| Three rows, nine unit entries per row | 1,680 | Each agent receives three chores: \(9!/(3!)^3\). |

For uniform positive costs, EFX requires every bundle size to be at most one larger than every other. At a multiple of three this forces equal sizes. These provide independent sanity checks for counts and boundary handling. There is no relevant spectral sequence or matrix-kernel alias to fingerprint.

Invariants are simultaneous chore permutation, simultaneous agent relabelling, and independent positive row scaling. The raw dimension is 27, or 24 after three row normalisations. The EFX-admitting set is a finite union of closed polyhedral cones; its complement is a finite conjunction of disjunctions of strict homogeneous linear inequalities.

## 4. Alias map

| Domain | Useful aliases or translation | Limitation |
|---|---|---|
| Fair division | Envy-free up to any chore; additive disutilities; zero-tolerant chores EFX | Avoid goods EFX, tEFX, and positive-only trim as silent substitutes. |
| Combinatorics | EFX bipartite graph; perfect matching between agents and unassigned bundles | Matching is a reformulation, not a theorem that such a partition exists. |
| Optimisation and logic | QF_LRA; disjunctive linear feasibility; strict linear counterexample formula; finite polyhedral covering | Encoding nonexistence is known and does not solve the formula. |
| Analysis | Finite-union closedness; generic perturbation; rational density; homogeneous scaling | These are routine reductions with no novelty claimed. |
| Probability | Deterministic allocation of additive burdens | Randomised or fractional fairness changes the target. |
| Mathematical physics / representation theory | No productive object identity identified | No artificial analogy was used to claim a bridge. |

## 5. Search log

All queries below were made on 7 October 2026. Exact query strings are retained to make the boundary reproducible.

| Corpus | Query or retrieval | Inspected result and consequence |
|---|---|---|
| General web/arXiv index | `"2609.10585"`; `"EFX" "nine chores" Zhang` | Located Zhang and the public artifact. |
| Primary arXiv | `https://arxiv.org/abs/2609.10585`; version-2 HTML | Version 2 was submitted 6 October 2026 and still leaves \(m=9\) unresolved. |
| General web | `"EFX" "nine chores"`; `"EFX" "three agents" "chores" existence October 2026`; exact Zhang title excluding arXiv and ArcXiv | No later resolution found in returned results. |
| General web | `"EFX" "chores" "nine" existence`; `"EFX" "chores" "9" "three"`; `"EFX" "three agents" "nonexistence" additive 2026` | Located He–Tao and older approximation/special-case literature; no nine-chore solution found. |
| Primary matching paper | `https://arxiv.org/pdf/2305.04168`, Lemma 4.2 and supporting observations | The insertion lemma's proof uses its displayed cheapest-item condition, not a hidden common-order assumption. |
| Generic-perturbation aliases | `"EFX" "chores" "generic" perturbation`; `"EFX" "chores" "strictly positive" perturbation`; primary retrieval of Yin–Mehta, arXiv:2211.15836 | The later structural rerun found an explicit prior formulation in Yin–Mehta, Lemma 2.1. Generic-density reasoning is not a research contribution of this project. |
| Source artifact | GitHub README, current solver file, and recent commits | Current commit is `b5121a08f21f1d1a75353d9cad4932a92540de64`, dated 5 October 2026. |

The current artifact commit renames files without changing the encoded formula, according to its commit message. The current Z3 file is `smt/eight_chores_z3.py`, blob SHA `149de581b4be79a30be1cc6683e5a156b06b7b9b`. The older `artifacts/s6_all_z3.py` path and `--residual-disjoint-argmins` flag refer to the preceding layout; the current flag is `--disjoint-argmins`.

## 6. Verified collisions and scope boundaries

### Zhang: exact predecessor and residual reduction

Zhang's version-2 Theorems 1.1–1.2 cover seven and eight chores. Section 6 explicitly extends the shared-cheapest insertion reduction to nine chores and leaves the disjoint-minimum residual undecided. Therefore neither this reduction nor writing its \(3^9\)-clause formula is new. The paper reports exact SMT unsatisfiability decisions and internal cvc5 proof checks, while the inspected artifact supplies no independently checked exported proof object. Source: [Zhang, version 2](https://arxiv.org/html/2609.10585v2), Sections 3–6; [artifact](https://github.com/KaixxxZhang/Chores-EFX-n3m7or8).

### Kobayashi–Mahara–Sakamoto: insertion

In the original full version, Lemma 4.2 says that an unallocated chore cheapest for all but one agent can be added to one existing bundle while preserving a perfect matching in the EFX graph. Observation 2.3 converts that matching into a complete EFX allocation. Its proof uses Lemma 2.4's edge preservation and an alternating cycle/path argument; it needs no identical ordering among the other allocated chores. The zero-cost convention matches the target. Source: [KMS full version](https://arxiv.org/pdf/2305.04168), Sections 2 and 4.

### Generic perturbation: explicit prior formulation

For a putative counterexample, select one strict failure inequality for each of finitely many allocations. Their positive minimum margin survives a sufficiently small perturbation. The perturbation can make entries positive and avoid the finitely many within-row equality hyperplanes. Hence restricting a counterexample search to positive costs and strict row rankings loses no counterexample. Equivalently, EFX existence on a dense class extends by closedness and the finite number of allocations. Yin–Mehta explicitly give the additive perturbation \(c'_i(S)=c_i(S)+\varepsilon\sum_{b_j\in S}2^j\), preserving all strict subset comparisons and transporting EFX back to the original instance (Lemma 2.1, PDF pages 4–5). This prior includes the zero-cost boundary and implies the needed strict-ranking reduction. Source: [Yin–Mehta](https://arxiv.org/pdf/2211.15836). No priority claim is made for it.

Once minima are pinned, pairwise disjointness can be written as \(c_{pg}>c_{pp}\lor c_{qg}>c_{qq}\) for every pair \(p<q\) and chore \(g\). With unique minima this reduces further to \(c_{ii}<c_{ig}\) for \(g\ne i\). Sorting free columns by their first-row entries needs no lexicographic tie clauses on the generic class. These are formula simplifications, not an independently novel existence theorem.

## 7. Negative evidence and missingness audit

No later nine-chore solution appeared in the recorded queries. This does not establish absolute priority. No author enquiry was sent. Dedicated MathSciNet and zbMATH searches were not available; non-English sources, unindexed preprints, private manuscripts and recent unindexed repository branches were not exhaustively checked. Some arXiv HTML retrievals failed, so the matching lemma was checked in the PDF. He–Tao's primary abstract was retrieved, but its full current text was not needed as a premise and was not successfully fetched in this audit.

The ORdős problem page encountered in the search uses a positive-cost-only trim convention and an older frontier. It was not used as a primary premise. Cached GitHub root pages exposed the old artifact layout; the current commit and pinned solver file were resolved through GitHub's repository API.

## 8. Outcome by contribution unit

| Unit | Outcome | Confidence within boundary | Allowed wording | Forbidden wording |
|---|---|---|---|---|
| Universal nine-chore statement | CLEAR TO PROVE within recorded boundary | Moderate–high | “Next case left open in the inspected 6 October source.” | “Proved historically novel by search.” |
| Complete nine-chore proof/counterexample | BOUNDED UNCERTAINTY until this project's exact result exists | No resolution yet | Claim only what the final certificate establishes. | “Solved” from an encoding, timeout, numerical run, or bounded scan. |
| Shared-cheapest reduction and disjoint residual | COLLISION | High | Attribute to Zhang §6 and KMS Lemma 4.2. | Claim as this project's new theorem. |
| Generic perturbation and strict rankings | COLLISION; routine reduction | High | Attribute the explicit perturbation to Yin–Mehta Lemma 2.1, and give the short argument needed here. | Claim a new fairness principle. |
| Exported independently checked proof | CLEAR TO DEVELOP; result pending | Moderate | “Independent checker accepted this specific proof,” if obtained. | Call cvc5's internal self-check an independent kernel check. |

## 9. Decision

**CLEAR TO PROVE within this bounded search.** A successful proof for nine chores would extend the inspected finite frontier. The prior reductions and the act of encoding the statement do not count as that extension. The current state of the theorem must be recorded separately from this novelty gate.

## 10. Rerun triggers

Rerun the gate if proof search yields a general potential function, an all-cardinality matching theorem, an equivalence to a known allocation concept, a new domain reduction, or another structural identity. Also rerun the recency search immediately before a public priority claim if work spans a substantial interval.

## Sources

Yin, L., & Mehta, R. (2022). *On the envy-free allocation of chores* [Preprint]. arXiv. https://arxiv.org/abs/2211.15836

Kobayashi, Y., Mahara, R., & Sakamoto, S. (2023). *EFX allocations for indivisible chores: Matching-based approach* [Full-version preprint]. arXiv. https://arxiv.org/abs/2305.04168 . Journal version (2025): *Theoretical Computer Science, 1026*, 115010. https://doi.org/10.1016/j.tcs.2024.115010

Zhang, X. (2026, October 6). *EFX allocations for three agents and seven or eight chores* (Version 2) [Preprint]. arXiv. https://arxiv.org/abs/2609.10585v2

Zhang, X. (2026, October 5). *Chores-EFX-n3m7or8* [Source code, commit b5121a08f21f1d1a75353d9cad4932a92540de64]. GitHub. https://github.com/KaixxxZhang/Chores-EFX-n3m7or8/tree/b5121a08f21f1d1a75353d9cad4932a92540de64
