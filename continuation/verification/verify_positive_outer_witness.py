"""Check an exact positive integer witness outside all final row regions.

This is a model of the two-row relaxation, not a three-agent counterexample.
It gives a concrete noncoverage witness for the currently frozen finite family.
"""
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

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
START = time.monotonic()
resource.setrlimit(resource.RLIMIT_AS, (480 * 1024**2,) * 2)
signal.alarm(29)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location("positive_outer_affine", HERE / "audit_row_compression.py")
    syntax = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(syntax)
    spec2 = importlib.util.spec_from_file_location("positive_outer_streaming", HERE / "audit_zero_minimum_formula.py")
    streaming = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(streaming)
    signal.setitimer(signal.ITIMER_REAL, max(0.01, 29 - (time.monotonic() - START)))
    model_file = ROOT / "continuation/structural_nine/zero_outer/run1_model.json"
    model_bytes = model_file.read_bytes()
    model = json.loads(model_bytes)
    zero_values = {k: Fraction(v) for k, v in model["coordinates"].items()}
    rows = []
    for i in (1, 2):
        values = [Fraction(1) if g == 0 else Fraction(0) if g == i else zero_values[f"c_{i}_{g}"] for g in range(9)]
        values[i] = Fraction(1, 304)
        scaled = [v * 304 for v in values]
        assert all(v.denominator == 1 for v in scaled)
        rows.append([v.numerator for v in scaled])
    assert rows == [[304, 1, 8, 1524, 860, 882, 216, 84, 120],
                    [304, 6, 1, 1002, 726, 902, 228, 36, 56]]
    vector = [v for row in rows for v in row] + [1]
    source = ROOT / "continuation/structural_nine/row_elimination_batch1/outer_final.smt2"
    digest = sha(source.read_bytes())
    index = json.loads((HERE / "release_certificate_index.json").read_text())
    assert digest == index["row_formula_sha256"]
    declarations, assertions, learned, checks = set(), 0, 0, 0
    margins = []
    for command in streaming.commands(source):
        op = command[0]
        if op == "declare-fun":
            assert command[2:] == [[], "Real"]
            declarations.add(command[1])
        elif op == "check-sat":
            assert command == ["check-sat"]
            checks += 1
        elif op == "set-logic":
            assert command == ["set-logic", "QF_LRA"]
        else:
            assert op == "assert" and len(command) == 2
            relation, form = syntax.boolform(streaming.expand_let(command[1]))
            if relation == "or":
                candidates = []
                for rel, coefficients in form:
                    assert rel == ">"
                    candidates.append(sum(a * b for a, b in zip(coefficients, vector)))
                assert candidates and max(candidates) > 0, assertions
                margins.append(max(candidates))
                learned += 1
            else:
                value = sum(a * b for a, b in zip(form, vector))
                assert (relation == "=" and value == 0) or (relation == ">" and value > 0), assertions
            assertions += 1
    assert len(declarations) == 18 and declarations == set(syntax.VARS)
    assert checks == 1 and assertions == 6309 and learned == 6291
    assert sha(source.read_bytes()) == digest and sha(model_file.read_bytes()) == sha(model_bytes)
    report = {
        "status": "PASS_EXACT_POSITIVE_OUTER_NONCOVERAGE_WITNESS_ONLY",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "input": str(source.relative_to(ROOT)), "input_sha256": digest,
        "source_zero_model": str(model_file.relative_to(ROOT)), "source_zero_model_sha256": sha(model_bytes),
        "rows_1_and_2": rows, "exact_assertions_checked": assertions,
        "learned_region_exclusions_checked": learned,
        "smallest_maximum_exclusion_margin": str(min(margins)),
        "current_frozen_row_region_family_is_not_complete": True,
        "main_target_counterexample": False,
        "scope": "These two positive integer cost rows have their pinned minima exactly one and satisfy every assertion in the original final two-row relaxation. Thus the currently frozen 6,291 sufficient regions do not cover its canonical two-row domain. No first row is supplied; this is not a three-agent instance without EFX, and the universal nine-chore problem remains unresolved.",
        "script_sha256": sha(Path(__file__).read_bytes()),
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (HERE / "positive_outer_noncoverage_witness.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
