"""Public entry point: restore, hash, control, or actually replay. No solver."""
from pathlib import Path
import gzip, hashlib, json, shutil, subprocess, sys, tempfile
R=Path(__file__).resolve().parents[1]
def run(args):
    subprocess.run([sys.executable]+(['-O'] if sys.flags.optimize else [])+args,cwd=R,check=True)
mode=sys.argv[1]
if mode=='restore':
    for p in R.rglob('*.jsonl.gz'):
        target=p.with_suffix('')
        if not target.exists():
            with gzip.open(p,'rb') as src,target.open('xb') as dst: shutil.copyfileobj(src,dst)
elif mode=='manifest':
    for line in (R/'MANIFEST.sha256').read_text().splitlines():
        expected,name=line.split('  ',1)
        p=R/name;h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''):h.update(b)
        if h.hexdigest()!=expected:raise RuntimeError('Digest mismatch: '+name)
    print('PASS publication manifest')
elif mode=='controls':
    with tempfile.TemporaryDirectory(prefix='efx-controls-') as t:
        dst=Path(t)/'verification';shutil.copytree(R/'continuation/verification',dst,ignore=shutil.ignore_patterns('__pycache__','budgeted_replay_controls'))
        for name in ['test_lra_certificate_checkers.py','test_lra_relocation.py','test_budgeted_lra_replay.py']:
            run([str(dst/name)])
elif mode=='replay':
    out=sys.argv[2] if len(sys.argv)>2 else str(R/'replay_results/zero9_fresh')
    run(['continuation/verification/run_lra_with_budget.py','--stage','all','--memory-mib','1600',
         '--input','continuation/exact_search/zero_minimum9_reference_strict.smt2',
         '--expected-sha256','65b0e3d6b2f234a6391db058771b8597a7bdd6feb003813ddc88630843ceab5b',
         '--capture','continuation/exact_search/zero9_minimal_replay_capture1/capture',
         '--trace','continuation/exact_search/zero9_rup_source_cache_run1/trimmed_trace.jsonl',
         '--certificates','continuation/exact_search/zero9_selected_farkas_final1/arithmetic_certificates.jsonl',
         '--selected-indices','continuation/exact_search/zero9_rup_source_cache_run1/selected_theory_indices.json',
         '--out-directory',out])
else:raise RuntimeError('Unknown mode')
