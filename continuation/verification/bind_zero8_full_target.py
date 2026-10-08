"""Bind the completed zero-eight proof to its mathematical residual audit."""
from pathlib import Path
import csv,hashlib,json
from itertools import product
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent

def h(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
expected='20d56e8ecd4bfad40ad5c7786c7865442c9961569dabb9e1a8dfe415b584c08f'
proof=json.loads((OUT/'zero8_complete_lra_certificate.json').read_text());audit=json.loads((OUT/'zero_minimum8_formula_audit.json').read_text())
assert proof['status']=='PASS_INDEPENDENT_EXACT_LRA_UNSAT_CERTIFICATE'
assert proof['input_sha256']==audit['input_sha256']==expected==h('continuation/exact_search/zero_minimum8_reference_strict.smt2')
assert audit['status']=='PASS_ALL_SERIALIZED_ZERO_MINIMUM_CLAUSES_RECONSTRUCTED_WITH_STDLIB'
assert (audit['allocation_clauses'],audit['domain_assertions'],audit['literal_positions_checked'])==(5796,23,54360)
rows=[]
for aid,allocation in enumerate(product(range(3),repeat=8)):
 if len(set(allocation))==3:continue
 bundles=[[g for g,owner in enumerate(allocation) if owner==i] for i in range(3)]
 target=next(i for i,b in enumerate(bundles) if not b)
 owner=next(i for i,b in enumerate(bundles) if len(b)>=2)
 retained=next(g for g in bundles[owner] if g!=owner)
 removed=next(g for g in bundles[owner] if g!=retained)
 rows.append([aid,owner,target,removed,retained])
file=OUT/'zero8_omitted_empty_allocation_witnesses.csv'
with file.open('w',newline='') as stream:
 writer=csv.writer(stream);writer.writerow(['allocation_id','failing_agent','empty_target','removed_chore','retained_positive_chore']);writer.writerows(rows)
seen=set()
with file.open() as stream:
 for row in csv.DictReader(stream):
  aid,i,j,removed,retained=[int(row[k]) for k in row]
  assert aid not in seen;seen.add(aid)
  code=aid;allocation=[0]*8
  for g in range(7,-1,-1):allocation[g]=code%3;code//=3
  assert code==0 and all(owner!=j for owner in allocation)
  assert i!=j and removed!=retained and retained!=i
  assert allocation[removed]==allocation[retained]==i
assert len(seen)==765 and 5796+len(seen)==3**8
inventory=json.loads((OUT/'baseline_dependency_inventory.json').read_text())
for path,digest in inventory['files_sha256'].items():assert h(path)==digest
paths=['continuation/exact_search/zero_minimum8_reference_strict.smt2','continuation/verification/zero8_complete_lra_certificate.json','continuation/verification/zero_minimum8_formula_audit.json','continuation/verification/zero8_full_target_completion.md','continuation/verification/zero8_omitted_empty_allocation_witnesses.csv','continuation/verification/baseline_dependency_inventory.json','continuation/verification/zero8_capture_composed1_provenance.json','continuation/verification/zero8_capture_v3_rejection.json','continuation/verification/zero8_selected_farkas_rejection.json']
report={'status':'PASS_ORDINARY_EIGHT_CHORE_INPUT_AND_COMPLETED_CERTIFICATE_BINDING','input_sha256':expected,'surjective_allocations_checked':5796,'omitted_allocations_independently_witnessed':765,'complete_allocations_accounted_for':6561,'independent_residual_unsat_certificate_complete':True,'prior_seven_certificate_carried_by_hash':True,'baseline_six_theorem':'Kobayashi–Mahara–Sakamoto Theorem 3.1, cited','handwritten_reductions_remain_explicit_premises':True,'P8_or_D8_required':False,'nine_chore_certificate_inferred':False,'files_sha256':{p:h(p) for p in paths},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'completed_at_utc':datetime.now(timezone.utc).isoformat()}
(OUT/'zero8_full_target_binding.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(seen))
