# Task: fix a buggy interpreter

## Context
`kite.py` is an interpreter for the Kite language. It should comply with the specification below, but it contains **exactly 3 bugs** introduced on purpose
(each one at a different place in the file). There are no other differences with respect to the correct implementation.

## What to deliver
The **complete, corrected `kite.py`** (Python 3.10+, standard library only), with the same interface `run(source: str) -> str`.
- Change the minimum necessary: do not rewrite the interpreter or change its structure.
- The specification overrides the current behavior of the code: if the code and the specification disagree, the specification wins.
- The bugs are not visible in the examples below; you will have to review the code against the specification (and, if you can run Python, write your own test programs).

## How it is scored
About 350 hidden Kite programs are executed and the output is compared character by character. The score is the fraction of the tests that **failed with the original `kite.py`** and now pass
(tests that used to pass and stop passing are subtracted). Delivering the file unchanged scores 0. Limit per test program: 15 s.

---

# The Kite language

Kite is a small imperative programming language with first-class functions and closures. This specification is **complete and normative**:
if something is not allowed here, do not invent it; if something is defined here, do it exactly that way (including the awkward details).

Interface: a function `run(source: str) -> str` that executes a Kite program and returns **everything the program prints** as a single string.

## 1. Lexical structure
- Spaces, tabs and newlines separate tokens and are ignored. `#` starts a comment that runs to the end of the line.
- Identifiers: `[A-Za-z_][A-Za-z0-9_]*` (ASCII only). Reserved words: `let fn if else while for in return break continue true false nil and or not`.
- Integers: sequences of decimal digits `0-9` (leading zeros are allowed: `007` is 7). There are no decimals. A number immediately followed by a letter or `_` (`12ab`) is a syntax error.
- Strings: between double quotes. Valid escapes: `\n`, `\t`, `\"`, `\\`. Any other escape, an unterminated string, or a real line break inside the string is a syntax error. Any Unicode character is allowed inside strings.
- Operators and punctuation: `+ - * / % == != < <= > >= = ( ) { } [ ] , ; :`. Any other character outside a string or comment is a syntax error.

## 2. Values and types
`int` (arbitrary precision), `string`, `bool` (`true`/`false`), `nil`, `array`, `dict` (keys are always strings; insertion order is preserved) and `function` (user-defined or built-in).
Arrays and dicts are **reference types** (two variables can point to the same object). Integers, strings, bools and nil are immutable.
`bool` **is not** an integer: `true` and `1` are different values in every sense.

**Truthiness** (used by `if`, `while`, `not`, `and`, `or`): `false`, `nil`, `0`, `""`, `[]` and `{}` are falsy. Everything else is truthy (including functions).

