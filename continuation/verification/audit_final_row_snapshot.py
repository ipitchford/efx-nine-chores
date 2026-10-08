"""Exact local-guarantee and assertion audit of the final frozen row input.

No solver is imported. Historical proofs are carried forward by exact hashes
by default; --replay-prior also checks all their rational branch identities.
New pair certificates and all region/source/compression bindings are checked.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (480 * 1024**2,) * 2)
signal.alarm(29)
START = time.monotonic()
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(value).hexdigest()


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    signal.setitimer(signal.ITIMER_REAL, max(0.01, 29 - (time.monotonic() - START)))
    return result


def path(value):
    value = Path(value)
    if not value.is_absolute():
        return ROOT / value
    if value.is_relative_to(ROOT):
        return value
    assert value.parts.count("continuation") == 1
    return ROOT.joinpath(*value.parts[value.parts.index("continuation"):])


def audit(manifest_file, replay_prior=False, pruning_receipt=None, extra_minimized_receipts=()):
    core_file = ROOT / "continuation/verify_row_cores.py"
    compression_file = OUT / "audit_row_compression.py"
    core_bytes, compression_bytes = core_file.read_bytes(), compression_file.read_bytes()
    core = module("final_exact_row_checker", core_file)
    compression = module("final_row_compression_checker", compression_file)
    bound_files = {}

    def read(file, expected_sha=None):
        file = path(file)
        value = file.read_bytes()
        digest = sha(value)
        if expected_sha is not None:
            assert digest == expected_sha, str(file)
        bound_files[str(file.relative_to(ROOT))] = digest
        return value

    def read_json(file, expected_sha=None):
        return json.loads(read(file, expected_sha))

    manifest_bytes = read(manifest_file)
    manifest = json.loads(manifest_bytes)
    assert manifest["status"] in ("frozen_after_normal_deadline", "frozen_after_completed_supervised_run")
    assert manifest["domain_assertions"] == 18
    terminal_file = path(manifest_file).parent / "terminal_receipt.json"
    terminal = read_json(terminal_file, manifest["terminal_receipt_sha256"])
    assert terminal["status"] == "child_completed" and terminal["child_returncode"] == 0
    assert terminal["completed_region_files"] == manifest["new_region_count"]
    assert terminal["worker_summary"]["outer_sha256"] == manifest["outer_sha256"]
    old = read_json(OUT / "row_core_audit.json")
    frozen = read_json(OUT / "frozen_row_core_audit.json")
    checkpoint = read_json(OUT / "outer_resumed2_checkpoint1_audit.json")
    remaining = read_json(OUT / "remaining_row_core_audit.json")
    assert old["checker_sha256"] == frozen["checker_sha256"] == remaining["checker_sha256"] == sha(core_bytes)
    assert checkpoint["checker_sources"][str(core_file.relative_to(ROOT))] == sha(core_bytes)
    prior_receipts = [r for r in old["receipts"] if r["format_version"] == 2]
    prior_receipts += frozen["receipts"] + checkpoint["new_certificate_manifest"] + remaining["receipts"]
    assert len(prior_receipts) == 889
    prior, prior_index, prior_items = {}, [], {}
    prior_branches = 0
    for item in prior_receipts:
        cert = read_json(item["file"], item["sha256"])
        assert cert["format_version"] == 2
        key = cert["source_core_sha256"], tuple(cert["core_allocation_ids"])
        assert key not in prior
        if replay_prior:
            checked = core.verify(cert)
            assert checked["exhaustive_failure_branches"] == item["exhaustive_failure_branches"]
        prior[key] = cert
        prior_items[key] = item
        prior_branches += item["exhaustive_failure_branches"]
        prior_index.append({"file": str(path(item["file"]).relative_to(ROOT)),
                            "sha256": item["sha256"], "kind": "archived_exact_core",
                            "replayed_in_this_run": replay_prior})

    reduced = {}
    reduced_sources = {}
    reduced_index = []
    for filename in (OUT / "generic_pair_minimized_audit.json", OUT / "short1_minimized_audit.json", *map(path, extra_minimized_receipts)):
        receipt = read_json(filename)
        assert receipt["status"] == "PASS_EXACT_REDUCED_CORES_AND_ORIGINAL_REGION_SUBSET_IMPLICATION"
        assert receipt["checker_sha256"] == sha(core_bytes)
        if replay_prior:
            subset_checker = module("release_subset_checker", OUT / "audit_minimized_row_cores.py")
            replay = subset_checker.audit(receipt["source_directory"])
            assert replay["receipts"] == receipt["receipts"]
        for item in receipt["receipts"]:
            original = path(item["original_source"])
            digest = item["original_source_sha256"]
            read(original, digest)
            read(item["reduced_source"], item["reduced_source_sha256"])
            cert = read_json(item["certificate"], item["certificate_sha256"])
            if replay_prior:
                core.verify(cert)
            assert digest not in reduced
            reduced[digest] = item
            reduced_sources[path(item["reduced_source"])] = (item, cert)
            reduced_index.append({"file": str(path(item["certificate"]).relative_to(ROOT)),
                                  "sha256": item["certificate_sha256"],
                                  "kind": "reduced_core_with_original_subset_implication",
                                  "original_source": str(original.relative_to(ROOT)),
                                  "original_source_sha256": digest,
                                  "subset_audit": str(path(filename).relative_to(ROOT))})

    pruning = None
    if pruning_receipt:
        pruning = read_json(pruning_receipt)
        assert pruning["status"] == "PASS_EXACT_SUBSET_PRUNING_COMPRESSION_AND_FOUR_SMOKE_PAIR_CERTIFICATES"
        directory = path(pruning["directory"])
        read(directory / "resume_manifest.json", pruning["resume_manifest_sha256"])
        read(directory / "resumed_regions.json", pruning["resumed_regions_sha256"])
        assert manifest["resume_pruning_manifest_sha256"] == pruning["resume_manifest_sha256"]
        read(manifest["resume_pruning_manifest"], manifest["resume_pruning_manifest_sha256"])
        for item in pruning["source_index"]:
            read(item["file"], item["sha256"])
            read(item["core_file"], item["core_sha256"])
        if replay_prior:
            pruning_checker = module("release_pruning_checker", OUT / "audit_row_resume_pruning.py")
            replay = pruning_checker.audit(directory)
            assert replay["source_index"] == pruning["source_index"]

    expected = []
    counts = Counter()
    atoms = Counter()
    used_prior, used_reduced = set(), set()
    allocation_sets = set()
    fresh_certificate_index = []
    used_certificates = set()
    region_bindings = []
    direct_branches = Counter()

    def check_core(record, original_file, original_bytes):
        original = json.loads(original_bytes)
        ids = original["core_allocation_ids"]
        assert [compression.allocation(aid) for aid in ids] == original["core_allocations"]
        assert record["core_allocation_ids"] == ids
        assert record["core_sha256"] == original["core_sha256"]
        assert record["region_atoms"] == original["region_atoms"]
        core_path = path(original_file).parent.parent / "inner" / path(original_file).with_suffix(".smt2").name
        read(core_path, original["core_sha256"])
        raw, kept = compression.check_region(record, ids)
        expected.append(compression.clause(kept))
        atoms["raw"] += len(raw)
        atoms["retained"] += len(kept)
        allocation_sets.add(tuple(sorted(ids)))
        key = original["core_sha256"], tuple(ids)
        if key in prior:
            cert = prior[key]
            assert cert["core_allocations"] == original["core_allocations"]
            assert cert["other_region_atoms"] == original["region_atoms"]
            used_prior.add(key)
            used_certificates.add(str(path(prior_items[key]["file"]).relative_to(ROOT)))
            kind = "archived_exact_core"
        elif path(original_file) in reduced_sources:
            item, cert = reduced_sources[path(original_file)]
            assert sha(original_bytes) == item["reduced_source_sha256"]
            assert cert["source_core_sha256"] == original["core_sha256"]
            assert cert["core_allocation_ids"] == ids
            assert cert["core_allocations"] == original["core_allocations"]
            assert cert["other_region_atoms"] == original["region_atoms"]
            assert original["exact_core_certificate_sha256"] == item["certificate_sha256"]
            used_certificates.add(str(path(item["certificate"]).relative_to(ROOT)))
            kind = "direct_reduced_core"
        elif original.get("inner_method") == "independent_exact_pair_certificate" or (path(original_file).parent.parent / "exact_fallback_certificates" / path(original_file).name).exists():
            is_pair = original.get("inner_method") == "independent_exact_pair_certificate"
            certificate_directory = "exact_pair_certificates" if is_pair else "exact_fallback_certificates"
            cert_path = path(original_file).parent.parent / certificate_directory / path(original_file).name
            cert = read_json(cert_path, original.get("exact_pair_certificate_sha256") if is_pair else None)
            assert cert["format_version"] == 2
            assert cert["source_core_sha256"] == original["core_sha256"]
            assert cert["core_allocation_ids"] == ids
            assert cert["core_allocations"] == original["core_allocations"]
            assert cert["other_region_atoms"] == original["region_atoms"]
            result = core.verify(cert)
            kind = "direct_pair" if is_pair else "direct_fallback"
            direct_branches[kind] += result["exhaustive_failure_branches"]
            fresh_certificate_index.append({"file": str(cert_path.relative_to(ROOT)),
                                            "sha256": sha(cert_path.read_bytes()),
                                            "kind": kind, **result})
            used_certificates.add(str(cert_path.relative_to(ROOT)))
        else:
            digest = sha(original_bytes)
            assert digest in reduced, str(original_file)
            item = reduced[digest]
            assert item["original_core_sha256"] == original["core_sha256"]
            assert item["original_allocation_ids"] == ids
            used_reduced.add(digest)
            used_certificates.add(str(path(item["certificate"]).relative_to(ROOT)))
            kind = "reduced_core_subset_implication"
        counts[kind] += 1
        if "unperturbed_other_rows" in original:
            rows, generic = original["unperturbed_other_rows"], original["other_rows"]
            assert len(rows) == len(generic) == 2
            for i, row in enumerate(rows, 1):
                assert isinstance(row, list) and len(row) == 9
                assert all(type(v) is int and v > 0 for v in row)
                assert all(row[g] > row[i] for g in range(9) if g != i)
                direction = [0] * 9
                for j, g in enumerate(h for h in range(9) if h != i):
                    direction[g] = 3**j
                assert generic[i - 1] == [3281 * v + d for v, d in zip(row, direction)]
            assert all(sum(q * v for q, v in zip(form, rows[i - 1])) <= 0 for i, form in raw)
            counts["generic_base_membership"] += 1
        region_bindings.append({"source": str(path(original_file).relative_to(ROOT)),
                                "source_sha256": sha(original_bytes),
                                "core_sha256": original["core_sha256"],
                                "allocation_ids": ids, "guarantee": kind,
                                "raw_atoms": len(raw), "retained_atoms": len(kept)})

    groups = manifest["ordered_sources"]
    assert [g["kind"] for g in groups] == ["robust_single", "resumed", "static_pair"]
    for group in groups:
        value = read(group["source"], group["source_sha256"])
        records = json.loads(value)
        assert len(records) == group["records"]
        if group["kind"] == "resumed":
            if pruning is not None:
                assert sha(value) == pruning["resumed_regions_sha256"]
                assert len(records) == pruning["retained_cores"]
            for record in records:
                original_bytes = read(record["source"])
                read(record["core_source"], record["core_sha256"])
                check_core(record, record["source"], original_bytes)
            counts["resumed_regions"] = len(records)
        else:
            historical_name = "seed_regions.json" if group["kind"] == "robust_single" else "paired_seed_regions.json"
            historical_path = OUT / "outer_resumed2_checkpoint1" / historical_name
            assert str(historical_path.relative_to(ROOT)) in checkpoint["bound_files"]
            assert sha(value) == checkpoint["bound_files"][str(historical_path.relative_to(ROOT))]
            if replay_prior and group["kind"] == "static_pair":
                pair_file = ROOT / "continuation/structural_nine/verify_pair_seeds.py"
                pair_checker = module("release_static_pair_checker", pair_file)
                read(pair_file)
                paired_receipt = read_json(OUT / "outer_resumed2_checkpoint1/paired_seed_verification.json")
                pair_source = read_json(paired_receipt["source"], paired_receipt["source_sha256"])
                assert pair_source["records"] == [r["source_record"] for r in records]
                pair_checker.verify(pair_source)
            for record in records:
                ids = [record["allocation_id"]] if group["kind"] == "robust_single" else record["allocation_ids"]
                if replay_prior and group["kind"] == "robust_single":
                    compression.check_seed(ids[0])
                raw, kept = compression.check_region(record, ids)
                expected.append(compression.clause(kept))
                atoms["raw"] += len(raw)
                atoms["retained"] += len(kept)
            counts[group["kind"]] = len(records)

    new_items = manifest["ordered_new_regions"]
    assert len(new_items) == manifest["new_region_count"]
    new_names = [path(r["source"]).name for r in new_items]
    assert new_names == sorted(set(new_names))
    if new_items:
        directory = path(new_items[0]["source"]).parent
        assert {path(r["source"]).parent for r in new_items} == {directory}
        assert set(new_names) == {p.name for p in directory.glob("*.json")}
    for item in new_items:
        value = read(item["source"], item["source_sha256"])
        record = json.loads(value)
        assert record["core_allocation_ids"] == item["allocation_ids"]
        assert record["core_sha256"] == item["core_sha256"]
        read(item["core_source"], item["core_sha256"])
        if "certificate" in item:
            read(item["certificate"], item["certificate_sha256"])
        check_core(record, item["source"], value)
    counts["new_regions"] = len(new_items)
    if pruning is None:
        assert used_prior == set(prior)
        assert used_reduced == set(reduced)

    smt_bytes = read(manifest["outer"], manifest["outer_sha256"])
    roots = compression.parse(smt_bytes.decode())
    assert all(r[0] in ("declare-fun", "assert", "check-sat") for r in roots)
    declarations = [r for r in roots if r[0] == "declare-fun"]
    assert len(declarations) == 18 and {r[1] for r in declarations} == set(compression.VARS)
    assert all(r[2:] == [[], "Real"] for r in declarations)
    assert [r for r in roots if r[0] == "check-sat"] == [["check-sat"]]
    assertions = [compression.boolform(r[1]) for r in roots if r[0] == "assert"]
    base = [r for r in assertions if r[0] != "or"]
    actual = [r for r in assertions if r[0] == "or"]
    expected_base = []
    for i in (1, 2):
        for g in range(9):
            row = [0] * 19
            row[9 * (i - 1) + g], row[-1] = 1, -1
            expected_base.append(("=" if g == i else ">", tuple(row)))
    assert Counter(base) == Counter(expected_base)
    assert actual == expected
    assert len(assertions) == manifest["total_assertions"] == 18 + len(expected)
    assert core_file.read_bytes() == core_bytes and compression_file.read_bytes() == compression_bytes
    for name, digest in bound_files.items():
        assert sha((ROOT / name).read_bytes()) == digest
    return {
        "status": "PASS_ALL_LOCAL_GUARANTEES_AND_EXACT_FINAL_OUTER_BINDING_NOT_GLOBAL_UNSAT",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "outer": str(path(manifest["outer"]).relative_to(ROOT)),
        "outer_sha256": sha(smt_bytes), "manifest_sha256": sha(manifest_bytes),
        "terminal_receipt": str(terminal_file.relative_to(ROOT)),
        "terminal_receipt_sha256": manifest["terminal_receipt_sha256"],
        "recorded_search_termination": terminal["worker_summary"]["termination"],
        "checker_sha256": sha(core_bytes), "compression_checker_sha256": sha(compression_bytes),
        "base_assertions": len(base), "learned_clauses": len(actual), "total_assertions": len(assertions),
        "guarantees": dict(counts), "distinct_core_allocation_sets": len(allocation_sets),
        "archived_exact_core_branches": sum(prior_items[key]["exhaustive_failure_branches"] for key in used_prior),
        "historical_core_registry_certificates": len(prior),
        "historical_core_registry_branches": prior_branches,
        "new_direct_pair_branches_checked": direct_branches["direct_pair"],
        "new_direct_fallback_branches_checked": direct_branches["direct_fallback"],
        "prior_exact_certificates_replayed": replay_prior,
        "raw_region_atoms": atoms["raw"], "retained_region_atoms": atoms["retained"],
        "scope": "All exact local guarantees, original/source/core hashes, literal other-row regions, compression witnesses, and the complete ordered final outer assertion set are bound. Historical proofs are carried forward from identified exact audit receipts by matching hashes unless prior_exact_certificates_replayed is true; in that mode all registered exact core, singleton, static-pair, reduced-core/subset and pruning checks are replayed. No solver runs and global coverage remains unresolved.",
        "certificate_index": [r for r in prior_index + reduced_index + fresh_certificate_index if r["file"] in used_certificates],
        "region_bindings": region_bindings, "bound_files": bound_files,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--output", required=True)
    parser.add_argument("--replay-prior", action="store_true")
    parser.add_argument("--pruning-receipt")
    parser.add_argument("--minimized-receipt", action="append", default=[])
    args = parser.parse_args()
    report = audit(path(args.manifest), args.replay_prior, args.pruning_receipt, args.minimized_receipt)
    path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("certificate_index", "region_bindings", "bound_files")}, indent=2))


if __name__ == "__main__":
    main()
