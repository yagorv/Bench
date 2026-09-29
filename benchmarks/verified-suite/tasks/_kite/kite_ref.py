"""Kite: intérprete de referencia (solo biblioteca estándar). Interfaz pública: run(source: str) -> str"""
import sys
import threading

DIGITS = "0123456789"
IDSTART = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
KEYWORDS = {"let", "fn", "if", "else", "while", "for", "in", "return", "break", "continue", "true", "false", "nil",
            "and", "or", "not"}


class KiteError(Exception):
    pass


class KiteSyntax(Exception):
    pass


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


class _Return(Exception):
    def __init__(self, value):
        self.value = value


def tokenize(src):
    toks, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\r\n":
            i += 1
        elif c == "#":
            while i < n and src[i] != "\n":
                i += 1
        elif c in DIGITS:
            j = i
            while j < n and src[j] in DIGITS:
                j += 1
            if j < n and (src[j] in IDSTART):
                raise KiteSyntax()
            toks.append(("num", int(src[i:j])))
            i = j
        elif c in IDSTART:
            j = i
            while j < n and (src[j] in IDSTART or src[j] in DIGITS):
                j += 1
            word = src[i:j]
            toks.append(("kw" if word in KEYWORDS else "id", word))
            i = j
        elif c == '"':
            j, buf = i + 1, []
            while True:
                if j >= n or src[j] == "\n":
                    raise KiteSyntax()
                ch = src[j]
                if ch == '"':
                    break
                if ch == "\\":
                    j += 1
                    if j >= n or src[j] not in "nt\"\\":
                        raise KiteSyntax()
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}[src[j]])
                else:
                    buf.append(ch)
                j += 1
            toks.append(("str", "".join(buf)))
            i = j + 1
        elif src[i:i + 2] in ("==", "!=", "<=", ">="):
            toks.append(("op", src[i:i + 2]))
            i += 2
        elif c in "+-*/%<>=(){}[],;:":
            toks.append(("op", c))
            i += 1
        else:
            raise KiteSyntax()
    toks.append(("eof", None))
    return toks


