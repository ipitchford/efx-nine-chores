"""Independently verify the frozen 284 + 57 core set and region compression.

No solver is imported or run. Reuses the inspected exact literal checker
and the previously audited compression identity checker.
"""
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
FROZEN = OUT / "row_regions_frozen_20261007"
CERTS = ROOT / "continuation/row_core_certificates_frozen_20261007"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def package_path(value):
    value = Path(value)
    if not value.is_absolute():
        return ROOT / value
    if value.is_relative_to(ROOT):
        return value
    parts = value.parts
    assert parts.count("continuation") == 1
    return ROOT.joinpath(*parts[parts.index("continuation"):])


def main():
    checker_path = ROOT / "continuation/verify_row_cores.py"
    compressor_path = OUT / "audit_row_compression.py"
    checker_bytes = checker_path.read_bytes()
    compressor_bytes = compressor_path.read_bytes()
    checker = module("frozen_exact_checker", checker_path)
    compressor = module("frozen_compression_checker", compressor_path)
    index_bytes = (FROZEN / "source_index.json").read_bytes()
    index = json.loads(index_bytes)
    assert index["counts"] == {"compressed": 284, "resumed1": 57}
    expected_names = {
        Path(record["frozen_region"]).name for record in index["records"]
    }
    assert len(expected_names) == len(index["records"]) == 341
    assert expected_names == {p.name for p in (FROZEN / "regions").glob("*.json")}
    assert expected_names == {
        p.name for p in CERTS.glob("*.json") if p.name != "verification.json"
    }
    receipts = []
    group_counts = Counter()
    branch_counts = Counter()
    raw_count = kept_count = 0
    unique_branches = set()
    for item in index["records"]:
        region_path = package_path(item["frozen_region"])
        core_path = package_path(item["frozen_core"])
        assert region_path.parent == FROZEN / "regions"
        assert core_path.parent == FROZEN / "inner"
        region_bytes, core_bytes = region_path.read_bytes(), core_path.read_bytes()
        assert sha(region_bytes) == item["region_sha256"]
        assert sha(core_bytes) == item["core_sha256"]
        assert package_path(item["source_region"]).read_bytes() == region_bytes
        assert package_path(item["source_core"]).read_bytes() == core_bytes
        record = json.loads(region_bytes)
        assert record["core_sha256"] == item["core_sha256"]
        assert record["core_allocation_ids"] == item["core_allocation_ids"]
        cert_path = CERTS / region_path.name
        cert_bytes = cert_path.read_bytes()
        cert = json.loads(cert_bytes)
        assert cert["format_version"] == 2
        assert cert["core_allocations"] == record["core_allocations"]
        assert cert["core_allocation_ids"] == record["core_allocation_ids"]
        assert cert["other_region_atoms"] == record["region_atoms"]
        assert cert["source_core_sha256"] == item["core_sha256"]
        receipt = checker.verify(cert)
        raw, retained = compressor.check_region(record, record["core_allocation_ids"])
        raw_count += len(raw)
        kept_count += len(retained)
        group = region_path.stem.split("_", 1)[0]
        group_counts[group] += 1
        branch_counts[group] += receipt["exhaustive_failure_branches"]
        for branch in cert["branches"]:
            unique_branches.add(
                tuple(tuple(row) for row in branch["failure_rows"])
            )
        receipts.append({
            "file": str(cert_path.relative_to(ROOT)),
            "sha256": sha(cert_bytes),
            "source_region": str(region_path.relative_to(ROOT)),
            "source_region_sha256": sha(region_bytes),
            "source_core_sha256": sha(core_bytes),
            "raw_region_atoms": len(raw),
            "retained_region_atoms": len(retained),
            **receipt,
        })
    assert group_counts == index["counts"]
    assert checker_path.read_bytes() == checker_bytes
    assert compressor_path.read_bytes() == compressor_bytes
    generation = json.loads((CERTS / "verification.json").read_text())
    assert generation["status"] == "PASS" and generation["cores"] == 341
    assert {
        p["file"]: p["certificate_sha256"] for p in generation["receipts"]
    } == {Path(r["file"]).name: r["sha256"] for r in receipts}
    report = {
        "status": "PASS_EXACT_FROZEN_CORES_AND_COMPRESSION_NOT_GLOBAL_COVERAGE",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "source_index_sha256": sha(index_bytes),
        "checker_sha256": sha(checker_bytes),
        "compression_checker_sha256": sha(compressor_bytes),
        "certifier_sha256": sha((ROOT / "continuation/certify_row_cores.py").read_bytes()),
        "certificates_verified": len(receipts),
        "group_counts": dict(group_counts),
        "failure_branch_counts": dict(branch_counts),
        "total_failure_branches": sum(branch_counts.values()),
        "unique_failure_branch_alternatives": len(unique_branches),
        "max_failure_branches": max(r["exhaustive_failure_branches"] for r in receipts),
        "raw_region_atoms": raw_count,
        "retained_region_atoms": kept_count,
        "generation_elapsed_seconds": generation["elapsed_seconds"],
        "scope": "Every frozen region and core input matches its source and index; every allocation, exact other-row literal, branch alternative, and compression witness passed. No outer solver verdict is claimed.",
        "receipts": receipts,
    }
    (OUT / "frozen_row_core_audit.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "receipts"}, indent=2))


if __name__ == "__main__":
    main()
