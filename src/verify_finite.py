#!/usr/bin/env python3
"""Standalone exact finite verification; Python standard library only.

This verifies a counterexample to the prescribed-agent strengthening at
eight chores. It does NOT claim a counterexample to ordinary EFX: the
displayed matrix has 36 ordinary EFX allocations.

All allocations are complete labelled allocations. Empty bundles remain
included, and zero-cost owned chores remain quantified in every EFX check.

Example:
  python src/verify_finite.py --out results/finite_verification.json
"""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path


P8_MATRIX = (
    (35, 48, 55, 239, 247, 304, 332, 500),
    (3, 15, 24, 136, 358, 171, 500, 294),
    (20, 4, 7, 235, 166, 500, 56, 203),
)


def allocation_from_id(identifier, chores):
    """Lexicographic base-three coding, chore 0 the most significant digit."""
    owners = [0] * chores
    for chore in range(chores - 1, -1, -1):
        identifier, owners[chore] = divmod(identifier, 3)
    assert identifier == 0
    return owners


def classify(matrix, owners, skip_zero_removals=False):
    bundles = [[g for g, owner in enumerate(owners) if owner == i]
               for i in range(3)]
    costs = [[sum(matrix[i][g] for g in bundles[j]) for j in range(3)]
             for i in range(3)]
    failure = None
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            for g in bundles[i]:
                if skip_zero_removals and matrix[i][g] == 0:
                    continue
                left = costs[i][i] - matrix[i][g]
                right = costs[i][j]
                if left > right:
                    failure = dict(kind="efx", agent=i, other=j,
                                   removed_chore=g, lhs=left, rhs=right)
                    break
            if failure is not None:
                break
        if failure is not None:
            break
    ordinary = [all(costs[i][i] <= costs[i][j] for j in range(3) if j != i)
                for i in range(3)]
    return failure is None, ordinary, failure, bundles, costs


def enumerate_matrix(matrix, make_failure_certificate=False,
                     skip_zero_removals=False):
    assert len(matrix) == 3
    chores = len(matrix[0])
    assert all(len(row) == chores for row in matrix)
    assert all(isinstance(v, int) and v >= 0 for row in matrix for v in row)
    efx_count = 0
    designated_counts = [0, 0, 0]
    first_efx = None
    first_designated = [None, None, None]
    failures = []
    for identifier, owners in enumerate(itertools.product(range(3), repeat=chores)):
        efx, ordinary, failure, bundles, costs = classify(
            matrix, owners, skip_zero_removals=skip_zero_removals)
        if efx:
            efx_count += 1
            witness = dict(allocation_id=identifier, owners=list(owners),
                           bundles=bundles)
            if first_efx is None:
                first_efx = witness
            for i in range(3):
                if ordinary[i]:
                    designated_counts[i] += 1
                    if first_designated[i] is None:
                        first_designated[i] = witness
        if make_failure_certificate:
            if not ordinary[0]:
                other = next(j for j in (1, 2) if costs[0][0] > costs[0][j])
                reason = dict(kind="ordinary_ef", agent=0, other=other,
                              removed_chore=-1, lhs=costs[0][0],
                              rhs=costs[0][other])
            else:
                assert failure is not None, "The alleged P8 counterexample has a witness"
                reason = failure
            failures.append(dict(allocation_id=identifier, **reason))
    result = dict(agents=3, chores=chores, allocations_checked=3 ** chores,
                  efx_allocations=efx_count,
                  prescribed_ordinary_ef_counts=designated_counts,
                  first_efx_witness=first_efx,
                  first_prescribed_ordinary_ef_witnesses=first_designated)
    return result, failures


def write_certificate(path, failures):
    fields = ("allocation_id", "kind", "agent", "other", "removed_chore", "lhs", "rhs")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(failures)


