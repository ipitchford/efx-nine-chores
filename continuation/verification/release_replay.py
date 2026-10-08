#!/usr/bin/env python3
"""Replay the explicit release certificate index using only Python's stdlib.

No solver, package installation, network access, or mutation fixtures are used.
Each mathematical audit runs in its own process with a 480 MiB/29 s guard.
Fresh output directories preserve every historical receipt byte for byte.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(value).hexdigest()


def package_path(value):
    path = Path(value)
    assert not path.is_absolute() and ".." not in path.parts
    return ROOT / path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="continuation/verification/release_certificate_index.json")
    parser.add_argument("--output-directory")
    parser.add_argument("--phase", choices=("certificates", "zero-formula", "all"), default="certificates")
    args = parser.parse_args()
    started = time.monotonic()
    index_file = package_path(args.index)
    index_bytes = index_file.read_bytes()
    index = json.loads(index_bytes)
    assert index["format_version"] == 1
    assert index["mutation_fixtures_included"] is False
    for item in index["prefix_certificates"] + index["row_certificates"]:
        name = item["file"]
        assert "float_unsound" not in name and "mutation" not in name
        assert sha(package_path(name).read_bytes()) == item["sha256"], name
    for name, digest in index["bound_files"].items():
        assert sha(package_path(name).read_bytes()) == digest, name
    if args.output_directory:
        output = package_path(args.output_directory)
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = HERE / f"release_replay_{stamp}"
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
        "index": str(index_file.relative_to(ROOT)), "index_sha256": sha(index_bytes),
        "python": sys.version, "phase": args.phase,
        "prefix_certificates_indexed": len(index["prefix_certificates"]),
        "row_certificates_indexed": len(index["row_certificates"]),
        "bound_files_checked": len(index["bound_files"]), "audits": [],
        "scope": "Exact local certificates and their bound input formulas only; no solver or global existence verdict. Mutation fixtures are excluded by the explicit index.",
    }

    def save():
        (output / "release_replay.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, arguments, receipt):
        start = time.monotonic()
        command = [sys.executable, *arguments]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30)
        (output / f"{name}.log").write_text(completed.stdout + completed.stderr)
        assert completed.returncode == 0, (name, completed.returncode, completed.stderr[-3000:])
        receipt_path = output / receipt
        value = json.loads(receipt_path.read_text())
        assert value["status"].startswith("PASS"), (name, value.get("status"))
        report["audits"].append({"name": name, "status": value["status"],
                                  "elapsed_seconds": time.monotonic() - start,
                                  "receipt": str(receipt_path.relative_to(ROOT)),
                                  "receipt_sha256": sha(receipt_path.read_bytes())})
        save()
        print(json.dumps(report["audits"][-1]), flush=True)

    save()
    try:
        output_name = str(output.relative_to(ROOT))
        if args.phase in ("certificates", "all"):
            run("bounded_prefix", ["continuation/verification/audit_bounded_prefix_snapshot.py",
                                   index["prefix_snapshot"], "--output-directory", output_name],
                "bounded_prefix_snapshot_audit.json")
            row_args = ["continuation/verification/audit_final_row_snapshot.py", index["row_manifest"],
                        "--output", output_name + "/row_snapshot_audit.json", "--replay-prior"]
            if index.get("row_pruning_receipt"):
                row_args += ["--pruning-receipt", index["row_pruning_receipt"]]
            for value in index.get("extra_minimized_receipts", []):
                row_args += ["--minimized-receipt", value]
            run("row_snapshot", row_args, "row_snapshot_audit.json")
        if args.phase in ("zero-formula", "all"):
            assert index.get("zero_minimum9")
            run("zero_minimum9_formula", ["continuation/verification/audit_zero_minimum_formula.py", "9",
                                         "--output", output_name + "/zero_minimum9_formula_audit.json"],
                "zero_minimum9_formula_audit.json")
        report.update(status="PASS_RELEASE_LOCAL_CERTIFICATES_AND_INPUT_BINDING_NO_GLOBAL_VERDICT",
                      finished_utc=datetime.now(timezone.utc).isoformat(),
                      elapsed_seconds=time.monotonic() - started)
        save()
        print(json.dumps({k: v for k, v in report.items() if k != "audits"}, indent=2))
    except BaseException as error:
        report.update(status="FAIL_RELEASE_REPLAY", error=repr(error),
                      elapsed_seconds=time.monotonic() - started)
        save()
        raise


if __name__ == "__main__":
    main()
