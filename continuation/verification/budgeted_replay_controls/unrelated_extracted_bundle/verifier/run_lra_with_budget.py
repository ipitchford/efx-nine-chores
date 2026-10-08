#!/usr/bin/env python3
"""Run the unchanged exact LRA checking functions with an explicit memory budget.

The original small-calibration CLIs keep their original resource limits. This
driver changes only orchestration and RLIMIT_AS. It does not patch, replace, or
weaken any parser, arithmetic, RUP, dependency-closure, or completion check.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import resource
import subprocess
import sys
import time

import check_lra_capture
import check_lra_farkas
import check_lra_rup
from lra_certificate_common import atomic_json, require, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('rup', 'farkas', 'all'), default='all')
    parser.add_argument('--memory-mib', type=int, default=1600)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--trace', type=Path)
    parser.add_argument('--certificates', type=Path)
    parser.add_argument('--selected-indices', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--out-directory', type=Path)
    args = parser.parse_args()
    require(args.memory_mib >= 128, 'memory budget must be at least 128 MiB')
    if args.stage in ('rup', 'all'):
        require(args.trace is not None, 'this stage requires a trace')
    if args.stage in ('farkas', 'all'):
        require(args.certificates is not None, 'this stage requires arithmetic certificates')
    if args.stage == 'all':
        require(args.out_directory is not None and not args.out_directory.exists(),
                'complete replay requires a new output directory')
        require(args.out is None and args.binding is None,
                'complete replay creates its own binding and stage receipts')
    else:
        require(args.binding is not None and args.out is not None,
                'individual replay requires an input binding and output receipt')
        require(not args.out.exists(), 'refusing to overwrite an existing stage receipt')
        require(args.out_directory is None, 'individual replay takes --out')
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_mib << 20,) * 2)
    require(sha256(args.input) == args.expected_sha256, 'frozen original input changed')
    root = Path(__file__).resolve().parent
    driver_digest = sha256(__file__)
    common_digest = sha256(root / 'lra_certificate_common.py')

    def run_stage(module, arguments, output):
        started = time.monotonic()
        module_digest = sha256(module.__file__)
        report = module.check(*arguments)
        require(report['input_sha256'] == args.expected_sha256,
                'completed stage belongs to a different original input')
        require(sha256(module.__file__) == module_digest and
                sha256(root / 'lra_certificate_common.py') == common_digest and
                sha256(__file__) == driver_digest, 'checker source changed during replay')
        report.update(
            completed_at_utc=datetime.now(timezone.utc).isoformat(),
            elapsed_seconds=time.monotonic() - started,
            max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            checker_sha256=module_digest, common_sha256=common_digest,
            orchestration_driver='run_lra_with_budget.py',
            orchestration_driver_sha256=driver_digest,
            address_space_cap_mib=args.memory_mib,
            mathematical_checking_function_unchanged=True)
        atomic_json(output, report)
        print(report['status'], flush=True)
        return report

    if args.stage == 'rup':
        run_stage(check_lra_rup,
                  (args.capture, args.binding, args.trace, args.selected_indices), args.out)
        return
    if args.stage == 'farkas':
        run_stage(check_lra_farkas,
                  (args.capture, args.binding, args.certificates, args.selected_indices), args.out)
        return

    args.out_directory.mkdir(parents=True)
    binding = args.out_directory / 'input_binding.json'
    rup = args.out_directory / 'rup_verification.json'
    arithmetic = args.out_directory / 'arithmetic_verification.json'
    complete = args.out_directory / 'complete_verification.json'
    started = time.monotonic()
    run_stage(check_lra_capture, (args.input, args.expected_sha256, args.capture), binding)
    run_stage(check_lra_rup, (args.capture, binding, args.trace, args.selected_indices), rup)
    run_stage(check_lra_farkas,
              (args.capture, binding, args.certificates, args.selected_indices), arithmetic)
    # The already reviewed completion binder checks all identities, counts,
    # source hashes, closure flags, and exact selected-set arithmetic coverage.
    subprocess.run([
        sys.executable, str(root / 'bind_completed_lra_checks.py'),
        '--input', str(args.input), '--expected-sha256', args.expected_sha256,
        '--capture', str(args.capture), '--binding', str(binding),
        '--rup-verification', str(rup), '--arithmetic-verification', str(arithmetic),
        '--trace', str(args.trace), '--certificates', str(args.certificates),
        '--selected-indices', str(args.selected_indices), '--out', str(complete)], check=True)
    atomic_json(args.out_directory / 'fresh_replay_manifest.json', dict(
        status='COMPLETE_FRESH_REPLAY_THEN_UNCHANGED_IMMUTABLE_STAGE_BINDING',
        complete_verification_sha256=sha256(complete),
        orchestration_driver_sha256=driver_digest,
        address_space_cap_mib=args.memory_mib,
        mathematical_checking_functions_unchanged=True,
        all_three_mathematical_stages_executed_in_this_process=True,
        elapsed_seconds=time.monotonic() - started,
        completed_at_utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    main()
