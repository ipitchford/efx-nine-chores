"""Audit allocation-subset pruning and the four retained smoke pair proofs.

The retained-core guarantees are bound separately by the final outer audit.
This check proves that every omitted original region is contained in a
retained region, using literal allocation subsets and exact compression.
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
    compression_file = OUT / "audit_row_compression.py"
    core_file = ROOT / "continuation/verify_row_cores.py"
    compression = module("resume_pruning_compression", compression_file)
    core = module("resume_pruning_core", core_file)
    manifest_bytes = (directory / "resume_manifest.json").read_bytes()
    resumed_bytes = (directory / "resumed_regions.json").read_bytes()
    manifest, resumed = map(json.loads, (manifest_bytes, resumed_bytes))
    originals, source_index, raw_atoms = {}, [], {}
    for source_directory in manifest["directories"]:
        for file in sorted((path(source_directory) / "regions").glob("*.json")):
            assert file not in originals
            value = file.read_bytes()
            record = json.loads(value)
            ids = record["core_allocation_ids"]
            assert len(ids) == len(set(ids))
            assert [compression.allocation(aid) for aid in ids] == record["core_allocations"]
            if "compressed_region_atoms" in record:
                raw, kept = compression.check_region(record, ids)
            else:
                # Legacy source records predate compression. Their resumed
                # copies carry the compression certificate checked below.
                raw = [compression.atom(p) for p in record["region_atoms"]]
                assert len(raw) == len(set(raw))
                assert set(raw) == compression.literal_other_rows(ids)
                kept = raw
            inner = file.parent.parent / "inner" / file.with_suffix(".smt2").name
            assert sha(inner.read_bytes()) == record["core_sha256"]
            originals[file] = record
            raw_atoms[file] = set(raw)
            source_index.append({"file": str(file.relative_to(ROOT)), "sha256": sha(value),
                                 "core_file": str(inner.relative_to(ROOT)),
                                 "core_sha256": record["core_sha256"], "allocation_ids": ids,
                                 "raw_atoms": len(raw), "retained_atoms": len(kept)})
    assert len(originals) == manifest["source_region_files"]
    assert len({tuple(sorted(r["core_allocation_ids"])) for r in originals.values()}) == manifest["distinct_source_cores"]
    retained_sources = set()
    for record in resumed:
        source = path(record["source"])
        assert source in originals and source not in retained_sources
        retained_sources.add(source)
        original = originals[source]
        assert record["core_allocation_ids"] == original["core_allocation_ids"]
        assert record["core_sha256"] == original["core_sha256"]
        assert record["region_atoms"] == original["region_atoms"]
        compression.check_region(record, record["core_allocation_ids"])
    assert len(retained_sources) == manifest["unique_cores"]
    subsumed_sources, duplicate_sources = set(), set()
    for record in manifest["subsumed_sources"]:
        source, retained = path(record["source"]), path(record["retained_source"])
        assert source in originals and retained in retained_sources
        assert source not in retained_sources and source not in subsumed_sources
        subsumed_sources.add(source)
        original_ids = originals[source]["core_allocation_ids"]
        retained_ids = originals[retained]["core_allocation_ids"]
        assert all(type(v) is int for v in record["source_core_allocation_ids"] + record["retained_core_allocation_ids"])
        assert sorted(record["source_core_allocation_ids"]) == sorted(original_ids)
        assert sorted(record["retained_core_allocation_ids"]) == sorted(retained_ids)
        assert set(retained_ids) < set(original_ids)
        assert raw_atoms[retained] <= raw_atoms[source]
    for record in manifest["duplicate_sources"]:
        source = path(record["source"])
        duplicate = path(record["duplicate_of"])
        retained = path(record["retained_source"])
        assert source in originals and duplicate in originals and retained in retained_sources
        assert source not in retained_sources | subsumed_sources | duplicate_sources
        duplicate_sources.add(source)
        assert set(originals[source]["core_allocation_ids"]) == set(originals[duplicate]["core_allocation_ids"]) == set(originals[retained]["core_allocation_ids"])
        assert raw_atoms[source] == raw_atoms[retained]
    assert retained_sources | subsumed_sources | duplicate_sources == set(originals)
    smoke_receipts = []
    for file, record in originals.items():
        if file.parent.parent.name != "row_elimination_batch_smoke":
            continue
        certificate_file = file.parent.parent / "exact_pair_certificates" / file.name
        certificate_bytes = certificate_file.read_bytes()
        assert sha(certificate_bytes) == record["exact_pair_certificate_sha256"]
        cert = json.loads(certificate_bytes)
        assert cert["source_core_sha256"] == record["core_sha256"]
        assert cert["core_allocation_ids"] == record["core_allocation_ids"]
        assert cert["core_allocations"] == record["core_allocations"]
        assert cert["other_region_atoms"] == record["region_atoms"]
        smoke_receipts.append({"file": str(certificate_file.relative_to(ROOT)),
                               "sha256": sha(certificate_bytes), **core.verify(cert)})
    assert len(smoke_receipts) == 4
    assert (directory / "resume_manifest.json").read_bytes() == manifest_bytes
    assert (directory / "resumed_regions.json").read_bytes() == resumed_bytes
    for item in source_index:
        assert sha((ROOT / item["file"]).read_bytes()) == item["sha256"]
    return {
        "status": "PASS_EXACT_SUBSET_PRUNING_COMPRESSION_AND_FOUR_SMOKE_PAIR_CERTIFICATES",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "directory": str(directory.relative_to(ROOT)),
        "resume_manifest_sha256": sha(manifest_bytes), "resumed_regions_sha256": sha(resumed_bytes),
        "core_checker_sha256": sha(core_file.read_bytes()),
        "compression_checker_sha256": sha(compression_file.read_bytes()),
        "source_region_files": len(originals), "distinct_source_cores": manifest["distinct_source_cores"],
        "retained_cores": len(retained_sources), "subsumed_cores": len(subsumed_sources),
        "duplicate_sources": len(duplicate_sources), "smoke_pair_certificates": len(smoke_receipts),
        "smoke_pair_failure_branches": sum(r["exhaustive_failure_branches"] for r in smoke_receipts),
        "scope": "All source allocations, core hashes, literal regions and compression are checked. Each pruned region implies a retained region by a strict allocation subset; duplicate records have equal allocation sets and literal regions. Four smoke pair certificates are replayed. The retained first-row guarantees and final outer assertion set require the separate final outer audit; no coverage result is claimed.",
        "source_index": source_index, "smoke_certificate_receipts": smoke_receipts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = audit(args.directory)
    path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("source_index", "smoke_certificate_receipts")}, indent=2))


if __name__ == "__main__":
    main()
