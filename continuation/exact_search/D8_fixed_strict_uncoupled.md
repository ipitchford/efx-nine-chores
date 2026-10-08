# Prescribed-agent D8 with fixed positive minima

7 October 2026. The bounded calibration returned **UNKNOWN / timeout**
after 120.061743 seconds. It does not prove D8 and does not refute D8.

## Exact target and normalization

For each complete allocation `(A0,A1,A2)`, the formula asserts that either
agent 0 fails ordinary envy-freeness, or agent 1 or 2 fails literal EFX.
The first alternative is

`c0(A0) > c0(A1) OR c0(A0) > c0(A2)`.

For agent `i` in `{1,2}`, an EFX failure is an ordered comparison `i,j`
and an owned chore `g` for which

`ci(Ai minus {g}) > ci(Aj)`.

All positive eight-chore allocations with an empty bundle automatically
fail EFX: another bundle has at least two chores and retains positive
cost after one deletion while it is compared with an empty bundle. Thus
the formula needs the 5,796 nonempty allocation clauses; a full SAT replay
still checks all 6,561 allocations.

The source is the archived `results/D8_root.smt2`, with SHA-256
`700a33e91a5ba54c777ee18a720f72c6e2537139be843902093b0eef01e5f1d0`.
The new input is `D8_fixed_strict_uncoupled.smt2`, with SHA-256
`2d0b7a3dbe1ae88f46b1413e7fc17af5c53ca734ccd0b2ecf67fa8d5498fe17c`.

Every row has a positive unique minimum, pinned at its diagonal column.
Dividing row `i` by `ci(i)` preserves the sign of every comparison made
by that agent, including ordinary-EF comparisons for agent 0. Every
source-domain condition is homogeneous within one row. Independent row
scaling therefore preserves the full source formula, and sets all three
pinned minima to one. Conversely, every model of the fixed-minimum
formula is already a model of the original homogeneous formula. No
unit failure margins are introduced: every failure comparison remains
strict.

The prescribed agent remains agent 0. Only agents 1 and 2, together with
their minimum columns, may be interchanged to obtain `c01<c02`. The free
columns 3 through 7 retain their descending row-0 order. There is no
comparison between different row totals. The resulting domain is a
product of three row domains, with 21 free real variables, 50 domain
assertions, and 5,796 allocation clauses.

## Semantic checks

`prepare_d8_fixed_min.py` substitutes the three diagonal constants into
the archived source, exports the result, and checks that all 5,846 parsed
assertions are identical to that exact substitution. It makes no
satisfiability call. It then evaluates both source and normalized clause
coefficients and compares them with the separate literal checker in
`src/efx_exact.py`, explicitly passing `designated=0`.

The finite audit covers 13 matrices and 85,293 complete allocation pairs.
All 75,348 nonempty clause comparisons agree with the literal predicate,
and all 9,945 empty-bundle allocations fail. Ten generic matrices include
independent row scalings. Two previously difficult candidates retain
exactly one and three prescribed-agent allocations after normalization.
The uniform-one control has 560 prescribed-agent allocations and 1,680
ordinary EFX allocations, which detects an accidental replacement of
ordinary envy-freeness by EFX for agent 0. A separate zero-deletion control
detects omission of zero-cost owned chores from the literal predicate.

These are finite encoder and transformation checks. They are not an
independent proof of D8. Their exact receipts are
`D8_fixed_strict_uncoupled_preparation.json` and
`D8_fixed_strict_uncoupled_audit.json`.

## Bounded solver calibration

`run_frozen_d8.py` checks this exact input using Z3 5.1.0, arithmetic
engine 2, seed 0, a 120-second solver timeout, and a 750-MiB address-space
cap. A launch guard required at least one GiB of shared memory headroom;
the observed headroom was 2,801,967,104 bytes.

The result was UNKNOWN with reason `timeout`, after 120.061743 seconds.
Peak process RSS was 203,024 KiB. No proof or SAT model was returned.
The saved log and receipt are
`D8_fixed_strict_uncoupled_calibration.log` and
`D8_fixed_strict_uncoupled_calibration.json`.

The runner's SAT branch separately checks both ordinary EFX and the
prescribed-agent condition on all 6,561 allocations. A counterexample to
D8 would concern the stronger prescribed-agent target and would not by
itself refute ordinary eight-chore or nine-chore EFX existence.
