# Bounded formula search for the primitive-Cramer refinement

Search date: 7 October 2026. Status: bounded uncertainty; no historical-priority claim.

## Objects compared

The economic target is three agents, nine chores, arbitrary nonnegative additive costs, and literal EFX including every zero-cost owned deletion. The independent auxiliary formula is Q_m = floor(sqrt((m-1)(m-2)^(m-2))), with one zero per row; its nine-chore value is 2566 and its positive common-minimum-one lift is 5132. The main 21-variable UNSAT input uses no integer ceiling.

## Queries

- "EFX" chores "minimum" "zero" "counterexample" normalization
- "EFX" chores "2566"
- "determinant" "primitive" "Hadamard" "gcd" inequalities
- "Cramer" "2^{f-1}" "Hadamard"

No returned primary result identified this exact auxiliary bound or a resolution of the specific nine-chore target. This is a finite search result, not evidence that no earlier treatment exists. Results about generic determinant estimates were treated as background methods, not as exact object matches. The argument is independently supplied in full and makes no novelty claim for the classical Cramer, parity, and Hadamard ingredients.

## Scope checks on nearby primary sources

Zhang's version2 and its companion repository concern seven/eight chores, use the same zero-inclusive EFX convention, and explicitly leave nine open in the inspected version: https://arxiv.org/html/2609.10585v2 and https://github.com/KaixxxZhang/Chores-EFX-n3m7or8/blob/main/README.md .

He and Tao's additive nonexistence statement concerns n >= 4, so its counterexamples are not counterexamples to the present three-agent target: https://arxiv.org/abs/2606.08872 .

Christoforidis and Santorinaios give a three-agent six-chore nonexistence construction for superadditive costs; that cost model differs from the additive target here: https://www.ijcai.org/proceedings/2024/300 .

The cited classical integer-inequality bound remains von zur Gathen and Sieveking (1978), https://doi.org/10.1090/S0002-9939-1978-0500555-0 . The specialized common-divisor refinement is proved directly in continuation/verification/primitive_cramer_bound.md, with its stated scope and no claim that a finite integer range was exhausted.
