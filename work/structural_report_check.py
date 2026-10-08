"""Review the report's actual literal tables using exact arithmetic.

Does not import the report builder, allocation checker, or solver encoders.
Only the standard library is used. This is a bounded document consistency
check, not a solver or a proof of the universal nine-chore statement.
"""
import ast
from collections import defaultdict
from itertools import product
import hashlib
import json
from pathlib import Path
import platform
import re
import time

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.perf_counter()
    builder = ROOT / "src/build_report.py"
    tree = ast.parse(builder.read_text())
    matrix_tree = ast.parse((ROOT / "src/verify_finite.py").read_text())
    C = next(ast.literal_eval(n.value) for n in matrix_tree.body
             if isinstance(n, ast.Assign) and any(
                 isinstance(t, ast.Name) and t.id == "P8_MATRIX" for t in n.targets))
    tables = {}
    equations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id == "eq":
            equations.append(ast.literal_eval(node.args[0]))
        if node.func.id == "table":
            try:
                headers, rows = map(ast.literal_eval, node.args[:2])
            except (ValueError, TypeError):
                continue
            tables[headers[0]] = rows

    groups = defaultdict(list)
    counts = [0, 0, 0]
    efx_count = 0
    for owners in product(range(3), repeat=8):
        A = [[g for g in range(8) if owners[g] == i] for i in range(3)]
        V = [[sum(C[i][g] for g in A[j]) for j in range(3)] for i in range(3)]
        if all(V[i][i] - C[i][g] <= V[i][j]
               for i in range(3) for g in A[i] for j in range(3) if i != j):
            efx_count += 1
            for i in range(3):
                counts[i] += all(V[i][i] <= V[i][j] for j in range(3))
            groups[tuple(g + 1 for g in A[0])].append(V[0][0] - min(V[0][1:]))
    assert efx_count == 36 and counts == [0, 31, 31] and len(groups) == 10

    witness = next(e for e in equations if e.startswith(r"A_0="))
    bundles = [[int(g) - 1 for g in re.findall(r"g_(\d+)", content)]
               for content in re.findall(r"\\\{([^}]+)\\\}", witness)]
    assert len(bundles) == 3 and sorted(sum(bundles, [])) == list(range(8))
    V = [[sum(C[i][g] for g in bundles[j]) for j in range(3)] for i in range(3)]
    residual = [V[i][i] - min(C[i][g] for g in bundles[i]) for i in range(3)]
    assert tables["Evaluating agent"] == [[str(i), *V[i], residual[i]] for i in range(3)]

    # Derive the exact rectangular region for each displayed extension
    # allocation. Each deletion inequality is constant + a*x_i <= 0,
    # with a in {-1,0,1}; no solver or floating-point arithmetic is needed.
    boxes = []
    for name, *fields in tables["Case"]:
        A = [[int(g) - 1 for g in re.findall(r"\d+", f)] for f in fields[:3]]
        assert sorted(sum(A, [])) == list(range(9))
        new_owner = next(i for i in range(3) if 8 in A[i])
        lower, upper = [0] * 3, [None] * 3
        for i in range(3):
            for g in A[i]:
                for j in range(3):
                    if i == j:
                        continue
                    const = (sum(C[i][h] for h in A[i] if h != 8 and h != g)
                             - sum(C[i][h] for h in A[j] if h != 8))
                    coeff = int(new_owner == i and g != 8) - int(new_owner == j)
                    if coeff == 0:
                        assert const <= 0, (name, i, g, j, const)
                    elif coeff == -1:
                        lower[i] = max(lower[i], const)
                    else:
                        assert coeff == 1
                        upper[i] = -const if upper[i] is None else min(upper[i], -const)
        stated_lower, stated_upper = [0] * 3, [None] * 3
        for i, op, value in re.findall(r"x([012]) (<=|>=) (\d+)", fields[3]):
            i, value = int(i), int(value)
            if op == "<=":
                stated_upper[i] = value
            else:
                stated_lower[i] = value
        assert lower == stated_lower and upper == stated_upper, (name, lower, upper)
        boxes.append(dict(case=name, lower=lower, upper=upper))
    assert boxes[0]["upper"][2] >= boxes[2]["lower"][2]
    assert boxes[1]["upper"][1] >= boxes[2]["lower"][1]

    result = dict(
        status="PASS", python=platform.python_version(),
        arithmetic="exact integers; no imported report/checker/solver code",
        report_builder_sha256=digest(builder),
        ancillary_sha256=digest(ROOT / "docs/ancillary_proofs.md"),
        matrix=C, allocations_checked=3**8, efx_count=efx_count,
        prescribed_counts=counts,
        agent_zero_groups=[dict(bundle=k, count=len(v), minimum_envy_gap=min(v))
                           for k, v in sorted(groups.items())],
        displayed_witness_costs=V, displayed_witness_residuals=residual,
        extension_boxes=boxes, extension_cover="PASS; the complement of A and B implies C",
        elapsed_s=time.perf_counter()-started)
    out = ROOT / "work/structural_report_check.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
