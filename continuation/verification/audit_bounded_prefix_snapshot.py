"""Bind a frozen bounded-prefix formula to every exact local certificate.

Only standard-library parsers and certificate checkers are used. No solver is
run, no new mutation campaign is repeated, and global coverage is not claimed.
The snapshot contains formula.smt2, config.json and either a regions/ directory
or region_*.json files directly. A complete independently hashed certificate
index and audit receipt are produced beside this script.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as Q
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
B = 11585
DELTA = Q(1, B)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def shifted(v, constant):
    value = list(v)
    value[-1] += constant
    return tuple(value)


def audit(snapshot, output_directory=OUT):
    parser_file = OUT / "audit_prefix_snapshot.py"
    checker_file = ROOT / "continuation/extension_geometry/verify_extension_certificate.py"
    source_file = ROOT / "continuation/prefix_cegis.py"
    theorem_file = ROOT / "continuation/exact_search/bounded_prefix_margin.md"
    source_bytes = {str(p.relative_to(ROOT)): p.read_bytes()
                    for p in (parser_file, checker_file, source_file, theorem_file)}
    syntax = module("bounded_prefix_independent_syntax", parser_file)
    checker = syntax.checker
    smt_bytes = (snapshot / "formula.smt2").read_bytes()
    config_bytes = (snapshot / "config.json").read_bytes()
    config = json.loads(config_bytes)
    assert all(config[k] is True for k in (
        "fixed_minima", "restricted_ninth", "bounded_representative"
    ))
    directory = snapshot / "regions" if (snapshot / "regions").is_dir() else snapshot
    files = sorted(directory.glob("region_*.json"))
    assert files
    assert [p.name for p in files] == [f"region_{j:05d}.json" for j in range(len(files))]
    bg = syntax.background()
    lower = [[int(g == k) for g in range(8)] for k in (3, 1, 2)]
    receipts, expected_learned = [], []
    seen = set()
    scope_counts = Counter()
    metadata_count = 0
    maximum_coefficient = 0
    for file in files:
        value = file.read_bytes()
        data = json.loads(value)
        receipt = checker.verify(data)
        assert data.get("domain_inequalities", []) == bg
        old_lower = data.get("extension_domain_lower", [[0] * 8 for _ in range(3)])
        assert len(old_lower) == 3 and all(len(row) == 8 for row in old_lower)
        assert all(type(a) is int and 0 <= a <= b
                   for old, new in zip(old_lower, lower) for a, b in zip(old, new))
        assert len(data["prefix"]) == 3 and all(len(row) == 8 for row in data["prefix"])
        key = []
        for p in data["region"]:
            assert type(p["row"]) is int and p["row"] in (0, 1, 2)
            assert isinstance(p["coeffs"], list) and len(p["coeffs"]) == 8
            assert all(type(v) is int for v in p["coeffs"])
            maximum_coefficient = max(maximum_coefficient, max(map(abs, p["coeffs"]), default=0))
            key.append((p["row"], tuple(p["coeffs"])))
        key = tuple(key)
        if key not in seen:
            seen.add(key)
            expected_learned.append(("or", frozenset(
                ("<=", shifted(syntax.row_form(i, q), DELTA)) for i, q in key
            )))
        has_base = "unperturbed_prefix" in data
        if int(file.stem.split("_")[1]) >= 1701:
            assert has_base
        if has_base:
            rows = data["unperturbed_prefix"]
            assert len(rows) == 3 and all(isinstance(row, list) and len(row) == 8 for row in rows)
            assert all(type(v) is int and v > 0 for row in rows for v in row)
            denominator = rows[0][0]
            assert rows[1][1] == rows[2][2] == denominator
            assert all(v <= B * denominator for row in rows for v in row)
            assert all(B * sum(a * v for a, v in zip(p["coeffs"], rows[p["row"]])) >= denominator for p in bg)
            assert all(sum(rows[i]) > sum(rows[0]) for i in (1, 2))
            assert data["unperturbed_prefix_in_region"] is True
            assert all(sum(a * v for a, v in zip(q, rows[i])) >= 0 for i, q in key)
            metadata_count += 1
        scope_counts[receipt["coverage_scope"]] += 1
        receipts.append({"file": str(file.relative_to(ROOT)), "sha256": sha(value),
                         "unperturbed_membership_checked": has_base, **receipt})

    roots = syntax.parse(smt_bytes.decode())
    assert all(r[0] in ("declare-fun", "assert", "check-sat") for r in roots)
    declarations = [r for r in roots if r[0] == "declare-fun"]
    assert len(declarations) == 24 and {r[1] for r in declarations} == set(syntax.NAMES)
    assert all(r[2:] == [[], "Real"] for r in declarations)
    assert [r for r in roots if r[0] == "check-sat"] == [["check-sat"]]
    assertions = [syntax.formula(r[1]) for r in roots if r[0] == "assert"]
    base = [r for r in assertions if r[0] != "or"]
    learned = [r for r in assertions if r[0] == "or"]
    expected_base = []
    for i in range(3):
        expected_base.append(("=", shifted(syntax.row_form(i, [int(g == i) for g in range(8)]), -1)))
    expected_base += [(">=", shifted(syntax.row_form(p["row"], p["coeffs"]), -DELTA)) for p in bg]
    for i in range(3):
        for g in range(8):
            if g != i:
                expected_base.append(("<=", shifted(syntax.row_form(i, [int(h == g) for h in range(8)]), -B)))
    for i in (1, 2):
        row = [Q(0)] * 25
        row[:8], row[8 * i:8 * (i + 1)] = [-1] * 8, [1] * 8
        expected_base.append((">", tuple(row)))
    assert len(expected_base) == 52
    assert Counter(base) == Counter(expected_base), "Bounded prefix base domain mismatch"
    assert learned == expected_learned, "Learned clauses differ from the exact ordered delta complements of all certified regions"
    assert len(assertions) == 52 + len(seen)
    for item in receipts:
        assert sha((ROOT / item["file"]).read_bytes()) == item["sha256"]
    assert (snapshot / "formula.smt2").read_bytes() == smt_bytes
    assert (snapshot / "config.json").read_bytes() == config_bytes
    for name, value in source_bytes.items():
        assert (ROOT / name).read_bytes() == value
    certificate_index = {
        "snapshot": str(snapshot.relative_to(ROOT)),
        "formula_sha256": sha(smt_bytes),
        "config_sha256": sha(config_bytes),
        "certificate_files": len(receipts), "unique_regions": len(seen),
        "records": [{k: r[k] for k in ("file", "sha256")} for r in receipts],
    }
    index_file = output_directory / "bounded_prefix_certificate_index.json"
    index_bytes = (json.dumps(certificate_index, indent=2) + "\n").encode()
    index_file.write_bytes(index_bytes)
    report = {
        "status": "PASS_ALL_PREFIX_CERTIFICATES_AND_EXACT_BOUNDED_INPUT_NOT_GLOBAL_UNSAT",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "snapshot": str(snapshot.relative_to(ROOT)),
        "formula_sha256": sha(smt_bytes), "config_sha256": sha(config_bytes),
        "certificate_index_sha256": sha(index_bytes),
        "source_sha256": {name: sha(value) for name, value in source_bytes.items()},
        "bound": B, "row_local_margin": [1, B],
        "base_assertions": {"fixed_minima": 3, "row_local_gaps": 26,
                            "nonminimum_upper_bounds": 21, "strict_cross_row_totals": 2, "total": 52},
        "learned_clauses": len(learned), "total_assertions": len(assertions),
        "certificates_verified": len(receipts), "coverage_scopes": dict(scope_counts),
        "unperturbed_model_domain_and_membership_checks": metadata_count,
        "maximum_retained_premise_coefficient": maximum_coefficient,
        "conic_identities_checked": sum(r["conic_identities"] for r in receipts),
        "boolean_states_checked": sum(r["propositional_states"] for r in receipts),
        "max_boolean_states": max(r["propositional_states"] for r in receipts),
        "scope": "Every frozen prefix certificate, its compatible ninth-column domain, weak row-local background, and the exact delta-complement assertion are independently checked. All 52 domain assertions match. New original SMT points satisfy the bounded domain and each learned region. A full counterexample implies a model outside every such finite valid family; SAT of this relaxation is not a counterexample. No solver verdict or global coverage proof is produced by this audit.",
        "receipts": receipts,
    }
    (output_directory / "bounded_prefix_snapshot_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot")
    parser.add_argument("--output-directory")
    args = parser.parse_args()
    snapshot = Path(args.snapshot)
    if not snapshot.is_absolute():
        snapshot = ROOT / snapshot
    output_directory = OUT
    if args.output_directory:
        output_directory = Path(args.output_directory)
        if not output_directory.is_absolute():
            output_directory = ROOT / output_directory
        output_directory.mkdir(parents=True, exist_ok=True)
    report = audit(snapshot, output_directory)
    print(json.dumps({k: v for k, v in report.items() if k != "receipts"}, indent=2))


if __name__ == "__main__":
    main()
