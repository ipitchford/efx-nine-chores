#!/usr/bin/env python3
"""Hard-supervise one separately authorized zero-minimum solve."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def save(path, record):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--m", type=int, choices=(8, 9), required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("--hard-seconds", type=int, required=True)
    parser.add_argument("--cap-mib", type=int, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--proof", action="store_true")
    args = parser.parse_args()
    output = HERE / args.name
    source = HERE / f"zero_minimum{args.m}_reference_strict.smt2"
    prep = json.loads((HERE / f"zero_minimum{args.m}_reference_preparation.json").read_text())
    audit = json.loads((HERE / f"zero_minimum{args.m}_reference_semantic_audit.json").read_text())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == prep["input_sha256"] == audit["input_sha256"]
    assert audit["status"] == "PASS"
    runner = HERE / "run_zero_minimum_z3.py"
    current = int(Path("/sys/fs/cgroup/memory.current").read_text())
    maximum = int(Path("/sys/fs/cgroup/memory.max").read_text())
    command = [sys.executable, "-u", str(runner), str(source), "--out", str(output),
               "--expected-sha256", digest, "--timeout", str(args.timeout),
               "--cap-mib", str(args.cap_mib), "--arith", "2", "--seed", "0", "--m", str(args.m)]
    if args.proof:
        command.append("--proof")
    record = dict(status="starting", started_at_utc=utcnow(), input=str(source), input_sha256=digest,
                  command=command, runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
                  supervisor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  solver_timeout_seconds=args.timeout, hard_wall_limit_seconds=args.hard_seconds,
                  address_space_cap_mib=args.cap_mib, arith_solver=2, random_seed=0,
                  proof_generation_enabled=args.proof, solver_verdict="none",
                  launch_memory_current_bytes=current, launch_memory_max_bytes=maximum,
                  launch_headroom_bytes=maximum - current, required_headroom_bytes=1 << 30,
                  hard_enforcement=["child POSIX alarm", "supervisor deadline and process-group SIGKILL"])
    target = output.with_suffix(".supervisor.json")
    save(target, record)
    save(output.with_suffix(".started.json"), record)
    print(json.dumps(record), flush=True)
    if maximum - current < 1 << 30:
        record.update(status="not_started_insufficient_memory_headroom", finished_at_utc=utcnow())
        save(target, record)
        print(json.dumps(record), flush=True)
        return
    def child_alarm():
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.alarm(args.hard_seconds)
    def child_receipt():
        try:
            return json.loads(output.with_suffix(".json").read_text())
        except (OSError, ValueError):
            return None
    started = time.monotonic()
    hard_killed = False
    with output.with_suffix(".log").open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True, preexec_fn=child_alarm)
        record.update(status="running", child_pid=process.pid, child_started_at_utc=utcnow())
        save(target, record)
        try:
            while True:
                remaining = args.hard_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        hard_killed = True
                    process.wait(timeout=5)
                    break
                try:
                    process.wait(timeout=min(5, remaining))
                    break
                except subprocess.TimeoutExpired:
                    child = child_receipt()
                    record.update(last_heartbeat_at_utc=utcnow(), elapsed_wall_seconds=time.monotonic() - started,
                                  child_receipt_status=child.get("status") if child else "missing",
                                  current_memory_bytes=int(Path("/sys/fs/cgroup/memory.current").read_text()))
                    save(target, record)
        finally:
            child = child_receipt()
            verdict = child.get("solver_verdict", child.get("status")) if child else "none"
            if verdict not in ("sat", "unsat", "unknown"):
                verdict = "none"
            if verdict != "none":
                status = "completed_with_solver_verdict" if process.returncode == 0 else "terminated_after_preserved_solver_verdict"
            elif hard_killed or process.returncode == -signal.SIGALRM:
                status = "hard_wall_termination_without_solver_verdict"
            else:
                status = "process_exit_without_solver_verdict"
            record.update(status=status, solver_verdict=verdict, child_returncode=process.returncode,
                          hard_killed_by_supervisor=hard_killed, finished_at_utc=utcnow(),
                          elapsed_wall_seconds=time.monotonic() - started,
                          child_receipt_status=child.get("status") if child else "missing")
            if verdict == "none":
                terminal = dict(child or {})
                terminal.update(status="terminated_without_solver_verdict", solver_verdict="none",
                                termination_status=status, supervisor_receipt=str(target),
                                finished_at_utc=record["finished_at_utc"],
                                prior_child_status=child.get("status") if child else "missing")
                if child:
                    save(output.with_suffix(".pretermination_child.json"), child)
                save(output.with_suffix(".json"), terminal)
            save(target, record)
            print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
