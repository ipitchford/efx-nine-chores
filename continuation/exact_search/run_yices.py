#!/usr/bin/env python3
"""Run an unchanged static QF_LRA formula with pinned official Yices binary.

This records a solver verdict, not an independently checked proof. SAT
models must be replayed separately against all complete allocations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import time


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--timeout',type=int,default=600)
    ap.add_argument('--cap-mib',type=int,default=2450)
    ap.add_argument('--mcsat',action='store_true')
    args=ap.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    binary=Path(__file__).resolve().parent/'yices/yices-2.7.0/bin/yices-smt2'
    data=args.input.read_bytes()
    if b'(set-logic' not in data:
        data=b'(set-logic QF_LRA)\n'+data
    submitted=args.out.with_suffix('.input.smt2')
    submitted.write_bytes(data)
    command=[str(binary),'--stats','--dump-models',f'--timeout={args.timeout}']
    if args.mcsat:command.append('--mcsat')
    command.append(str(submitted))
    def limits():
        limit=args.cap_mib<<20
        resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
    version=subprocess.check_output([str(binary),'--version'],text=True)
    started=time.monotonic()
    try:
        result=subprocess.run(command,capture_output=True,text=True,preexec_fn=limits,timeout=args.timeout+30)
        stdout,stderr,code=result.stdout,result.stderr,result.returncode
    except subprocess.TimeoutExpired as e:
        stdout=e.stdout or b'';stderr=e.stderr or b'';code='parent timeout'
        if isinstance(stdout,bytes):stdout=stdout.decode(errors='replace')
        if isinstance(stderr,bytes):stderr=stderr.decode(errors='replace')
    elapsed=time.monotonic()-started
    args.out.with_suffix('.stdout').write_text(stdout)
    args.out.with_suffix('.stderr').write_text(stderr)
    lines=stdout.splitlines()
    verdict=next((v for v in lines if v in ('sat','unsat','unknown')),'no verdict')
    record=dict(command=command,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                version=version,input_original=str(args.input.resolve()),
                input_original_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                input_submitted=str(submitted.resolve()),
                input_submitted_sha256=hashlib.sha256(data).hexdigest(),
                verdict=verdict,exit_code=code,elapsed_seconds=elapsed,
                mcsat=args.mcsat,cap_mib=args.cap_mib,stdout=stdout,stderr=stderr,
                proof_status='no independently checked proof')
    args.out.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record),flush=True)


if __name__=='__main__':main()
