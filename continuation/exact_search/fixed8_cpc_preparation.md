# Fixed-minimum eight-chore proof preparation

Prepared 7 October 2026. **No proof-generation job was started by this preparation.**

The exact input which returned Z3 UNSAT in 21.583789244999934 seconds is
`fixed8_strict.smt2`, SHA-256
`d400ce0303c71da3c3c883130b401335bcef86861f213887843570c90d8ba9cd`.
Its calibration receipt is `fixed8_strict.json`. It asks whether a positive
eight-chore ordinary-EFX counterexample exists with distinct minima pinned
in columns 0, 1, 2, each fixed to one. It has no row-total comparisons.

The project inventory contains no native or external proof object for this
exact fixed-minimum input. The older native `root8_pruned.z3proof` belongs
to a different input. The old full-eight-chore cvc5 attempt was killed
without a verdict; it supplies no independent proof for either input.

The installed cvc5 Python package is 1.4.1. The existing CPC/Ethos wrapper,
checker binary, and version-matched signature files are present. After the
main nine-chore search budget finishes, the following is a minimal bounded
export attempt, run from the project root:

```bash
python src/check_cvc5.py continuation/exact_search/fixed8_strict.smt2 \
  --output continuation/exact_search/fixed8_strict_cvc5 \
  --report continuation/exact_search/fixed8_strict_cvc5.json \
  --format cpc --logic QF_LRA --granularity dsl-rewrite \
  --timeout 600 --address-space-mib 2450 \
  > continuation/exact_search/fixed8_strict_cvc5.log 2>&1
```

If the export succeeds, the separate input-bound verification is:

```bash
python src/check_ethos.py continuation/exact_search/fixed8_strict.smt2 \
  continuation/exact_search/fixed8_strict_cvc5.cpc \
  --timeout 600 --report continuation/exact_search/fixed8_strict_ethos.json \
  > continuation/exact_search/fixed8_strict_ethos.log 2>&1
```

The existing Ethos adapter sends the proof through stdin, preserves the
original constants, checks every global assumption against the input, and
requires a proof of false at global scope. Success requires exit zero and
the verdict `correct`. CPC export alone is not independent verification.
The 21.58-second Z3 solve does not predict cvc5 time or memory use.

`fixed8_cpc_prepared_config.json` records absolute command arguments,
hashes, proposed resource limits, and the preparation-only status.
