# Novelty-gate rerun: a prescribed agent receives an envy-free bundle

**Date:** 7 October 2026. This is a bounded primary-source search prompted by a new structural target. It does not change the original nine-chore problem. The exact positive theorem remains subject to the proof and encoding audit; the eight-chore obstruction has been checked by the project's independent enumerators.

## 1. Frozen statement and negation

For an integer \(m\ge0\), let \(P_m\) mean

\[
\forall C\in\mathbb R_{\ge0}^{3\times m}\;\forall d\in\{0,1,2\}\;
\exists (A_0,A_1,A_2):
\quad\operatorname{EFX}_0(C,A)
\quad\text{and}\quad
c_d(A_d)\le c_d(A_j)\;(j\ne d),
\]

where the allocation is a complete labelled partition and \(\operatorname{EFX}_0\) quantifies deletion of every owned chore, including zero-cost chores. Agent symmetry permits fixing \(d=0\). Since ordinary envy-freeness implies the designated agent's EFX inequalities, the exact failure clause for any fixed allocation is

\[
\bigvee_{j\ne0}\big(c_0(A_0)>c_0(A_j)\big)
\;\lor\;
\bigvee_{i\in\{1,2\}}\bigvee_{j\ne i}\bigvee_{g\in A_i}
\big(c_i(A_i\setminus\{g\})>c_i(A_j)\big).
\]

The prospective ancillary result is that \(P_m\) holds through seven chores and fails at eight. It is stronger than ordinary EFX existence. A failure of \(P_8\) is **not** a failure of EFX existence at eight or nine chores.

## 2. Object identity and aliases

For a fixed partition \(B=(B_0,B_1,B_2)\), define an EFX edge \((i,k)\) by
\[
\max_{g\in B_k}c_i(B_k\setminus\{g\})\le\min_\ell c_i(B_\ell),
\]
with the maximum over an empty bundle defined as zero. A minimum edge satisfies \(c_i(B_k)=\min_\ell c_i(B_\ell)\). The target asks for a partition whose EFX graph has a perfect matching using a minimum edge incident to the prescribed agent. It does not prescribe which bundle is that agent's minimum, and it does not ask that a prescribed edge of an arbitrary pre-existing graph be extendible.

Equivalent search language includes “designated/prescribed/specified/prespecified envy-free agent,” “non-envious agent,” and “designated sink of the ordinary envy graph.” In the latter graph an arc \(i\to j\) means \(c_i(A_i)>c_i(A_j)\); a sink has no outgoing arcs. “Unenvied agent” usually means no incoming arcs and must not silently replace this condition.

Positive row scaling and simultaneous agent/chore relabelling preserve the object. A proportional-share guarantee \(c_d(A_d)\le c_d(M)/3\) is weaker than the designated envy-free condition. Approximate EFX, EF1, partial allocations and an unspecified choice of the envy-free agent are separate targets.

## 3. Exact fingerprint of the obstruction

The eight-chore matrix recorded by this project is

\[
C=\begin{pmatrix}
37&51&59&255&264&325&355&534\\
12&57&90&511&1343&643&1878&1106\\
2885&595&1010&33353&23598&71016&7970&28773
\end{pmatrix}.
\]

All entries are positive. The independent literal record `results/p8_obstruction_verified.json` checks all \(3^8=6561\) complete labelled allocations. Exactly 36 are EFX; the numbers that also make agent 0, 1, or 2 fully envy-free are respectively \((0,31,31)\). Thus no definition issue concerning zero chores explains the negative result. Raw matrix fingerprints were searched, in addition to its invariant description. No indexed copy was returned.

A later simplification from the computational agent, `work/compute_p8_refutation_500.json`, has rows `(35,48,55,239,247,304,332,500)`, `(3,15,24,136,358,171,500,294)`, and `(20,4,7,235,166,500,56,203)`. Its first-row fingerprint and a fingerprint of its third row were also searched, with no indexed copy returned. The verification record for whichever matrix is selected for release must accompany that exact matrix; the counts above refer to the displayed original matrix.

## 4. Primary neighbors and collisions

| Source | Inspected statement | Relation to the frozen target |
|---|---|---|
| Kobayashi–Mahara–Sakamoto, arXiv:2305.04168, Observation 2.2(iii) | If an EFX graph has a perfect matching, one exists using a minimum edge for **some** agent. | The existential choice of agent does not establish the prescribed-agent condition. This is the closest matching-language neighbor. |
| Same paper, Theorem 3.1 and Algorithm 1 | Ordinary EFX exists for \(m\le2n\); the algorithm maintains a perfect EFX matching. | The stated theorem does not retain an arbitrary designated agent's ordinary envy-freeness. It covers ordinary EFX at six chores. |
| Same paper, Lemma 4.2 | Insertion of a chore cheapest for all but one agent can preserve an EFX matching. | The project's designated-agent variant follows its cycle/path mechanism with a stronger branch test. Attribute that mechanism; no claim of a novel general insertion principle. |
| Yin–Mehta, arXiv:2211.15836, Lemma 2.1 and §3 | Explicit generic perturbation; EFX under additional restrictions on two agents, using EFX-feasible bundles. | Direct prior for perturbation. The main theorem's common-order/collectivity hypotheses do not cover arbitrary seven-chore inputs. Some algorithm branches allow a particular chooser a favorite bundle, which is insufficient to assert the unrestricted target. |
| Feige–Norkin, arXiv:2205.05363, abstract | A prescribed agent receives proportional share while the allocation satisfies a \(19/18\)-MMS guarantee for chores. | A genuine prescribed-agent result, but neither EFX nor ordinary envy-freeness; it does not imply \(P_m\). |
| Zhang, arXiv:2609.10585v2, Theorems 1.1–1.2 | Ordinary EFX for seven/eight chores. | Same small cardinalities, different strengthened property. Its theorem already ensures that the displayed eight-chore matrix has ordinary EFX allocations. |
| Bhaskar–Sricharan–Vaish, APPROX/RANDOM 2021 | Top-trading envy-cycle elimination produces non-envious agents and maintains EF1 in its allocation algorithm. | Useful graph terminology, but the chosen non-envious agent is not prescribed, and EF1 is weaker than EFX. |

