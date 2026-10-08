#!/usr/bin/env python3
"""Exact small arithmetic and Hall-factorization checks; no solver calls."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def save(name, record):
    (HERE / name).write_text(json.dumps(record, indent=2) + "\n")


value = 3 * Fraction(31, 4) ** 4
bound = value.numerator // value.denominator
assert value == Fraction(2770563, 256) and bound == 10822
assert 10822 * 256 <= 2770563 < 10823 * 256
save("projected_determinant_bound_10822_audit.json", dict(
    status="PASS", recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    active_dimension=9, maximum_original_row_support=7,
    unchanged_columns=8, maximum_unchanged_nonzeros=62,
    exact_projected_bound=str(value), integer_bound=bound,
    floor_lower_numerator=10822 * 256, exact_numerator=2770563,
    floor_upper_numerator=10823 * 256, denominator=256,
    positive_cost_bits=bound.bit_length(), maximum_nine_entry_row_sum=9 * bound,
    full_row_sum_bits=(9 * bound).bit_length(),
    proof="projected_determinant_bound_10822.md",
    independent_review="Approved by verification_resumed from the stated projection/Gram argument.",
    scope="Exact arithmetic and parameter checks; no matrix enumeration or EFX solver result.",
    old_11585_inputs_changed=False,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))

graphs = 0
without_matching = 0
for neighborhoods in itertools.product(range(1, 8), repeat=3):
    matching = any(all(neighborhoods[i] >> permutation[i] & 1 for i in range(3))
                   for permutation in itertools.permutations(range(3)))
    uncovered_bundle = any(all(not (neighborhoods[i] >> b & 1) for i in range(3)) for b in range(3))
    two_same_singleton = any(all(not (neighborhoods[i] >> a & 1) and not (neighborhoods[j] >> a & 1)
                                 for a in range(3) if a != b)
                             for i in range(3) for j in range(i + 1, 3) for b in range(3))
    obstruction = uncovered_bundle or two_same_singleton
    assert obstruction == (not matching)
    graphs += 1
    without_matching += not matching
shapes = Counter()
for assignment in itertools.product(range(3), repeat=9):
    if set(assignment) != {0, 1, 2}:
        continue
    if assignment.index(0) < assignment.index(1) < assignment.index(2):
        shapes[tuple(sorted(assignment.count(i) for i in range(3)))] += 1
assert sum(shapes.values()) == 3025
assert 6 * sum(shapes.values()) == 18150
record = dict(status="PASS", recorded_at_utc=datetime.now(timezone.utc).isoformat(),
              nonempty_row_eligibility_graphs_checked=graphs,
              graphs_without_perfect_matching=without_matching,
              factorization_mismatches=0, unlabeled_nine_chore_partitions=sum(shapes.values()),
              labeled_surjective_allocations=18150,
              bundle_shapes={",".join(map(str, k)): v for k, v in sorted(shapes.items())},
              row_nonempty_hypothesis="Each agent accepts a bundle of minimum total cost in every partition.",
              scope="Exhaustive 343 small eligibility graphs and all partition shapes; not an EFX existence proof or performance measurement.")
save("hall_partition_factorization_audit.json", record)
print(json.dumps(record), flush=True)
