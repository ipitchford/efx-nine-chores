#!/usr/bin/env python3
"""Package one frozen, independently audited continuation checkpoint."""
import hashlib,json,shutil,sys,tempfile,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'output'/'economics-problem-2-continuation-checkpoint.zip'
stage=Path(tempfile.mkdtemp(prefix='continuation_checkpoint_',dir=ROOT/'tmp'))
bundle=stage/'economics_problem2_continuation_checkpoint';bundle.mkdir()

files=[
 'continuation/extension_geometry/extension_oracle.py',
 'continuation/extension_geometry/verify_extension_certificate.py',
 'continuation/extension_geometry/extension_method.md',
 'continuation/verify_row_cores.py',
 'continuation/certify_row_cores.py',
 'continuation/prefix_cegis.py',
 'continuation/structural_nine/row_elimination_proof.md',
 'continuation/structural_nine/cardinality_cut.md',
 'continuation/structural_nine/cardinality_cut_check.py',
 'continuation/exact_search/finite_integer_bound.md',
 'continuation/verification/prefix_snapshot_audit.json',
 'continuation/verification/prefix_v3_snapshot.smt2',
 'continuation/verification/prefix_v3_portable_snapshot.smt2',
 'continuation/verification/row_core_audit.json',
]
files += [f'continuation/prefix_regions_v3/region_{j:05d}.json' for j in range(641)]
files += [f'continuation/row_core_certificates_v2/{j:05d}.json' for j in range(109)]
for rel in files:
 source=ROOT/rel;assert source.is_file(),str(source)
 target=bundle/rel;target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(source,target)

readme='''# Economics problem two: verified continuation checkpoint

**Main target remains unresolved in this checkpoint.** This archive contains
verified reductions and sufficient families for three agents and nine chores.
It contains neither a universal nine-chore existence proof nor a counterexample.
Searches continued after this frozen checkpoint was taken.

The exact target is a complete labelled allocation with nonnegative additive
costs, satisfying every owned-chore EFX deletion inequality, including deletion
of zero-cost chores. The previously delivered full research package contains
the earlier six-, seven-, and eight-chore work; this checkpoint is additional.

## Verified contents

- 641 extension-region certificates: 300 cover every nonnegative ninth cost
  column; 341 cover columns above their explicitly recorded linear lower
  bounds. All retain the same 26 stated within-row canonical inequalities.
- A portable SMT snapshot with 31 canonical-domain assertions and precisely
  those 641 region complements. Its assertion correspondence was audited;
  **UNSAT has not been established for this snapshot**.
- 109 certificates eliminating the first valuation row on specified regions
  of the other two rows. Every possible remaining EFX-failure branch is
  refuted by exact nonnegative rational linear identities.
- Self-contained proofs of the finite integer bound
  B9 = 194,368,031,998, the canonical deletion choice, and a cardinality-aware
  cut-and-choose sufficient condition. No priority claim is made for the
  classical determinant method used in the bound.

## Replay without an SMT solver

From this extracted directory, run:

    python3 verify_checkpoint.py

Only the Python standard library is required. The script checks every payload
hash and every included regional certificate. Regenerating regions requires
Z3; the original run used z3-solver 5.1.0.0 and Python 3.12.14.

The row-core audit receipt also refers to 60 older, uncompressed certificates
that are omitted here as redundant. The included 109 format-2 certificates
are complete and are replayed directly by verify_checkpoint.py. A discovered
floating-point type-validation defect in an earlier row-core checker was
corrected before this checkpoint; the included checker requires integer
coefficients and checks all alternative identities with Fraction arithmetic.

The original raw SMT snapshot contains 24 nonstandard model-add metadata
commands. The separately supplied portable snapshot removes precisely those
audited commands; its declarations and assertions are unchanged. Use the
portable snapshot for an external solver.
'''
(bundle/'README.md').write_text(readme)
verify='''#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
r=Path(__file__).resolve().parent
m=json.loads((r/'MANIFEST.json').read_text())
for name,h in m.items():
    assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
sys.path.insert(0,str(r/'continuation'/'extension_geometry'))
from verify_extension_certificate import verify as extension
sys.path.insert(0,str(r/'continuation'))
from verify_row_cores import verify as row_core
p=list(sorted((r/'continuation'/'prefix_regions_v3').glob('region_*.json')))
q=list(sorted((r/'continuation'/'row_core_certificates_v2').glob('*.json')))
assert len(p)==641 and len(q)==109
for f in p:extension(json.loads(f.read_text()))
for f in q:row_core(json.loads(f.read_text()))
print(json.dumps({'status':'PASS','payload_hashes':len(m),
                  'extension_regions':len(p),'row_core_regions':len(q),
                  'main_nine_chore_problem':'unresolved'}))
'''
(bundle/'verify_checkpoint.py').write_text(verify)
manifest={p.relative_to(bundle).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(bundle.rglob('*')) if p.is_file()}
(bundle/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(bundle.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(stage))
with zipfile.ZipFile(DEST) as z:assert z.testzip() is None
receipt={'archive':str(DEST),'bytes':DEST.stat().st_size,
         'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),
         'staged_root':str(bundle),'payload_files':len(manifest)}
(ROOT/'output'/'continuation_checkpoint_build.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
