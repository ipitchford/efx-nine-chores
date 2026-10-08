# External SMT proof checking: implementation notes

Status recorded on 7 October 2026. The run receipts, rather than this prose, are authoritative for numerical results.

## Implemented route

`src/check_cvc5.py` reads the exported SMT-LIB problem through cvc5's public `InputParser`, checks it once, requests the complete proof through `getProof(ProofComponent.FULL)`, and serialises it with `proofToString`. It does not import the generator. It refuses incremental inputs, input options that might change proof configuration, and commands after the terminal check. The default proof granularity is `dsl-rewrite`.

`src/check_ethos.py` then runs an independently built Ethos executable against the exported CPC proof, using the core CPC signature shipped with cvc5 1.4.1. Two flags and the invocation mode are essential:

- `--reference=original.smt2` makes Ethos check that every global proof assumption is among the original input assertions.
- `--require-proof-of-false` requires the final step to prove false at global assumption scope.

The proof must be sent through **stdin**, while reusing the original input's variable declarations. Negative controls found that the pinned Ethos `includeFile` implementation resets its reference-state flag when opening a positional proof file. Merely passing `--reference` together with a positional proof therefore did not enforce reference membership. Feeding the proof through stdin avoids that state reset. Initial CPC declarations would otherwise create fresh constants with the same printed names, so the adapter matches each such declaration to the original attribute-free Real declaration and removes only that duplicate declaration from the streamed copy. All proof definitions, assumptions and inference steps are retained. The original CPC object stays unchanged; the receipt records both its hash and the hash of the adapted stream. Other proof command classes that could include files or reset state are rejected.

`src/check_ethos_controls.py` reproduces four small controls: the valid refutation is accepted; deleting one reference assertion causes rejection at the missing assumption; a valid non-refuting prefix is accepted when the false requirement is omitted; the same prefix is rejected when that requirement is enabled. All four pass in `results/checker_controls.json`. These tests check boundary enforcement, not the mathematical soundness of the checker or calculus. Source inspection located the state reset in the pinned `src/state.cpp` implementation of `includeFile` and the fresh-symbol creation in `mkSymbolInternal`. The checker binary was not patched. Older positional-mode receipts are retained with explicit deprecated/unbound status; only corrected stdin-mode receipts support an input-bound verification claim.

The wrapper accepts only exit code zero and the verdict `correct`. A timeout, parse failure, rejected rule application, or `incomplete` verdict does not verify the proof. It enables no “skip unknown” option. Hashes of the input, proof, executable and all signature files appear in the receipt. Ethos checks each application of the supplied rules; the correctness of the CPC calculus and the checker implementation remain declared premises. This is an external checker result, not a claim that the whole fair-division theorem has been formalised in Lean.

## Completed seven-chore calibration

The supplied `results/root7_pruned.smt2` was independently read by cvc5 1.4.1, which returned UNSAT after approximately 8.71 seconds. Its CPC proof contains 94,014 steps and occupies 6,515,732 bytes. The export contains no `trust` or `hole` steps and no warning lines. Corrected stdin-mode Ethos replay checked that proof against the exact input in approximately 26.97 seconds and returned `correct`, with no diagnostic output. See `results/root7_cvc5.json` and `results/root7_ethos.json`.

An Alethe export is also retained for this calibration, but it has not been externally checked. It must not be described as an independently verified Alethe proof.

## Designated-agent six-chore certificate

The stronger formula requires agent 0 to be ordinarily envy-free and agents 1 and 2 to be EFX. For `work/structural_designated_m6.standard.smt2`, cvc5 returned UNSAT in 94.63 seconds and exported a 70,716,103-byte CPC proof with 857,855 steps, no trust/hole steps and no warnings. The first Ethos derivation replay passed in positional mode but was subsequently marked unbound after the controls above. Corrected stdin-mode replay then passed in 90.49 seconds, binding every global assumption to the exact standardized input and proving final global false. Its authoritative corrected receipt is `results/designated6_ethos.json`.

The portable input differs from the frozen Z3 input only by removal of unary additions and addition of an explicit QF_LRA declaration. Unary addition is the identity. `work/structural_standardise_receipt.json` records hashes and the check that all 755 corresponding assertions have identical simplified ASTs. The external certificate itself binds to the portable input; the mathematical encoding audit and this syntax conversion remain separate obligations. A positive result for six chores alone does not settle the seven-chore residual or the original nine-chore target.

The first full residual seven-chore cvc5 attempt used a 1,800 MiB virtual-memory cap and aborted with `std::bad_alloc` before reporting a solver verdict or proof. Its receipt records `memory_exhaustion_no_verdict`; it is not evidence of UNSAT. A reduced assertion subset or a later run requires a separate successful proof-generation and checking receipt.

The final bounded route selected 853 of the full residual's 1,847 assertions verbatim using Z3 with the original arithmetic engine. That selector returned UNSAT in 125.169974 seconds; its exact original assertion indices and input hashes are in `results/designated7_core_select.json`. A cvc5 proof run on this subset used a 600-second solver limit and an initial 2,300 MiB address-space cap. It ended with exit 139 and no diagnostic, verdict or proof file. The cause of the native exit was not established. A late request to raise the cap to 4,500 MiB was not applied because `prlimit` could no longer find the process; no timeout extension or further proof attempt followed. See `results/designated7_core_cvc5.json` and `results/designated7_core_limit_change.json`. Consequently P7 has the exact Z3 results and the separately audited encoding, but no successful external certificate in this package.

