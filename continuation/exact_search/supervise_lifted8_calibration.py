#!/usr/bin/env python3
"""Supervise the short lifted eight-chore calibration.

The child uses a 27-second solver timeout, a 600 MiB address-space cap,
and no proof generation. Parent and child enforce a 30-second hard wall.
A one-GiB shared-memory headroom guard applies before launch.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "lifted8_common_minimum_calibration"
EXPECTED = "51c67bdca332dd676c9292b4f01e61c3be360ada9b6383f8adae53fec06daab8"
HARD_SECONDS = 30


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def save(path, record):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def child_alarm():
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(HARD_SECONDS)


def read_child():
    try:
        return json.loads(OUTPUT.with_suffix(".json").read_text())
    except (OSError, ValueError):
        return None


def main():
    input_path = BASE / "lifted8_common_minimum_unit_margin.smt2"
    runner = BASE / "run_frozen_z3.py"
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    assert digest == EXPECTED
    current = int(Path("/sys/fs/cgroup/memory.current").read_text())
    maximum = int(Path("/sys/fs/cgroup/memory.max").read_text())
    command = [sys.executable, "-u", str(runner), str(input_path), "--out", str(OUTPUT),
               "--expected-sha256", EXPECTED, "--timeout", "27", "--cap-mib", "600",
               "--arith", "2", "--seed", "0", "--m", "8"]
    record = dict(status="starting", started_at_utc=utcnow(), input=str(input_path),
                  input_sha256=digest, runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
                  supervisor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  command=command, solver_timeout_seconds=27, hard_wall_limit_seconds=HARD_SECONDS,
                  address_space_cap_mib=600, arith_solver=2, random_seed=0,
                  hard_enforcement=["child POSIX alarm with default terminating action", "supervisor monotonic deadline and process-group SIGKILL"],
                  launch_memory_current_bytes=current, launch_memory_max_bytes=maximum,
                  launch_headroom_bytes=maximum-current, required_headroom_bytes=1 << 30,
                  solver_verdict="none", proof_status="no independently checked proof")
    target = OUTPUT.with_suffix(".supervisor.json")
    save(target, record); save(OUTPUT.with_suffix(".started.json"), record)
    print(json.dumps(record), flush=True)
    if maximum-current < 1 << 30:
        record.update(status="not_started_insufficient_memory_headroom", finished_at_utc=utcnow())
        save(target, record); print(json.dumps(record), flush=True); return
    started = time.monotonic()
    hard_killed = False
    with OUTPUT.with_suffix(".log").open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True, preexec_fn=child_alarm)
        record.update(status="running", child_pid=process.pid, child_started_at_utc=utcnow())
        save(target, record)
        try:
            while True:
                elapsed = time.monotonic()-started
                remaining = HARD_SECONDS-elapsed
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
                    child = read_child()
                    record.update(last_heartbeat_at_utc=utcnow(), elapsed_wall_seconds=time.monotonic()-started,
                                  child_receipt_status=child.get("status") if child else "not_yet_written")
                    save(target, record)
        except BaseException as error:
            record.update(supervisor_exception=type(error).__name__ + ": " + str(error))
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            raise
        finally:
            child = read_child()
            verdict = child.get("status") if child else None
            if verdict not in ("sat", "unsat", "unknown"):
                verdict = "none"
            if verdict != "none": status = "completed_with_solver_verdict"
            elif hard_killed or process.returncode == -signal.SIGALRM: status = "hard_wall_termination_without_solver_verdict"
            else: status = "process_exit_without_solver_verdict"
            record.update(status=status, solver_verdict=verdict, child_returncode=process.returncode,
                          hard_killed_by_supervisor=hard_killed, finished_at_utc=utcnow(),
                          elapsed_wall_seconds=time.monotonic()-started,
                          child_receipt_status=child.get("status") if child else "missing")
            if verdict == "none":
                terminal = dict(child or {})
                terminal.update(status="terminated_without_solver_verdict", solver_verdict="none",
                                termination_status=status, supervisor_receipt=str(target),
                                finished_at_utc=record["finished_at_utc"],
                                prior_child_status=child.get("status") if child else "missing")
                if child is not None:
                    save(OUTPUT.with_suffix(".pretermination_child.json"), child)
                save(OUTPUT.with_suffix(".json"), terminal)
            save(target, record)
            print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
