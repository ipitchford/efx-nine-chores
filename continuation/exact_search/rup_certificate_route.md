# Input-bound arithmetic and Boolean certificate route

The solved nine-chore formula is `zero_minimum9_reference_strict.smt2`, SHA-256
`65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b`.
Its native-proof-free Z3 run returned UNSAT. That verdict is motivation for
certificate production; it is not a premise accepted by the independent checker.

The certificate has three independently checked layers:

1. `continuation/verification/check_lra_capture.py` parses the exact frozen SMT
   using Python's standard library, expands simultaneous `let` expressions, and
   reconstructs every original clause under the captured exact affine atom map.
2. `check_lra_rup.py` checks each selected source axiom and every ordered unit
   propagation reason, including the final falsified conflict clause. Every RUP
   inference assumes the negation of its proposed clause. Its reasons refer only
   to already checked clauses. The final derived clause is empty, and the trace
   contains exactly its backward dependency closure.
3. `check_lra_certificate.py` additionally checks all selected arithmetic theory
   clauses with exact `Fraction` multipliers. Nonnegative combinations cancel
   every variable coefficient and yield either a positive constant contradiction
   or a zero constant with positive strict-inequality weight.

Neither callback assumptions nor a solver verdict are admitted as axioms. A
theory clause may be placed before any Boolean proof step because its arithmetic
certificate independently establishes validity. Integrality, approximate LP
feasibility, and native solver proof objects are not checking assumptions.

The untrusted C++ producer `rup_dependency_producer.cpp` uses watched literals to
replay the recorded RUP stream over all original and theory clauses, ignoring
deletions. Each check starts from a fresh assignment. It records reasons, slices
them locally to the conflict, then trims the complete proof backward from the
empty clause. Stable IDs preserve original JSONL source positions: input record
`i` has ID `i+1`, theory record `j` has ID `I+j+1`, and derived IDs exceed `I+T`.
Null original records reserve an ID but cannot be axioms. A duplicate learned
clause may cite its older identical clause. An extra final empty clause is
emitted only after successful unit propagation.

All solver/capture and producer inputs remain frozen and hash-bound. Producer
outputs are fsynced after closing their output streams. The supervisor enforces
a process address-space cap and a hard process-group wall deadline. A produced
trace is always labeled untrusted until the independent checker accepts it.

## Eight-chore calibration

The raw v3 capture's original input/atom streams had missing terminal suffixes.
They remain preserved and rejected. The cause was not identified by the bounded
source/path inspection. `rebuild_static_capture.py` made a separate package at
`zero8_clause_capture_composed1/capture`: it regenerated all static clauses and
atoms from the frozen SMT without calling a solver check, and copied only the
v3 theory/RUP streams. Rebuilt bytes equal the complete v2 streams and extend the
surviving v3 prefixes exactly. The independent standard-library binder checks
this combined package directly against the frozen source, so neither the
reconstruction program nor agreement with v2 is a trusted proof premise.

The producer controls in `rup_dependency_producer_controls.json` cover exact
duplicates, null input holes, watched propagation and resolution proofs on two
through six variables, plus rejection of a non-RUP clause. Their accepted traces
were replayed with the independent checker.

The real eight-chore trim uses `zero8_rup_trim1_config.json`, with 900 MiB AS and
180 seconds hard wall. It completed normally in 20.82 seconds total with
108,540 KiB peak RSS. It processed all 189,184 RUP records and selected 898
original clauses, 27,637 theory clauses, and 10,845 derived clauses. The trace
has 405,499 ordered reasons and ends at empty clause ID 443989.

`continuation/verification/zero8_rup_trim1_independent.json` records successful
independent replay of the Boolean refutation. The first multiplier stream was
preserved and rejected for a missing 237-record suffix and a hash mismatch.
Only that suffix was regenerated; the separately composed full stream exactly
matches the originally recorded intended hash. The full stream was fsynced and
independently checked. All 27,637 selected exact Farkas identities passed, and
`continuation/verification/zero8_complete_lra_certificate.json` binds the
complete computational certificate.

No statement in this calibration supplies a nine-chore certificate by itself.

## Larger-input extraction and checkpoints

The complete nine-chore callback capture returned UNSAT and its terminal raw
snapshot passed independent reconstruction. It contains 3,234,215 theory clauses
and 2,480,762 recorded RUP steps. Forward replay proved too slow. The backward
producer first treats recorded RUP clauses provisionally when propagating the
final empty goal, then recursively justifies every required derived premise
using only strictly earlier source IDs. Provisional clauses are never accepted
as axioms in the final proof. The unchanged independent checker enforces ordinary
chronological RUP and complete dependency closure.

