#!/usr/bin/env python3
"""Package the selected, byte-identified research objects; never publish them."""
from pathlib import Path
import datetime
import hashlib
import json
import platform
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
ZIP=OUT/'economics-problem-2-reproducibility.zip'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads((ROOT/path).read_text())

root7=read('results/root7_ethos.json')
p6=read('results/designated6_ethos.json')
continuation=read('docs/CONTINUATION_STATUS.json')
assert continuation['main_status']=='unresolved', 'A resolving result requires a new theorem manuscript and claim ledger.'
assert continuation['all_supervised_runs_terminal'] is True
assert continuation['release_audit_status']=='PASS'
for record, input_name, proof_name in [(root7, 'results/root7_pruned.smt2', 'certificates/root7_cvc5.cpc'), (p6, 'work/structural_designated_m6.standard.smt2', 'certificates/designated6_cvc5.cpc')]:
    assert record['result']=='verified'
    assert record['reference_binding'] and record['requires_final_false_at_global_scope']
    assert sha(ROOT/input_name)==record['input_sha256']
    assert sha(ROOT/proof_name)==record['proof_sha256']

status={
 'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'main_target':'Every nonnegative additive 3x9 cost matrix admits a complete EFX allocation, with owned zero-cost chores included in every deletion quantifier.',
 'main_target_status':'UNRESOLVED: no proof or counterexample obtained',
 'claims':{
  'prescribed_agent_six_chores':{'status':'COMPUTER_ASSISTED_POSITIVE_RESULT','finite_certificate':'Externally checked CPC refutation bound to exact input','receipt':'results/designated6_ethos.json','remaining_trust':'Handwritten interpretation/reductions, CPC calculus, checker and runtime'},
  'ordinary_seven_chores_residual':{'status':'EXTERNALLY_CHECKED_FINITE_REFUTATION','receipt':'results/root7_ethos.json','general_coverage':'Known six-chore theorem plus shared-minimum insertion and generic reduction'},
  'prescribed_agent_seven_chores':{'status':'Z3_UNSAT; EXTERNAL_CERTIFICATE_NOT_OBTAINED','z3_receipt':'work/structural_designated_reduced_m7_seed0.json','core_z3_receipt':'results/designated7_core_select.json','last_external_attempt':'results/designated7_core_cvc5.json','last_external_exit':139,'cause':'not established; no solver verdict or proof emitted'},
  'prescribed_agent_eight_chores':{'status':'EXACT_COUNTEREXAMPLE_TO_STRENGTHENING','matrix_source':'src/verify_finite.py','all_allocations':6561,'ordinary_efx_count':36,'prescribed_ordinary_ef_counts':[0,31,31],'certificate':'results/p8_designated_failure_certificate.csv'},
  'arbitrary_ninth_column_added_to_displayed_matrix':{'status':'PROVED_EFX_FOR_ALL_NONNEGATIVE_NEW_COLUMNS','proof':'docs/ancillary_proofs.md, Section 4','independent_symbolic_audit':'work/structural_report_check.json'},
  'ordinary_eight_chores':{'status':'PRIOR_THEOREM; LOCAL_Z3_UNSAT_REPRODUCTION','local_external_certificate':'not obtained','source':'https://arxiv.org/abs/2609.10585v2'},
  'D8_distinct_minimum_strengthening':{'status':'UNRESOLVED','full_solver_receipt':'results/D8_root.json','cegis_stop_receipt':'work/compute_designated8_allmin/stop_receipt.json'},
  'fourteen_second_minimum_cones':{'status':'ALL_14_UNKNOWN','scope':'These cones require a separate unproved D8 premise to cover the generic target. They have no completed UNSAT cover.','receipt':'results/second_min_cases/summary.json'}
 },
 'release_scope':'Research memorandum and exact ancillary results; no solution announcement for Problem 2.',
 'recorded_supervised_continuation_runs_terminal':True,
 'continuation_status':'docs/CONTINUATION_STATUS.json',
 'python':platform.python_version()
}
status['claims'].update({
 'zero_minimum_normalization':{
  'status':'PROVED_COUNTEREXAMPLE_PRESERVING_REDUCTION',
  'free_real_variables_after_reference_scaling':21,
  'proof':'continuation/exact_search/zero_minimum_reduction.md',
  'independent_review':'continuation/verification/zero_minimum_independent_review.md',
  'whole_nine_chore_formula_audit':'continuation/verification/zero_minimum9_formula_audit.json',
  'scope':'Zero one selected global minimum per row; EFX after zeroing implies EFX before zeroing. Owned zero deletions are retained.'},
 'zero_integer_representative_bound':{
  'status':'PROVED_COMPLETE_RANGE; DOMAIN_NOT_EXHAUSTED',
  'one_fixed_zero_per_row':True,'other_costs_positive_integers_at_most':3831,
  'proof':'continuation/exact_search/zero_minimum_reduction.md'},
 'positive_common_minimum_one_representative':{
  'status':'PROVED_COMPLETE_RANGE; DOMAIN_NOT_EXHAUSTED',
  'minimum_in_every_row':1,'other_costs_even_integers_from':2,'other_costs_even_integers_to':7662,
  'selected_failure_margins_at_least':1,
  'proof':'continuation/exact_search/zero_minimum_reduction.md'},
 'row_local_integer_representative_bound':{
  'status':'PROVED_SEARCH_REDUCTION; DOMAIN_NOT_EXHAUSTED',
  'bound_per_positive_integer_entry':11585,
  'independent_row_minima':True,
  'proof':'continuation/exact_search/row_local_integer_bound.md',
  'review':'continuation/verification/row_local_integer_bound_check.json',
  'scope':'A counterexample exists over nonnegative real costs iff one exists with all 27 costs positive integers at most 11585. No equality of integer minima is imposed.'},
 'bounded_real_nine_chore_formula':{
  'status':'EXISTENCE_EQUIVALENT_FORMULATION; UNKNOWN_TIMEOUT',
  'receipt':'continuation/exact_search/bounded9_fixed_min_fractional_run1.json',
  'proof':'continuation/exact_search/row_local_integer_bound.md',
  'fixed_minimum':1,'row_local_margin':'1/11585','upper_bound':11585,
  'scope':'The scaled-unit alternative still has real variables; no cross-row total margin is justified.'},
 'prefix_extension_regions':continuation['prefix_evidence'],
 'two_row_elimination_regions':continuation['row_evidence'],
 'cardinality_cut':{
  'status':'PROVED_SUFFICIENT_CONDITION; NOT_UNIVERSAL',
  'proof':'continuation/structural_nine/cardinality_cut.md',
  'scope':'The protected-bundle construction gives an EFX allocation when its stated inequalities hold. An explicit positive nine-chore instance lies outside that sufficient condition.'}
})
(ROOT/'docs/CLAIM_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')

