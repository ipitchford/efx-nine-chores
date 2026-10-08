"""Exact arithmetic and exhaustive d=3 sanity checks for the proved bound."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,json,math
from itertools import product
from pathlib import Path

def det(a):
 return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
        -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
        +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))
rows=[r for r in product((-1,0,1),repeat=3) if sum(x!=0 for x in r)<=2]
matrices=coordinates=parity_nontrivial=0
for a in product(rows,repeat=3):
 delta=det(a)
 if not delta:continue
 nums=[];fs=[]
 for j in range(3):
  b=[list(r) for r in a]
  for r in b:r[j]=1
  nums.append(det(b));fs.append(sum(all(r) for r in b))
 g=math.gcd(abs(delta),*nums)
 assert g>0 and abs(delta)%g==0
 for n,f in zip(nums,fs):
  if f>=1:assert g%2**(f-1)==0
  if f>=2:parity_nontrivial+=1
  assert n*n<=3**f*2**(3-f)
  assert abs(n)//g<=math.isqrt(3*2**2)
  coordinates+=1
 matrices+=1
bounds={}
for m in range(4,21):
 d=m-1;rad=d*(d-1)**(d-1);q=math.isqrt(rad)
 assert q*q<=rad<(q+1)**2
 assert 4*(d-1)>d
 assert (d-1)**d<rad
 for f in range(1,d+1):
  assert Fraction(d**f*(d-1)**(d-f),4**(f-1))<=rad
 bounds[m]={'squared_bound':rad,'integer_bound':q,'positive_lift_bound':2*q}
assert bounds[8]['integer_bound']==571 and bounds[9]['integer_bound']==2566
root=Path(__file__).parent
files=['primitive_cramer_bound.md','check_primitive_cramer_bound.py']
receipt={'status':'PASS_PRIMITIVE_CRAMER_BOUND_ARITHMETIC_AND_SMALL_DIMENSION_CONTROLS','general_bound':'floor(sqrt((m-1)*(m-2)^(m-2)))','m8':bounds[8],'m9':bounds[9],'exact_integer_bounds_m4_through_m20':bounds,'dimension3_admissible_nonsingular_matrices':matrices,'dimension3_coordinates_checked':coordinates,'nontrivial_parity_divisor_coordinates':parity_nontrivial,'general_theorem_basis':'Written proof; finite controls are not a substitute for the parity/Hadamard argument.','frozen_search_inputs_modified':False,'exhaustive_counterexample_search_performed':False,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'files_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}}
(root/'primitive_cramer_bound_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(receipt['status'],matrices,coordinates)
