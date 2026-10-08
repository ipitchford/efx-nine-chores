"""Exact, solver-free controls for zero-minimum normalization and its bound."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
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


def violations(rows, allocation, skip_owned_zero=False):
    result = []
    bundles = [[g for g, owner in enumerate(allocation) if owner == i] for i in range(3)]
    for i, owned in enumerate(bundles):
        for g in owned:
            if skip_owned_zero and rows[i][g] == 0:
                continue
            residual = sum(rows[i][h] for h in owned if h != g)
            for j in range(3):
                if i != j:
                    margin = residual - sum(rows[i][h] for h in bundles[j])
                    if margin > 0:
                        result.append({"agent": i, "target": j, "deleted": g, "margin": str(margin)})
    return result


def main():
    integers = [
        [0, 2, 4, 200, 12, 10, 8, 6, 5],
        [100, 0, 101, 102, 1, 2, 103, 104, 105],
        [100, 101, 0, 102, 103, 104, 1, 2, 3],
    ]
    allocation = [0, 1, 2, 0, 1, 1, 2, 2, 2]
    literal_failures = violations(integers, allocation)
    assert literal_failures == [
        {"agent": 0, "target": 1, "deleted": 0, "margin": "176"},
        {"agent": 0, "target": 2, "deleted": 0, "margin": "177"},
    ]
    assert not violations(integers, allocation, skip_owned_zero=True)
    references = [1, 0, 0]
    normalized = [[Fraction(v, row[references[i]]) for v in row] for i, row in enumerate(integers)]
    assert all(row[i] == 0 and row[references[i]] == 1 for i, row in enumerate(normalized))
    assert all(len(set(row)) == 9 for row in normalized)
    assert normalized[0][1] < normalized[0][2]
    assert all(normalized[0][g] > normalized[0][g + 1] for g in range(3, 8))
    assert violations(normalized, allocation) and not violations(normalized, allocation, True)
    bounds = {}
    for m in (8, 9):
        square = (m - 2) * (m - 1)**(m - 2)
        bound = isqrt(square)
        assert bound**2 <= square < (bound + 1)**2
        maximum_row_sum = (m - 1) * bound
        cost_width = bound.bit_length()
        sum_width = maximum_row_sum.bit_length()
        assert bound < 2**cost_width and maximum_row_sum < 2**sum_width
        bounds[str(m)] = {"row_dimension": m - 1, "max_constraint_support": m - 2,
                          "numerator_bound_squared": square, "bound": bound,
                          "lower_square": bound**2, "upper_square": (bound + 1)**2,
                          "cost_width": cost_width, "sum_width": sum_width,
                          "maximum_row_sum": maximum_row_sum}
    assert bounds["9"]["bound"] == 3831 and bounds["9"]["sum_width"] == 15
    assert bounds["8"]["bound"] == 840
    bundle_checks = 0
    for i, zero_row in enumerate(integers):
        positive = [v * 3 + 1 for v in zero_row]
        lowered = list(positive)
        lowered[i] = 0
        assert positive[i] == min(positive) == 1
        for mask in range(1, 1 << 9):
            owned = [g for g in range(9) if mask >> g & 1]
            old_residuals = [sum(positive[h] for h in owned if h != g) for g in owned]
            new_residuals = [sum(lowered[h] for h in owned if h != g) for g in owned]
            assert max(old_residuals) == max(new_residuals)
            assert max(old_residuals) == sum(positive[g] for g in owned) - min(positive[g] for g in owned)
            if len(owned) >= 2:
                assert max(new_residuals) > 0
            bundle_checks += 1
    report = {
        "status": "PASS_EXACT_ZERO_MINIMUM_BOUND_AND_ZERO_DELETION_CONTROLS",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "bounds": bounds,
        "owned_bundle_residual_checks": bundle_checks,
        "zero_deletion_mutation_fixture": {"rows": integers, "allocation": allocation,
                                           "literal_failures": literal_failures,
                                           "skip_owned_zero_mutant_accepts": True,
                                           "normalized_references": references,
                                           "normalized_rows": [[str(v) for v in row] for row in normalized]},
        "mathematical_argument": "Lowering only a row's minimum coordinate to zero leaves every maximum owned-deletion residual unchanged and decreases all target-bundle sums; EFX after lowering implies EFX before lowering. One zero per row allows empty-bundle allocations to be omitted for m>n. The eight positive variables admit independent row-local Cramer bounds; one numerator row has squared norm at most seven and the other seven at most eight.",
        "scope": "Exact arithmetic, all 511 nonempty owned-bundle shapes for each of three fixture rows, and a definition-sensitive false-acceptance control were checked. These checks supplement the general proof; no search or global counterexample claim is made.",
    }
    (OUT / "zero_minimum_normalization_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