## 3. Expressions (from lowest to highest precedence)
1. `or` — short-circuit; returns the first operand if it is truthy, otherwise the second (**the operand's value, not a bool**).
2. `and` — short-circuit; returns the first operand if it is falsy, otherwise the second.
3. `not e` — always returns a bool.
4. Comparisons `== != < <= > >=` (left-associative).
5. `+ -`
6. `* / %`
7. `-e` (unary negation; integers only)
8. Postfix: call `f(a, b)` and indexing `e[i]`.
9. Primaries: literals, identifiers, `( e )`, arrays `[a, b, c]`, dicts `{"k": e, ...}` (the keys of a literal must be **string literals**; if a key is repeated, the value is overwritten keeping the position of the first occurrence), and anonymous functions `fn(p1, p2) { ... }`. A trailing comma is not allowed in element lists, argument lists or parameter lists.

Operands are evaluated left to right and **both** are evaluated before types are checked (except for `and`/`or`). In a call, the called expression is evaluated first and then the arguments from left to right.

**Operators:**
- `+`: `int+int` adds; `string+string` concatenates; `array+array` creates a new array (concatenation). Any other combination: `type mismatch`.
- `-`: only `int-int`. `*`: `int*int`; `string*int` or `int*string` repeats the string (a count ≤ 0 gives `""`). Other combinations: `type mismatch`.
- `/` is integer division **truncated toward zero** (`-7 / 2` is `-3`). `%` is the remainder with the **sign of the dividend**, consistent with `/` (`a == (a/b)*b + a%b`; so `-7 % 3` is `-1` and `7 % -3` is `1`). Dividing or taking the remainder by zero: `division by zero`. Only `int` with `int`; otherwise `type mismatch` (the type check comes before the zero check).
- `< <= > >=`: only `int` with `int` or `string` with `string` (ordered by Unicode code point). Other combinations: `type mismatch`.
- `==` / `!=`: never fail. Values of different types are different (`true == 1` is `false`, `nil == false` is `false`). Arrays: element-by-element equality. Dicts: same keys (regardless of order) and equal values. Functions: equal only if they are the same object.
- Unary negation: only `int`, otherwise `type mismatch`.

**Indexing** `e[i]`:
- `array[int]` and `string[int]` (returns a 1-character string): a negative index `-k` means `length-k`. Out of range: `index out of range`.
- `dict[string]`: missing key → `key not found`.
- Any other container type or index type: `type mismatch`.

## 4. Statements
Every statement ends with `;` except those that end with a block `{ ... }`. There is no empty statement (`;` alone) — it is a syntax error.
- `let x = e;` declares `x` in the current scope. If `x` is already declared **in that same scope**: error `redeclaration x`.
- `x = e;` assigns to the nearest existing variable in the scope chain; if none exists: `undefined variable x`.
- `t[i] = e;` assigns to an element. Evaluation order: first `e`, then `t`, then `i`. For arrays the index must exist (negatives are valid as in reads; otherwise `index out of range`). For dicts the key must be a string (otherwise `type mismatch`); the key is created if missing or its value is updated keeping its position. For strings and any type that is neither array nor dict: `type mismatch`.
- The target of an assignment can only be an identifier or an indexing expression; anything else is a syntax error.
- `if (c) { ... } else { ... }` and `else if (c) { ... }`. Parentheses and braces are mandatory.
- `while (c) { ... }`.
- `for x in e { ... }`: `e` can be an array (iterates the elements), a string (iterates its characters) or a dict (iterates its keys); otherwise `type mismatch`. Iteration runs over a **copy** taken when the loop starts (modifying the array inside the loop does not change the iterations). The variable `x` is new on each iteration.
- `fn name(params) { ... }` declares `name` in the current scope (like `let`, with the same redeclaration error). There is no hoisting: it exists only from the moment the statement executes. Parameters cannot be repeated (syntax error).
- `return e;` / `return;` (returns `nil`), `break;`, `continue;`. `break` and `continue` may only appear inside a loop **of the same function**; `return` only inside a function. Otherwise it is a syntax error (detected before anything is executed).
- A bare block `{ ... }` as a statement creates a new scope (a statement that starts with `{` is always a block).
- Expression statement: `e;` (typically calls).

## 5. Scopes and functions
- Lexical scoping. Every block `{ ... }` (of `if`, `while`, `for`, or bare) creates a new scope each time it runs (in a `while`, **each iteration** has its own new scope). In a `for`, the loop variable lives in its own per-iteration scope and the body is a scope nested inside it (so `let x` inside the body can shadow the loop variable without error).
- Functions are **closures**: they capture the scope where they were created (by reference, not by copy). Anonymous and named functions behave the same.
- Calling a function creates a scope with the parameters; the body runs **directly in that scope** (so `let p = ...;` with `p` a parameter is `redeclaration p`). A number of arguments different from the number of parameters: `wrong argument count`. Calling something that is not a function: `not callable`. A function without `return` (or with `return;`) returns `nil`.
- Built-in functions live in a scope outside the global one: you can override them with `let` in the global scope without error.
- Test programs do not exceed a call depth of 2500 nor require more than a few hundred thousand operations.

## 6. Built-in functions
If the number of arguments is not the one indicated: `wrong argument count` (checked before types). Wrong type: `type mismatch`, except where another error is indicated.

| Function | Behavior |
|---|---|
| `print(x)` | Writes `str(x)` followed by `\n`. Returns `nil`. |
| `len(x)` | Length of a string (in characters), array or dict. |
| `str(x)` | Textual representation (see §7). |
| `int(x)` | An `int` is returned unchanged. A string that is exactly `-?[0-9]+` is converted; any other string: error `invalid integer`. Other types: `type mismatch`. |
| `push(a, x)` | Appends `x` to the end of array `a`. Returns `nil`. |
| `pop(a)` | Removes and returns the last element. Empty array: `index out of range`. |
| `range(n)` / `range(a, b)` | Array `[0..n-1]` / `[a..b-1]` (empty if `b <= a`). Integers only. Accepts 1 or 2 arguments. |
| `keys(d)` | Array with the dict's keys, in insertion order. |
| `has(d, k)` | `true` if the key (a string) exists in the dict. |
| `substr(s, i, j)` | Substring from `i` (inclusive) to `j` (exclusive). Both indices are first clamped to the range `[0, len(s)]`; if `i >= j`, returns `""`. There are **no** negative indices here. |
| `upper(s)`, `lower(s)` | Upper case / lower case. |
| `split(s, sep)` | Array of pieces (like Python's `str.split(sep)`). `sep == ""`: `invalid argument`. |
| `join(a, sep)` | Joins an array of strings with `sep`. If any element is not a string: `type mismatch`. |
| `sort(a)` | Returns a **new** array sorted ascending. All elements integers or all strings (an empty array is fine); otherwise `type mismatch`. |
| `abs(n)`, `min(a, b)`, `max(a, b)` | Integers only. |
| `ord(s)` | Code point of a string of exactly 1 character (otherwise `invalid argument`). |
| `chr(n)` | 1-character string for `0 <= n <= 1114111` (otherwise `invalid argument`). |

## 7. Textual representation (`str` and `print`)
- `int`: decimal (`-5`). `bool`: `true`/`false`. `nil`: `nil`.
- A string at the top level is printed as is. **Inside an array or dict**, it is wrapped in double quotes **without escaping anything** (the content is copied literally).
- Array: `[a, b, c]` (elements separated by `", "`); empty: `[]`.
- Dict: `{"k1": v1, "k2": v2}` (keys always in double quotes); empty: `{}`.
- Functions: `<fn name>` if named, `<fn>` if anonymous, `<builtin name>` for built-ins.

## 8. Errors and output
- **Syntax error** (lexical, grammar, or the static checks mentioned): `run` returns exactly `"error: syntax\n"`; nothing is executed.
- **Runtime error**: the program stops. Output already produced is kept and a final line `error: MESSAGE\n` is appended. The exact messages are:
  `division by zero`, `undefined variable NAME`, `redeclaration NAME`, `type mismatch`, `index out of range`, `key not found`, `not callable`, `wrong argument count`, `invalid integer`, `invalid argument`.
- If the program ends without error, `run` returns only what was printed (it may be `""`).
- The first problem that appears in the described evaluation order is always the one reported.

## 9. Examples
**integer division and remainder**
```kite
print(7 / 2);
print(-7 / 2);
print(-7 % 3);
print(7 % -3);
```
Expected output (`run` returns exactly this):
```text
3
-3
-1
1
```

**bool is not int**
```kite
print(true == 1);
print([1, 2] == [1, 2]);
print({"a": 1, "b": 2} == {"b": 2, "a": 1});
```
Expected output (`run` returns exactly this):
```text
false
true
true
```

**and/or return operands**
```kite
print(0 or "x");
print(1 and 2);
print("" and 3);
print(not []);
```
Expected output (`run` returns exactly this):
```text
x
2

true
```

**recursion**
```kite
fn fib(n) {
  if (n < 2) { return n; }
  return fib(n - 1) + fib(n - 2);
}
print(fib(15));
```
Expected output (`run` returns exactly this):
```text
610
```

**arrays and formatting**
```kite
let a = [3, 1, 2];
print(sort(a));
print(a[-1]);
print(["x", 1, nil, true, {"k": []}]);
```
Expected output (`run` returns exactly this):
```text
[1, 2, 3]
2
["x", 1, nil, true, {"k": []}]
```

**closures in a loop**
```kite
let fs = [];
for i in range(3) {
  push(fs, fn() { return i; });
}
print(fs[0]() + fs[1]() * 10 + fs[2]() * 100);
```
Expected output (`run` returns exactly this):
```text
210
```

**runtime error**
```kite
print(1);
print(1 / 0);
print(2);
```
Expected output (`run` returns exactly this):
```text
1
error: division by zero
```

**redeclaration**
```kite
let x = 1;
let x = 2;
```
Expected output (`run` returns exactly this):
```text
error: redeclaration x
```

**syntax error**
```kite
print(1)
```
Expected output (`run` returns exactly this):
```text
error: syntax
```

**strings**
```kite
print("ab" * 3);
print(3 * "z");
print("a" * -1);
print(len("héllo"));
let s = "hello";
print(s[-1]);
print(substr(s, 1, 100));
print(split("a,b,,c", ","));
```
Expected output (`run` returns exactly this):
```text
ababab
zzz

5
o
ello
["a", "b", "", "c"]
```


---

## Code to fix: `kite.py`
(The same content is in the attached file `kite.py`.)

```python
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
        return v
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
            i, j = i, j
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
                seq = it
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
```