sources=[]
for name,url in [('zhang_2609_10585v2.pdf','https://arxiv.org/pdf/2609.10585v2'),('kms_2305_04168.pdf','https://arxiv.org/pdf/2305.04168')]:
    p=ROOT/'sources'/name
    if p.exists():sources.append({'inspected_local_name':'sources/'+name,'url':url,'bytes':p.stat().st_size,'sha256':sha(p),'included_in_archive':False})
original=ROOT.parent/'upload'/'Pasted text(20261007-174935).txt'
if original.exists():sources.append({'role':'User-provided shortlist containing Problem 2','bytes':original.stat().st_size,'sha256':sha(original),'included_in_archive':False,'scope_restatement':'target.yaml and docs/research_report.md'})
if sources or not (ROOT/'docs/original_sources_manifest.json').exists():
    (ROOT/'docs/original_sources_manifest.json').write_text(json.dumps(sources,indent=2)+'\n')

files=set()
def add(p):
    if p.is_file() and not p.is_symlink():files.add(p)
def glob(pattern):
    for p in ROOT.glob(pattern):add(p)
for name in ['README.md','target.yaml','novelty_report.md','novelty_designated_addendum.md','proof_export_notes.md','requirements-solver.txt','requirements-report.txt','requirements-continuation.txt']:
    add(ROOT/name)
glob('docs/*')
glob('src/*.py')
glob('scripts/*.sh')
for ext in ['json','smt2','log','csv']:
    glob('results/**/*.'+ext)
for name in ['root7_cvc5.cpc','designated6_cvc5.cpc']:
    add(ROOT/'certificates'/name)
add(ROOT/'results/root8_pruned.z3proof')
for ext in ['py','json','smt2','md','csv']:
    glob('work/structural_*.'+ext)
    glob('work/compute_*.'+ext)
    glob('work/compute_*/**/*.'+ext)
for ext in ['smt2','cpc','json']:
    glob('work/checker_controls/**/*.'+ext)
glob('work/cvc5_signatures/proofs/eo/cpc/**/*.eo')
for name in ['work/cvc5_signatures/COPYING','work/cvc5_signatures/AUTHORS','work/ethos/COPYING','work/ethos/AUTHORS','work/ethos/licenses/lgpl-3.0.txt']:
    add(ROOT/name)
for name in ['replay/setup_checker_validation.json','replay/checker_controls.json']:
    add(ROOT/name)
add(ROOT/'output/pdf/economics-problem-2-research-report.pdf')

# Retain complete continuation evidence and historical frozen boundaries.
# Runtime distributions, Python caches and compiled executables are rebuilt
# from recorded source/version pins rather than shipped as platform binaries.
continuation_extensions={'.py','.cpp','.md','.yaml','.json','.jsonl','.smt2','.log','.csv','.txt','.bin','.pbtxt','.stdout','.stderr'}
for p in (ROOT/'continuation').rglob('*'):
    rel=p.relative_to(ROOT/'continuation')
    if any(part in {'ortools_runtime','yices','__pycache__'} for part in rel.parts):continue
    if p.suffix in continuation_extensions:add(p)

entries=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]
manifest={'scope':'Original and continuation reproducibility objects, excluding platform runtimes and caches; this manifest excludes itself and MANIFEST.sha256 to avoid self-reference.','central_result':'Nine-chore target unresolved. A complete representative has one zero per row and other integer costs at most3831; a positive representative has common minimum1 and other even costs at most7662. Neither domain has been exhausted.','files':entries}
(ROOT/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'MANIFEST.sha256').write_text(''.join(x['sha256']+'  '+x['path']+'\n' for x in entries))
files.update([ROOT/'artifact_manifest.json',ROOT/'MANIFEST.sha256'])

with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8,allowZip64=True) as archive:
    for p in sorted(files):archive.write(p,'economics_problem2/'+str(p.relative_to(ROOT)))
print(json.dumps({'archive':str(ZIP),'archive_bytes':ZIP.stat().st_size,'archive_sha256':sha(ZIP),'files':len(files),'uncompressed_bytes':sum(p.stat().st_size for p in files)}))