def replay_certificate(path, matrix):
    """Check recorded local inequalities directly, without classify()."""
    chores = len(matrix[0])
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for expected_id, record in enumerate(reader):
            identifier = int(record["allocation_id"])
            assert identifier == expected_id
            owners = allocation_from_id(identifier, chores)
            agent, other = int(record["agent"]), int(record["other"])
            removed = int(record["removed_chore"])
            assert 0 <= agent < 3 and 0 <= other < 3 and agent != other
            if record["kind"] == "ordinary_ef":
                assert agent == 0 and removed == -1
                left = sum(matrix[agent][g] for g in range(chores)
                           if owners[g] == agent)
            else:
                assert record["kind"] == "efx"
                assert 0 <= removed < chores and owners[removed] == agent
                left = sum(matrix[agent][g] for g in range(chores)
                           if owners[g] == agent and g != removed)
            right = sum(matrix[agent][g] for g in range(chores)
                        if owners[g] == other)
            assert left == int(record["lhs"])
            assert right == int(record["rhs"])
            assert left > right
        rows_checked = expected_id + 1
    assert rows_checked == 3 ** chores
    return dict(status="PASS", local_inequalities_checked=rows_checked,
                allocation_coding="base 3; chore 0 is the most significant digit",
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/finite_verification.json")
    parser.add_argument("--certificate")
    args = parser.parse_args()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    certificate = (Path(args.certificate) if args.certificate else
                   output.with_name("p8_designated_failure_certificate.csv"))
    certificate.parent.mkdir(parents=True, exist_ok=True)

    small, failures = enumerate_matrix(P8_MATRIX, make_failure_certificate=True)
    assert small["allocations_checked"] == 6561
    assert small["efx_allocations"] == 36
    assert small["prescribed_ordinary_ef_counts"] == [0, 31, 31]
    assert small["first_efx_witness"] is not None
    write_certificate(certificate, failures)
    certificate_check = replay_certificate(certificate, P8_MATRIX)

    uniform, _ = enumerate_matrix(((1,) * 9,) * 3)
    multinomial = math.factorial(9) // math.factorial(3) ** 3
    assert multinomial == 1680
    assert uniform["allocations_checked"] == 19683
    assert uniform["efx_allocations"] == multinomial
    assert uniform["prescribed_ordinary_ef_counts"] == [1680, 1680, 1680]

    all_zero, _ = enumerate_matrix(((0,) * 9,) * 3)
    assert all_zero["allocations_checked"] == 19683
    assert all_zero["efx_allocations"] == 19683
    assert all_zero["prescribed_ordinary_ef_counts"] == [19683] * 3

    # Mutant: silently omit removals of owned zero-cost chores. Both the
    # chosen allocation and the complete finite count distinguish it.
    zero_control_matrix = ((0, 1, 1),) * 3
    zero_control_owners = (0, 0, 1)
    exact = classify(zero_control_matrix, zero_control_owners)
    mutant = classify(zero_control_matrix, zero_control_owners,
                      skip_zero_removals=True)
    assert exact[0] is False and mutant[0] is True
    assert exact[2] == dict(kind="efx", agent=0, other=2, removed_chore=0,
                            lhs=1, rhs=0)
    exact_zero_count, _ = enumerate_matrix(zero_control_matrix)
    mutant_zero_count, _ = enumerate_matrix(zero_control_matrix,
                                           skip_zero_removals=True)
    assert exact_zero_count["efx_allocations"] == 6
    assert mutant_zero_count["efx_allocations"] == 18

    result = dict(
        status="PASS",
        checker_version="1.0",
        arithmetic="exact integer arithmetic; Python standard library only",
        efx_convention="all owned chores quantified, including zero-cost chores",
        small_p8_matrix=[list(row) for row in P8_MATRIX],
        small_p8=small,
        p8_failure_certificate=dict(path=str(certificate), **certificate_check),
        uniform_nine=uniform,
        uniform_count_identity="9! / (3!^3) = 1680",
        all_zero_nine=all_zero,
        zero_quantifier_mutation_control=dict(
            status="MUTANT_REJECTED", matrix=[list(row) for row in zero_control_matrix],
            owners=list(zero_control_owners), complete_efx=exact[0],
            positive_only_mutant_efx=mutant[0], exact_failure=exact[2],
            complete_efx_count=exact_zero_count["efx_allocations"],
            positive_only_mutant_efx_count=mutant_zero_count["efx_allocations"]),
        limitation="The eight-chore matrix refutes the prescribed-agent strengthening only; it has 36 EFX allocations and does not refute nine-chore EFX."
    )
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", small_p8_efx=36,
                          prescribed_counts=[0, 31, 31], uniform_nine_efx=1680,
                          all_zero_nine_efx=19683,
                          zero_quantifier_mutant="REJECTED", output=str(output),
                          certificate=str(certificate)), indent=2))


if __name__ == "__main__":
    main()