The first nine-chore backward attempt hit its 900-second hard producer limit;
43,000 candidate counts were logged but no complete trace or hint checkpoint
was emitted. The successor v6 processes goals in decreasing ID order, allowing
permanent removal of ineligible future watches and unit clauses. It writes each
candidate derivation to `candidate_justifications.jsonl`, flushing and fsyncing
every 1000 new records. An optional fourth CLI argument loads such an untrusted
checkpoint into a fresh output directory. IDs, clauses, and strict earlier-ID
references must match the captured source; resumed dependency closures are still
expanded. A final unterminated checkpoint line is explicitly discarded and its
work recomputed. Final independent replay remains necessary for every resumed
hint, regardless of producer-side checks.

The v6 controls cover five complete small proofs and their resumed replays,
self-referential checkpoint rejection, truncated-tail recovery, and four
invalid provisional-refutation patterns. Separate v3/v4/v5 real-eight Boolean
calibrations also passed the existing independent checker without changing the
accepted eight-chore certificate. The nine-chore v6 attempt was deliberately stopped after 49,312 candidate
records were sealed in a separate read-only checkpoint. Its source hash is
`2648db7a10c77853c6dcf66ff628ef0ead590a0a2c34c6ac5c1ca153ddb47097`.

Arithmetic generation can be pipelined from sealed complete-line checkpoint
prefixes. Here input source IDs are 1 through 18,178; theory source index `j`
has global ID `18,179+j`, up to 3,252,393. Only references in that interval are
theory candidates. A prefix snapshot records its initial byte bound, copies only
complete lines, then fsyncs, atomically renames, and binds all observed hashes.
Any extra arithmetic candidates are filtered against the completed proof's
selected theory indices before independent acceptance.


## Source-only closure caching and resumption

The v7 successor computes unit propagation from original and theory source
clauses before loading any provisional captured RUP nodes. Each nontrivial
forced literal becomes an explicit ordinary RUP unit node; the independent
checker does not preload a trusted assignment. Nine chores produced 2727 such
nodes, supplementing 28 original units. These source-only consequences remain
valid for every earlier-prefix goal. Newly loaded provisional clauses are also
indexed if they are already unit or conflicting under the source assignment;
otherwise their permanently false watches would not be revisited.

Original input and theory IDs are unchanged. In the final trace the cached unit
nodes immediately follow source axioms, and captured RUP IDs are shifted by
the number of cache nodes. Checkpoints retain the old external captured IDs
for compatibility with v6; cached node external IDs sit above the original
captured range. Every external ID is mapped to the final internal ordering,
and previously saved hints remain untrusted until independent replay. Thus a
v7 external checkpoint may refer to a cache node with a larger external ID
without creating a future dependency in the final proof.

Both a fresh real-eight extraction and a real old-hint cross-version resumption
passed the unchanged independent checker. Nineteen producer controls include
conditional units under the permanent source assignment and old/new checkpoint
resumption. The nine successor, `zero9_rup_source_cache_run1`, resumes the sealed
49,312-record prefix under a new 1800-second hard and 3000 MiB address-space
budget. This changes proof production only; the frozen SMT input, arithmetic
interpretations, and trusted acceptance rules remain unchanged.


The nine source-cache run completed normally at 00:11:39 UTC on 8 October
2026 after 1124.329 supervisor seconds, with peak RSS 1,322,588 KiB. It emitted
a complete untrusted candidate trace: 4550 original axioms, 370780 selected
theory axioms, 172146 derived clauses, and 8088323 ordered reason positions.
The final empty clause ID is 5735883. All output files were fsynced, read back,
hashed, and marked read-only in `zero9_rup_source_cache_run1`; the separate
`sealed_output_manifest.json` binds their counts and hashes. Independent
Boolean replay and selected exact arithmetic verification remain acceptance
requirements.

The unchanged independent Boolean checker accepted the complete nine trace in
`../verification/zero9_rup_source_cache_independent.json`. It checked every
source clause, chronological reason, final empty clause, and exact backward
dependency closure in 30.267 seconds under a 1600 MiB address-space budget.
The first 700 MiB attempt raised MemoryError and is preserved separately.
All 370780 selected arithmetic theory axioms still require exact Farkas
acceptance before the complete LRA certificate can be claimed.

## Completed nine certificate

All 370780 selected exact Farkas clauses subsequently passed independent
standard-library rational checking, using 1317350 multiplier positions.
`../verification/zero9_complete_lra_certificate.json` now records
`PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE` and binds the completed input,
Boolean, and arithmetic stages. The source-cache optimization and resumed
candidate hints therefore supplied a fully checked refutation of the frozen
canonical nine-chore formula. No arithmetic bound or additional symmetry
condition was added to that formula. The full mathematical target binding is
`../verification/zero9_full_target_binding.json`; it retains the handwritten
reductions and ordinary eight-chore baseline as explicit premises.
