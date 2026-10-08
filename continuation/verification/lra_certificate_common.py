"""Small, solver-free exact primitives for checking captured LRA certificates.

This module does not import the untrusted producer, Z3, NumPy, or SciPy.
SMT parsing deliberately accepts only the arithmetic/CNF fragment used here.
"""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def json_loads(text):
    return json.loads(text, object_pairs_hook=no_duplicate_keys,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError('nonfinite JSON number: ' + value)))


def json_file(path):
    return json_loads(Path(path).read_text())


def json_lines(path):
    with Path(path).open() as stream:
        for number, line in enumerate(stream):
            require(bool(line.strip()), f'blank JSONL line {number}')
            value = json_loads(line)
            require(type(value) is dict, f'nonobject JSONL line {number}')
            yield value


def rational(value):
    # In particular reject float underflow and bool's subclassing of int.
    require(type(value) in (int, str), 'rational must be an integer or exact string')
    return Fraction(value)


def parse_sexpr(text):
    stack, roots = [], []
    for token in re.findall(r'\(|\)|[^\s()]+', text):
        if token == '(':
            row = []
            (stack[-1] if stack else roots).append(row)
            stack.append(row)
        elif token == ')':
            require(bool(stack), 'unmatched closing parenthesis')
            stack.pop()
        else:
            require(bool(stack), 'token outside command')
            stack[-1].append(token)
    require(not stack and len(roots) == 1, 'malformed command')
    return roots[0]


def commands(path):
    depth, lines = 0, []
    with Path(path).open() as stream:
        for line in stream:
            line = line.split(';', 1)[0]
            if not line.strip():
                continue
            require('"' not in line and '|' not in line, 'quoted syntax unsupported')
            depth += line.count('(') - line.count(')')
            require(depth >= 0, 'unbalanced parentheses')
            lines.append(line)
            if depth == 0:
                yield parse_sexpr(' '.join(lines))
                lines = []
    require(depth == 0 and not lines, 'truncated SMT input')


def expand_let(expr, environment=None):
    environment = {} if environment is None else environment
    if type(expr) is str:
        return environment.get(expr, expr)
    require(type(expr) is list and bool(expr), 'empty expression')
    if expr[0] == 'let':
        require(len(expr) == 3 and type(expr[1]) is list, 'malformed let')
        names = [b[0] for b in expr[1]]
        require(all(type(b) is list and len(b) == 2 for b in expr[1]), 'bad binding')
        require(len(set(names)) == len(names), 'duplicate let name')
        extended = dict(environment)
        # Simultaneous, not sequential, SMT-LIB let semantics.
        extended.update((name, expand_let(value, environment)) for name, value in expr[1])
        return expand_let(expr[2], extended)
    return [expand_let(part, environment) for part in expr]


def frozen(expr):
    return tuple(frozen(x) for x in expr) if type(expr) is list else expr


