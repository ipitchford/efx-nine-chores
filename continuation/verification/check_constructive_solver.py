"""Independent exact cross-checks for the constructive solver; no solver search oracle."""
from datetime import datetime,timezone
from fractions import Fraction
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
source=ROOT/'src/solve_efx9.py';before=hashlib.sha256(source.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('reviewed_constructive_solver',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
row=['0','1/3','2/5','7/11','1e-40','0','100000000000000000000000000000000000000000000000000','3/7','0']
costs=module.parse_costs([row,list(reversed(row)),['0']*9]);scaled=module.integer_rows(costs)
subset_count=deletion_positions=zero_deletion_positions=0
for original,integers in zip(costs,scaled):
 positive=next((g for g,q in enumerate(original) if q),None)
 scale=Fraction(integers[positive],1)/original[positive] if positive is not None else Fraction(1)
 assert scale>0 and all(Fraction(v)==scale*q for v,q in zip(integers,original))
 totals,residuals=module.subset_tables(integers)
 for mask in range(512):
  owned=[g for g in range(9) if mask&(1<<g)]
  total=sum((original[g] for g in owned),Fraction(0))
  literal=[]
  for removed in owned:
   literal.append(sum((original[g] for g in owned if g!=removed),Fraction(0)))
   deletion_positions+=1;zero_deletion_positions+=int(original[removed]==0)
  maximum=max(literal,default=Fraction(0))
  assert Fraction(totals[mask],1)==scale*total
  assert Fraction(residuals[mask],1)==scale*maximum
  subset_count+=1
rejected=[]
for name,value in [('boolean',True),('binary_float',0.1),('nan_string','nan'),('infinity_string','inf'),('negative','-1'),('zero_denominator','1/0')]:
 rows=[['0']*9 for _ in range(3)];rows[0][0]=value
 try:module.parse_costs(rows)
 except ValueError:rejected.append(name)
 else:raise AssertionError('invalid input accepted: '+name)
checks=OUT/'constructive_solver_checks';checks.mkdir(exist_ok=True)
decimal='0.1000000000000000001';raw='{"costs":['+','.join('['+','.join([decimal]*9)+']' for _ in range(3))+']}\n'
input_file=checks/'decimal_fixture_input.json';output_file=checks/'decimal_fixture_output.json';input_file.write_text(raw)
run=subprocess.run([sys.executable,str(source),str(input_file),'--out',str(output_file)],capture_output=True,text=True,timeout=20)
assert run.returncode==0,run.stderr
output=json.loads(output_file.read_text());q=Fraction(decimal)
assert output['status']=='EFX_ALLOCATION_FOUND_AND_LITERALLY_VERIFIED'
assert all(Fraction(v)==q for r in output['costs'] for v in r)
a=output['assignment_by_chore'];assert len(a)==9 and all(type(i)is int and 1<=i<=3 for i in a)
bundles=[[g for g,i in enumerate(a) if i==owner] for owner in range(1,4)]
assert sorted(g for b in bundles for g in b)==list(range(9))
assert output['literal_inequalities_checked']==18==len(output['efx_certificate'])
for i,owned in enumerate(bundles):
 for j,target in enumerate(bundles):
  if i==j:continue
  for removed in owned:assert q*(len(owned)-1)<=q*len(target)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
receipt={'status':'PASS_CONSTRUCTIVE_SOLVER_INDEPENDENT_EXACT_CHECKS','source_sha256':before,'all_subset_tables_checked_on_mixed_zero_rational_fixture':subset_count,'literal_deletion_positions_checked':deletion_positions,'zero_cost_deletion_positions_checked':zero_deletion_positions,'invalid_input_controls_rejected':rejected,'exact_nonbinary_decimal_cli_case_passed':True,'decimal_cost':str(q),'complete_labelled_assignment_checked':True,'literal_output_inequalities_checked':18,'implementation_modified':False,'general_correctness_basis':'Independent source review plus the displayed exact scaling and sum-minus-minimum arguments; finite controls supplement rather than replace those arguments.','files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [input_file,output_file,Path(__file__)]},'completed_at_utc':datetime.now(timezone.utc).isoformat()}
(OUT/'constructive_solver_independent_review.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],subset_count,deletion_positions,zero_deletion_positions)
