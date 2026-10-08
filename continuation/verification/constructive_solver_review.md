# Independent review of the constructive nine-chore solver

**Outcome:** no mathematical correctness gap identified in `src/solve_efx9.py`. The implementation was read without alteration. Its exact source hash and the completed controls are in `constructive_solver_independent_review.json`.

## Exact input and scaling

The command-line JSON loader converts decimal-number tokens to strings before constructing `Fraction`, so decimal and scientific-notation inputs retain their written rational values. Integer tokens remain integers. Boolean values, binary floating-point objects passed directly to the Python API, nonfinite constants/strings, negative values, and zero denominators are rejected. The solver requires exactly three rows of nine costs.

Each row is multiplied by the least common multiple of its nine denominators. That factor is a positive integer, including for an all-zero row. Every scaled entry is therefore an exact integer, and comparisons are preserved because each EFX inequality uses a single evaluating agent's row. No common normalization across agents is assumed.

## Subsets, zeros, and complete enumeration

For each subset mask the table computes its sum and true minimum, using the smaller mask obtained by removing one bit. The singleton branch initializes its own minimum rather than carrying the empty set's zero. The residual is `sum - minimum`, which equals the maximum cost after deleting one owned chore. If an owned chore costs zero, deleting it is included and leaves the entire bundle total. The empty set has residual zero; for nonnegative costs this convention is equivalent to the vacuous empty-owner EFX condition.

The enumerator visits `product(range(3), repeat=9)`. This gives all 19,683 complete labelled assignments, including assignments with empty bundles. Each chore contributes exactly one bit to exactly one owner's mask. The six row/bundle comparisons use the evaluating row for both owned residual and target-bundle cost. Thus the search test is equivalent to every literal owned-chore deletion inequality.

## Returned witness and scope

The selected assignment is rechecked with original exact `Fraction` costs, independently of the subset tables and row scaling. The literal checker loops over every owned chore for both other agents, with no filter on removed cost. A complete nine-chore assignment therefore yields 18 literal inequalities. All displayed indices are consistently converted to one-based agent and chore numbers.

Allocation completeness is guaranteed by the enumerator. `literal_certificate` is an internal literal re-evaluation routine; it is not presented as a validator for arbitrary externally supplied malformed assignments. If no allocation passed, the program would report that explicit finite-search outcome instead of assuming the theorem and fabricating an allocation.

## Complementary finite controls

The independent check compared all 1,536 subset-table entries across three rows containing zeros, distinct denominators, a very small rational, a large integer, and an entirely zero row. It evaluated 6,912 literal deletion residuals directly, including 3,840 zero-cost deletions. All exact row-scaling identities, subset sums, and maximum residuals agreed. Six invalid-input controls were rejected.

A command-line JSON fixture with cost token `0.1000000000000000001` verified that the written decimal, which is not exactly representable as a binary floating-point value, is retained exactly. Its returned assignment covers all nine chores and passes every literal comparison. These finite controls supplement the preceding general source argument and do not replace the independent existence certificate for the economics theorem.