class Parser:
    def __init__(self, toks):
        self.t = toks
        self.p = 0
        self.loop_depth = 0
        self.fn_depth = 0

    def peek(self):
        return self.t[self.p]

    def next(self):
        tok = self.t[self.p]
        self.p += 1
        return tok

    def is_op(self, v):
        return self.peek() == ("op", v)

    def is_kw(self, v):
        return self.peek() == ("kw", v)

    def expect_op(self, v):
        if not self.is_op(v):
            raise KiteSyntax()
        self.p += 1

    def expect_id(self):
        tok = self.next()
        if tok[0] != "id":
            raise KiteSyntax()
        return tok[1]

    def program(self):
        stmts = []
        while self.peek()[0] != "eof":
            stmts.append(self.statement())
        return stmts

    def block(self):
        self.expect_op("{")
        stmts = []
        while not self.is_op("}"):
            if self.peek()[0] == "eof":
                raise KiteSyntax()
            stmts.append(self.statement())
        self.p += 1
        return stmts

    def params(self):
        self.expect_op("(")
        names = []
        if not self.is_op(")"):
            while True:
                names.append(self.expect_id())
                if self.is_op(","):
                    self.p += 1
                else:
                    break
        self.expect_op(")")
        if len(set(names)) != len(names):
            raise KiteSyntax()
        return names

    def fn_body(self):
        saved = self.loop_depth
        self.loop_depth = 0
        self.fn_depth += 1
        body = self.block()
        self.fn_depth -= 1
        self.loop_depth = saved
        return body

    def statement(self):
        tok = self.peek()
        if tok == ("kw", "let"):
            self.p += 1
            name = self.expect_id()
            self.expect_op("=")
            e = self.expr()
            self.expect_op(";")
            return ("let", name, e)
        if tok == ("kw", "fn") and self.t[self.p + 1][0] == "id":
            self.p += 1
            name = self.expect_id()
            params = self.params()
            return ("fndecl", name, params, self.fn_body())
        if tok == ("kw", "if"):
            return self.if_stmt()
        if tok == ("kw", "while"):
            self.p += 1
            self.expect_op("(")
            cond = self.expr()
            self.expect_op(")")
            self.loop_depth += 1
            body = self.block()
            self.loop_depth -= 1
            return ("while", cond, body)
        if tok == ("kw", "for"):
            self.p += 1
            name = self.expect_id()
            if not self.is_kw("in"):
                raise KiteSyntax()
            self.p += 1
            it = self.expr()
            self.loop_depth += 1
            body = self.block()
            self.loop_depth -= 1
            return ("for", name, it, body)
        if tok == ("kw", "return"):
            if self.fn_depth == 0:
                raise KiteSyntax()
            self.p += 1
            e = None
            if not self.is_op(";"):
                e = self.expr()
            self.expect_op(";")
            return ("ret", e)
        if tok == ("kw", "break") or tok == ("kw", "continue"):
            if self.loop_depth == 0:
                raise KiteSyntax()
            self.p += 1
            self.expect_op(";")
            return ("brk",) if tok[1] == "break" else ("cont",)
        if tok == ("op", "{"):
            return ("block", self.block())
        e = self.expr()
        if self.is_op("="):
            if e[0] not in ("id", "idx"):
                raise KiteSyntax()
            self.p += 1
            v = self.expr()
            self.expect_op(";")
            return ("assign", e, v)
        self.expect_op(";")
        return ("expr", e)

    def if_stmt(self):
        self.p += 1
        self.expect_op("(")
        cond = self.expr()
        self.expect_op(")")
        then = self.block()
        els = None
        if self.is_kw("else"):
            self.p += 1
            els = [self.if_stmt()] if self.is_kw("if") else self.block()
        return ("if", cond, then, els)

    def expr(self):
        return self.or_expr()

    def or_expr(self):
        left = self.and_expr()
        while self.is_kw("or"):
            self.p += 1
            left = ("or", left, self.and_expr())
        return left

    def and_expr(self):
        left = self.not_expr()
        while self.is_kw("and"):
            self.p += 1
            left = ("and", left, self.not_expr())
        return left

    def not_expr(self):
        if self.is_kw("not"):
            self.p += 1
            return ("not", self.not_expr())
        return self.cmp_expr()

    def cmp_expr(self):
        left = self.add_expr()
        while self.peek()[0] == "op" and self.peek()[1] in ("==", "!=", "<", "<=", ">", ">="):
            op = self.next()[1]
            left = ("bin", op, left, self.add_expr())
        return left

    def add_expr(self):
        left = self.mul_expr()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            left = ("bin", op, left, self.mul_expr())
        return left

    def mul_expr(self):
        left = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/", "%"):
            op = self.next()[1]
            left = ("bin", op, left, self.unary())
        return left

    def unary(self):
        if self.is_op("-"):
            self.p += 1
            return ("neg", self.unary())
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while True:
            if self.is_op("("):
                self.p += 1
                args = []
                if not self.is_op(")"):
                    while True:
                        args.append(self.expr())
                        if self.is_op(","):
                            self.p += 1
                        else:
                            break
                self.expect_op(")")
                e = ("call", e, args)
            elif self.is_op("["):
                self.p += 1
                idx = self.expr()
                self.expect_op("]")
                e = ("idx", e, idx)
            else:
                return e

    def primary(self):
        kind, val = self.next()
        if kind == "num":
            return ("lit", val)
        if kind == "str":
            return ("lit", val)
        if kind == "id":
            return ("id", val)
        if kind == "kw":
            if val == "true":
                return ("lit", True)
            if val == "false":
                return ("lit", False)
            if val == "nil":
                return ("lit", None)
            if val == "fn":
                params = self.params()
                return ("lam", params, self.fn_body())
            raise KiteSyntax()
        if (kind, val) == ("op", "("):
            e = self.expr()
            self.expect_op(")")
            return e
        if (kind, val) == ("op", "["):
            items = []
            if not self.is_op("]"):
                while True:
                    items.append(self.expr())
                    if self.is_op(","):
                        self.p += 1
                    else:
                        break
            self.expect_op("]")
            return ("arr", items)
        if (kind, val) == ("op", "{"):
            items = []
            if not self.is_op("}"):
                while True:
                    k = self.next()
                    if k[0] != "str":
                        raise KiteSyntax()
                    self.expect_op(":")
                    items.append((k[1], self.expr()))
                    if self.is_op(","):
                        self.p += 1
                    else:
                        break
            self.expect_op("}")
            return ("dict", items)
        raise KiteSyntax()


