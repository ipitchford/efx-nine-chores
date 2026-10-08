# Reproducing the finite checks and proof certificates

The package now contains a **complete independently checked computer-assisted proof** of EFX existence for three agents and nine chores with arbitrary nonnegative additive costs. The concrete fresh replay command is in [zero9_replay_command.txt](zero9_replay_command.txt) and Section 15 below. Earlier ancillary results and unsuccessful attempts retain their original scopes. In particular, the eight-chore integer example refutes a prescribed-agent strengthening and has 36 ordinary EFX allocations; it is not a counterexample to ordinary EFX. Read [VERIFICATION.md](VERIFICATION.md) for the distinct claims and checker boundaries.

Commands below run from the package directory, the directory containing `src/`, `results/`, `certificates/` and this `docs/` directory. Complete eight- and nine-chore exact LRA replay uses Python's standard library and writes to a new explicitly named output directory. The historical CPC replays additionally require a locally built pinned Ethos checker and the supplied signatures; that requirement does not apply to the complete exact LRA replay. The original receipts remain available for comparison.

## 1. Choose the level of reproduction

| Task | Required software | What a successful run establishes |
|---|---|---|
| Replay the complete nine-chore exact certificate | Python standard library, Unix-like `resource` support, explicit 1,600 MiB process cap; command in §15 | Complete original-input/atom binding, Boolean refutation, and exact arithmetic axiom coverage for the stated input; the supplied written reduction links this to the economics theorem |
| Exhaustive integer example, all-zero and uniform controls | Python standard library only | The exact allocation counts and the failure certificate for the displayed eight-chore matrix |
| Replay an archived CPC proof | Python standard library, a locally built pinned Ethos checker, bundled CPC signatures | A checked refutation bound to its recorded SMT input, subject to the declared checker/calculus and encoding premises |
| Run checker boundary controls | The preceding row plus `cvc5==1.4.1` | Enforcement of reference membership and the final-false requirement on four small controls |
| Regenerate solver proofs or formulas | `cvc5==1.4.1` for proof export; `z3-solver==5.1.0.0` for the Z3 generator | A new solver execution, which requires its own receipt and external checking |
| Rebuild the final PDF report | Pandoc/XeLaTeX and fonts in §13; §8 is the historical ReportLab path | Presentation output; no additional mathematical verification |

The recorded Python interpreter was **3.12.14**. The replay/setup scripts target Python 3.10 or newer, but the recorded checks were run on 3.12.14. A Python package installation is unnecessary for the standalone finite check or for replaying an existing proof with an already built checker.

## 2. Run the standalone exact finite checker

```sh
python3 src/verify_finite.py \
  --out replay/finite_verification.json \
  --certificate replay/p8_designated_failure_certificate.csv
```

Expected output is `status: PASS`, with these exact counts:

| Check | Expected result |
|---|---:|
| Complete labelled allocations of the eight chores | 6,561 |
| Ordinary EFX allocations for the displayed integer matrix | 36 |
| EFX allocations also making prescribed agents 0, 1 and 2 ordinarily envy-free | `[0, 31, 31]` |
| EFX allocations for identical all-one costs on nine chores | 1,680 |
| EFX allocations for all-zero costs on nine chores | 19,683 |
| Deliberate mutation omitting zero-cost owned removals | Rejected |

The checker uses integer arithmetic, includes empty bundles, and quantifies over every owned chore, including a zero-cost chore. It writes one failing inequality for every eight-chore allocation under the prescribed-agent target, then independently replays those inequalities from the matrix and the decoded allocation. The certificate uses lexicographic base-three allocation IDs, with chore 0 as the most significant digit. Its columns are `allocation_id,kind,agent,other,removed_chore,lhs,rhs`; `removed_chore=-1` denotes an ordinary-envy inequality. Every certified failure has `lhs > rhs`.

