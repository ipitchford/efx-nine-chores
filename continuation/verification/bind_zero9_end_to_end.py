"""Bind the full-target reduction review to the observed exact UNSAT input.

The only new combinatorial check explicitly covers every omitted empty-bundle
allocation. Unchanged full-clause audits are carried forward by their hashes.
No solver or proof checker is invoked by this program.
"""
import csv
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
START = time.monotonic()
resource.setrlimit(resource.RLIMIT_AS, (480 * 1024**2,) * 2)
signal.alarm(29)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    files = {}

    def read(name, expected=None):
        path = ROOT / name
        content = path.read_bytes()
        digest = sha(content)
        if expected is not None:
            assert digest == expected, name
        files[name] = digest
        return content

    index = json.loads(read("continuation/verification/release_certificate_index.json"))
    formula = "continuation/exact_search/zero_minimum9_reference_strict.smt2"
    digest = index["zero_minimum9"]["input_sha256"]
    read(formula, digest)
    phase = json.loads(read("continuation/verification/release_replay_final_zero_formula/release_replay.json"))
    assert phase["status"] == "PASS_RELEASE_LOCAL_CERTIFICATES_AND_INPUT_BINDING_NO_GLOBAL_VERDICT"
    assert phase["index_sha256"] == files["continuation/verification/release_certificate_index.json"]
    assert len(phase["audits"]) == 1
    record = phase["audits"][0]
    audit = json.loads(read(record["receipt"], record["receipt_sha256"]))
    assert audit["input_sha256"] == digest
    assert [audit[k] for k in ("free_real_variables", "domain_assertions", "allocation_clauses", "total_assertions", "literal_positions_checked")] == [21, 27, 18150, 18177, 191104]
    checker = "continuation/verification/audit_zero_minimum_formula.py"
    read(checker, index["bound_files"][checker])
    stem = "continuation/exact_search/zero_minimum9_reference_noproof_run1"
    run = json.loads(read(stem + ".json"))
    supervisor = json.loads(read(stem + ".supervisor.json"))
    read(stem + ".started.json")
    assert run["input_sha256"] == supervisor["input_sha256"] == digest
    assert run["status"] == run["solver_verdict"] == "unsat"
    assert run["assertions"] == 18177 and run["proof_generation_enabled"] is False
    assert run["proof_status"] == "no independently checked proof"
    assert "exception" not in run and run["check_seconds"] > 0
    assert supervisor["status"] == "completed_with_solver_verdict"
    assert supervisor["child_returncode"] == 0 and supervisor["hard_killed_by_supervisor"] is False
    assert supervisor["solver_verdict"] == "unsat"
    read("continuation/exact_search/run_zero_minimum_z3.py", supervisor["runner_sha256"])
    read("continuation/exact_search/supervise_zero_minimum.py", supervisor["supervisor_sha256"])
    for source in (
        "target.yaml", "continuation/verification/zero9_end_to_end_audit.md",
        "continuation/verification/bind_zero9_end_to_end.py",
        "continuation/exact_search/zero_minimum_reduction.md",
        "continuation/verification/zero_minimum_independent_review.md",
        "sources/zhang_2609_10585v2.pdf", "work/zhang_v2.txt",
        "sources/kms_2305_04168.pdf", "work/kms.txt",
    ):
        read(source)

    expected = {}
    surjective = 0
    for aid, allocation in enumerate(product(range(3), repeat=9)):
        bundles = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
        if all(bundles):
            surjective += 1
            continue
        target = next(j for j in range(3) if not bundles[j])
        owner = max(range(3), key=lambda i: len(bundles[i]))
        assert len(bundles[owner]) >= 2 and owner != target
        retained = next(g for g in bundles[owner] if g != owner)
        removed = next(g for g in bundles[owner] if g != retained)
        expected[aid] = (owner, target, removed, retained)
    assert surjective == 18150 and len(expected) == 1533
    witness_file = HERE / "zero9_omitted_empty_allocation_witnesses.csv"
    with witness_file.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["allocation_id", "failing_agent", "empty_target_agent", "removed_chore", "retained_positive_chore"])
        for aid, witness in expected.items():
            writer.writerow([aid, *witness])
    seen = set()
    with witness_file.open(newline="") as stream:
        for row in csv.DictReader(stream):
            aid, i, j, removed, retained = map(int, row.values())
            assert aid in expected and aid not in seen
            allocation = [(aid // 3**(8 - g)) % 3 for g in range(9)]
            assert all(owner != j for owner in allocation)
            assert allocation[removed] == allocation[retained] == i
            assert removed != retained and retained != i and i != j
            seen.add(aid)
    assert seen == set(expected)
    read(str(witness_file.relative_to(ROOT)))
    report = {
        "status": "PASS_END_TO_END_INPUT_BINDING_AND_OMITTED_ALLOCATION_COVERAGE",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "input": formula, "input_sha256": digest,
        "observed_solver_verdict": "unsat", "solver_check_seconds": run["check_seconds"],
        "solver_normal_exit": True, "solver_proof_generation_enabled": False,
        "independently_checked_unsat_certificate": False,
        "free_real_variables": 21, "domain_assertions": 27,
        "surjective_allocation_clauses": 18150,
        "omitted_empty_bundle_allocations_checked": 1533,
        "complete_labelled_allocations_accounted_for": 19683,
        "logical_review": "No missing hypothesis found: strict positive genericity, shared-minimum insertion using the prior eight-chore theorem, minimum lowering, simultaneous relabelling, positive reference scaling, all literal allocation failures, and the empty-bundle argument cover the original nonnegative target.",
        "dependencies": ["The cited eight-chore existence theorem", "The supplied elementary insertion and normalization arguments", "The independent exact affine/Boolean input audit", "Soundness of the recorded Z3 verdict until an independent UNSAT certificate is checked"],
        "excluded_dependencies": ["P8", "D8", "Finite integer bounds", "Any finite region family", "Additional minimum-preference symmetry"],
        "scope": "This binds the completed literal formula audit and normal UNSAT run, and separately verifies a positive-retained-chore failure witness for every omitted empty-bundle allocation. The handwritten reduction supplies the full-target implication. This program does not verify the solver's UNSAT derivation and does not upgrade it to an externally certified proof.",
        "bound_files": files, "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (HERE / "zero9_end_to_end_binding.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "bound_files"}, indent=2))


if __name__ == "__main__":
    main()
