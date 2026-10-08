"""Bind the prepared zero-minimum outer formula to the fully checked source.

Only standard-library syntax and exact affine forms are used. The unchanged
positive-minimum local certificates are inherited by their indexed hashes;
the finite-union closedness transfer is a separate mathematical argument.
No solver is imported or run.
"""
from collections import Counter
from datetime import datetime, timezone
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


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    signal.setitimer(signal.ITIMER_REAL, max(0.01, 29 - (time.monotonic() - START)))
    return result


def relocate(value):
    p = Path(value)
    if not p.is_absolute():
        return ROOT / p
    if p.is_relative_to(ROOT):
        return p
    assert p.parts.count("continuation") == 1
    return ROOT.joinpath(*p.parts[p.parts.index("continuation"):])


def main():
    syntax = module("zero_outer_affine", "audit_row_compression.py")
    streaming = module("zero_outer_streaming", "audit_zero_minimum_formula.py")
    bound = {}

    def read(p, expected=None):
        p = relocate(p)
        value = p.read_bytes()
        digest = sha(value)
        if expected is not None:
            assert digest == expected, str(p)
        bound[str(p.relative_to(ROOT))] = digest
        return value

    index = json.loads(read(HERE / "release_certificate_index.json"))
    phase_file = HERE / "release_replay_final_certificates/release_replay.json"
    phase = json.loads(read(phase_file))
    assert phase["status"] == "PASS_RELEASE_LOCAL_CERTIFICATES_AND_INPUT_BINDING_NO_GLOBAL_VERDICT"
    assert phase["phase"] == "certificates"
    assert phase["index_sha256"] == bound["continuation/verification/release_certificate_index.json"]
    row_record = next(r for r in phase["audits"] if r["name"] == "row_snapshot")
    row = json.loads(read(row_record["receipt"], row_record["receipt_sha256"]))
    assert row["prior_exact_certificates_replayed"] is True
    assert row["total_assertions"] == 6309 and row["learned_clauses"] == 6291
    assert row["distinct_core_allocation_sets"] == 2005
    original_file = relocate(index["row_formula"])
    original_bytes = read(original_file, row["outer_sha256"])
    manifest_file = relocate(index["row_manifest"])
    manifest = json.loads(read(manifest_file, row["manifest_sha256"]))
    prepared_dir = ROOT / "continuation/structural_nine/zero_outer"
    prep = json.loads(read(prepared_dir / "preparation.json"))
    new_file = prepared_dir / "zero_minimum_final_outer.smt2"
    read(new_file, prep["formula_sha256"])
    assert prep["status"] == "prepared_not_solved"
    assert prep["source_outer_sha256"] == sha(original_bytes)
    assert prep["source_manifest_sha256"] == row["manifest_sha256"]
    assert prep["substitutions"] == {"c_1_1": 0, "c_2_2": 0, "c_1_0": 1, "c_2_0": 1}
    assert prep["retained_exclusions"] == 6291

    # Reconstruct the original literal compressed predicates in their exact
    # manifest order, relying on the earlier independent compression proof.
    source_clauses = []
    for item in manifest["ordered_sources"] + manifest["ordered_new_regions"]:
        data = json.loads(read(item["source"], item["source_sha256"]))
        records = data if isinstance(data, list) else [data]
        if "records" in item:
            assert len(records) == item["records"]
        for record in records:
            atoms = record.get("compressed_region_atoms", record["region_atoms"])
            forms = []
            for atom in atoms:
                i, q = atom["agent"], atom["coefficients"]
                assert type(i) is int and i in (1, 2)
                assert len(q) == 9 and all(type(v) is int for v in q)
                vector = [0] * 19
                vector[9 * (i - 1):9 * i] = q
                forms.append((">", tuple(vector)))
            source_clauses.append(("or", frozenset(forms)))
    assert len(source_clauses) == 6291

    def forms(file):
        declarations, assertions, checks, logic = [], [], 0, 0
        for command in streaming.commands(file):
            if command[0] == "set-logic":
                assert command == ["set-logic", "QF_LRA"]
                logic += 1
            elif command[0] == "declare-fun":
                assert command[2:] == [[], "Real"]
                declarations.append(command[1])
            elif command[0] == "check-sat":
                assert command == ["check-sat"]
                checks += 1
            else:
                assert command[0] == "assert" and len(command) == 2
                e = streaming.expand_let(command[1])
                if e == "false":
                    assertions.append(("or", frozenset()))
                else:
                    assertions.append(syntax.boolform(e))
        assert checks == 1 and len(declarations) == len(set(declarations))
        return declarations, assertions, logic

    old_decl, old_forms, old_logic = forms(original_file)
    assert len(old_decl) == 18 and set(old_decl) == set(syntax.VARS)
    assert len(old_forms) == 6309 and old_logic in (0, 1)
    old_domain = []
    for i in (1, 2):
        for g in range(9):
            v = [0] * 19
            v[9 * (i - 1) + g], v[-1] = 1, -1
            old_domain.append(("=" if g == i else ">", tuple(v)))
    assert Counter(old_forms[:18]) == Counter(old_domain)
    assert old_forms[18:] == source_clauses

    def substituted(clause):
        assert clause[0] == "or"
        atoms = []
        for relation, coefficients in clause[1]:
            assert relation == ">"
            v = list(coefficients)
            v[-1] += v[0] + v[9]
            for j in (0, 1, 9, 11):
                v[j] = 0
            atoms.append((">", tuple(v)))
        return "or", frozenset(atoms)

    free = {f"c_{i}_{g}" for i in (1, 2) for g in range(9) if g not in (0, i)}
    declarations, assertions, logic = forms(new_file)
    assert len(declarations) == 14 and set(declarations) == free
    expected_domain = []
    for name in sorted(free):
        v = [0] * 19
        v[syntax.VARS[name]] = 1
        expected_domain.append((">", tuple(v)))
    assert logic == 1 and len(assertions) == 6305
    assert Counter(assertions[:14]) == Counter(expected_domain)
    actual_exclusions = [a if a[0] == "or" else ("or", frozenset([a])) for a in assertions[14:]]
    expected_exclusions = [substituted(a) for a in source_clauses]
    assert actual_exclusions == expected_exclusions
    for name, digest in bound.items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    report = {
        "status": "PASS_ZERO_OUTER_DOMAIN_AND_ALL_ORDERED_EXCLUSIONS_NO_SOLVER_VERDICT",
        "time_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "source_outer_sha256": row["outer_sha256"],
        "input": str(new_file.relative_to(ROOT)), "input_sha256": prep["formula_sha256"],
        "free_real_variables": 14, "domain_assertions": 14,
        "ordered_exclusions": 6291, "total_assertions": 6305,
        "retained_literal_positions": sum(len(c[1]) for c in expected_exclusions),
        "prior_local_certificates_replayed": False,
        "prior_complete_replay": str(phase_file.relative_to(ROOT)),
        "prior_complete_replay_sha256": sha(phase_file.read_bytes()),
        "source_binding_files": len(bound), "bound_files": bound,
        "mathematical_transfer": "For each finite allocation list K, its first-row guarantee extends to a zero minimum by continuity and a repeated allocation in a sequence of positive minima. Compression holds on the weak nonnegative-minimum cone, and positive other-row reference entries may be independently normalized to one.",
        "scope": "All original literal compressed predicates and every ordered transformed exclusion are reconstructed, source/hash-bound to the completed prior replay, and matched to the actual fresh 14-variable positive domain. This is a necessary-condition relaxation. No local certificate is recomputed, no solver is run, and no global coverage or main-target counterexample is asserted.",
        "elapsed_seconds": time.monotonic() - START,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output = HERE / "zero_outer_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "bound_files"}, indent=2))


if __name__ == "__main__":
    main()
