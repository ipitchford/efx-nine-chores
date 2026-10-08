"""Check reduced exact core proofs and their implication for original regions.

This standard-library audit runs no solver. The smaller certified allocation
set suffices for the original larger core, and the original region retains
its original literal predicates and independently checked compression.
"""
import argparse
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
    return result


def path(value):
    value = Path(value)
    if not value.is_absolute():
        return ROOT / value
    if value.is_relative_to(ROOT):
        return value
    assert value.parts.count("continuation") == 1
    return ROOT.joinpath(*value.parts[value.parts.index("continuation"):])


def audit(directory):
    directory = path(directory)
    checker_path = ROOT / "continuation/verify_row_cores.py"
    compression_path = OUT / "audit_row_compression.py"
    checker_bytes, compression_bytes = checker_path.read_bytes(), compression_path.read_bytes()
    checker = module("minimized_core_checker", checker_path)
    compression = module("minimized_compression_checker", compression_path)
    generation_file = directory / "final_verification.json"
    if not generation_file.exists():
        generation_file = directory / "verification.json"
    generation_bytes = generation_file.read_bytes()
    generation = json.loads(generation_bytes)
    assert generation["status"] == "PASS"
    assert len(generation["receipts"]) == generation["cores"]
    records = []
    used = set()
    for item in generation["receipts"]:
        original_file, reduced_file, cert_file = map(path, (
            item["original_source"], item["reduced_source"], item["certificate"]
        ))
        assert reduced_file.parent == directory / "regions"
        assert cert_file.parent == directory / "certificates"
        assert reduced_file.name == cert_file.name
        assert reduced_file.name not in used
        used.add(reduced_file.name)
        old_bytes, new_bytes, cert_bytes = (
            original_file.read_bytes(), reduced_file.read_bytes(), cert_file.read_bytes()
        )
        assert sha(old_bytes) == item["original_source_sha256"]
        assert sha(new_bytes) == item["reduced_source_sha256"]
        assert sha(cert_bytes) == item["certificate_sha256"]
        old, new, cert = map(json.loads, (old_bytes, new_bytes, cert_bytes))
        assert new["original_source_sha256"] == sha(old_bytes)
        assert new["original_core_sha256"] == old["core_sha256"]
        assert new["original_allocation_ids"] == old["core_allocation_ids"] == item["original_allocation_ids"]
        assert path(new["original_source"]) == original_file
        positions = new["retained_original_indices"]
        assert positions == item["retained_original_indices"]
        assert all(type(i) is int and 0 <= i < len(old["core_allocation_ids"]) for i in positions)
        assert len(positions) == len(set(positions))
        assert [old["core_allocation_ids"][i] for i in positions] == new["core_allocation_ids"] == item["retained_allocation_ids"]
        assert [old["core_allocations"][i] for i in positions] == new["core_allocations"]
        for record in (old, new):
            assert [compression.allocation(aid) for aid in record["core_allocation_ids"]] == record["core_allocations"]
            assert record["core_size"] == len(record["core_allocation_ids"])
        old_core = original_file.parent.parent / "inner" / original_file.with_suffix(".smt2").name
        new_core = directory / "inner" / reduced_file.with_suffix(".smt2").name
        assert sha(old_core.read_bytes()) == old["core_sha256"]
        assert sha(new_core.read_bytes()) == new["core_sha256"]
        assert cert["format_version"] == 2
        assert cert["source_core_sha256"] == new["core_sha256"]
        assert cert["core_allocation_ids"] == new["core_allocation_ids"]
        assert cert["core_allocations"] == new["core_allocations"]
        assert cert["other_region_atoms"] == new["region_atoms"]
        assert new["exact_core_certificate_sha256"] == sha(cert_bytes)
        receipt = checker.verify(cert)
        old_raw, old_kept = compression.check_region(old, old["core_allocation_ids"])
        new_raw, new_kept = compression.check_region(new, new["core_allocation_ids"])
        assert set(new_raw) <= set(old_raw)
        records.append({
            "original_source": str(original_file.relative_to(ROOT)),
            "original_source_sha256": sha(old_bytes),
            "original_core_sha256": old["core_sha256"],
            "original_allocation_ids": old["core_allocation_ids"],
            "reduced_source": str(reduced_file.relative_to(ROOT)),
            "reduced_source_sha256": sha(new_bytes),
            "reduced_core_sha256": new["core_sha256"],
            "retained_allocation_ids": new["core_allocation_ids"],
            "retained_original_indices": positions,
            "certificate": str(cert_file.relative_to(ROOT)),
            "certificate_sha256": sha(cert_bytes),
            "original_raw_atoms": len(old_raw), "original_retained_atoms": len(old_kept),
            "reduced_raw_atoms": len(new_raw), "reduced_retained_atoms": len(new_kept),
            **receipt,
        })
    assert used == {p.name for p in (directory / "regions").glob("*.json")}
    assert used == {p.name for p in (directory / "certificates").glob("*.json")}
    assert checker_path.read_bytes() == checker_bytes
    assert compression_path.read_bytes() == compression_bytes
    return {
        "status": "PASS_EXACT_REDUCED_CORES_AND_ORIGINAL_REGION_SUBSET_IMPLICATION",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "source_directory": str(directory.relative_to(ROOT)),
        "generation_receipt": str(generation_file.relative_to(ROOT)),
        "generation_receipt_sha256": sha(generation_bytes),
        "checker_sha256": sha(checker_bytes),
        "compression_checker_sha256": sha(compression_bytes),
        "original_regions_certified": len(records),
        "reduced_failure_branches": sum(r["exhaustive_failure_branches"] for r in records),
        "maximum_original_core_size": max(map(lambda r: len(r["original_allocation_ids"]), records), default=0),
        "maximum_reduced_core_size": max(map(lambda r: len(r["retained_allocation_ids"]), records), default=0),
        "scope": "Every reduced exact certificate, original and reduced core hash, allocation subset, full original literal region and original compression is checked. Original-region predicates imply the reduced predicates; a first-row allocation guaranteed in the reduced set is also in the original set. This is local validity, not global coverage.",
        "receipts": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = audit(args.directory)
    path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "receipts"}, indent=2))


if __name__ == "__main__":
    main()