The frozen reference outputs are [finite_verification.json](../results/finite_verification.json) and [p8_designated_failure_certificate.csv](../results/p8_designated_failure_certificate.csv). For a byte comparison of the deterministic CSV, use:

```sh
cmp results/p8_designated_failure_certificate.csv \
  replay/p8_designated_failure_certificate.csv
```

The JSON receipt contains an output path, so a fresh receipt need not be byte-identical to the archived one. No SMT solver or external proof checker is involved in this section.

## 3. Build the pinned external checker

### Exact source pins

The source pins are recorded in [checker_build.json](../results/checker_build.json) and checked by the setup script before it builds anything.

| Component | Version or commit |
|---|---|
| Ethos source | `08e4aa40c4f8a6e00833f10e8d8985777e424027` |
| cvc5 source supplying the signatures | `2b2e84419f70817ec919a784a48806e79f677240` |
| cvc5 Python package and signature release | `1.4.1` |
| Z3 Python package for formula regeneration | `z3-solver==5.1.0.0` |

The source repositories are [cvc5/ethos](https://github.com/cvc5/ethos) and [cvc5/cvc5](https://github.com/cvc5/cvc5). The cvc5 commit is the recorded resolution of the `cvc5-1.4.1` tag. The Ethos commit is the one selected by that release's checker helper. The setup script fetches those exact commits; it does not follow the current main branch or an unpinned tag.

### Build prerequisites and command

Provide Bash, Python 3.10+, Git, CMake 3.13+, Make or Ninja, a C++17 compiler, and GMP C/C++ development headers and libraries. GMP must supply `gmp.h`, `gmpxx.h`, and both C and C++ link libraries. The script checks the compiler and GMP with a small compile-and-run probe before fetching source code. It reports missing dependencies and does not install system packages.

```sh
bash scripts/setup_checker.sh --build --jobs 2
bash scripts/setup_checker.sh --check
```

The first command needs network access to the two GitHub repositories. It obtains the pinned sources under `work/checker_sources/`, compares the fetched CPC signature files with the archived hashes, and builds:

```text
work/checker_rebuilt/ethos/build/src/ethos
```

It saves compiler, platform, GMP version, source pins and the new executable hash in `work/checker_rebuilt/build_receipt.json`. It creates no proof certificate and rewrites no frozen SMT input or CPC object. The `--check` command checks signature bytes and executable startup; a successful setup check is not a proof verdict.

After the exact commits are present in the source cache, the build can be repeated without source downloads:

```sh
bash scripts/setup_checker.sh --build --offline --jobs 2
```

For nonstandard development-library locations, supply semicolon-separated header directories and absolute library files. For example, replace the illustrative paths below with the installed paths on the host:

```sh
GMP_INCLUDE_DIR='/path/to/include;/path/to/multiarch/include' \
GMP_LIBRARIES='/path/to/libgmpxx.a;/path/to/libgmp.so' \
  bash scripts/setup_checker.sh --build --jobs 2
```

`CXX` can select a compiler executable without extra flags. `EVIDENCE_PYTHON` can select a Python executable. Run the script with `--help` for alternate source/output directories. A checkout containing local edits is refused rather than reset. The script's syntax, help, signature verification and startup check were exercised during packaging; its network-fetch branch and a fresh full build through this script were not rerun. The original checker had already been built from the pinned source using the configuration recorded below.

### Observed build platform, not a cross-platform binary guarantee

The original successful checker was built on **Ubuntu 24.04.3 LTS, x86-64**, with GNU C++ **13.3.0**, CMake **4.4.4**, two build workers, and GMP **6.3.0**. The missing GMP development files were extracted locally from the matching Ubuntu development archive; its URL and SHA-256 are in `checker_build.json`. No system package installation was performed for that build.

The original executable was a dynamically linked x86-64 Linux ELF binary using `/lib64/ld-linux-x86-64.so.2`. The observed loaded libraries were:

| Library | Observed host package/version |
|---|---|
| `libgmp.so.10` | `libgmp10` `2:6.3.0+dfsg-2ubuntu6.1` |
| `libstdc++.so.6` | `libstdc++6` `14.2.0-4ubuntu2~24.04.1` |
| `libgcc_s.so.1` | `libgcc-s1` `14.2.0-4ubuntu2~24.04.1` |
| `libc.so.6`, `libm.so.6` | `libc6` `2.39-0ubuntu8.6` |

The link command also used `libgmpxx.a`. The executable's directly requested versioned symbols included `GLIBC_2.34`, `GLIBCXX_3.4.32` and `CXXABI_1.3.9`; those observations alone do not establish compatibility with every host providing those versions. No Windows or macOS execution was tested. The package omits that platform-specific executable and asks readers to compile locally.

The original binary hash remains a provenance record:

```text
11c3f0685eeac19c655f8305af4cb75fd775639ad9c27aa2e2ac9ca7df66de8b
```

A local build may have a different hash even at the same source commit because its compiler, library linkage, paths or build metadata differ. Record the new hash and replay the actual proofs; the source pin does not promise a bit-identical executable. Authorship and licence notices are retained under `work/ethos/` and `work/cvc5_signatures/`, including Ethos's `COPYING`, `AUTHORS` and `licenses/lgpl-3.0.txt`.

## 4. Replay the archived, input-bound CPC proofs

After building the checker, use these commands:

```sh
python3 src/check_ethos.py \
  results/root7_pruned.smt2 certificates/root7_cvc5.cpc \
  --checker work/checker_rebuilt/ethos/build/src/ethos \
  --report replay/root7_ethos.json

python3 src/check_ethos.py \
  work/structural_designated_m6.standard.smt2 \
  certificates/designated6_cvc5.cpc \
  --checker work/checker_rebuilt/ethos/build/src/ethos \
  --report replay/designated6_ethos.json
```

The wrapper defaults to a 1,200-second timeout, adjustable with `--timeout`. The recorded checks took about 27 and 90 seconds respectively; these timings are observations, not guarantees on another host. The corresponding original receipts are [root7_ethos.json](../results/root7_ethos.json) and [designated6_ethos.json](../results/designated6_ethos.json).

Each fresh receipt must have `result: verified`, `returncode: 0`, `verdict: correct`, `timed_out: false`, `reference_binding: true`, `requires_final_false_at_global_scope: true`, and `expert_signature_enabled: false`. The wrapper returns nonzero when these acceptance conditions fail. Its recorded `input_sha256`, `proof_sha256`, complete `signature_sha256` map and `proof_stream_adaptation.stream_sha256` should agree with the archived receipt for the corresponding object. Absolute paths, elapsed time and the executable hash can differ between hosts.

The seven-chore ordinary refutation and six-chore prescribed-agent refutation have different mathematical scopes. Further certificates, if present, are identified by their successful receipts in [VERIFICATION.md](VERIFICATION.md). An unverified proof file, a solver timeout or a killed process is not an additional certificate.

### Why the wrapper and its arguments matter

`src/check_ethos.py` retains its original default executable path, `work/ethos/build/src/ethos`, for provenance and older local invocations. That executable is not distributed. The `--checker` option above selects the separately rebuilt executable. The default signatures path is `work/cvc5_signatures/proofs/eo/cpc`, which **is** supplied, so no signature-path override is needed. The full tree contains 51 `.eo` files, including 16 unused expert files retained to preserve the original hash manifest. Only `Cpc.eo` is loaded; do not enable `--include-expert` for these replay claims.

The wrapper loads the reference input with `--reference` and enforces `--require-proof-of-false`. It sends the proof through stdin. For this pinned Ethos version, opening the proof as a positional file resets the reference-state flag. A positional invocation can therefore give a derivation verdict without enforcing the required link to the original assertions.

The wrapper also checks and removes only duplicate initial Real declarations from a temporary streamed copy, so the proof reuses the reference's constants. Every actual proof definition, assumption and inference step is retained. The archived CPC bytes remain unchanged, and the temporary stream has its own recorded hash. Unsupported declarations and command classes that could include files or reset state are rejected. Do not manually rewrite the frozen CPC files or replace the wrapper with a positional Ethos command.

Ethos checks applications of the supplied calculus. The calculus, checker implementation, parsing and arithmetic runtime remain premises, as does the mathematical correspondence between the allocation problem and the SMT input. These checks are not an end-to-end proof-assistant formalisation of the fair-division theorem.

## 5. Reproduce the four boundary controls

This optional control run needs cvc5 because it regenerates a tiny contradiction proof. In an isolated Python environment, install the pinned package if needed:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install 'cvc5==1.4.1'

python3 src/check_ethos_controls.py \
  --checker work/checker_rebuilt/ethos/build/src/ethos \
  --work-dir replay/checker_controls \
  --report replay/checker_controls.json
```

The receipt must say `result: PASS` and all four cases must have `passed: true`: a valid refutation is accepted; deleting a required reference assumption is rejected; a valid non-refuting prefix is accepted without the false requirement; and that same prefix is rejected with the false requirement. The retained default paths in the controls script reproduce the old command's behaviour, but the explicit paths above use the rebuilt checker and protect the original receipt.

The archived result is [checker_controls.json](../results/checker_controls.json). These controls test boundary enforcement; they do not prove the soundness of the checker or calculus.

## 6. Optional arithmetic regeneration

Use the exact Python package pins for regeneration:

```sh
python3 -m pip install 'z3-solver==5.1.0.0' 'cvc5==1.4.1'
```

Replaying an existing CPC proof does not require re-solving the SMT problem. To create a new proof from the frozen ordinary seven-chore input with the original export options:

```sh
python3 src/check_cvc5.py results/root7_pruned.smt2 \
  --format cpc --granularity dsl-rewrite --timeout 120 \
  --output replay/root7_regenerated \
  --report replay/root7_regenerated_cvc5.json

python3 src/check_ethos.py \
  results/root7_pruned.smt2 replay/root7_regenerated.cpc \
  --checker work/checker_rebuilt/ethos/build/src/ethos \
  --report replay/root7_regenerated_ethos.json
```

For the prescribed-agent six-chore input, the recorded cvc5 options used a 240-second timeout and a 1,800 MiB address-space cap:

```sh
python3 src/check_cvc5.py \
  work/structural_designated_m6.standard.smt2 \
  --format cpc --granularity dsl-rewrite --timeout 240 \
  --address-space-mib 1800 \
  --output replay/designated6_regenerated \
  --report replay/designated6_regenerated_cvc5.json
```

The proof-export wrapper reads the static input through cvc5's public parser without importing the generator. Its receipt must report `result: unsat` and an exported proof before a subsequent replay is possible. Exit zero alone is insufficient: the exporter also returns zero for SAT. Any regenerated proof requires a new external-checking receipt. A different valid proof stream can result from a new solver execution; it does not replace the archived object's hash.

The original Z3 generator can also be rerun separately, for example:

```sh
python3 src/strict_lra.py --m 7 --timeout 120 --arith 2 \
  --normalisation none --order descending --row-symmetry \
  --prune --proof --export --out replay/root7_generator
```

That command creates a fresh formula and native solver result. It is not external verification of a native Z3 proof. The independently checked archived input remains the reference for the corresponding old certificate. Compare the generated input before associating a new file with an existing receipt.

The optional `src/verify_encoding.py` audit additionally imports NumPy; its recorded package version was `numpy==2.3.5`. It is not a dependency of the standalone finite checker or CPC replay. Exact semantic audits and the mathematical reductions are separate evidence layers described in [VERIFICATION.md](VERIFICATION.md).

## 7. Interpret failures and preserve the evidence

`verified` is the external wrapper's successful result; `correct` is the required Ethos verdict. `incomplete`, parse errors, nonzero exit status, timeouts, memory exhaustion and missing output do not verify a proof. They also do not prove the opposite mathematical statement. Older receipts marked with `_positional_deprecated` record a superseded invocation and do not establish reference-bound verification.

Retain the exact input, CPC object, signature files and receipts. Fresh runs should write to `replay/`. When reporting a new verification, identify the exact input/proof hashes and the locally built checker hash, and retain the receipt recording stdin adaptation and global-false enforcement. The central nine-chore existence question remains unresolved by the archived searches, regardless of whether the smaller certificates replay successfully.

## 8. Optional report reproduction

The mathematical checks do not depend on report-generation packages. This section records the historical ReportLab-based `src/build_report.py`; the final theorem manuscript uses the separate builder and dependencies in §13. The observed direct dependencies of the historical builder were:

```text
reportlab==4.4.9
matplotlib==3.10.8
svglib==2.3.0
```

The script expects DejaVu Serif, Sans and Sans Mono TrueType font files under `/usr/share/fonts/truetype/dejavu/`. Its current font paths are specific to that Linux layout. Regenerating the document on another host may require that font layout or a local presentation-only path adjustment. The supplied PDF can be read without those packages. Changes to document dependencies or fonts do not affect the frozen proof inputs or the integer verification.

## 9. Replay the completed continuation evidence

From the package root, run:

```sh
python3 continuation/verification/release_replay.py --phase all
```

This command uses only Python's standard library and creates a fresh timestamped output directory under `continuation/verification/`. It does not overwrite the preserved receipts. Its three audits independently recheck all 1,956 prefix certificates, all local guarantees and bindings in the 6,309-assertion positive-minimum two-row input, and every assertion in the full 18,177-assertion zero-minimum nine-chore input. Invalid mutation fixtures are excluded by the explicit [release index](../continuation/verification/release_certificate_index.json). Every indexed certificate and all 8,245 bound files are checked against their recorded hashes before replay. The scripts use Unix-like resource and alarm guards; the recorded Python version is 3.12.14.

The phases may also be run separately:

```sh
python3 continuation/verification/release_replay.py --phase certificates
python3 continuation/verification/release_replay.py --phase zero-formula
```

The preserved executions of those two phases passed against the same index. The certificate phase took 27.728 seconds, including the prefix and two-row audits; the zero-formula phase took 5.118 seconds. These figures describe the recorded environment and are not runtime guarantees. Each mathematical subprocess has its own 480 MiB address-space and 29-second alarm guard. A resource failure on another host is a failed replay attempt, not a mathematical result.

The expected top-level status is `PASS_RELEASE_LOCAL_CERTIFICATES_AND_INPUT_BINDING_NO_GLOBAL_VERDICT`. That last qualification is substantive: none of these checks runs a global SMT solver, proves that the certified regions cover their domain, or discovers a nine-chore counterexample. The final formulas and their exact hashes are described in [the consolidated review](../continuation/verification/consolidated_review.md), and completed versus active search attempts are kept separately in [CONTINUATION_STATUS.json](CONTINUATION_STATUS.json).

The reviewed search-domain theorem is also included: any counterexample has a representative with one zero per row and all positive integer costs at most **3,831**, hence a positive integer representative with common minimum one and even other costs at most **7,662**. See [the complete proof](../continuation/exact_search/zero_minimum_reduction.md) and [its independent review](../continuation/verification/zero_minimum_independent_review.md). The finite arithmetic controls and full serialized input reconstruction supplement that general argument. The bound does not claim that its integer domain has been exhausted, and old formulas that used the earlier 11,585 bound retain their recorded semantics.

### Additional completed continuation checks

The later [release_completion_audit.json](../continuation/verification/release_completion_audit.json) links the successful portable phases to the zero-outer and positive-lifted formula audits, the exact positive outer noncoverage witness, and their proof/source files. Its binding-only replay is:

```sh
python3 continuation/verification/audit_release_completion.py
```

This recomputes exact file hashes and cross-checks the recorded scopes; it does not repeat the mathematical certificate audits. Its expected status is `PASS_COMPLETED_RELEASE_EVIDENCE_BOUND_NO_GLOBAL_VERDICT`. It writes a new copy of that binding receipt at its stated path. Run it in a working copy if preserving the original recorded timestamp byte for byte is important.

The new static audit sources are `continuation/verification/audit_zero_outer.py`, `audit_lifted_formula.py`, and `verify_positive_outer_witness.py`. Their stored receipts record full assertion reconstruction or exact evaluation, rather than random samples. The noncoverage witness passes all 6,309 assertions of the original positive-minimum row relaxation and proves that the present 6,291-region family needs more regions. It is a pair of evaluating rows, not a full three-agent counterexample. The full zero-minimum and positive-lifted allocation formulas remain separate decision problems with their own recorded solver outcomes.

## 10. Historical complete-LRA replay interface

The following interface was prepared before the full nine-chore proof completed. Its original 700 MiB resource cap is retained. Section 15 gives the actual complete nine-chore command with the reviewed larger-budget wrapper and all final paths; this earlier template is preserved as part of the development record.

```sh
python continuation/verification/check_lra_certificate.py \
  --input continuation/exact_search/zero_minimum9_reference_strict.smt2 \
  --expected-sha256 65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b \
  --capture CAPTURE \
  --trace TRACE \
  --certificates CERTIFICATES \
  --selected-indices SELECTED \
  --out-directory continuation/verification/fresh_complete_lra_replay
```

Every stage uses Python's standard library, exact integers, and `Fraction`; no SMT/Boolean solver or floating-point linear-programming library is invoked. The checker reconstructs original CNF and affine atoms, checks a trimmed ordered RUP refutation, and checks every selected arithmetic theory axiom. It emits a complete UNSAT-certificate PASS only after all stages agree on input, source files, theory selection, and hashes. The separate end-to-end written reduction still links this finite input to the original economics problem.

## 11. Primitive-Cramer bound arithmetic

The strongest representative theorem is now **2,566** for the nonzero integer costs of a row with one zero, or **5,132** for positive integer costs with common minimum one. The full proof is `continuation/verification/primitive_cramer_bound.md`. Its exact numerical and small-dimension controls can be replayed with:

```sh
python continuation/verification/check_primitive_cramer_bound.py
```

The script is solver-free and writes a fresh arithmetic receipt. These are controls of the stated determinant argument, not an exhaustive economics search. Historical 3,831/7,662 inputs retain their original bounds and identities.

## 12. Complete portable eight-chore certificate replay

The following command replays the **accepted complete eight-chore certificate** from the root of an extracted bundle. The output directory must be new. Every input path may instead be supplied as an absolute path; historical absolute paths in producer receipts are preserved only as provenance, and checking uses the explicitly supplied files and their hashes.

```sh
python continuation/verification/check_lra_certificate.py \
  --input continuation/exact_search/zero_minimum8_reference_strict.smt2 \
  --expected-sha256 20d56e8ecd4bfad40ad5c7786c7865442c9961569dabb9e1a8dfe415b584c08f \
  --capture continuation/exact_search/zero8_clause_capture_composed1/capture \
  --trace continuation/exact_search/zero8_rup_trim1/trimmed_trace.jsonl \
  --certificates continuation/exact_search/zero8_selected_farkas_composed1/arithmetic_certificates.jsonl \
  --selected-indices continuation/exact_search/zero8_rup_trim1/selected_theory_indices.json \
  --out-directory replay_results/zero8_fresh
```

The entry point requires only Python's standard library and its four adjacent modules: `lra_certificate_common.py`, `check_lra_capture.py`, `check_lra_rup.py`, and `check_lra_farkas.py`. It does not require Z3, cvc5, Ethos, SciPy, a compiler, or a producer binary. The accepted receipt is `continuation/verification/zero8_complete_lra_certificate.json`; its separately completed input, Boolean, and arithmetic checks were composed by immutable content hashes rather than unnecessarily rerun. Fresh reproduction uses the complete command above and writes all three stage receipts followed by `complete_verification.json`.

The proof checks 898 original axioms, 27,637 exact arithmetic theory axioms, 10,845 RUP derivations, and 405,499 ordered propagation reasons. The full target correspondence and seven/six baseline chain are recorded in `zero8_full_target_completion.md` and `zero8_full_target_binding.json`. The nine-chore independent certificate is separate; its completed replay is in Section 15.

`test_lra_relocation.py` copied a tiny complete certificate and all required checker modules into a different directory, removed the original location, retained a deliberately unavailable historical absolute input path, and successfully replayed all three stages using mixed relative and absolute explicit arguments. Its receipt is `lra_relocation_control.json`. This verifies the relocation requirement without rerunning a large accepted proof.

## 13. Final theorem manuscript and release archive

The final manuscript uses `src/build_release_report.py`. It requires a completed independently checked nine-chore certificate, the matching `continuation/verification/nine_release_index.json`, and the concrete `docs/zero9_replay_command.txt`. The final gate checks the input identity and every indexed proof-object hash. Before that certificate completed, only the explicitly marked draft path was available. The final gate now has the complete certificate and index; it still refuses mismatched or missing evidence.

From the extracted project root, the final presentation command is:

```sh
python3 src/build_release_report.py
```

The observed presentation toolchain is Pandoc 3.1.3 with XeLaTeX, Latin Modern Roman, and DejaVu Sans/Sans Mono fonts. The builder itself uses Python's standard library. Standard TeX packages used by the supplied header include `fancyhdr`, `fvextra`, `xurl`, `titlesec`, and `needspace`; the complete header is `src/release_header.tex`. These tools convert the reviewed Markdown and mathematical notation into the PDF. They perform no mathematical proof checking. The historical ReportLab versions and font paths in §8 apply to `src/build_report.py`, rather than this final manuscript builder.

For a private preview, run:

```sh
python3 src/build_release_report.py --draft
```

The preview is explicitly marked provisional and is written under `tmp/pdfs/release_draft/`. The final builder writes `docs/research_report.md`, `docs/prospective_release.md`, and `output/pdf/economics-problem-2-research-report.pdf`. The current final PDF must then receive the separate visual-review receipt `output/pdf/release_visual_review.json`; a draft or a review of different PDF bytes does not satisfy the release gate.

The final archive command is:

```sh
python3 src/build_release_bundle.py
```

This builder requires all supervised jobs to be terminal, validates the complete nine-chore index and every required file hash, and requires the current final PDF build and visual-review receipts. It writes `output/economics-problem-2-reproducibility.zip`, then checks ZIP CRCs and payload hashes in a fresh process. The archive records the exact proof, source, and receipt bytes used; no external publication is performed by either builder.

Retrieved prior-work PDFs and their full extracted texts are excluded from required redistributed replay files. Their inspected identities and URLs are retained as external-source provenance, while the cited smaller-case theorems remain explicit mathematical premises. Executing the exact eight- or nine-chore certificate replay requires no presentation tools and no retrieved source paper.

## 14. Minimal nine-chore replay capture

The final nine-chore replay source is `continuation/exact_search/zero9_minimal_replay_capture1/capture`. Its affine atoms, original CNF records, theory-clause records, and metadata are byte-identical to the separately preserved full capture. Every atom ID, original assertion index, theory index, and proof ID is unchanged. Only the raw callback RUP and assumption logs are omitted from this derived package; they are not premises of the final hinted RUP/Farkas proof. The checked trimmed trace remains a separate required proof file.

The unchanged capture checker independently reconstructed this derived package in `continuation/verification/zero9_minimal_capture_input_binding.json`. Its preparation manifest and copies of the original source receipt and binding preserve exact historical identities. The derivation omits 138,584,363 raw log bytes without changing the checking calculus. The final release index exposes the directory in `accepted_capture` and inventories the omitted logs by hash and byte length. The original full snapshot is preserved as historical provenance; no old receipt is rewritten.

Final Boolean, arithmetic, and combined acceptance consistently use this minimal capture and its new binding receipt. Source binding alone was not a complete proof; the final selected arithmetic stream and complete Boolean refutation subsequently passed their separate checks, as recorded in Section 15.

## 15. Complete portable nine-chore certificate replay

The following is the actual accepted proof's complete fresh replay command. Run it from an extracted package root with a new output directory:

```sh
python3 continuation/verification/run_lra_with_budget.py \
  --stage all \
  --memory-mib 1600 \
  --input continuation/exact_search/zero_minimum9_reference_strict.smt2 \
  --expected-sha256 65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b \
  --capture continuation/exact_search/zero9_minimal_replay_capture1/capture \
  --trace continuation/exact_search/zero9_rup_source_cache_run1/trimmed_trace.jsonl \
  --certificates continuation/exact_search/zero9_selected_farkas_final1/arithmetic_certificates.jsonl \
  --selected-indices continuation/exact_search/zero9_rup_source_cache_run1/selected_theory_indices.json \
  --out-directory replay_results/zero9_fresh
```

Equivalently, run `sh docs/zero9_replay_command.txt`. Explicit input paths may be relative or absolute. Historical absolute paths in provenance are not needed: the checkers use the files supplied on the command line and bind their contents by hash. The minimal capture retains every original atom and source index; raw callback logs have no role as proof premises. No Z3, cvc5, Ethos, SciPy, compiler, producer binary, or presentation tool is needed for this replay.

The driver calls the unchanged capture, RUP, and Farkas checking functions, then invokes the unchanged completion binder. A successful fresh run writes `input_binding.json`, `rup_verification.json`, `arithmetic_verification.json`, `complete_verification.json`, and `fresh_replay_manifest.json` in the new directory. The complete certificate status must be `PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE`, with **4,550 original axioms**, **370,780 selected theory axioms**, **172,146 derived RUP clauses**, and **8,088,323 ordered reason positions**. Every selected arithmetic clause is checked with exact `Fraction` arithmetic.

The original small-calibration RUP CLI retained its 700 MiB cap and exhausted it on the nine-chore proof. The explicit 1,600 MiB wrapper leaves the mathematical functions and calculus unchanged. The accepted RUP stage used 902,792 KiB maximum resident memory and 30.267 seconds; the exact arithmetic stage used 195,164 KiB and 82.486 seconds. The minimal input/atom binding took 24.642 seconds. These observed stage timings do not include all final packaging/hash work and are not a guarantee for a different machine. A resource failure produces no successful proof receipt.

`budgeted_replay_controls.json` records a tiny complete relocation test and three failure controls: an existing output is not overwritten, missing arithmetic coverage cannot produce a combined PASS, and a wrong original input is rejected before replay outputs are created. `nine_replay_orchestration_review.json` records the separate source review. These controls do not rerun an accepted large proof.

The accepted stages are preserved in `continuation/verification/zero9_complete_lra_certificate.json`; their final composition verified immutable hashes instead of repeating successful mathematical checks. The mathematical theorem is separately bound in `zero9_full_target_binding.json`, and `nine_release_index.json` binds 96 required proof/checker/reduction/baseline files plus the concrete command. The cited smaller-case theorem and handwritten reductions remain explicit dependencies of the theorem, while the exact certificate replay itself requires no retrieved source paper. All recorded search and proof-production jobs are terminal.
