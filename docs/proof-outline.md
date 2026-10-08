# Proof outline and status

## Statement

The commissioned statement is universal complete EFX existence for three agents and nine indivisible chores, with arbitrary nonnegative additive costs and with every owned chore in the removal quantifier, including zero-cost chores. **No proof or counterexample to this statement was obtained.**

The completed ancillary statements are different:

1. A particular positive integer eight-chore matrix has exactly 36 EFX allocations, none also making prescribed agent 0 ordinarily envy-free.
2. Appending any nonnegative ninth cost column to that matrix still permits EFX. Three explicit allocations cover all values of the new column.
3. A prescribed agent can be made ordinarily envy-free together with EFX for six chores. The finite arithmetic refutation has been checked externally against its exact input; the mathematical encoding argument remains separate.
4. Minimum insertion can preserve a prescribed agent's ordinary envy-freeness when the new chore is cheapest for all other agents. This lemma holds for any number of agents, zero costs, and empty bundles.

The positive prescribed-agent seven-chore statement has a complete mathematical reduction and a Z3 UNSAT result. Its final external-certificate status is in `CLAIM_STATUS.json` and the authoritative verification record. The ordinary seven/eight EFX frontier is prior work.

## Idea

The allocation space is finite while the cost space is continuous. Negating fairness for a fixed allocation gives a disjunction of strict linear inequalities; conjoining those failures produces an exact linear-real-arithmetic decision problem. This supplies an exhaustive certificate mechanism, not a runtime guarantee. The prescribed-agent strengthening would have made insertion of one cheapest chore immediate, but it fails at eight chores. The exact obstruction explains why that stronger induction does not establish the ninth case. A separate cycle/path argument preserves prescribed envy-freeness under the more restrictive shared-minimum insertion condition.

## Outline

1. **State the exact predicate.** Each agent evaluates both bundles with its own costs; every owned chore is removable. Empty-bundle residuals are zero. Location: memorandum Sections 1-2; `target.yaml`. **Standard.**
2. **Justify the canonical domain.** Positive row scaling and common column permutations preserve comparisons. A finite selection of strict failure witnesses survives a sufficiently small positive generic perturbation. Location: memorandum Section 2; ancillary proof record Section 1. **Standard/routine.** The explicit perturbation idea appears in Yin-Mehta, Lemma 2.1.
3. **Separate the known shared-minimum case.** The KMS insertion lemma plus the previous cardinality theorem handles a chore cheapest for two agents. Zhang already states the nine-chore use of this reduction. Location: memorandum Section 2 and novelty report. **Standard.**
4. **Preserve the prescribed agent under insertion.** A directed cycle among nonprescribed agents permits rotation and insertion; otherwise a directed path ends at the prescribed agent and can be rerouted to preserve its minimum bundle. Location: ancillary Theorem 1; memorandum Section 3. **The point.** It is a refinement of the KMS method, with no historical-priority claim.
5. **Refute the full six-chore prescribed-agent formula.** Handle zero rows directly, normalise nonzero rows, sort columns, and rule out all 729 allocation failures simultaneously. Location: the standardized six-chore SMT input, exported CPC proof, corrected Ethos receipt, and full coefficient audit. **The point.** The numerical refutation is computer-assisted; no short human proof of that finite arithmetic core is supplied.
6. **Identify the failed eight-chore strengthening.** Enumerate all 6,561 allocations of the displayed positive integer matrix, and check one strict failure inequality for each allocation. Location: memorandum Section 4; `src/verify_finite.py`; the CSV certificate. **The point.** This is a finite counterexample to the stronger property only.
7. **Prove the fixed-matrix ninth-column cover.** Two upper-bound insertion regions and one lower-bound singleton region cover every possible nonnegative added column. Location: memorandum Section 5; ancillary Section 4; exact extension-box record. **The point.** The statement fixes the first eight columns.
8. **Retain the missing nine-chore obligation.** Full residual searches and conditional case searches did not supply a resolving verdict. Location: memorandum Section 7; `CLAIM_STATUS.json`; run receipts. **Unfinished target.** There is no valid final inference establishing or refuting universal nine-chore existence.

## New components

The exact positive integer obstruction and its complete allocation certificate can be reused to falsify prescribed-agent induction arguments. The three-allocation extension cover gives a short complete analysis of one natural attempted nine-chore construction. The any-agent insertion lemma has a natural invariant and supports the prescribed-agent cardinality reduction. The external proof-checking wrapper and its negative controls address a concrete input-binding problem in the recorded checker invocation.

None of these components is labelled a new solution of the nine-chore problem. The novelty searches found no earlier prescribed-agent seven/eight boundary in the inspected corpus, but absence from that search does not establish historical priority, and the positive side requires its own proof evidence.

## Prior work

- Zhang, X. (2026), version 2 of *EFX allocations for three agents and seven or eight chores*: the ordinary frontier and the exact nine-chore residual programme. https://arxiv.org/abs/2609.10585v2
- Kobayashi, Y., Mahara, R., and Sakamoto, S. (2023 full preprint; 2025 journal article): EFX graphs, the at-most-twice-the-agent-count theorem, and minimum insertion. https://arxiv.org/abs/2305.04168
- Yin, L., and Mehta, R. (2022), Lemma 2.1: explicit generic perturbation for chores EFX. https://arxiv.org/abs/2211.15836

Search date, queries, inspected versions, object distinctions and bounded novelty conclusions are recorded in the two novelty reports.

## Verification status

The standard-library enumeration and CSV replay were independently rerun by the root agent, in addition to separate structural and computation implementations. The prescribed-agent static formulas were independently parsed and compared coefficient by coefficient with the literal specification. External CPC checks bind the successful smaller refutations to their reference inputs and require global false; corrected receipts supersede the deprecated positional-file checks. The source of every count is identified in the verification record.

The handwritten reductions have not been formalised in a proof assistant. Finite semantic tests do not prove unrestricted real-domain existence. Main-nine solver timeouts, memory failures and interrupted searches remain undecided. A concrete sanity check is the exact uniform-nine count, 9!/(3!)^3 = 1,680, and the all-zero count, 3^9 = 19,683. Both are reproduced by the standalone checker.
