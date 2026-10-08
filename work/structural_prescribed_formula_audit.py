"""Exact structural and bounded semantic audit of frozen P6/P7 SMT2 inputs.

This script does not import either formula generator. It parses the referenced
portable SMT2 inputs, decodes arithmetic atoms into exact integer coefficients,
and compares every allocation clause to coefficients constructed directly from
the specification. Domain assertions are separately compared to their stated
canonical constraints. Direct integer point checks include zero rows and ties.
"""
from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib,json,time
import z3


def audit(m,path,reduced):
    path=Path(path);assertions=list(z3.parse_smt2_file(str(path)))
    allocations=[a for a in product(range(3),repeat=m) if not reduced or len(set(a))==3]
    domain_count=len(assertions)-len(allocations)
    assert domain_count==(41 if reduced else 26)
    dimension=3*m+1;cache={}
    def polynomial(term):
        tid=term.get_id()
        if tid in cache:return cache[tid]
        out=[Fraction(0)]*dimension
        if z3.is_rational_value(term):
            out[-1]=Fraction(term.numerator_as_long(),term.denominator_as_long())
        elif z3.is_const(term):
            bits=str(term).split('_')
            assert len(bits)==3 and bits[0]=='c'
            i,g=map(int,bits[1:]);assert 0<=i<3 and 0<=g<m
            out[i*m+g]=1
        else:
            kind=term.decl().kind()
            if kind==z3.Z3_OP_ADD:
                for child in term.children():out=[a+b for a,b in zip(out,polynomial(child))]
            elif kind==z3.Z3_OP_SUB:
                out=list(polynomial(term.arg(0)))
                for child in term.children()[1:]:out=[a-b for a,b in zip(out,polynomial(child))]
            elif kind==z3.Z3_OP_UMINUS:out=[-a for a in polynomial(term.arg(0))]
            elif kind==z3.Z3_OP_TO_REAL:out=list(polynomial(term.arg(0)))
            else:raise AssertionError(('unexpected arithmetic',term))
        cache[tid]=tuple(out);return cache[tid]
    def relation(atom):
        kind=atom.decl().kind()
        assert kind in [z3.Z3_OP_GT,z3.Z3_OP_GE,z3.Z3_OP_LT,z3.Z3_OP_LE,z3.Z3_OP_EQ]
        coeff=tuple(a-b for a,b in zip(polynomial(atom.arg(0)),polynomial(atom.arg(1))))
        if kind in [z3.Z3_OP_GT,z3.Z3_OP_GE]:coeff=tuple(-x for x in coeff)
        label={z3.Z3_OP_GT:'lt',z3.Z3_OP_LT:'lt',z3.Z3_OP_GE:'le',z3.Z3_OP_LE:'le',z3.Z3_OP_EQ:'eq'}[kind]
        if label=='eq':
            first=next((v for v in coeff if v),0)
            if first<0:coeff=tuple(-v for v in coeff)
        return label,coeff
    def boolean(expr):
        if z3.is_true(expr):return ('true',)
        if z3.is_false(expr):return ('false',)
        if z3.is_and(expr) or z3.is_or(expr):
            op='and' if z3.is_and(expr) else 'or';terms=[]
            for child in expr.children():
                b=boolean(child)
                if b[0]==op:terms.extend(b[1])
                else:terms.append(b)
            terms=sorted(set(terms),key=repr)
            if len(terms)==1:return terms[0]
            return (op,tuple(terms))
        return relation(expr)
    c=[[z3.Real(f'c_{i}_{g}') for g in range(m)] for i in range(3)]
    expected_domain=[]
    for i in range(3):
        expected_domain.extend([v>0 if reduced else v>=0 for v in c[i]])
        expected_domain.append(z3.Sum(c[i])==1)
    if reduced:
        for i,pin in [(1,0),(2,1)]:
            expected_domain.extend(c[i][pin]<c[i][g] for g in range(m) if g!=pin)
        expected_domain.append(c[0][0]<c[0][1])
        expected_domain.extend(c[0][g]<c[0][g+1] for g in range(2,m-1))
    else:
        for g in range(m-1):
            expected_domain.append(z3.Or(c[0][g]<c[0][g+1],
                z3.And(c[0][g]==c[0][g+1],c[1][g]<c[1][g+1]),
                z3.And(c[0][g]==c[0][g+1],c[1][g]==c[1][g+1],c[2][g]<=c[2][g+1])))
    assert sorted(map(boolean,assertions[:domain_count]),key=repr)==sorted(map(boolean,expected_domain),key=repr)
    clauses=[]
    for a,clause in zip(allocations,assertions[domain_count:]):
        assert z3.is_or(clause)
        actual=set()
        for atom in clause.children():
            # Python's reflected comparison turns 0 > symbolic_sum into
            # symbolic_sum < 0. Comparing two empty sums yields False.
            if z3.is_false(atom):
                actual.add((0,)*dimension)
                continue
            kind=atom.decl().kind()
            assert kind in [z3.Z3_OP_GT,z3.Z3_OP_LT],atom
            coeff=tuple(x-y for x,y in zip(polynomial(atom.arg(0)),polynomial(atom.arg(1))))
            if kind==z3.Z3_OP_LT:coeff=tuple(-v for v in coeff)
            assert all(v.denominator==1 for v in coeff)
            actual.add(tuple(int(v) for v in coeff))
        expected=set()
        for i in range(3):
            removals=[None] if i==0 else [g for g in range(m) if a[g]==i]
            for removed in removals:
                for j in range(3):
                    if j==i:continue
                    vector=[0]*dimension
                    for h in range(m):
                        vector[i*m+h]=int(a[h]==i and h!=removed)-int(a[h]==j)
                    expected.add(tuple(vector))
        assert actual==expected,(m,a,actual^expected)
        clauses.append(actual)
    fixtures=[
        ('all_zero',[[0]*m for i in range(3)]),
        ('identical_ones',[[1]*m for i in range(3)]),
        ('zero_prescribed_row',[[0]*m,list(range(1,m+1)),list(range(m,0,-1))]),
        ('zero_other_row_1',[list(range(1,m+1)),[0]*m,list(range(m,0,-1))]),
        ('zero_other_row_2',[list(range(1,m+1)),list(range(m,0,-1)),[0]*m]),
        ('zeros_and_ties',[[0,0,1,1,2,2,3][:m],[2,0,0,2,1,1,0][:m],[0,1,0,1,0,1,2][:m]]),
        ('strict_positive',[[1,4,2,5,6,7,8][:m],[1,7,3,5,9,13,17][:m],[7,1,8,5,2,9,6][:m]]),
    ]
    point_results=[]
    for label,C in fixtures:
        flat=sum(C,[])+[1];atomic={}
        for atoms in clauses:
            for v in atoms:
                if v not in atomic:atomic[v]=sum(x*y for x,y in zip(v,flat))>0
        count=0
        for a,atoms in zip(allocations,clauses):
            A=[[g for g in range(m) if a[g]==i] for i in range(3)]
            V=[[sum(C[i][g] for g in A[j]) for j in range(3)] for i in range(3)]
            prescribed=all(V[0][0]<=V[0][j] for j in [1,2])
            others_efx=all(V[i][i]-C[i][g]<=V[i][j] for i in [1,2] for g in A[i] for j in range(3) if j!=i)
            direct_bad=not (prescribed and others_efx)
            assert any(atomic[v] for v in atoms)==direct_bad,(m,label,a)
            count+=int(not direct_bad)
        empty_checked=0
        if reduced and min(flat[:-1])>0:
            for a in product(range(3),repeat=m):
                if len(set(a))==3:continue
                A=[[g for g in range(m) if a[g]==i] for i in range(3)]
                V=[[sum(C[i][g] for g in A[j]) for j in range(3)] for i in range(3)]
                p=all(V[0][0]<=V[0][j] for j in [1,2])
                e=all(V[i][i]-C[i][g]<=V[i][j] for i in [1,2] for g in A[i] for j in range(3) if j!=i)
                assert not(p and e)
                empty_checked+=1
        point_results.append(dict(fixture=label,clauses_checked=len(allocations),acceptable_allocations_among_checked=count,empty_omissions_checked=empty_checked))
    return dict(m=m,input=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),domain_assertions=domain_count,domain_structural_match='PASS',allocation_clauses=len(allocations),exact_literal_coefficient_match='PASS',point_checks=point_results,result='PASS')


if __name__=='__main__':
    started=time.monotonic()
    results=[
        audit(6,'economics_problem2/work/structural_designated_m6.standard.smt2',False),
        audit(7,'economics_problem2/work/structural_designated_reduced_m7_seed0.standard.smt2',True),
    ]
    out=dict(results=results,elapsed_s=time.monotonic()-started,result='PASS',interpretation='Every actual allocation clause has exactly the specified strict linear literals, modulo duplicate disjuncts, reversed comparison orientation, and False representing the empty-sum comparison 0 > 0. Canonical domain assertions match independently constructed definitions. Point checks are separate from domain membership; zero/tie fixtures test clauses, while empty-allocation omission is checked only for positive costs.')
    Path('economics_problem2/work/structural_prescribed_formula_audit.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out),flush=True)