## Eight-chore resource-limited attempt and exact assertion subset

The full ordinary eight-chore cvc5 attempt was killed with exit code 137 before returning a verdict. The cgroup OOM-kill counter increased during the run. `results/root8_cvc5.json` explicitly records `killed_no_verdict`; the guard's observation that the process ended before its own threshold is not a success verdict. No externally checked eight-chore cvc5 proof is claimed from that attempt.

The root solver did export a native Z3 proof. `src/extract_z3_core.py` identifies its asserted leaves and matches them to original assertions using exact rational linear and Boolean normal forms. It then copies the matched original assertion commands verbatim, never creating new assumptions. This selected 934 of 5,846 assertions for `results/root8_core.smt2`; hashes and original assertion indices are in `results/root8_core_extract.json`. The extraction is a proposal for a smaller input, not a verification of the native Z3 proof and not an UNSAT result. A subsequent independent refutation of that exact subset would imply that the full input is unsatisfiable. That subsequent result, if obtained, must have its own receipt.

## Final unresolved search status

No proof worker remains active. The nine-chore baseline and unit-margin runs were killed without verdicts, the cut-based run returned UNKNOWN, and all 14 second-minimum graph/rank cases returned UNKNOWN with 45-second solver budgets. The restricted eight-chore prescribed-agent problem with all three minima distinct returned UNKNOWN after 903.677793 seconds in `results/D8_root.json`. The simultaneous deleted-minimum search returned UNKNOWN after 1,200.416110 seconds, and the distinct-minimum CEGIS search was stopped at its total budget after 137 partial SAT models. Their final receipts are `work/compute_deleted_min9_full/stop_receipt.json` and `work/compute_designated8_allmin/stop_receipt.json`. `work/compute_run_summary.json` also retains seven earlier searches' explicit no-conclusion stop receipts. These partial SAT models still have fair-allocation witnesses and are not counterexamples. The full claim mapping and authoritative failed-run inventory appear in `docs/VERIFICATION.md` and `docs/claim_check_ledger.md`.

## Version pins and build

The Ethos source commit is `08e4aa40c4f8a6e00833f10e8d8985777e424027`, the version selected by cvc5 1.4.1's `contrib/get-ethos-checker`. The cvc5 signature checkout resolves the `cvc5-1.4.1` tag to `2b2e84419f70817ec919a784a48806e79f677240`. The build used GNU C++ 13.3, CMake 4.4.4, two compile workers, and the system GMP 6.3.0 runtime. The missing GMP development headers were obtained from Ubuntu's matching development package and extracted locally. This installed no system package and altered no access controls. Full dependency hashes are in `results/checker_build.json`.

Source repositories and the locally built executable are in `work/ethos` and `work/cvc5_signatures`. A release should retain the version pins, required signatures and their licences, the proof-generation and checking scripts, the exact SMT-LIB problems and proof objects, and the successful checking receipts. A portable setup script may instead obtain the exact source commits before building; the proof files remain independently replayable either way.

## Why CPC/Ethos was selected

The current cvc5 1.4.1 documentation lists CPC, Alethe and DOT exports. Older LFSC/ALF instructions do not describe the installed version's formats. CPC provides a direct route to Ethos; `correct` and `incomplete` are distinct outcomes, and reference-input checking binds the proof to its problem. Current documentation: https://cvc5.github.io/docs/cvc5-1.4.1/proofs/proofs.html and https://cvc5.github.io/docs/cvc5-1.4.1/proofs/output_cpc.html .

Alethe supports linear arithmetic and can be checked by Carcara. However, the helper shipped with cvc5 1.4.1 invokes its pinned Carcara fork with `--ignore-unknown-rules`. That convenience wrapper is insufficient for a release claiming a completely checked derivation unless its output is separately shown to contain no unchecked steps. Building current Carcara also requires a Rust toolchain absent from this environment. These are practical reasons for selecting the working CPC route, not evidence that Alethe itself is unsound. Sources: https://cvc5.github.io/docs/cvc5-1.4.1/proofs/output_alethe.html and https://github.com/cvc5/cvc5/blob/cvc5-1.4.1/contrib/get-carcara-checker .

Logos is a further CPC checker implemented in Lean, with a proved soundness theorem for its supported fragment. Its `correct` verdict concerns the assumptions parsed from its proof file. An eventual Logos replay would therefore retain input-assumption binding as an explicit check. No Logos run is claimed in this package. Source and stated scope: https://github.com/cvc5/logos .

## Primary references

Barbosa, H., et al. (2022). cvc5: A versatile and industrial-strength SMT solver. In *Tools and Algorithms for the Construction and Analysis of Systems* (pp. 415–442). Springer. https://doi.org/10.1007/978-3-030-99524-9_24

cvc5 developers. (2026). *Proof production; Cooperating Proof Calculus; Alethe* (cvc5 1.4.1 documentation). https://cvc5.github.io/docs/cvc5-1.4.1/proofs/proofs.html

cvc5 developers. (2026). *Ethos: A flexible and efficient proof checker for SMT solvers* [Source code]. https://github.com/cvc5/ethos

cvc5 developers. (2026). *Logos: A Lean-based verified proof checker for Eunoia* [Source code]. https://github.com/cvc5/logos