Primary texts: [KMS full version](https://arxiv.org/pdf/2305.04168), [Yin–Mehta full version](https://arxiv.org/pdf/2211.15836), [Feige–Norkin](https://arxiv.org/abs/2205.05363), [Zhang v2](https://arxiv.org/html/2609.10585v2), [Bhaskar–Sricharan–Vaish full conference paper](https://drops.dagstuhl.de/storage/00lipics/lipics-vol207-approx-random2021/LIPIcs.APPROX-RANDOM.2021.1/LIPIcs.APPROX-RANDOM.2021.1.pdf).

## 5. Query log

The following exact strings were searched in the general web/arXiv index on 7 October 2026. Returned primary sources were preferred; secondary pages served only as discovery aids.

```text
"EFX" "chores" "designated" "envy-free"
"EFX" "chores" "prescribed" agent
"EFX" "chores" "one agent" "envy-free"
"EFX" "matching" "minimum" "prescribed"
"chores" "EFX" "specified agent"
"chores" "EFX" "particular agent" "envy-free"
"EFX" "prescribed" "envy"
"EFX" "envy-free agent"
"EFX" "chores" "prescribed" "envy-free"
"EFX" "chores" "minimum edge" matching
"37" "51" "59" "255" "264" "325" chores
"EFX" "chores" "2885" "595"
"EFX" "chores" "designated agent"
"EFX" "chores" "prespecified"
"EFX" "matching" "minimum cost" agent
"Improved maximin fair allocation of indivisible items to three agents"
"chores" "EFX" "envy-free" "seven"
"chores" "EFX" "fully envy-free"
"EFX" "prescribed" "minimum"
"EFX" "chores" "EF agent"
"EFX" "chores" "non-envious"
"EFX" "chores" "sink"
"EFX" "chores" "specified" "envy"
"EFX" "chores" "envy-free agent"
"EFX" "designated sink"
"EFX" "chores" "non-envious agent" prescribed
"EFX" "chores" "prescribed agent" seven eight
"EFX" "chores" "33353" "71016"
"35" "48" "55" "239" "247" "304" "332" "500" chores
"EFX" "chores" "20" "4" "7" "235" "166" "500"
"chores" "every EFX allocation" "envies"
"chores" "EFX" "non-envious" "agent 1"
"chores" "EFX" "prescribed minimum"
"chores" "EFX" "inevitable envy"
```

## 6. Outcome and permitted claims

**CLEAR TO PROVE within this bounded search:** no inspected source states the sharp prescribed-agent seven/eight boundary or supplies the displayed obstruction. Confidence is moderate, because this specific quantifier strengthening may appear as an unadvertised invariant in other proofs. Search did find the close matching statement with “some agent,” which must be kept distinct.

The insertion argument and perturbation are related to explicit prior work. They should be presented as attributed ingredients or elementary consequences, not as independent novel principles. The project's strongest potential contribution unit is the exact sharp small-cardinality result, supported by its semantic encoding audit and externally checked finite refutations.

Permitted wording, once the proofs pass: “In a bounded primary-source search conducted on 7 October 2026, we found no earlier statement of this prescribed-agent threshold.” Avoid “first,” “unprecedented,” or an unconditional historical-priority claim. Do not label this result a solution of the original nine-chore problem.

The six-chore finite refutation has a cvc5 proof export and a successful corrected input-bound Ethos check. The residual seven-chore formula and an exact assertion subset received Z3 UNSAT verdicts, but both bounded cvc5 proof attempts ended without a certificate; the full attempt exhausted memory and the core attempt exited 139 without a diagnostic or verdict. Thus the sharp seven/eight conclusion retains a solver-trust dependency at P7 and is not externally certified in this package. Negative controls exposed an Ethos reference-binding pitfall in positional-file mode; the runner was corrected to stream the proof while reusing original declarations. Only corrected successful receipts establish external proof checking bound to the exact input. Solver/checker receipts are authoritative for the final proof status. The search covers indexed English-language primary sources, not private manuscripts, exhaustive bibliographic databases, all unindexed branches, or author correspondence. No author contact was made.
