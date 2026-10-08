"""Test a stronger structural hypothesis about prescribed-EF failure.

Input: exact pre-existing reduced P8 formula. The prescribed row's cheapest
chore is shared with agent 1, but its second-cheapest is NOT agent 2's
cheapest. Free columns are already strictly ordered by row 0 in this input,
so column 2 must be its second-cheapest. No conclusion follows from UNKNOWN.
"""
import hashlib
import json
import resource
import time
from pathlib import Path

resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
import z3

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "work/structural_designated_reduced_m8_seed0.standard.smt2"
beg = time.monotonic()
s = z3.SolverFor("QF_LRA")
s.set(timeout=120000, **{"arith.solver": 2})
s.add(z3.parse_smt2_file(str(SOURCE)))
c = [[z3.Real(f"c_{i}_{g}") for g in range(8)] for i in range(3)]
s.add(c[0][0] < c[0][2], c[0][2] < c[0][1])
formula = OUT / "p8_second_min.smt2"
formula.write_text(s.to_smt2())
start = time.monotonic()
result = s.check()
record = dict(
    result=str(result), source=str(SOURCE.relative_to(ROOT)),
    source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    assertions=len(s.assertions()), build_seconds=start-beg,
    check_seconds=time.monotonic()-start,
    scope="P8 failure with prescribed minimum shared with agent 1 but prescribed second minimum not agent 2 minimum",
)
if result == z3.unknown:
    record["reason"] = s.reason_unknown()
elif result == z3.sat:
    model = s.model()
    record["matrix"] = [[str(model.eval(x)) for x in row] for row in c]
record["statistics"] = str(s.statistics())
(OUT / "p8_second_min.json").write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2), flush=True)
