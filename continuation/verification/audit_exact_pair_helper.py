"""Small exact controls for the direct pair helper; no census or solver run."""
from datetime import datetime, timezone
from fractions import Fraction
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


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    source = ROOT / "continuation/structural_nine/exact_pair_core.py"
    checker_file = ROOT / "continuation/verify_row_cores.py"
    source_bytes, checker_bytes = source.read_bytes(), checker_file.read_bytes()
    helper = load("direct_pair_helper_review", source)
    checker = load("direct_pair_independent_checker", checker_file)
    domain = helper.domain_rows()
    indices = [0, 1, 9, 8, 10, 11, 12, 13, 14]
    for g in range(9):
        basis = tuple(int(h == g) for h in range(9))
        coefficients = helper.gaps(basis)
        assert tuple(
            sum(coefficients[k] * domain[index][h] for k, index in enumerate(indices))
            for h in range(9)
        ) == basis
    fixture_file = OUT / "row_regions_frozen_20261007/regions/compressed_00000.json"
    fixture_bytes = fixture_file.read_bytes()
    fixture = json.loads(fixture_bytes)
    # Deliberately verify the returned Python object directly: the former
    # tuple/list interface problem must not be hidden by JSON conversion.
    cert = helper.certify(fixture)
    certificate_receipt = checker.verify(cert)
    rows = [[2 if g != i else 1 for g in range(9)] for i in (1, 2)]
    generic, meta = helper.generic_rows(rows)
    assert meta["scale"] == 3281
    assert all(sum(d) == 3280 for d in meta["directions"])
    rejected = []
    for name, changed in (
        ("floating_entry", [[1.5] + rows[0][1:], list(rows[1])]),
        ("missing_row", [list(rows[0])]),
        ("zero_entry", [[0] + rows[0][1:], list(rows[1])]),
    ):
        try:
            helper.generic_rows(changed)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError(("Invalid generic-row input accepted", name))
    previous = ROOT / "continuation/structural_nine/on_demand_pair_validation.json"
    prior_bytes = previous.read_bytes()
    assert source.read_bytes() == source_bytes
    assert checker_file.read_bytes() == checker_bytes
    report = {
        "status": "PASS_EXACT_MAPPING_INTERFACE_AND_INPUT_CONTROLS_NO_CENSUS_REPLAY",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "source_sha256": sha(source_bytes),
        "checker_sha256": sha(checker_bytes),
        "basis_identities_checked": 9,
        "gap_to_domain_indices": indices,
        "in_memory_certificate_fixture": {
            "file": str(fixture_file.relative_to(ROOT)),
            "sha256": sha(fixture_bytes), **certificate_receipt,
        },
        "invalid_inputs_rejected": rejected,
        "generic_sign_argument": "For integral rows and q in {-1,0,1}^9, |q.d| <= 3280 < 3281 preserves every nonzero old sign. Balanced ternary uniqueness removes zero signs with an unpinned coefficient; positivity handles vectors supported only at the pinned coordinate.",
        "branch_argument": "Componentwise impossible atoms are handled separately. Otherwise normalize the second atom weight to one and intersect the exact lower/upper constraints for a nonnegative first weight; the resulting combination is nonpositive in every positive gap.",
        "previous_sample_receipt_sha256": sha(prior_bytes),
        "scope": "Full helper source and mathematical arguments reviewed. Nine basis identities, one direct in-memory certificate, one generic transform and three input guards were checked. The recorded 500-pair/census sampling was not repeated, and exhaustive census certification is not claimed.",
    }
    (OUT / "exact_pair_helper_review.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