class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def find(self, name):
        e = self
        while e is not None:
            if name in e.vars:
                return e
            e = e.parent
        raise KiteError("undefined variable " + name)

    def declare(self, name, value):
        if name in self.vars:
            raise KiteError("redeclaration " + name)
        self.vars[name] = value


class Func:
    def __init__(self, name, params, body, env):
        self.name, self.params, self.body, self.env = name, params, body, env


class Builtin:
    def __init__(self, name, fn):
        self.name, self.fn = name, fn


def is_int(v):
    return type(v) is int


def truthy(v):
    if v is None:
        return False
    if type(v) is bool:
        return v
    if type(v) is int:
        return v != 0
    if type(v) is str:
        return v != ""
    if type(v) in (list, dict):
        return len(v) > 0
    return True


def kite_eq(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is list:
        return len(a) == len(b) and all(kite_eq(x, y) for x, y in zip(a, b))
    if type(a) is dict:
        return set(a) == set(b) and all(kite_eq(a[k], b[k]) for k in a)
    if isinstance(a, (Func, Builtin)):
        return a is b
    return a == b


def trunc_div(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def trunc_mod(a, b):
    return a - b * trunc_div(a, b)


def to_str(v, top=True):
    if v is None:
        return "nil"
    if type(v) is bool:
        return "true" if v else "false"
    if type(v) is int:
        return str(v)
    if type(v) is str:
        return v if top else '"' + v + '"'
    if type(v) is list:
        return "[" + ", ".join(to_str(x, False) for x in v) + "]"
    if type(v) is dict:
        return "{" + ", ".join('"' + k + '": ' + to_str(x, False) for k, x in v.items()) + "}"
    if isinstance(v, Func):
        return "<fn " + v.name + ">" if v.name else "<fn>"
    return "<builtin " + v.name + ">"


class Interp:
    def __init__(self):
        self.out = []
        self.builtins = Env()
        self.install_builtins()
        self.globals = Env(self.builtins)

    # ---- builtins
    def install_builtins(self):
        def need(args, n):
            if len(args) != n:
                raise KiteError("wrong argument count")

        def b_print(args):
            need(args, 1)
            self.out.append(to_str(args[0]) + "\n")

        def b_len(args):
            need(args, 1)
            if type(args[0]) not in (str, list, dict):
                raise KiteError("type mismatch")
            return len(args[0])

        def b_str(args):
            need(args, 1)
            return to_str(args[0])

        def b_int(args):
            need(args, 1)
            v = args[0]
            if type(v) is int:
                return v
            if type(v) is not str:
                raise KiteError("type mismatch")
            body = v[1:] if v.startswith("-") else v
            if body == "" or any(ch not in DIGITS for ch in body):
                raise KiteError("invalid integer")
            return int(v)

        def b_push(args):
            need(args, 2)
            if type(args[0]) is not list:
                raise KiteError("type mismatch")
            args[0].append(args[1])
            return None

        def b_pop(args):
            need(args, 1)
            if type(args[0]) is not list:
                raise KiteError("type mismatch")
            if not args[0]:
                raise KiteError("index out of range")
            return args[0].pop()

        def b_range(args):
            if len(args) not in (1, 2):
                raise KiteError("wrong argument count")
            if not all(is_int(a) for a in args):
                raise KiteError("type mismatch")
            lo, hi = (0, args[0]) if len(args) == 1 else (args[0], args[1])
            return list(range(lo, hi))

        def b_keys(args):
            need(args, 1)
            if type(args[0]) is not dict:
                raise KiteError("type mismatch")
            return list(args[0].keys())

        def b_has(args):
            need(args, 2)
            if type(args[0]) is not dict or type(args[1]) is not str:
                raise KiteError("type mismatch")
            return args[1] in args[0]

        def b_substr(args):
            need(args, 3)
            s, i, j = args
            if type(s) is not str or not is_int(i) or not is_int(j):
                raise KiteError("type mismatch")
            n = len(s)
            i, j = max(0, min(i, n)), max(0, min(j, n))
            return s[i:j] if i < j else ""

        def b_upper(args):
            need(args, 1)
            if type(args[0]) is not str:
                raise KiteError("type mismatch")
            return args[0].upper()

        def b_lower(args):
            need(args, 1)
            if type(args[0]) is not str:
                raise KiteError("type mismatch")
            return args[0].lower()

        def b_split(args):
            need(args, 2)
            if type(args[0]) is not str or type(args[1]) is not str:
                raise KiteError("type mismatch")
            if args[1] == "":
                raise KiteError("invalid argument")
            return args[0].split(args[1])

        def b_join(args):
            need(args, 2)
            if type(args[0]) is not list or type(args[1]) is not str:
                raise KiteError("type mismatch")
            if not all(type(x) is str for x in args[0]):
                raise KiteError("type mismatch")
            return args[1].join(args[0])

        def b_sort(args):
            need(args, 1)
            a = args[0]
            if type(a) is not list:
                raise KiteError("type mismatch")
            if all(is_int(x) for x in a) or all(type(x) is str for x in a):
                return sorted(a)
            raise KiteError("type mismatch")

        def b_abs(args):
            need(args, 1)
            if not is_int(args[0]):
                raise KiteError("type mismatch")
            return abs(args[0])

        def b_min(args):
            need(args, 2)
            if not (is_int(args[0]) and is_int(args[1])):
                raise KiteError("type mismatch")
            return min(args)

        def b_max(args):
            need(args, 2)
            if not (is_int(args[0]) and is_int(args[1])):
                raise KiteError("type mismatch")
            return max(args)

        def b_ord(args):
            need(args, 1)
            if type(args[0]) is not str:
                raise KiteError("type mismatch")
            if len(args[0]) != 1:
                raise KiteError("invalid argument")
            return ord(args[0])

        def b_chr(args):
            need(args, 1)
            if not is_int(args[0]):
                raise KiteError("type mismatch")
            if not 0 <= args[0] <= 1114111:
                raise KiteError("invalid argument")
            return chr(args[0])

        for name, fn in list(locals().items()):
            if name.startswith("b_"):
                self.builtins.vars[name[2:]] = Builtin(name[2:], fn)

    # ---- ejecución
    def run_program(self, stmts):
        try:
            self.exec_stmts(stmts, self.globals)
        except KiteError as e:
            self.out.append("error: " + str(e) + "\n")

    def exec_stmts(self, stmts, env):
        for s in stmts:
            self.exec_stmt(s, env)

    def exec_block(self, stmts, env):
        self.exec_stmts(stmts, Env(env))

    def exec_stmt(self, s, env):
        k = s[0]
        if k == "expr":
            self.eval(s[1], env)
        elif k == "let":
            env.declare(s[1], self.eval(s[2], env))
        elif k == "assign":
            target, value = s[1], self.eval(s[2], env)
            if target[0] == "id":
                env.find(target[1]).vars[target[1]] = value
            else:
                obj = self.eval(target[1], env)
                idx = self.eval(target[2], env)
                self.store_index(obj, idx, value)
        elif k == "if":
            if truthy(self.eval(s[1], env)):
                self.exec_block(s[2], env)
            elif s[3] is not None:
                self.exec_block(s[3], env)
        elif k == "while":
            while truthy(self.eval(s[1], env)):
                try:
                    self.exec_block(s[2], env)
                except _Break:
                    break
                except _Continue:
                    continue
        elif k == "for":
            it = self.eval(s[2], env)
            if type(it) is str or type(it) is list:
                seq = list(it)
            elif type(it) is dict:
                seq = list(it.keys())
            else:
                raise KiteError("type mismatch")
            for item in seq:
                loop_env = Env(env)
                loop_env.vars[s[1]] = item
                try:
                    self.exec_block(s[3], loop_env)
                except _Break:
                    break
                except _Continue:
                    continue
        elif k == "fndecl":
            env.declare(s[1], Func(s[1], s[2], s[3], env))
        elif k == "ret":
            raise _Return(None if s[1] is None else self.eval(s[1], env))
        elif k == "brk":
            raise _Break()
        elif k == "cont":
            raise _Continue()
        elif k == "block":
            self.exec_block(s[1], env)

    def store_index(self, obj, idx, value):
        if type(obj) is list:
            if not is_int(idx):
                raise KiteError("type mismatch")
            n = len(obj)
            if idx < 0:
                idx += n
            if not 0 <= idx < n:
                raise KiteError("index out of range")
            obj[idx] = value
        elif type(obj) is dict:
            if type(idx) is not str:
                raise KiteError("type mismatch")
            obj[idx] = value
        else:
            raise KiteError("type mismatch")

    def load_index(self, obj, idx):
        if type(obj) is list or type(obj) is str:
            if not is_int(idx):
                raise KiteError("type mismatch")
            n = len(obj)
            if idx < 0:
                idx += n
            if not 0 <= idx < n:
                raise KiteError("index out of range")
            return obj[idx]
        if type(obj) is dict:
            if type(idx) is not str:
                raise KiteError("type mismatch")
            if idx not in obj:
                raise KiteError("key not found")
            return obj[idx]
        raise KiteError("type mismatch")

    def eval(self, e, env):
        k = e[0]
        if k == "lit":
            return e[1]
        if k == "id":
            return env.find(e[1]).vars[e[1]]
        if k == "bin":
            return self.binop(e[1], self.eval(e[2], env), self.eval(e[3], env))
        if k == "and":
            left = self.eval(e[1], env)
            return left if not truthy(left) else self.eval(e[2], env)
        if k == "or":
            left = self.eval(e[1], env)
            return left if truthy(left) else self.eval(e[2], env)
        if k == "not":
            return not truthy(self.eval(e[1], env))
        if k == "neg":
            v = self.eval(e[1], env)
            if not is_int(v):
                raise KiteError("type mismatch")
            return -v
        if k == "call":
            f = self.eval(e[1], env)
            args = [self.eval(a, env) for a in e[2]]
            return self.call(f, args)
        if k == "idx":
            return self.load_index(self.eval(e[1], env), self.eval(e[2], env))
        if k == "arr":
            return [self.eval(x, env) for x in e[1]]
        if k == "dict":
            d = {}
            for key, ex in e[1]:
                d[key] = self.eval(ex, env)
            return d
        if k == "lam":
            return Func(None, e[1], e[2], env)
        raise AssertionError(k)

    def call(self, f, args):
        if isinstance(f, Builtin):
            return f.fn(args)
        if not isinstance(f, Func):
            raise KiteError("not callable")
        if len(args) != len(f.params):
            raise KiteError("wrong argument count")
        fenv = Env(f.env)
        for name, val in zip(f.params, args):
            fenv.vars[name] = val
        try:
            self.exec_stmts(f.body, fenv)
        except _Return as r:
            return r.value
        return None

    def binop(self, op, a, b):
        if op == "==":
            return kite_eq(a, b)
        if op == "!=":
            return not kite_eq(a, b)
        if op == "+":
            if is_int(a) and is_int(b):
                return a + b
            if type(a) is str and type(b) is str:
                return a + b
            if type(a) is list and type(b) is list:
                return a + b
            raise KiteError("type mismatch")
        if op == "*":
            if is_int(a) and is_int(b):
                return a * b
            if type(a) is str and is_int(b):
                return a * max(0, b)
            if is_int(a) and type(b) is str:
                return b * max(0, a)
            raise KiteError("type mismatch")
        if op in ("-", "/", "%"):
            if not (is_int(a) and is_int(b)):
                raise KiteError("type mismatch")
            if op == "-":
                return a - b
            if b == 0:
                raise KiteError("division by zero")
            return trunc_div(a, b) if op == "/" else trunc_mod(a, b)
        # <, <=, >, >=
        if (is_int(a) and is_int(b)) or (type(a) is str and type(b) is str):
            return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        raise KiteError("type mismatch")


def _run(source):
    try:
        prog = Parser(tokenize(source)).program()
    except KiteSyntax:
        return "error: syntax\n"
    it = Interp()
    it.run_program(prog)
    return "".join(it.out)


def run(source):
    """Ejecuta un programa Kite y devuelve toda su salida estándar como texto."""
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(256 * 1024 * 1024)
    box = []
    t = threading.Thread(target=lambda: box.append(_run(source)), daemon=True)
    t.start()
    t.join()
    return box[0]


if __name__ == "__main__":
    sys.stdout.write(run(sys.stdin.read()))