class LinearReader:
    def __init__(self, variables, atoms):
        self.names = list(variables)
        self.positions = {name: j for j, name in enumerate(variables)}
        self.width = len(variables) + 1
        self.atoms = atoms
        self.by_vector = {tuple(vector): ident for ident, vector in atoms.items()}
        require(len(self.by_vector) == len(atoms), 'duplicate affine atom')
        self.affine_cache, self.literal_cache = {}, {}
        self.used_atoms = set()

    def affine(self, expr):
        key = frozen(expr)
        if key in self.affine_cache:
            return self.affine_cache[key]
        if type(expr) is str:
            out = [Fraction(0)] * self.width
            if expr in self.positions:
                out[self.positions[expr]] = Fraction(1)
            else:
                out[-1] = Fraction(expr)
        else:
            require(type(expr) is list and len(expr) >= 1, 'bad affine expression')
            op, *args = expr
            parts = [self.affine(a) for a in args]
            if op == '+':
                out = [sum(p[j] for p in parts) for j in range(self.width)]
            elif op == '-':
                require(bool(parts), 'empty subtraction')
                out = ([-v for v in parts[0]] if len(parts) == 1 else
                       [parts[0][j] - sum(p[j] for p in parts[1:]) for j in range(self.width)])
            elif op == '*':
                nonconstant = [p for p in parts if any(p[:-1])]
                require(len(nonconstant) <= 1, 'nonlinear multiplication')
                scale = math.prod(p[-1] for p in parts if not any(p[:-1]))
                out = ([scale * v for v in nonconstant[0]] if nonconstant else
                       [Fraction(0)] * (self.width - 1) + [scale])
            elif op == '/':
                require(len(parts) == 2 and not any(parts[1][:-1]), 'nonconstant denominator')
                require(parts[1][-1] != 0, 'division by zero')
                out = [v / parts[1][-1] for v in parts[0]]
            else:
                raise ValueError('unsupported affine operation: ' + str(op))
        answer = tuple(Fraction(v) for v in out)
        self.affine_cache[key] = answer
        return answer

    def literal(self, expr):
        key = frozen(expr)
        if key in self.literal_cache:
            return self.literal_cache[key]
        if expr in ('true', 'false'):
            answer = 1 if expr == 'true' else -1
        else:
            require(type(expr) is list and bool(expr), 'expected arithmetic literal')
            if expr[0] == 'not':
                require(len(expr) == 2, 'bad negation')
                answer = -self.literal(expr[1])
            else:
                require(len(expr) == 3 and expr[0] in ('<=', '<', '>=', '>'),
                        'unsupported literal (equality deliberately rejected)')
                op, lhs, rhs = expr
                left, right = self.affine(lhs), self.affine(rhs)
                vector = [a - b for a, b in zip(left, right)]
                # Weak inequality is always the atom; strictness is its complement.
                if op in ('>=', '<'):
                    vector = [-v for v in vector]
                sign = -1 if op in ('>', '<') else 1
                denominator = math.lcm(*(q.denominator for q in vector))
                integer = [int(q * denominator) for q in vector]
                divisor = math.gcd(*integer)
                if divisor:
                    integer = [v // divisor for v in integer]
                if not any(integer[:-1]):
                    answer = sign * (1 if integer[-1] <= 0 else -1)
                else:
                    # Do not change orientation: a<=0 and -a<=0 are distinct at 0.
                    require(tuple(integer) in self.by_vector, 'original atom missing from capture')
                    ident = self.by_vector[tuple(integer)]
                    self.used_atoms.add(ident)
                    answer = sign * ident
        self.literal_cache[key] = answer
        return answer

    def clause(self, expression):
        expression = expand_let(expression)
        parts = expression[1:] if type(expression) is list and expression[0] == 'or' else [expression]
        literals = {self.literal(part) for part in parts}
        if 1 in literals or any(-literal in literals for literal in literals):
            return None
        literals.discard(-1)
        return sorted(literals)


def read_atoms(path, width):
    atoms = {}
    vectors = set()
    for record in json_lines(path):
        require(set(record) == {'id', 'affine_le_zero'}, 'unexpected atom fields')
        ident, vector = record['id'], record['affine_le_zero']
        require(type(ident) is int and ident == len(atoms) + 2, 'atom IDs must be consecutive from 2')
        require(type(vector) is list and len(vector) == width, 'wrong atom dimension')
        require(all(type(v) is int for v in vector), 'atom coefficients must be exact integers')
        require(any(vector[:-1]), 'constant must use reserved atom 1')
        require(math.gcd(*vector) == 1, 'atom vector is not primitive')
        require(tuple(vector) not in vectors, 'duplicate oriented atom')
        vectors.add(tuple(vector))
        atoms[ident] = vector
    return atoms


def validate_clause(clause, maximum, allow_reserved=False):
    require(type(clause) is list, 'clause must be an array')
    require(all(type(lit) is int and 0 < abs(lit) <= maximum for lit in clause), 'invalid literal ID')
    require(allow_reserved or all(abs(lit) >= 2 for lit in clause), 'unexpected reserved truth literal')
    require(clause == sorted(set(clause)), 'clause must be sorted without repetitions')
    require(not any(-lit in clause for lit in clause), 'tautological clause must be omitted')
    return clause


def capture_files(capture):
    capture = Path(capture)
    receipt = json_file(capture / 'receipt.json')
    require('finished_at_utc' in receipt and type(receipt.get('files')) is dict,
            'capture has no terminal file manifest')
    required = {'atoms.jsonl', 'input_clauses.jsonl', 'theory_clauses.jsonl'}
    require(required <= set(receipt['files']), 'incomplete capture manifest')
    # Callback assumptions have no proof role. Derived packages may omit them.
    require(set(receipt['files']) <= required | {'rup_clauses.jsonl', 'assumptions.jsonl'}, 'unexpected capture stream')
    bindings = {}
    for name, entry in receipt['files'].items():
        path = capture / name
        digest = sha256(path)
        require(digest == entry['sha256'] and path.stat().st_size == entry['bytes'],
                'capture hash/length mismatch: ' + name)
        bindings[name] = digest
    bindings['metadata.json'] = sha256(capture / 'metadata.json')
    bindings['receipt.json'] = sha256(capture / 'receipt.json')
    return receipt, bindings


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)
