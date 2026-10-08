"""Bind the completed portable phases and later new evidence without redoing them.

Only file hashes, exact counts, and finite-bound integer arithmetic are checked
here. The mathematical phase receipts retain their explicit original scopes.
Run release_replay.py --phase all to repeat their underlying certificate work.
"""
from datetime import datetime, timezone
import hashlib
import json
from math import isqrt
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


def local(value):
    p = Path(value)
    if not p.is_absolute():
        assert ".." not in p.parts
        return ROOT / p
    if p.is_relative_to(ROOT):
        return p
    assert p.parts.count("economics_problem2") == 1
    return ROOT.joinpath(*p.parts[p.parts.index("economics_problem2") + 1:])


def main():
    files = {}

    def read(value, expected=None):
        p = local(value)
        data = p.read_bytes()
        digest = sha(data)
        if expected is not None:
            assert digest == expected, str(p)
        files[str(p.relative_to(ROOT))] = digest
        return data

    def data(value, expected=None):
        return json.loads(read(value, expected))

    index_file = HERE / "release_certificate_index.json"
    index_bytes = read(index_file)
    index = json.loads(index_bytes)
    assert index["mutation_fixtures_included"] is False
    assert len(index["prefix_certificates"]) == 1956
    assert len(index["row_certificates"]) == 2005
    assert len(index["bound_files"]) == 8245
    for item in index["prefix_certificates"] + index["row_certificates"]:
        read(item["file"], item["sha256"])
    for name, digest in index["bound_files"].items():
        read(name, digest)

    phase_records = []
    for phase, directory in (("certificates", "release_replay_final_certificates"),
                             ("zero-formula", "release_replay_final_zero_formula")):
        file = HERE / directory / "release_replay.json"
        receipt = data(file)
        assert receipt["status"] == "PASS_RELEASE_LOCAL_CERTIFICATES_AND_INPUT_BINDING_NO_GLOBAL_VERDICT"
        assert receipt["index_sha256"] == sha(index_bytes)
        assert receipt["phase"] == phase
        assert receipt["bound_files_checked"] == 8245
        for audit in receipt["audits"]:
            result = data(audit["receipt"], audit["receipt_sha256"])
            assert result["status"] == audit["status"] and result["status"].startswith("PASS")
        phase_records.append({"phase": phase, "receipt": str(file.relative_to(ROOT)),
                              "sha256": sha(file.read_bytes()), "finished_utc": receipt["finished_utc"]})

    zero_file = HERE / "release_replay_final_zero_formula/zero_minimum9_formula_audit.json"
    zero = data(zero_file)
    assert zero["input_sha256"] == index["zero_minimum9"]["input_sha256"]
    assert [zero[k] for k in ("free_real_variables", "domain_assertions", "allocation_clauses", "total_assertions", "literal_positions_checked")] == [21, 27, 18150, 18177, 191104]
    additional = []
    for name in ("zero_outer_audit.json", "lifted8_formula_audit.json", "lifted9_formula_audit.json", "positive_outer_noncoverage_witness.json"):
        value = data(HERE / name)
        assert value["status"].startswith("PASS")
        read(value["input"], value["input_sha256"])
        for filename, digest in value.get("bound_files", {}).items():
            read(filename, digest)
        additional.append({"audit": f"continuation/verification/{name}", "status": value["status"],
                           "input": value["input"], "input_sha256": value["input_sha256"]})
    noncoverage = data(HERE / "positive_outer_noncoverage_witness.json")
    assert noncoverage["main_target_counterexample"] is False
    assert noncoverage["current_frozen_row_region_family_is_not_complete"] is True
    assert noncoverage["exact_assertions_checked"] == 6309
    zero_model = data("continuation/structural_nine/zero_outer/run1_model_verification.json")
    assert zero_model["status"] == "PASS_EXACT_OUTER_MODEL_ONLY"
    assert zero_model["exact_assertions_checked"] == 6305
    read("continuation/structural_nine/zero_outer/run1_model.json", zero_model["model_sha256"])

    proof_sources = [
        "continuation/exact_search/zero_minimum_reduction.md",
        "continuation/verification/zero_minimum_independent_review.md",
        "continuation/verification/audit_zero_minimum_normalization.py",
        "continuation/verification/zero_minimum_normalization_audit.json",
        "continuation/exact_search/zero_minimum_reduction_audit.json",
        "continuation/exact_search/prepare_zero_minimum.py",
        "continuation/exact_search/zero_minimum9_reference_preparation.json",
        "continuation/exact_search/zero_minimum9_reference_semantic_audit.json",
        "continuation/exact_search/prepare_lifted_bounded_lra.py",
        "continuation/exact_search/lifted8_common_minimum_preparation.json",
        "continuation/exact_search/lifted9_common_minimum_preparation.json",
        "continuation/structural_nine/zero_outer/transfer_proof.md",
        "continuation/structural_nine/prepare_zero_outer.py",
        "continuation/structural_nine/zero_outer/verify_outer_model.py",
        "continuation/verification/audit_zero_outer.py",
        "continuation/verification/audit_lifted_formula.py",
        "continuation/verification/verify_positive_outer_witness.py",
        "continuation/verification/audit_release_completion.py",
    ]
    for name in proof_sources:
        read(name)
    z8, z9 = isqrt(6 * 7**6), isqrt(7 * 8**7)
    assert (z8, z9, 2 * z9) == (840, 3831, 7662)
    prep = data("continuation/exact_search/zero_minimum9_reference_preparation.json")
    assert prep["input_sha256"] == zero["input_sha256"]
    read(prep["source"], prep["source_sha256"])

    config = data("continuation/exact_search/zero9_cpc_prepared_config.json")
    assert config["status"] == "prepared_not_executed"
    assert config["input_sha256"] == zero["input_sha256"]
    read(config["runner"], config["runner_sha256"])
    replay = config["replay_argv"]
    read(replay[1], config["replay_runner_sha256"])
    signatures = local(replay[replay.index("--signatures") + 1])
    assert len(config["signature_sha256"]) == 51
    for name, digest in config["signature_sha256"].items():
        read(signatures / name, digest)
    controls = data("continuation/exact_search/cpc_preparation_tests/validation.json")
    assert controls["status"] == "PASS_SYNTHETIC_IO_AND_FAILURE_INJECTION"
    assert controls["real_solver_invoked"] is False
    assert controls["runner_sha256"] == config["runner_sha256"]
    policy = config["replay_policy"]
    assert policy["input_reference_required"] and policy["proof_of_false_at_global_scope_required"]
    assert policy["expert_signature"] is False and policy["expected_process_exit_code"] == 0
    assert policy["accepted_verdict"] == "correct"

    report = {
        "status": "PASS_COMPLETED_RELEASE_EVIDENCE_BOUND_NO_GLOBAL_VERDICT",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "main_target_status": "unresolved", "index_sha256": sha(index_bytes),
        "completed_replay_phases": phase_records, "additional_completed_audits": additional,
        "zero_minimum_positive_integer_bound": z9,
        "positive_common_minimum_one_integer_bound": 2 * z9,
        "current_frozen_row_family_incomplete": True,
        "cpc_configuration_status": "prepared_not_executed",
        "cpc_controls_scope": "Synthetic I/O and failure injection only; no real solver or proof checker invoked.",
        "new_mathematical_tests_in_this_binding_run": False,
        "file_bindings_checked": len(files), "bound_files": files,
        "scope": "The unchanged successful portable phases and later exact static audits/witness checks are carried forward by exact file hashes. Reviewed proof texts, input preparation sources and CPC configuration are additionally bound. Handwritten reductions are not proof-assistant formalizations. No successful main-target proof or counterexample, solver result, or exhausted integer domain is inferred.",
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output = HERE / "release_completion_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "bound_files"}, indent=2))


if __name__ == "__main__":
    main()
