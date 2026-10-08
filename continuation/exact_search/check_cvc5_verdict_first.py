#!/usr/bin/env python3
"""Decide an SMT-LIB QF_LRA file with cvc5 and export its complete proof.

This runner is independent of the formula generator. It accepts a single static
SMT problem, ignores its terminal check-sat/exit commands, and checks it once.
An exported proof is not an independently checked proof: that requires a
separate checker. CPC files contain the body expected by Logos/Ethos, without
cvc5's enclosing list. Ethos also needs the version-matched CPC signature.

API documentation: https://cvc5.github.io/docs/cvc5-1.4.1/proofs/proofs.html
CPC documentation: https://cvc5.github.io/docs/cvc5-1.4.1/proofs/output_cpc.html
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import sys
import time

import cvc5


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open('wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_proof_string(value: str, output: Path) -> dict:
    """Avoid a second full-sized Python bytes copy of the proof string.

    cvc5's installed Python API inherently materializes proofToString().
    Only the subsequent encoding and disk output are streamed in chunks.
    """
    start,end=0,len(value)
    while start<end and value[start] in ' \t\r\n':start+=1
    while end>start and value[end-1] in ' \t\r\n':end-=1
    if value[start:start+2]!='(\n' or value[end-2:end]!='\n)':
        raise ValueError('unexpected cvc5 full-proof wrapper')
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.tmp');hasher=hashlib.sha256();count=0
    with temporary.open('wb') as stream:
        for offset in range(start+2,end-2,1<<20):
            chunk=value[offset:min(offset+(1<<20),end-2)].encode('utf-8')
            stream.write(chunk);hasher.update(chunk);count+=len(chunk)
        stream.write(b'\n');hasher.update(b'\n');count+=1
        stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,output)
    return dict(path=str(output.resolve()),sha256=hasher.hexdigest(),bytes=count)


def proof_statistics(path: Path) -> dict:
    steps=holes=warning_count=0;warnings=[]
    with path.open('rb') as stream:
        for line in stream:
            steps+=int(re.match(rb'^\(step(?:-pop)?\s',line) is not None)
            holes+=sum(1 for _ in re.finditer(rb':rule\s+(?:trust|hole)\b',line))
            if b'WARNING' in line:
                warning_count+=1
                if len(warnings)<10:warnings.append(line[:2000].decode('utf-8',errors='replace').rstrip())
    return dict(steps=steps,trust_or_hole_steps=holes,warnings=warnings,warning_count=warning_count)


def proof_body(value: bytes | str) -> memoryview:
    """View the documented proof-list body without copying a large certificate."""
    raw = value.encode("utf-8") if isinstance(value, str) else value
    start, end = 0, len(raw)
    while start < end and raw[start] in b" \t\r\n":
        start += 1
    while end > start and raw[end - 1] in b" \t\r\n":
        end -= 1
    if raw[start:start + 2] != b"(\n" or raw[end - 2:end] != b"\n)":
        raise ValueError("unexpected cvc5 full-proof wrapper; refusing to strip it")
    return memoryview(raw)[start + 2:end - 2]


def run(args: argparse.Namespace) -> tuple[dict, int]:
    started = time.perf_counter()
    if args.address_space_mib is not None:
        cap = args.address_space_mib * (1 << 20)
        old_soft, old_hard = resource.getrlimit(resource.RLIMIT_AS)
        if old_hard != resource.RLIM_INFINITY:
            cap = min(cap, old_hard)
        resource.setrlimit(resource.RLIMIT_AS, (cap, old_hard))
    input_bytes = args.input.read_bytes()
    if sha256(input_bytes)!=args.expected_input_sha256:
        raise ValueError('frozen input SHA-256 does not match the configured reference')
    solver = cvc5.Solver()
    options = {
        "produce-proofs": "true",
        "check-proofs": "true",
        "proof-granularity": args.granularity,
        "tlimit-per": str(int(args.timeout * 1000)),
    }
    for option in args.option:
        key, separator, value = option.partition("=")
        if not separator or not key:
            raise ValueError("each --option must be KEY=VALUE")
        options[key] = value
    if options.get("produce-proofs") != "true":
        raise ValueError("this proof-export runner requires produce-proofs=true")
    for key, value in options.items():
        solver.setOption(key, value)
    input_text = input_bytes.decode("utf-8")
    logic_commands = re.findall(r"(?m)^\s*\(set-logic\s+([^\s()]+)\s*\)\s*$", input_text)
    if len(logic_commands) > 1 or (logic_commands and logic_commands[0] != args.logic):
        raise ValueError("input logic must agree with the one configured for this run")
    injected_logic = not logic_commands
    parser_text = f"(set-logic {args.logic})\n" + input_text if injected_logic else input_text
    parser = cvc5.InputParser(solver)
    parser.setStringInput(
        cvc5.InputLanguage.SMT_LIB_2_6,
        parser_text,
        str(args.input),
    )
    symbols = parser.getSymbolManager()
    allowed = {
        "set-logic", "set-info", "declare-fun", "declare-const", "define-fun",
        "declare-sort", "define-sort", "assert",
    }
    command_counts: dict[str, int] = {}
    encountered_check = False
    encountered_exit = False
    while True:
        command = parser.nextCommand()
        if command.isNull():
            break
        name = command.getCommandName()
        command_counts[name] = command_counts.get(name, 0) + 1
        if encountered_exit:
            raise ValueError("command after terminal exit")
        if name == "check-sat":
            if encountered_check:
                raise ValueError("multiple check-sat commands are outside this runner's scope")
            encountered_check = True
            continue
        if name == "exit":
            encountered_exit = True
            continue
        if encountered_check:
            raise ValueError(f"nonterminal command after check-sat: {name}")
        if name not in allowed:
            raise ValueError(f"unsupported command in a static proof input: {name}")
        if name == "set-logic":
            if command_counts[name] != 1 or str(command).strip() != f"(set-logic {args.logic})":
                raise ValueError("input logic must agree with the one configured for this run")
        response = command.invoke(solver, symbols)
        if response.strip() not in {"", "success"}:
            raise ValueError(f"cvc5 command {name} returned {response!r}")

    assertions = list(solver.getAssertions())
    assertion_text = "\n".join(str(assertion) for assertion in assertions) + "\n"
    parsed = time.perf_counter()
    result = solver.checkSat()
    checked = time.perf_counter()
    report = {
        "solver": f"cvc5-{cvc5.__version__}",
        "input": str(args.input.resolve()),
        "input_sha256": sha256(input_bytes),
        "logic": args.logic,
        "logic_declaration_injected": injected_logic,
        "address_space_limit_mib": args.address_space_mib,
        "options": options,
        "command_counts": command_counts,
        "assertions": len(assertions),
        "parsed_assertions_sha256": sha256(assertion_text.encode("utf-8")),
        "result": str(result),
        "reason_unknown": str(result.getUnknownExplanation()) if result.isUnknown() else None,
        "parse_s": round(parsed - started, 6),
        "check_s": round(checked - parsed, 6),
        "proofs_checked_internally": options.get("check-proofs") == "true",
        "independent_proof_check": "pending",
        "proofs": [],
    }
    # This durable receipt must precede getProof() and proofToString(): either
    # operation can exhaust memory or terminate natively after UNSAT is known.
    verdict=dict(report,phase='solver_verdict',proof_export='not_started')
    atomic_write(args.verdict_report,(json.dumps(verdict,indent=2)+'\n').encode())
    print(json.dumps(dict(phase='solver_verdict',result=str(result),
                          input_sha256=report['input_sha256'],
                          verdict_report=str(args.verdict_report.resolve()))),flush=True)
    if result.isUnsat():
        atomic_write(args.export_status_report,json.dumps(dict(
            phase='getting_full_proof',input_sha256=report['input_sha256'],
            verdict_report=str(args.verdict_report.resolve()))).encode())
        proofs = solver.getProof(cvc5.ProofComponent.FULL)
        if len(proofs) != 1:
            raise ValueError(f"expected one full proof, received {len(proofs)}")
        formats = ("cpc", "alethe") if args.format == "both" else (args.format,)
        for format_name in formats:
            export_started = time.perf_counter()
            proof_format = getattr(cvc5.ProofFormat, format_name.upper())
            atomic_write(args.export_status_report,json.dumps(dict(
                phase='serializing_full_proof',format=format_name,
                input_sha256=report['input_sha256'],
                memory_limitation='proofToString materializes one complete Python string; output encoding is chunked.')).encode())
            printed=solver.proofToString(proofs[0], proof_format)
            output = args.output.with_suffix("." + format_name)
            proof_record=write_proof_string(printed,output);del printed
            proof_record.update(proof_statistics(output))
            proof_record.update(format=format_name,export_s=round(time.perf_counter()-export_started,6))
            report['proofs'].append(proof_record)
            atomic_write(args.export_status_report,json.dumps(dict(
                phase='proof_export_complete',input_sha256=report['input_sha256'],
                proof=proof_record),indent=2).encode())
    report["total_s"] = round(time.perf_counter() - started, 6)
    return report, 0 if result.isSat() or result.isUnsat() else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument('--expected-input-sha256',required=True)
    parser.add_argument('--verdict-report',type=Path,required=True)
    parser.add_argument('--export-status-report',type=Path,required=True)
    parser.add_argument("--output", type=Path, help="proof filename prefix (suffix replaced)")
    parser.add_argument("--report", type=Path, help="also save the JSON report here")
    parser.add_argument("--format", choices=("cpc", "alethe", "both"), default="cpc")
    parser.add_argument("--logic", default="QF_LRA")
    parser.add_argument("--timeout", type=float, default=3600, help="solver soft timeout, seconds")
    parser.add_argument("--granularity", default="dsl-rewrite")
    parser.add_argument("--address-space-mib", type=int, help="optional process virtual-memory cap")
    parser.add_argument("--option", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.address_space_mib is not None and args.address_space_mib <= 0:
        parser.error("--address-space-mib must be positive")
    if args.output is None:
        args.output = args.input.with_suffix("")
    try:
        report, status = run(args)
    except Exception as error:
        report, status = {
            "result": "error",
            "error_type": type(error).__name__,
            "error": str(error),
            "solver": f"cvc5-{cvc5.__version__}",
            "input": str(args.input.resolve()),
            "input_sha256": sha256(args.input.read_bytes()) if args.input.is_file() else None,
            "address_space_limit_mib": args.address_space_mib,
            "independent_proof_check": "not_performed_by_this_runner",
            "verdict_report": str(args.verdict_report.resolve()),
            "durable_verdict_preserved": args.verdict_report.exists(),
        }, 2
    serialized = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    if args.report is not None:
        atomic_write(args.report, serialized)
    sys.stdout.write(serialized.decode("utf-8"))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
