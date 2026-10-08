"""Freeze an explicit valid-certificate release index from completed audits."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(value).hexdigest()


def path(value):
    value = Path(value)
    if not value.is_absolute():
        return ROOT / value
    if value.is_relative_to(ROOT):
        return value
    assert value.parts.count("continuation") == 1
    return ROOT.joinpath(*value.parts[value.parts.index("continuation"):])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-audit", required=True)
    parser.add_argument("--row-manifest", required=True)
    parser.add_argument("--pruning-receipt")
    parser.add_argument("--zero-result")
    parser.add_argument("--output", default="continuation/verification/release_certificate_index.json")
    args = parser.parse_args()
    row_file, manifest_file = path(args.row_audit), path(args.row_manifest)
    row = json.loads(row_file.read_text())
    assert row["status"] == "PASS_ALL_LOCAL_GUARANTEES_AND_EXACT_FINAL_OUTER_BINDING_NOT_GLOBAL_UNSAT"
    assert sha(manifest_file.read_bytes()) == row["manifest_sha256"]
    prefix_index_file = HERE / "bounded_prefix_certificate_index.json"
    prefix_index = json.loads(prefix_index_file.read_text())
    prefix_audit_file = HERE / "bounded_prefix_snapshot_audit.json"
    prefix_audit = json.loads(prefix_audit_file.read_text())
    assert prefix_audit["status"] == "PASS_ALL_PREFIX_CERTIFICATES_AND_EXACT_BOUNDED_INPUT_NOT_GLOBAL_UNSAT"
    assert sha(prefix_index_file.read_bytes()) == prefix_audit["certificate_index_sha256"]
    prefix = prefix_index["records"]
    unique = {}
    for item in row["certificate_index"]:
        name = str(path(item["file"]).relative_to(ROOT))
        digest = item["sha256"]
        if name in unique:
            assert unique[name]["sha256"] == digest
        else:
            unique[name] = {"file": name, "sha256": digest, "kind": item["kind"]}
    row_certificates = list(unique.values())
    for item in prefix + row_certificates:
        assert "float_unsound" not in item["file"] and "mutation" not in item["file"]
        assert sha(path(item["file"]).read_bytes()) == item["sha256"]
    bound_files = dict(row["bound_files"])

    def bind(file):
        file = path(file)
        name = str(file.relative_to(ROOT))
        digest = sha(file.read_bytes())
        if name in bound_files:
            assert bound_files[name] == digest
        bound_files[name] = digest
        return name, digest

    for file in (row_file, manifest_file, prefix_index_file, prefix_audit_file):
        bind(file)
    for item in prefix:
        bind(item["file"])
    snapshot = path(prefix_index["snapshot"])
    for name in ("formula.smt2", "config.json", "source_index.json", "result.json", "supervisor.json"):
        bind(snapshot / name)
    for name in (
        "audit_prefix_snapshot.py", "audit_bounded_prefix_snapshot.py", "audit_row_compression.py",
        "audit_minimized_row_cores.py", "audit_row_resume_pruning.py", "audit_final_row_snapshot.py",
        "audit_zero_minimum_formula.py", "release_replay.py", "build_release_index.py",
        "zero_minimum_normalization_audit.json", "zero_minimum_independent_review.md",
    ):
        bind(HERE / name)
    for name in (
        "continuation/verify_row_cores.py",
        "continuation/extension_geometry/verify_extension_certificate.py",
        "continuation/structural_nine/verify_pair_seeds.py",
        "continuation/exact_search/bounded_prefix_margin.md",
        "continuation/exact_search/row_local_integer_bound.md",
    ):
        bind(name)
    pair_receipt_path = HERE / "outer_resumed2_checkpoint1/paired_seed_verification.json"
    bind(pair_receipt_path)
    pair_receipt = json.loads(pair_receipt_path.read_text())
    assert bind(pair_receipt["source"])[1] == pair_receipt["source_sha256"]
    if args.pruning_receipt:
        bind(args.pruning_receipt)
    zero_input = ROOT / "continuation/exact_search/zero_minimum9_reference_strict.smt2"
    zero_audit = HERE / "zero_minimum9_formula_audit.json"
    zero_data = json.loads(zero_audit.read_text())
    assert zero_data["status"] == "PASS_ALL_SERIALIZED_ZERO_MINIMUM_CLAUSES_RECONSTRUCTED_WITH_STDLIB"
    assert bind(zero_input)[1] == zero_data["input_sha256"]
    bind(zero_audit)
    zero = {"input": str(zero_input.relative_to(ROOT)), "input_sha256": zero_data["input_sha256"],
            "static_audit": str(zero_audit.relative_to(ROOT)), "static_audit_sha256": sha(zero_audit.read_bytes()),
            "free_real_variables": 21, "domain_assertions": 27, "allocation_clauses": 18150,
            "recorded_result": None}
    if args.zero_result:
        result_file = path(args.zero_result)
        bind(result_file)
        zero["recorded_result"] = {"file": str(result_file.relative_to(ROOT)),
                                    "sha256": sha(result_file.read_bytes()),
                                    "data": json.loads(result_file.read_text())}
    for name, digest in bound_files.items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    report = {
        "format_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EXPLICIT_VALID_LOCAL_CERTIFICATE_INDEX_NO_GLOBAL_VERDICT",
        "mutation_fixtures_included": False,
        "prefix_snapshot": str(snapshot.relative_to(ROOT)),
        "prefix_formula_sha256": prefix_index["formula_sha256"],
        "prefix_assertions": prefix_audit["total_assertions"],
        "prefix_certificates": prefix,
        "row_manifest": str(manifest_file.relative_to(ROOT)),
        "row_audit": str(row_file.relative_to(ROOT)), "row_formula": row["outer"],
        "row_formula_sha256": row["outer_sha256"], "row_assertions": row["total_assertions"],
        "row_pruning_receipt": str(path(args.pruning_receipt).relative_to(ROOT)) if args.pruning_receipt else None,
        "extra_minimized_receipts": [], "row_certificates": row_certificates,
        "static_singleton_and_pair_sources": [
            r for r in json.loads(manifest_file.read_text())["ordered_sources"]
            if r["kind"] in ("robust_single", "static_pair")
        ],
        "zero_minimum9": zero, "bound_files": bound_files,
        "replay": "python continuation/verification/release_replay.py --phase certificates",
        "zero_formula_replay": "python continuation/verification/release_replay.py --phase zero-formula",
        "scope": "Only explicitly identified valid extension/core certificates and bound static inputs are included. Historical invalid mutation certificates are excluded. Static singleton/pair guarantees and exact source/subset/compression binding are fully recomputed by release replay. Recorded solver outcomes retain their own scope and are not turned into independent UNSAT certificates.",
    }
    path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "prefix_certificates": len(prefix),
                      "row_certificates": len(row_certificates), "bound_files": len(bound_files),
                      "prefix_assertions": report["prefix_assertions"], "row_assertions": report["row_assertions"],
                      "zero_result_recorded": bool(args.zero_result)}, indent=2))


if __name__ == "__main__":
    main()
