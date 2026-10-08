"""Bind every clause of one frozen outer input to exact local guarantees.

Carries completed singleton and core checks forward by hash; verifies new
paired alternatives and the 51 new nonordinal cores; checks all new region
compression and exact SMT assertions. No solver is imported or run.
"""
from collections import Counter
from copy import deepcopy
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
SNAP = OUT / "outer_resumed2_checkpoint1"
NEW_CERTS = ROOT / "continuation/row_core_certificates_resumed2_checkpoint1"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def path(value):
    value = Path(value)
    if not value.is_absolute():
        return ROOT / value
    if value.is_relative_to(ROOT):
        return value
    # The archived source indices retain their original absolute workspace
    # prefix. All inspected package sources are under continuation/.
    parts = value.parts
    assert parts.count("continuation") == 1
    return ROOT.joinpath(*parts[parts.index("continuation"):])


def reject(checker, value):
    try:
        checker.verify(value)
    except (AssertionError, KeyError, IndexError, ValueError, TypeError) as error:
        return type(error).__name__ + ": " + str(error)
    raise AssertionError("Invalid paired-certificate mutation accepted")


def main():
    compression_path = OUT / "audit_row_compression.py"
    core_path = ROOT / "continuation/verify_row_cores.py"
    pair_path = ROOT / "continuation/structural_nine/verify_pair_seeds.py"
    source_bytes = {
        str(p.relative_to(ROOT)): p.read_bytes()
        for p in (compression_path, core_path, pair_path)
    }
    compression = module("checkpoint_compression_checker", compression_path)
    core_checker = module("checkpoint_core_checker", core_path)
    pair_checker = module("checkpoint_pair_checker", pair_path)
    index_bytes = (SNAP / "source_index.json").read_bytes()
    index = json.loads(index_bytes)
    assert {
        key: index[key] for key in (
            "outer_assertions", "domain_assertions", "robust_single_regions",
            "resumed_regions", "paired_regions", "new_regions"
        )
    } == {
        "outer_assertions": 4805, "domain_assertions": 18,
        "robust_single_regions": 3238, "resumed_regions": 450,
        "paired_regions": 1048, "new_regions": 51
    }
    bound_files = {}
    learned_items = []
    for item in index["records"]:
        frozen = path(item["frozen"])
        assert frozen.is_relative_to(SNAP)
        value = frozen.read_bytes()
        assert sha(value) == item["sha256"]
        assert path(item["source"]).read_bytes() == value
        bound_files[str(frozen.relative_to(ROOT))] = sha(value)
        if item["kind"] == "learned_region":
            learned_items.append(item)
            inner = path(item["core"])
            assert inner.is_relative_to(SNAP / "inner")
            inner_bytes = inner.read_bytes()
            assert sha(inner_bytes) == item["core_sha256"]
            bound_files[str(inner.relative_to(ROOT))] = sha(inner_bytes)
        else:
            assert item["kind"] == "seed_or_manifest"
    assert len(learned_items) == 51
    assert {path(r["frozen"]).name for r in learned_items} == {
        p.name for p in (SNAP / "regions").glob("*.json")
    }

    completed_compression_bytes = (OUT / "row_compression_audit.json").read_bytes()
    completed_compression = json.loads(completed_compression_bytes)
    seed_bytes = (SNAP / "seed_regions.json").read_bytes()
    robust_bytes = (SNAP / "robust_seed.json").read_bytes()
    assert sha(seed_bytes) == completed_compression["seed_regions_sha256"]
    assert sha(robust_bytes) == completed_compression["robust_seed_sha256"]
    seeds = json.loads(seed_bytes)
    assert len(seeds) == 3238
    expected = []
    atom_counts = {}
    seed_raw = seed_kept = 0
    for record in seeds:
        retained = [compression.atom(p) for p in record["compressed_region_atoms"]]
        expected.append(compression.clause(retained))
        seed_raw += len(record["region_atoms"])
        seed_kept += len(retained)
    atom_counts["singleton_seeds"] = {"raw": seed_raw, "retained": seed_kept}
    del seeds, seed_bytes

    # Both completed receipt sets were checked with the same repaired
    # independent core checker. Carry only the v2 legacy format forward.
    old_bytes = (OUT / "row_core_audit.json").read_bytes()
    frozen_bytes = (OUT / "frozen_row_core_audit.json").read_bytes()
    old, frozen = json.loads(old_bytes), json.loads(frozen_bytes)
    assert old["checker_sha256"] == frozen["checker_sha256"] == sha(
        source_bytes[str(core_path.relative_to(ROOT))]
    )
    prior_records = [r for r in old["receipts"] if r["format_version"] == 2]
    prior_records += frozen["receipts"]
    assert len(prior_records) == 450
    prior = {}
    prior_manifest = []
    for item in prior_records:
        file = path(item["file"])
        value = file.read_bytes()
        assert sha(value) == item["sha256"]
        data = json.loads(value)
        key = (data["source_core_sha256"], tuple(data["core_allocation_ids"]))
        assert key not in prior
        prior[key] = data
        prior_manifest.append({"file": str(file.relative_to(ROOT)), "sha256": sha(value)})
    resumed = json.loads((SNAP / "resumed_regions.json").read_text())
    assert len(resumed) == 450
    used = set()
    resumed_raw = resumed_kept = 0
    core_allocation_sets = set()
    for record in resumed:
        key = (record["core_sha256"], tuple(record["core_allocation_ids"]))
        assert key in prior and key not in used
        used.add(key)
        cert = prior[key]
        original = json.loads(path(record["source"]).read_text())
        assert cert["core_allocation_ids"] == original["core_allocation_ids"]
        assert cert["core_allocations"] == original["core_allocations"]
        assert cert["other_region_atoms"] == original["region_atoms"] == record["region_atoms"]
        assert original["core_sha256"] == key[0]
        assert sha(path(record["core_source"]).read_bytes()) == key[0]
        raw, retained = compression.check_region(record, record["core_allocation_ids"])
        expected.append(compression.clause(retained))
        resumed_raw += len(raw)
        resumed_kept += len(retained)
        core_allocation_sets.add(tuple(sorted(record["core_allocation_ids"])))
    assert used == set(prior)
    atom_counts["resumed_cores"] = {"raw": resumed_raw, "retained": resumed_kept}
    del prior, resumed

    pairs = json.loads((SNAP / "paired_seed_regions.json").read_text())
    assert len(pairs) == 1048
    pair_receipt = json.loads((SNAP / "paired_seed_verification.json").read_text())
    pair_source_path = path(pair_receipt["source"])
    pair_source_bytes = pair_source_path.read_bytes()
    assert sha(pair_source_bytes) == pair_receipt["source_sha256"]
    pair_source = json.loads(pair_source_bytes)
    assert pair_source["records"] == [r["source_record"] for r in pairs]
    pair_result = pair_checker.verify(pair_source)
    assert pair_result["certified_pairs"] == 1048
    assert pair_result["exhaustive_failure_branches"] == 4192
    paired_raw = paired_kept = 0
    for record in pairs:
        assert record["allocation_ids"] == record["source_record"]["allocation_ids"]
        for allocation, aid in zip(
            record["source_record"]["allocations"], record["allocation_ids"]
        ):
            assert allocation == compression.allocation(aid)
        # Even metadata coefficient rows are kept in their literal exact type.
        assert all(
            type(v) is int
            for rows in record["source_record"]["first_row_bad_coefficients"]
            for row in rows for v in row
        )
        raw, retained = compression.check_region(record, record["allocation_ids"])
        expected.append(compression.clause(retained))
        paired_raw += len(raw)
        paired_kept += len(retained)
    atom_counts["paired_seeds"] = {"raw": paired_raw, "retained": paired_kept}
    mutations = {}
    one = deepcopy(pair_source)
    one["records"] = [one["records"][0]]
    one["certified_pairs"] = 1
    pair_checker.verify(one)
    bad = deepcopy(one)
    bad["records"][0]["proof_branches"].pop()
    mutations["missing_failure_pair"] = reject(pair_checker, bad)
    bad = deepcopy(one)
    bad["records"][0]["proof_branches"][0]["atom_weights"][0] = [-1, 1]
    mutations["negative_atom_weight"] = reject(pair_checker, bad)
    bad = deepcopy(one)
    bad["records"][0]["proof_branches"][0]["atom_weights"] = [[0, 1], [0, 1]]
    mutations["zero_atom_weights"] = reject(pair_checker, bad)
    bad = deepcopy(one)
    bad["records"][0]["proof_branches"][0]["gap_weights"][0][0] = 1.0
    mutations["floating_rational_numerator"] = reject(pair_checker, bad)
    bad = deepcopy(one)
    bad["records"][0]["allocation_ids"][0] += 1
    mutations["wrong_allocation_id"] = reject(pair_checker, bad)
    del pairs, pair_source, pair_source_bytes

    new_manifest = []
    new_raw = new_kept = 0
    for item in learned_items:
        region = path(item["frozen"])
        record = json.loads(region.read_text())
        assert record["core_sha256"] == item["core_sha256"]
        assert [
            compression.allocation(aid) for aid in record["core_allocation_ids"]
        ] == record["core_allocations"]
        cert_file = NEW_CERTS / region.name
        cert_bytes = cert_file.read_bytes()
        cert = json.loads(cert_bytes)
        assert cert["format_version"] == 2
        assert cert["source_core_sha256"] == item["core_sha256"]
        assert cert["core_allocations"] == record["core_allocations"]
        assert cert["core_allocation_ids"] == record["core_allocation_ids"]
        assert cert["other_region_atoms"] == record["region_atoms"]
        receipt = core_checker.verify(cert)
        raw, retained = compression.check_region(record, record["core_allocation_ids"])
        expected.append(compression.clause(retained))
        new_raw += len(raw)
        new_kept += len(retained)
        core_allocation_sets.add(tuple(sorted(record["core_allocation_ids"])))
        new_manifest.append({
            "file": str(cert_file.relative_to(ROOT)), "sha256": sha(cert_bytes),
            "source_region": str(region.relative_to(ROOT)),
            "source_region_sha256": item["sha256"],
            "source_core_sha256": item["core_sha256"], **receipt,
        })
    atom_counts["new_cores"] = {"raw": new_raw, "retained": new_kept}
    generation = json.loads((NEW_CERTS / "verification.json").read_text())
    assert generation["status"] == "PASS" and generation["cores"] == 51
    assert {
        r["file"]: r["certificate_sha256"] for r in generation["receipts"]
    } == {Path(r["file"]).name: r["sha256"] for r in new_manifest}
    assert len(core_allocation_sets) == 501

    outer_bytes = (SNAP / "outer.smt2").read_bytes()
    assert sha(outer_bytes) == index["outer_sha256"]
    roots = compression.parse(outer_bytes.decode())
    assert all(r[0] in ("declare-fun", "assert", "check-sat") for r in roots)
    declarations = [r for r in roots if r[0] == "declare-fun"]
    assert len(declarations) == 18
    assert {r[1] for r in declarations} == set(compression.VARS)
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
    assert len(base) == 18 and len(actual) == 4787 and len(assertions) == 4805
    for name, value in source_bytes.items():
        assert (ROOT / name).read_bytes() == value
    report = {
        "status": "PASS_ALL_LOCAL_GUARANTEES_AND_EXACT_OUTER_BINDING_NOT_GLOBAL_UNSAT",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "outer_sha256": sha(outer_bytes),
        "source_index_sha256": sha(index_bytes),
        "completed_receipt_sha256": {
            "row_compression_audit.json": sha(completed_compression_bytes),
            "row_core_audit.json": sha(old_bytes),
            "frozen_row_core_audit.json": sha(frozen_bytes),
        },
        "checker_sources": {name: sha(value) for name, value in source_bytes.items()},
        "base_assertions": len(base),
        "learned_clauses": len(actual),
        "total_assertions": len(assertions),
        "seed_singleton_guarantees": 3238,
        "resumed_exact_core_guarantees": 450,
        "paired_exact_guarantees": pair_result,
        "new_exact_core_guarantees": len(new_manifest),
        "distinct_nonordinal_core_allocation_sets": len(core_allocation_sets),
        "new_core_failure_branches": sum(r["exhaustive_failure_branches"] for r in new_manifest),
        "new_core_max_failure_branches": max(r["exhaustive_failure_branches"] for r in new_manifest),
        "new_core_generation_elapsed_seconds": generation["elapsed_seconds"],
        "paired_source_sha256": pair_receipt["source_sha256"],
        "paired_mutations_rejected": mutations,
        "region_atom_counts": atom_counts,
        "total_raw_region_atoms": sum(v["raw"] for v in atom_counts.values()),
        "total_retained_region_atoms": sum(v["retained"] for v in atom_counts.values()),
        "scope": "Every one of the 4,787 learned clauses has an exact locally verified guarantee and matches its frozen literal/compressed region. No solver was run and no global coverage or counterexample verdict is asserted.",
        "bound_files": bound_files,
        "resumed_certificate_manifest": prior_manifest,
        "new_certificate_manifest": new_manifest,
    }
    (OUT / "outer_resumed2_checkpoint1_audit.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    hidden = {"bound_files", "resumed_certificate_manifest", "new_certificate_manifest"}
    print(json.dumps({k: v for k, v in report.items() if k not in hidden}, indent=2))


if __name__ == "__main__":
    main()
