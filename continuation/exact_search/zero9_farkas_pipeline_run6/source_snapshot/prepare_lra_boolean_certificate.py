#!/usr/bin/env python3
"""Untrusted arithmetic multiplier search and Boolean abstraction producer.

Every accepted arithmetic multiplier is rechecked with fractions.Fraction.
Independent verification of both those identities and the source binding is
still required. This program does not solve the resulting Boolean formula.
"""
import argparse,hashlib,itertools,json,os,resource,time
from fractions import Fraction
from pathlib import Path

for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
def atomic(path,data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        f.write(json.dumps(data,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)
    directory_fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(directory_fd)
    finally:os.close(directory_fd)
def lines(path):
    with path.open() as f:
        for line in f:yield json.loads(line)

def exact_check(rows,strict,weights):
    if any(type(w) not in (int,Fraction) for w in weights):
        raise TypeError('Exact acceptance requires integers or Fractions, never floats')
    if len(weights)!=len(rows) or any(w<0 for w in weights):return None
    total=[sum(w*r[g] for w,r in zip(weights,rows)) for g in range(len(rows[0]))]
    strict_weight=sum(w for w,s in zip(weights,strict) if s)
    if any(total[:-1]) or total[-1]<0 or (total[-1]==0 and strict_weight<=0):return None
    return dict(constant=str(total[-1]),strict_weight=str(strict_weight))

def rational_solution(equations,rhs,approx):
    """Solve exact equalities, assigning only free variables from a guess."""
    if not approx:return []
    a=[[Fraction(v) for v in row]+[Fraction(b)] for row,b in zip(equations,rhs)]
    n=len(approx);pivots=[];r=0
    for col in range(n):
        found=next((k for k in range(r,len(a)) if a[k][col]),None)
        if found is None:continue
        a[r],a[found]=a[found],a[r];pivot=a[r][col]
        a[r]=[v/pivot for v in a[r]]
        for k in range(len(a)):
            if k!=r and a[k][col]:
                factor=a[k][col];a[k]=[u-factor*v for u,v in zip(a[k],a[r])]
        pivots.append((r,col));r+=1
    if any(not any(row[:-1]) and row[-1] for row in a):return None
    result=[Fraction(str(float(v))).limit_denominator(1000000) for v in approx]
    for row,col in reversed(pivots):result[col]=a[row][-1]-sum(a[row][j]*result[j] for j in range(n) if j!=col)
    return result

def find_weights(rows,strict):
    count=len(rows);n=len(rows[0])-1
    # The many binary implication clauses admit a direct rational identity.
    for i,j in itertools.combinations(range(count),2):
        pivot=next((g for g in range(n) if rows[i][g]),None)
        if pivot is None:continue
        ratio=Fraction(-rows[j][pivot],rows[i][pivot])
        if ratio<0:continue
        weights=[Fraction(0)]*count;weights[i]=ratio;weights[j]=Fraction(1)
        valid=exact_check(rows,strict,weights)
        if valid is not None:return weights,valid,'direct_pair'
    for i in range(count):
        weights=[Fraction(0)]*count;weights[i]=Fraction(1)
        valid=exact_check(rows,strict,weights)
        if valid is not None:return weights,valid,'direct_single'
    import numpy as np
    from scipy.optimize import linprog
    matrix=np.asarray(rows,dtype=float)
    equality=np.vstack([matrix[:,:n].T,np.ones(count)])
    rhs=np.r_[np.zeros(n),1.0]
    result=linprog(-(matrix[:,-1]+np.asarray(strict,dtype=float)),
        A_ub=-matrix[:,-1][None,:],b_ub=[0.0],A_eq=equality,b_eq=rhs,
        bounds=(0,None),method='highs')
    if not result.success:return None,None,'linear_search_'+str(result.status)
    for denominator in (1000,1000000,1000000000):
        weights=[Fraction(str(float(v))).limit_denominator(denominator) for v in result.x]
        valid=exact_check(rows,strict,weights)
        if valid is not None:return weights,valid,'rationalized_lp'
    for threshold in (1e-8,0.0,-1.0):
        support=[i for i,v in enumerate(result.x) if v>threshold]
        equations=[[rows[i][g] for i in support] for g in range(n)]+[[1]*len(support)]
        target=[0]*n+[1]
        # A numerically active constant inequality is fixed exactly at zero.
        if abs(sum(result.x[i]*rows[i][-1] for i in support))<1e-7:
            equations.append([rows[i][-1] for i in support]);target.append(0)
        reduced=rational_solution(equations,target,[result.x[i] for i in support])
        if reduced is None:continue
        weights=[Fraction(0)]*count
        for i,value in zip(support,reduced):weights[i]=value
        valid=exact_check(rows,strict,weights)
        if valid is not None:return weights,valid,'exact_basis_reconstruction'
    return None,None,'no_exact_certificate_from_lp_candidate'

def bool_expression(clause):
    if clause is None:return 'true'
    if not clause:return 'false'
    def literal(v):
        if v==1:return 'true'
        if v==-1:return 'false'
        name=f'p_{abs(v)}'
        return name if v>0 else f'(not {name})'
    values=[literal(v) for v in clause]
    return values[0] if len(values)==1 else '(or '+' '.join(values)+')'

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--core-map',type=Path,help='Boolean producer core.json; certify only its theory-clause source indices')
    p.add_argument('--selected-theories',type=Path,help='Explicit JSON list of original theory JSONL source indices, e.g. a RUP dependency trim')
    p.add_argument('--memory-mib',type=int,default=600);a=p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(a.memory_mib*1024**2,)*2)
    assert not a.out.exists(),'Use a fresh artifact directory'
    receipt=json.loads((a.capture/'receipt.json').read_text())
    assert receipt.get('finished_at_utc') and not receipt.get('callback_errors'),'Only a frozen completed capture is supported'
    names=['metadata.json','atoms.jsonl','input_clauses.jsonl','theory_clauses.jsonl']
    bindings={name:dict(path=str((a.capture/name).resolve()),sha256=digest(a.capture/name)) for name in names}
    for name in names[1:]:assert bindings[name]['sha256']==receipt['files'][name]['sha256']
    metadata=json.loads((a.capture/'metadata.json').read_text());assert metadata['input_sha256']==receipt['input_sha256']
    selected=None;core_binding=None;selection_binding=None
    assert not (a.core_map and a.selected_theories),'Select one source-index mechanism'
    if a.selected_theories:
        indices=json.loads(a.selected_theories.read_text())
        theory_count=sum(1 for _ in lines(a.capture/'theory_clauses.jsonl'))
        assert isinstance(indices,list) and len(indices)==len(set(indices))
        assert all(type(i) is int and 0<=i<theory_count for i in indices)
        selected=set(indices)
        selection_binding=dict(path=str(a.selected_theories.resolve()),sha256=digest(a.selected_theories),
                               selected_theory_clause_indices=sorted(selected))
    if a.core_map:
        core=json.loads(a.core_map.read_text())
        boolean_preparation=json.loads((a.core_map.parent/'preparation.json').read_text())
        assert core['input_sha256']==boolean_preparation['boolean_sha256']
        assert boolean_preparation['capture_receipt_sha256']==digest(a.capture/'receipt.json')
        input_count=sum(1 for _ in lines(a.capture/'input_clauses.jsonl'))
        theory_count=sum(1 for _ in lines(a.capture/'theory_clauses.jsonl'))
        indices=core['core_assertion_indices']
        assert len(indices)==len(set(indices)) and all(type(i) is int and 0<=i<input_count+theory_count for i in indices)
        selected={i-input_count for i in indices if i>=input_count}
        core_binding=dict(path=str(a.core_map.resolve()),sha256=digest(a.core_map),
                          selected_theory_clause_indices=sorted(selected))
    atoms={}
    for r in lines(a.capture/'atoms.jsonl'):
        key=r['id'];v=r['affine_le_zero']
        assert type(key) is int and key>=2 and key not in atoms
        assert len(v)==len(metadata['variables'])+1 and all(type(x) is int for x in v)
        atoms[key]=v
    a.out.mkdir(parents=True);start=time.monotonic();completed=0;methods={};failed=None
    cert=a.out/'arithmetic_certificates.jsonl'
    partial=cert.with_suffix('.jsonl.partial')
    with partial.open('w') as stream:
        for index,record in enumerate(lines(a.capture/'theory_clauses.jsonl')):
            if selected is not None and index not in selected:continue
            clause=record['clause'];assert all(type(v) is int and abs(v) in atoms for v in clause)
            rows=[[-x for x in atoms[v]] if v>0 else atoms[-v] for v in clause]
            strict=[v>0 for v in clause]
            if time.monotonic()-start>=a.seconds:failed=dict(clause_index=index,reason='budget');break
            if not rows:failed=dict(clause_index=index,reason='empty_theory_clause_cannot_be_valid');break
            try:weights,check,method=find_weights(rows,strict)
            except Exception as error:
                failed=dict(clause_index=index,clause=clause,reason=type(error).__name__+': '+str(error));break
            if weights is None:failed=dict(clause_index=index,clause=clause,reason=method);break
            result=dict(clause_index=index,clause=clause,
                weights=[[i,str(w)] for i,w in enumerate(weights) if w],**check,method=method)
            stream.write(json.dumps(result,separators=(',',':'))+'\n');completed+=1
            methods[method]=methods.get(method,0)+1
            if completed%100==0:
                stream.flush();os.fsync(stream.fileno())
                atomic(a.out/'heartbeat.json',dict(completed=completed,seconds=time.monotonic()-start,methods=methods))
        stream.flush();os.fsync(stream.fileno())
    os.replace(partial,cert)
    directory_fd=os.open(a.out,os.O_RDONLY)
    try:os.fsync(directory_fd)
    finally:os.close(directory_fd)
    read_back_count=sum(1 for _ in lines(cert))
    assert read_back_count==completed,'Closed artifact record count does not match completed counter'
    status='COMPLETE_EXACT_MULTIPLIER_CANDIDATES' if failed is None else 'INCOMPLETE'
    manifest=dict(status=status,input_sha256=receipt['input_sha256'],capture_bindings=bindings,
        capture_receipt_sha256=digest(a.capture/'receipt.json'),variables=metadata['variables'],
        certificates_sha256=digest(cert),certified_theory_clauses=completed,read_back_count=read_back_count,methods=methods,
        seconds=time.monotonic()-start,failure=failed,
        interpretation='Positive theory literal v<=0 negates to -v<0; negative theory literal negates to v<=0. Nonnegative weights cancel all variable coefficients; constant C>=0 and either C>0 or positive strict-premise weight proves the clause.',
        scope='Untrusted producer output. Independent arithmetic and original-CNF binding checks required. No Boolean solver invoked.')
    if core_binding is not None:manifest['boolean_core_binding']=core_binding
    if selection_binding is not None:manifest['theory_selection']=selection_binding
    if failed is None:
        target=a.out/'boolean_refutation.smt2';counts={}
        with target.open('w') as f:
            f.write('(set-logic QF_UF)\n')
            for ident in sorted(atoms):f.write(f'(declare-fun p_{ident} () Bool)\n')
            for category in ('input_clauses','theory_clauses'):
                counts[category]=0
                for index,record in enumerate(lines(a.capture/(category+'.jsonl'))):
                    if category=='theory_clauses' and selected is not None and index not in selected:continue
                    f.write('(assert '+bool_expression(record['clause'])+')\n');counts[category]+=1
            f.write('(check-sat)\n')
        manifest.update(boolean_input=str(target.resolve()),boolean_sha256=digest(target),boolean_counts=counts,
            boolean_atoms=len(atoms),assumption_callbacks_used=False,rup_callbacks_used=False)
    atomic(a.out/'preparation.json',manifest);print(json.dumps(manifest),flush=True)

if __name__=='__main__':main()
