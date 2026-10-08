"""Portable SMT2 syntax for frozen Z3-generated designated-target formulas.

Z3 writes unary '(+ c_i_g)' for singleton bundle sums. cvc5's parser rejects
this form, so we apply the identity (+ x)=x and check every assertion after
parsing both forms into Z3. Original files remain unchanged.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import z3


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def standardise(path):
    path=Path(path);src=path.read_text()
    dst,n=re.subn(r'\(\+\s+([^\s()]+)\s*\)',r'\1',src)
    if '(set-logic' not in dst:dst='(set-logic QF_LRA)\n'+dst
    target=path.with_suffix('.standard.smt2');target.write_text(dst)
    original=z3.parse_smt2_file(str(path));portable=z3.parse_smt2_file(str(target))
    assert len(original)==len(portable)
    assert all(z3.eq(z3.simplify(a),z3.simplify(b)) for a,b in zip(original,portable))
    return dict(original=str(path),original_sha256=sha(path),portable=str(target),portable_sha256=sha(target),unary_additions_eliminated=n,assertions_verified=len(original),verification='Every corresponding assertion has identical Z3-simplified AST; only unary addition identity and set-logic declaration change',result='PASS')


if __name__=='__main__':
    receipts=[standardise(p) for p in sys.argv[1:]]
    Path('economics_problem2/work/structural_standardise_receipt.json').write_text(json.dumps(receipts,indent=2))
    print(json.dumps(receipts),flush=True)
