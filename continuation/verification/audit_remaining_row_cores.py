"""Exact local audit of the frozen remaining 388 resumed2 cores.

No solver is run. Later live search regions and outer coverage are outside
the scope of this receipt.
"""
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
FROZEN = OUT / "row_regions_resumed2_remaining"
CERTS = ROOT / "continuation/row_core_certificates_resumed2_remaining"


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


def main():
    checker_file = ROOT / "continuation/verify_row_cores.py"
    compression_file = OUT / "audit_row_compression.py"
    checker_bytes, compression_bytes = checker_file.read_bytes(), compression_file.read_bytes()
    checker = module("remaining_exact_checker", checker_file)
    compression = module("remaining_compression_checker", compression_file)
    index_bytes = (FROZEN / "source_index.json").read_bytes()
    index = json.loads(index_bytes)
    assert index["count"] == len(index["records"]) == 388
    names = {path(r["frozen_region"]).name for r in index["records"]}
    assert len(names) == 388
    assert names == {p.name for p in (FROZEN / "regions").glob("*.json")}
    assert names == {p.name for p in CERTS.glob("*.json") if p.name != "verification.json"}
    receipts = []
    raw_total = kept_total = 0
    allocation_sets = set()
    for item in index["records"]:
        region_path, inner_path = path(item["frozen_region"]), path(item["frozen_core"])
        assert region_path.parent == FROZEN / "regions"
        assert inner_path.parent == FROZEN / "inner"
        region_bytes, inner_bytes = region_path.read_bytes(), inner_path.read_bytes()
        assert sha(region_bytes) == item["region_sha256"]
        assert sha(inner_bytes) == item["core_sha256"]
        assert path(item["source_region"]).read_bytes() == region_bytes
        assert path(item["source_core"]).read_bytes() == inner_bytes
        record = json.loads(region_bytes)
        assert record["core_allocation_ids"] == item["core_allocation_ids"]
        assert record["core_sha256"] == item["core_sha256"]
        cert_path = CERTS / region_path.name
        cert_bytes = cert_path.read_bytes()
        data = json.loads(cert_bytes)
        assert data["format_version"] == 2
        assert data["source_core_sha256"] == item["core_sha256"]
        assert data["core_allocations"] == record["core_allocations"]
        assert data["core_allocation_ids"] == record["core_allocation_ids"]
        assert data["other_region_atoms"] == record["region_atoms"]
        receipt = checker.verify(data)
        raw, retained = compression.check_region(record, record["core_allocation_ids"])
        raw_total += len(raw)
        kept_total += len(retained)
        allocation_sets.add(tuple(sorted(record["core_allocation_ids"])))
        receipts.append({
            "file": str(cert_path.relative_to(ROOT)), "sha256": sha(cert_bytes),
            "source_region": str(region_path.relative_to(ROOT)),
            "source_region_sha256": sha(region_bytes),
            "source_core_sha256": sha(inner_bytes),
            "raw_region_atoms": len(raw), "retained_region_atoms": len(retained),
            **receipt,
        })
    generation = json.loads((CERTS / "verification.json").read_text())
    assert generation["status"] == "PASS" and generation["cores"] == 388
    assert {
        r["file"]: r["certificate_sha256"] for r in generation["receipts"]
    } == {Path(r["file"]).name: r["sha256"] for r in receipts}
    assert checker_file.read_bytes() == checker_bytes
    assert compression_file.read_bytes() == compression_bytes
    report = {
        "status": "PASS_EXACT_388_CORES_AND_COMPRESSION_NOT_OUTER_COVERAGE",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "source_index_sha256": sha(index_bytes),
        "checker_sha256": sha(checker_bytes),
        "compression_checker_sha256": sha(compression_bytes),
        "certificates_verified": len(receipts),
        "distinct_allocation_sets": len(allocation_sets),
        "failure_branches_verified": sum(r["exhaustive_failure_branches"] for r in receipts),
        "max_failure_branches": max(r["exhaustive_failure_branches"] for r in receipts),
        "raw_region_atoms": raw_total, "retained_region_atoms": kept_total,
        "generation_resume": {
            "preexisting_certificates_reused": 200,
            "missing_certificates_generated": 188,
            "completed_generation_and_replay_seconds": generation["elapsed_seconds"],
        },
        "scope": "Every frozen source/core hash, allocation, literal other-row predicate, exact branch alternative and compression witness passed. This receipt does not bind a later outer formula or assert global coverage.",
        "receipts": receipts,
    }
    (OUT / "remaining_row_core_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "receipts"}, indent=2))


if __name__ == "__main__":
    main()
