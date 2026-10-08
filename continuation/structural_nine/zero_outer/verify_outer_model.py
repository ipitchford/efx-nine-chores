#!/usr/bin/env python3
"""Standard-library evaluation of every serialized zero-outer assertion."""
from fractions import Fraction
import hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def parse(text):
    tokens=re.findall(r'\(|\)|[^\s()]+',text);position=0
    def term():
        nonlocal position
        token=tokens[position];position+=1
        if token!='(':return token
        result=[]
        while tokens[position]!=')':result.append(term())
        position+=1;return result
    result=term();assert position==len(tokens);return result


def evaluate(term,values):
    if isinstance(term,str):
        if term=='true':return True
        if term=='false':return False
        return values[term] if term in values else Fraction(term)
    operator,*arguments=term;items=[evaluate(a,values) for a in arguments]
    if operator=='+':return sum(items,Fraction(0))
    if operator=='-':
        assert len(items) in (1,2)
        return -items[0] if len(items)==1 else items[0]-items[1]
    if operator=='*':
        product=Fraction(1)
        for item in items:product*=item
        return product
    if operator=='>':assert len(items)==2;return items[0]>items[1]
    if operator=='or':assert all(type(x) is bool for x in items);return any(items)
    raise AssertionError(('Unsupported operator',operator))


def main():
    source=ROOT/'zero_minimum_final_outer.smt2';model_file=ROOT/'run1_model.json'
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    model=json.loads(model_file.read_text());assert sha(source)==model['input_sha256']
    values={name:Fraction(value) for name,value in model['coordinates'].items()}
    declared=set();assertions=0;failed=[]
    for line in source.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith(';'):continue
        command=parse(line)
        if command[0]=='declare-fun':
            assert command[2]==[] and command[3]=='Real';declared.add(command[1])
        elif command[0]=='assert':
            assert len(command)==2
            if evaluate(command[1],values) is not True:failed.append(assertions)
            assertions+=1
        else:assert command[0] in ('set-logic','check-sat')
    assert declared==set(values) and len(declared)==14
    assert assertions==6305 and not failed
    rows=[]
    for i in (1,2):rows.append(['1' if g==0 else '0' if g==i else str(values[f'c_{i}_{g}']) for g in range(9)])
    receipt=dict(status='PASS_EXACT_OUTER_MODEL_ONLY',input_sha256=sha(source),model_sha256=sha(model_file),
                 exact_assertions_checked=assertions,free_coordinates=len(values),failed_assertions=failed,
                 candidate_rows_1_and_2=rows,arithmetic='fractions.Fraction, standard library only',
                 scope='These rows satisfy the learned outer exclusions. No first row has been supplied and no three-agent counterexample follows.')
    (ROOT/'run1_model_verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))


if __name__=='__main__':main()
