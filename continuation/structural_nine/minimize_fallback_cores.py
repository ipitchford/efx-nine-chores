#!/usr/bin/env python3
"""Minimize saved fallback cores, then certify their literal allocation subsets.

The resulting certificate also proves the original larger core's claim because
the retained allocation IDs are a subset of the original IDs. Original source
files are preserved byte for byte. The generated directory is itself resumable.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--check-timeout', type=int, default=1000)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (500 * 1024**2,) * 2)
    import z3
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from certify_row_cores import certify
    from verify_row_cores import verify
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ['regions', 'inner', 'certificates']:
        (args.out / name).mkdir(exist_ok=True)
    started = time.monotonic()
    receipts = []
    cache = {}
    for source in sorted((args.source / 'regions').glob('*.json')):
        original = json.loads(source.read_text())
        if original.get('inner_method') != 'QF_LRA_solver':
            continue
        core_source = args.source / 'inner' / source.with_suffix('.smt2').name
        assert sha(core_source) == original['core_sha256']
        formulas = list(z3.parse_smt2_file(str(core_source)))
        size = original['core_size']
        assert len(formulas) == 15 + size
        domain, failures = formulas[:15], formulas[15:]
        solver = z3.SolverFor('QF_LRA')
        solver.set(**{'arith.solver': 2, 'timeout': args.check_timeout})
        solver.add(*domain)
        gates = [z3.Bool(f'minimize_{source.stem}_{i}') for i in range(size)]
        for gate, failure in zip(gates, failures):
            solver.add(z3.Implies(gate, failure))
        assert solver.check(*gates) == z3.unsat
        kept = list(range(size))
        checks = []
        for index in range(size):
            if time.monotonic() - started >= args.seconds:
                break
            trial = [i for i in kept if i != index]
            tick = time.monotonic()
            status = solver.check(*(gates[i] for i in trial))
            checks.append(dict(index=index, status=str(status), seconds=time.monotonic()-tick))
            if status == z3.unsat:
                kept = trial
        allocation_ids = [original['core_allocation_ids'][i] for i in kept]
        allocations = [original['core_allocations'][i] for i in kept]
        raw = set()
        for allocation in allocations:
            bundles = [{g for g, owner in enumerate(allocation) if owner == i} for i in range(3)]
            for agent in (1, 2):
                for removed in bundles[agent]:
                    for target in range(3):
                        if target == agent:
                            continue
                        row = tuple(int(g in bundles[agent] and g != removed) - int(g in bundles[target]) for g in range(9))
                        if any(v > 0 for v in row):
                            raw.add((agent, row))
        raw = sorted(raw)
        def dominated(a, b):
            ia, va = a
            ib, vb = b
            return ia == ib and sum(va) <= sum(vb) and all(va[g] <= vb[g] for g in range(9) if g != ia)
        zeros = {i: (i, (0,) * 9) for i in (1, 2)}
        surviving = [a for a in raw if not dominated(a, zeros[a[0]])]
        retained = [a for a in surviving if not any(a != b and dominated(a, b) for b in surviving)]
        dominance = []
        for index, atom in enumerate(raw):
            is_zero = dominated(atom, zeros[atom[0]])
            retained_index = None if is_zero else next(j for j, other in enumerate(retained) if dominated(atom, other))
            dominance.append(dict(raw_index=index, retained_index=retained_index, zero=is_zero))
        literal_core = z3.SolverFor('QF_LRA')
        literal_core.add(*domain, *(failures[i] for i in kept))
        core_text = literal_core.sexpr() + '\n(check-sat)\n'
        new_core = args.out / 'inner' / source.with_suffix('.smt2').name
        new_core.write_text(core_text)
        record = dict(original)
        record.update(
            core_size=len(kept), core_allocation_ids=allocation_ids,
            core_allocations=allocations, core_sha256=sha(new_core),
            region_atoms=[dict(agent=i, coefficients=list(v)) for i, v in raw],
            compressed_region_atoms=[dict(agent=i, coefficients=list(v)) for i, v in retained],
            dominance_certificate=dominance,
            compression_counts=dict(raw=len(raw), kept=len(retained)),
            original_source=str(source.resolve()), original_source_sha256=sha(source),
            original_core_sha256=original['core_sha256'],
            original_allocation_ids=original['core_allocation_ids'],
            retained_original_indices=kept, minimization_checks=checks)
        certificate = certify(record, cache)
        verification = verify(certificate)
        certificate_file = args.out / 'certificates' / source.name
        certificate_file.write_text(json.dumps(certificate, indent=2) + '\n')
        record['exact_core_certificate_sha256'] = sha(certificate_file)
        record['exact_core_verification'] = verification
        region_file = args.out / 'regions' / source.name
        region_file.write_text(json.dumps(record, indent=2) + '\n')
        receipt = dict(
            original_source=str(source.resolve()), original_source_sha256=sha(source),
            original_allocation_ids=original['core_allocation_ids'],
            reduced_source=str(region_file.resolve()), reduced_source_sha256=sha(region_file),
            retained_allocation_ids=allocation_ids, retained_original_indices=kept,
            certificate=str(certificate_file.resolve()), certificate_sha256=sha(certificate_file),
            original_size=size, reduced_size=len(kept), verification=verification,
            old_region_implication='Retained allocation IDs are a subset of the original core. Every literal other-agent EFX premise for the retained allocations is included among the original region premises, with nonnegative-only tautologies omitted consistently.')
        receipts.append(receipt)
        summary = dict(status='PASS', utc=datetime.now(timezone.utc).isoformat(),
                       elapsed=time.monotonic()-started, cores=len(receipts), receipts=receipts)
        (args.out / 'verification.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(json.dumps({k:v for k,v in receipt.items() if k in ('original_source','original_size','reduced_size','verification')}), flush=True)
    print(json.dumps(dict(status='PASS', cores=len(receipts), elapsed=time.monotonic()-started)), flush=True)


if __name__ == '__main__':
    main()
