"""Bounded source and targeted boundary checks; never calls a solver."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from math import isqrt
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
SOURCE = ROOT / "continuation/bitvector_search.py"
source_bytes = SOURCE.read_bytes()
spec = importlib.util.spec_from_file_location("inspected_bitvector_search", SOURCE)
encoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(encoder)
z3 = encoder.z3


def sha(value):
    return hashlib.sha256(value).hexdigest()


def selected_failures(rows, assignment, mutate_free_trim=False):
    answer = []
    for i in range(3):
        owned = [g for g, owner in enumerate(assignment) if owner == i]
        trims = encoder.minimum_candidates(i, owned)
        if mutate_free_trim and i == 0 and 0 not in owned:
            fixed = [g for g in owned if g in (1, 2)]
            free = [g for g in owned if g >= 3]
            trims = ([min(fixed)] if fixed else []) + ([min(free)] if free else [])
        for removed in trims:
            left = sum(rows[i][g] for g in owned if g != removed)
            for j in range(3):
                if i != j:
                    right = sum(
                        rows[i][g] for g, owner in enumerate(assignment) if owner == j
                    )
                    if left > right:
                        answer.append((i, j, removed, left - right))
    return answer


def main():
    widths = {}
    for m in (8, 9):
        bound = isqrt((m - 1) ** m)
        cw, sw = bound.bit_length(), (m * bound).bit_length()
        assert bound <= (1 << cw) - 1
        assert m * bound <= (1 << sw) - 1
        assert sw >= cw
        value = z3.BitVecVal(bound, cw)
        extended = z3.ZeroExt(sw - cw, value)
        full = sum([extended] * m, z3.BitVecVal(0, sw))
        assert z3.simplify(full).as_long() == m * bound
        widths[str(m)] = {
            "bound": bound, "cost_width": cw, "sum_width": sw,
            "largest_possible_subset_sum": m * bound,
            "largest_representable_sum": (1 << sw) - 1,
        }

    # Nine-chores boundary: six high-cost residual items can cross the
    # signed midpoint of the correct 17-bit sum width.
    bound = 11585
    value = z3.BitVecVal(bound, 14)
    widened = z3.ZeroExt(3, value)
    six = sum([widened] * 6, z3.BitVecVal(0, 17))
    assert z3.simplify(six).as_long() == 69510
    unsigned_correct = z3.is_true(z3.simplify(z3.UGT(six, widened)))
    signed_mutant = z3.is_true(z3.simplify(six > widened))
    narrow_six = sum([value] * 6, z3.BitVecVal(0, 14))
    unwidened_mutant = z3.is_true(z3.simplify(z3.UGT(narrow_six, value)))
    assert unsigned_correct and not signed_mutant and not unwidened_mutant

    # Only the last free item is the cheapest owned chore in row 0.
    rows = [
        [1, 2, 6, 10, 9, 8, 7, 5, 4],
        [2, 1, 2, 2, 2, 2, 2, 2, 2],
        [2, 3, 1, 12, 4, 10, 11, 5, 13],
    ]
    allocation = [2, 2, 0, 0, 2, 1, 1, 2, 0]
    assert encoder.minimum_candidates(0, [2, 3, 8]) == [2, 8]
    failures = selected_failures(rows, allocation)
    assert failures == [(0, 1, 8, 1)]
    assert not encoder.literal_good(rows, allocation)
    assert selected_failures(rows, allocation, mutate_free_trim=True) == []

    calibration_path = ROOT / "continuation/exact_search/bitvector8_rowwise.json"
    audit_path = ROOT / "continuation/exact_search/bitvector8_rowwise.audit.json"
    calibration_bytes, audit_bytes = calibration_path.read_bytes(), audit_path.read_bytes()
    calibration, audit = json.loads(calibration_bytes), json.loads(audit_bytes)
    assert calibration["status"] == "unknown"
    assert calibration["reason_unknown"] == "out of memory"
    assert audit["status"] == "PASS" and len(audit["fixtures"]) == 6
    assert audit["actual_bv_atoms_checked"] == 57822
    assert audit["allocation_clauses_checked"] == 34776
    formula_path = calibration_path.with_suffix(".smt2")
    assert sha(formula_path.read_bytes()) == calibration["input_sha256"]
    assert SOURCE.read_bytes() == source_bytes
    report = {
        "status": "PASS_SOURCE_WIDTH_AND_TARGETED_CONTROLS_NOT_SOLVER_VERDICT",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "z3": z3.get_version_string(),
        "source_sha256": sha(source_bytes),
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "widths": widths,
        "domain_source_review": "Positive integer entries <= derived B; distinct prescribed minimum columns; private row minima; canonical row-0 order only; no cross-row totals or common-minimum equalities.",
        "minimum_trim_source_review": "Pinned owned minimum suffices; otherwise all owned items are retained in rows 1 and 2; row 0 retains the least item of each of its two ordered chains.",
        "unsigned_boundary_control": {
            "residual": 69510, "comparison": 11585,
            "correct_unsigned_result": unsigned_correct,
            "signed_comparison_mutant_result": signed_mutant,
            "unwidened_sum_mutant_result": unwidened_mutant,
        },
        "free_chain_trim_control": {
            "rows": rows, "allocation": allocation,
            "unique_literal_failure": list(failures[0]),
            "wrong_free_chain_endpoint_would_miss_failure": True,
        },
        "prior_calibration": {
            "receipt_sha256": sha(calibration_bytes),
            "audit_sha256": sha(audit_bytes),
            "input_sha256": calibration["input_sha256"],
            "verdict": calibration["status"],
            "reason": calibration["reason_unknown"],
            "check_seconds": calibration["check_seconds"],
            "peak_rss_kib": calibration["peak_rss_kib"],
            "audit_fixtures": 6, "actual_bv_atoms_checked": 57822,
            "allocation_clauses_checked": 34776,
        },
        "scope": "Full encoder source inspected; only tiny bit-vector arithmetic controls and one minimum-trim mutation fixture executed here. Existing eight-chore calibration was not rerun. No complete nine-chore BV formula was built and no solver.check call was made.",
    }
    (OUT / "bitvector_source_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
