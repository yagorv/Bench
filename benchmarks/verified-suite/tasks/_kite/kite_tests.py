"""Generador de tests de Kite. Salida esperada = intérprete de referencia. SOLO biblioteca estándar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from suite_lib import rng  # noqa: E402
from kite_ref import run as ref_run  # noqa: E402

# ---------------------------------------------------------------- ejemplos visibles (fijos)
EXAMPLES = [
    ("integer division and remainder", 'print(7 / 2);\nprint(-7 / 2);\nprint(-7 % 3);\nprint(7 % -3);\n'),
    ("bool is not int", 'print(true == 1);\nprint([1, 2] == [1, 2]);\nprint({"a": 1, "b": 2} == {"b": 2, "a": 1});\n'),
    ("and/or return operands", 'print(0 or "x");\nprint(1 and 2);\nprint("" and 3);\nprint(not []);\n'),
    ("recursion", 'fn fib(n) {\n  if (n < 2) { return n; }\n  return fib(n - 1) + fib(n - 2);\n}\nprint(fib(15));\n'),
    ("arrays and formatting", 'let a = [3, 1, 2];\nprint(sort(a));\nprint(a[-1]);\nprint(["x", 1, nil, true, {"k": []}]);\n'),
    ("closures in a loop", 'let fs = [];\nfor i in range(3) {\n  push(fs, fn() { return i; });\n}\nprint(fs[0]() + fs[1]() * 10 + fs[2]() * 100);\n'),
    ("runtime error", 'print(1);\nprint(1 / 0);\nprint(2);\n'),
    ("redeclaration", 'let x = 1;\nlet x = 2;\n'),
    ("syntax error", 'print(1)\n'),
    ("strings", 'print("ab" * 3);\nprint(3 * "z");\nprint("a" * -1);\nprint(len("héllo"));\nlet s = "hello";\nprint(s[-1]);\nprint(substr(s, 1, 100));\nprint(split("a,b,,c", ","));\n'),
]

N = 0


def expr_tree(r, depth):
    if depth == 0 or r.random() < 0.25:
        v = r.randint(-20, 20)
        return f"(-{-v})" if v < 0 else str(v)
    op = r.choice(["+", "-", "*", "/", "%", "+", "-", "*"])
    return f"({expr_tree(r, depth - 1)} {op} {expr_tree(r, depth - 1)})"


def lit_int(v):
    return f"(-{-v})" if v < 0 else str(v)


def arr(vals):
    return "[" + ", ".join(lit_int(v) if isinstance(v, int) else '"' + v + '"' for v in vals) + "]"


# ---------------------------------------------------------------- plantillas aleatorias
def t_arith(r):
    return "\n".join(f"print({expr_tree(r, 3)});" for _ in range(r.randint(3, 6)))


def t_logic(r):
    pool = ['0', '1', '(-1)', '""', '"a"', 'true', 'false', 'nil', '[]', '[1]', '{}', '5', '"0"', '[0]', '[nil]', '{"a": 0}']
    a, b = r.choice(pool), r.choice(pool)
    return "\n".join([f"print({a} or {b});", f"print({a} and {b});", f"print(not {a});", f"print({a} == {b});", f"print({a} != {b});",
                      f'if ({a}) {{ print("T"); }} else {{ print("F"); }}'])


def t_cmp(r):
    pairs = [("3", "5"), ('"a"', '"b"'), ('"ab"', '"a"'), ("(-2)", "(-2)"), ('"Z"', '"a"'), ("3", '"3"'), ("true", "false"), ("nil", "1"), ("[1]", "[2]")]
    a, b = r.choice(pairs)
    return "\n".join(f"print({a} {op} {b});" for op in r.sample(["<", "<=", ">", ">=", "==", "!="], 3))


def t_strings(r):
    w = r.choice(["alpha", "Beta", "gamma delta", "", "x", "Hello, World", "añb"])
    i, j = r.randint(-2, 12), r.randint(-2, 12)
    lines = [f'let w = "{w}";', f"print(substr(w, {lit_int(i)}, {lit_int(j)}));", "print(upper(w) + lower(w));", "print(len(w));",
             f"print(w * {lit_int(r.randint(-1, 4))});", 'print(split(w, " "));', 'print(join(split(w, " "), "-"));']
    if w:
        lines.append(f"print(w[{lit_int(r.randint(-len(w), len(w) - 1))}]);")
    if r.random() < 0.3:
        lines.append(f"print(w[{len(w)}]);")
    return "\n".join(lines)


def t_ord(r):
    k = r.randint(0, 25)
    return f'let c = chr(ord("a") + {k});\nprint(c);\nprint(ord(c));\nprint(chr(ord(upper(c)) + 1));'


def t_arrays(r):
    vals = [r.randint(-30, 30) for _ in range(r.randint(1, 8))]
    lines = [f"let a = {arr(vals)};", "print(sort(a));", "print(a);", f"push(a, {lit_int(r.randint(0, 99))});", "print(a);", "print(pop(a));",
             f"print(a[{lit_int(r.randint(-len(vals), len(vals) - 1))}]);", "print(len(a));", "let b = a;", "push(b, 7);", "print(a);",
             "print(a + [1, 2]);", "print(a == b);", f"a[{lit_int(r.randint(-len(vals), len(vals) - 1))}] = 100;", "print(b);"]
    if r.random() < 0.4:
        lines.append(f"print(a[{len(vals) + 5}]);")
    return "\n".join(lines)


def t_sort_big(r):
    vals = [r.randint(0, 40) for _ in range(r.randint(5, 12))]
    return f"let a = {arr(vals)};\nprint(sort(a));\nprint(a);\nlet s = {arr([str(v) for v in vals])};\nprint(sort(s));"


def t_dicts(r):
    keys = r.sample(["a", "b", "c", "d", "e", "zz"], 4)
    lines = ['let d = {"%s": 1, "%s": 2};' % (keys[0], keys[1]), f'd["{keys[2]}"] = 3;', f'd["{keys[0]}"] = 10;', "print(d);", "print(keys(d));",
             f'print(has(d, "{keys[3]}"));', f'print(has(d, "{keys[0]}"));', "print(len(d));", "for k in d { print(k + \"=\" + str(d[k])); }",
             'let e = {"x": [1, "two"], "y": {"z": nil}};', "print(e);", "print(e == e);"]
    if r.random() < 0.5:
        lines.append(f'print(d["{keys[3]}"]);')
    return "\n".join(lines)


def t_control(r):
    n, m, k = r.randint(5, 25), r.randint(2, 4), r.randint(2, 12)
    return (f"let total = 0;\nfor i in range({n}) {{\n  if (i % {m} == 0) {{ continue; }}\n  for j in range(i) {{\n    if (j > {k}) {{ break; }}\n"
            f"    total = total + i * j;\n  }}\n}}\nprint(total);")


def t_collatz(r):
    n = r.randint(2, 200)
    return f"let n = {n};\nlet steps = 0;\nwhile (n != 1) {{\n  if (n % 2 == 0) {{ n = n / 2; }} else {{ n = 3 * n + 1; }}\n  steps = steps + 1;\n}}\nprint(steps);"


def t_sieve(r):
    n = r.randint(10, 120)
    return (f"let n = {n};\nlet is = [];\nfor i in range(n + 1) {{ push(is, true); }}\nis[0] = false;\nis[1] = false;\n"
            "for i in range(2, n + 1) {\n  if (is[i]) {\n    let j = i * i;\n    while (j <= n) { is[j] = false; j = j + i; }\n  }\n}\n"
            "let count = 0;\nlet last = 0;\nfor i in range(n + 1) { if (is[i]) { count = count + 1; last = i; } }\nprint(count);\nprint(last);")


def t_bubble(r):
    vals = [r.randint(-50, 50) for _ in range(r.randint(4, 9))]
    return (f"let a = {arr(vals)};\nlet n = len(a);\nlet swapped = true;\nwhile (swapped) {{\n  swapped = false;\n  for i in range(n - 1) {{\n"
            "    if (a[i] > a[i + 1]) {\n      let t = a[i];\n      a[i] = a[i + 1];\n      a[i + 1] = t;\n      swapped = true;\n    }\n  }\n}\nprint(a);")


def t_fizz(r):
    n = r.randint(5, 30)
    return (f'let out = [];\nfor i in range(1, {n + 1}) {{\n  if (i % 15 == 0) {{ push(out, "FizzBuzz"); }}\n  else if (i % 3 == 0) {{ push(out, "Fizz"); }}\n'
            '  else if (i % 5 == 0) {{ push(out, "Buzz"); }}\n  else {{ push(out, str(i)); }}\n}}\nprint(join(out, " "));').replace("{{", "{").replace("}}", "}")


def t_strloop(r):
    w = r.choice(["kite", "banana", "Hello World", "abcdef"])
    return f'let s = "{w}";\nlet rev = "";\nfor c in s {{ rev = c + rev; }}\nprint(rev);\nlet n = 0;\nfor c in s {{ if (c == "a" or c == "e") {{ n = n + 1; }} }}\nprint(n);'


def t_digits(r):
    n = r.randint(1, 10 ** 9)
    return f"let n = {n};\nlet s = 0;\nwhile (n > 0) {{ s = s + n % 10; n = n / 10; }}\nprint(s);"


def t_fn_classic(r):
    which = r.choice(["fib", "fact", "gcd", "ack", "pow", "hanoi", "sumlist"])
    if which == "fib":
        return f"fn fib(n) {{ if (n < 2) {{ return n; }} return fib(n - 1) + fib(n - 2); }}\nprint(fib({r.randint(0, 16)}));"
    if which == "fact":
        return f"fn fact(n) {{ if (n <= 1) {{ return 1; }} return n * fact(n - 1); }}\nprint(fact({r.randint(0, 30)}));"
    if which == "gcd":
        return f"fn gcd(a, b) {{ if (b == 0) {{ return a; }} return gcd(b, a % b); }}\nprint(gcd({r.randint(1, 500)}, {r.randint(1, 500)}));"
    if which == "ack":
        return f"fn ack(m, n) {{\n  if (m == 0) {{ return n + 1; }}\n  if (n == 0) {{ return ack(m - 1, 1); }}\n  return ack(m - 1, ack(m, n - 1));\n}}\nprint(ack(2, {r.randint(0, 3)}));"
    if which == "pow":
        return (f"fn pw(b, e) {{\n  if (e == 0) {{ return 1; }}\n  let h = pw(b, e / 2);\n  if (e % 2 == 0) {{ return h * h; }}\n  return h * h * b;\n}}\n"
                f"print(pw({r.randint(2, 9)}, {r.randint(0, 40)}));")
    if which == "hanoi":
        return f"fn hanoi(n) {{ if (n == 0) {{ return 0; }} return 2 * hanoi(n - 1) + 1; }}\nprint(hanoi({r.randint(0, 20)}));"
    vals = [r.randint(-9, 9) for _ in range(r.randint(0, 8))]
    return f"fn sum(a, i) {{ if (i >= len(a)) {{ return 0; }} return a[i] + sum(a, i + 1); }}\nprint(sum({arr(vals)}, 0));"


def t_closure(r):
    k = r.randint(1, 5)
    which = r.choice(["counter", "adder", "compose", "loopcap", "apply", "memo"])
    if which == "counter":
        return (f"fn make() {{ let c = 0; return fn() {{ c = c + {k}; return c; }}; }}\nlet a = make();\nlet b = make();\n"
                "print(a()); print(a()); print(b()); print(a());")
    if which == "adder":
        return f"fn adder(n) {{ return fn(x) {{ return x + n; }}; }}\nlet f = adder({k});\nlet g = adder({k * 10});\nprint(f(1)); print(g(1)); print(adder(2)(3));"
    if which == "compose":
        return (f"fn compose(f, g) {{ return fn(x) {{ return f(g(x)); }}; }}\nlet inc = fn(x) {{ return x + {k}; }};\nlet dbl = fn(x) {{ return x * 2; }};\n"
                "print(compose(inc, dbl)(5)); print(compose(dbl, inc)(5));")
    if which == "loopcap":
        return (f"let fs = [];\nfor i in range({k + 1}) {{ let j = i * i; push(fs, fn() {{ return j + i; }}); }}\n"
                "let out = [];\nfor f in fs { push(out, f()); }\nprint(out);\nlet ws = [];\nlet n = 0;\nwhile (n < 3) { let m = n; push(ws, fn() { return m; }); n = n + 1; }\nprint(ws[0]() + ws[1]() + ws[2]());")
    if which == "apply":
        return (f"fn times(f, n, x) {{ for i in range(n) {{ x = f(x); }} return x; }}\nprint(times(fn(v) {{ return v * 2 + 1; }}, {r.randint(0, 10)}, {k}));")
    return (f"let memo = {{}};\nfn fib(n) {{\n  let key = str(n);\n  if (has(memo, key)) {{ return memo[key]; }}\n  let v = n;\n  if (n >= 2) {{ v = fib(n - 1) + fib(n - 2); }}\n"
            f"  memo[key] = v;\n  return v;\n}}\nprint(fib({r.randint(5, 60)}));\nprint(len(memo));")


def t_hof(r):
    vals = [r.randint(-9, 30) for _ in range(r.randint(3, 9))]
    return (f"fn map(f, a) {{ let o = []; for x in a {{ push(o, f(x)); }} return o; }}\nfn filter(f, a) {{ let o = []; for x in a {{ if (f(x)) {{ push(o, x); }} }} return o; }}\n"
            f"fn reduce(f, a, z) {{ let acc = z; for x in a {{ acc = f(acc, x); }} return acc; }}\nlet a = {arr(vals)};\n"
            f"print(map(fn(x) {{ return x * {r.randint(2, 5)}; }}, a));\nprint(filter(fn(x) {{ return x % 2 == 0; }}, a));\n"
            "print(reduce(fn(s, x) { return s + x; }, a, 0));\nprint(reduce(fn(m, x) { return max(m, x); }, a, -1000));")


RANDOM_TEMPLATES = [("arith", t_arith, 45), ("logic", t_logic, 16), ("compare", t_cmp, 8), ("strings", t_strings, 14), ("strings", t_ord, 3),
                    ("collections", t_arrays, 14), ("collections", t_sort_big, 4), ("collections", t_dicts, 8),
                    ("control", t_control, 6), ("control", t_collatz, 3), ("control", t_sieve, 3), ("control", t_bubble, 4),
                    ("control", t_fizz, 2), ("control", t_strloop, 3), ("control", t_digits, 3),
                    ("functions", t_fn_classic, 10), ("functions", t_closure, 12), ("functions", t_hof, 4)]

# ---------------------------------------------------------------- programas escritos a mano (cubren cada matiz de la especificación)
HAND = {
    "semantics": [
        'print(true + 1);', 'print(1 + true);', 'print(-true);', 'print(nil == false); print(nil == nil); print(0 == false); print("" == nil);',
        'let a = [1, [2, 3], {"k": [4]}]; let b = [1, [2, 3], {"k": [4]}]; print(a == b); b[1][0] = 9; print(a == b); print(a);',
        'let d1 = {"a": 1, "b": 2}; let d2 = {"b": 2, "a": 1}; print(d1 == d2); print(keys(d1)); print(keys(d2)); print(d1 == {"a": 1});',
        'fn f() {} let g = f; print(f == g); print(f == fn() {}); print(fn() {} == fn() {}); print(len == len); print(len == abs);',
        'print(f);', 'fn f() {} print(f); print(fn() {}); print(len); print([f, len]);',
        'print(7 / -2); print(-7 / -2); print(-8 / 2); print(0 / 5); print(-0);', 'print(100 % 7); print(-100 % 7); print(100 % -7); print(-100 % -7); print(5 % 5);',
        'print(1 / 0);', 'print(1 % 0);', 'print(true / 0);', 'print("a" - 1);',
        'print(12345678901234567890 * 98765432109876543210); print(2 * 3 * 4 * 5 * 6 * 7 * 8 * 9 * 10 * 11 * 12 * 13 * 14 * 15 * 16 * 17 * 18 * 19 * 20 * 21);',
        'print("a" + 1);', 'print([1] + 2);', 'print([1] + [2] + [3]);', 'let a = [1]; let b = a + [2]; push(a, 5); print(a); print(b);',
        'print("x" < 1);', 'print([1] < [2]);', 'print(nil < nil);', 'print("apple" < "banana"); print("b" > "abc"); print("A" < "a"); print("" < "a");',
        'print(not 0); print(not 1); print(not ""); print(not "x"); print(not nil); print(not [nil]); print(not {});',
        'print(1 < 2 == true); print(1 + 2 * 3 - 4 / 2 % 3); print(-2 * -3); print(- - 4); print(2 * -3);',
        'print(1 or 2 and 3); print(0 or 0 and 3); print(nil and nil or "z"); print(1 and 0 or 7);',
        'let calls = []; fn t(x) { push(calls, x); return x; } t(0) and t(1); t(1) or t(2); t(0) or t(3); print(calls);',
        '# comentario\nprint(1); # otro\nprint("# no es comentario");', 'print("a\\nb\\tc\\"d\\\\e");', 'print(["a\\nb"]);', 'print(007 + 1);',
    ],
    "collections": [
        'let a = [1, 2, 3]; print(a[-1]); print(a[-3]); print(a[-4]);', 'let a = [1, 2, 3]; a[-1] = 9; a[0] = 7; print(a); a[3] = 1;', 'let a = [1]; a["x"] = 1;',
        'let s = "abc"; s[0] = "x";', 'let s = "abc"; print(s[3]);', 'print("abc"[-1]); print("abc"[-3]);', 'print([1, 2][true]);', 'let d = {}; print(d["x"]);',
        'let d = {}; d[1] = 2;', 'let d = {"a": 1}; d["b"] = 2; d["a"] = 3; print(d); print(keys(d)); for k in d { print(k); }',
        'let d = {"x": 1, "x": 2, "y": 3}; print(d); print(len(d));',
        'let a = [1, 2, 3]; for x in a { pop(a); } print(a);', 'let a = [1, 2]; let n = 0; for x in a { if (n < 6) { push(a, x * 10); } n = n + 1; } print(n); print(a);',
        'let a = [1, 2, 3]; let n = 0; for x in a { if (n < 8) { push(a, 0); } n = n + 1; } print(n); print(len(a));',
        'let d = {"a": 1}; for k in d { d[k + "x"] = 0; } print(d);',
        'print(range(5)); print(range(2, 6)); print(range(3, 3)); print(range(5, 2)); print(range(0)); print(range(-3, 0));', 'print(range(1, 2, 3));', 'print(range("a"));',
        'print(sort([10, 9, 2, 33, 1])); print(sort(["b", "a", "B", "10", "9"])); print(sort([]));', 'print(sort([1, "a"]));', 'print(sort([true, false]));',
        'let a = [3, 1]; let b = sort(a); push(b, 0); print(a); print(b);',
        'print(pop([]));', 'let a = [1, 2]; print(pop(a)); print(pop(a)); print(pop(a));', 'print(push(1, 2));', 'print(len(5));', 'print(len(nil));',
        'print([1, "a", [2, "b"], {"k": "v"}, nil, true, false, fn() {}]);', 'print(str([]) + str({}) + str("x") + str(nil) + str(12));',
        'print(join(["a", "b"], ", ")); print(join([], "-")); print(join(["a", 1], "-"));', 'print(split("abc", "")); ',
        'print(split("a--b--c", "--")); print(split("", ",")); print(split("abc", "x"));', 'print(has({"a": 1}, "a")); print(has({}, 1));',
        'let m = [[0, 0], [0, 0]]; m[1][0] = 5; print(m); let r = [[0]] + [[0]]; r[0][0] = 1; print(r);',
        'let row = [0, 0]; let g = [row, row]; g[0][0] = 1; print(g);', 'print(min(3, 9) + max(3, 9) + abs(-4)); print(min(3, "a"));', 'print(substr("hello", -3, 3)); print(substr("hello", 2, 1)); print(substr("hello", 3, 50)); print(substr("hello", -5, -1));',
        'print(ord("é")); print(chr(233)); print(chr(65)); print(ord("ab"));', 'print(chr(-1));', 'print(int("42") + 1); print(int("-7")); print(int(5)); print(int("+5"));',
        'print(int("12a"));', 'print(int(""));', 'print(int("-"));', 'print(int(" 5"));', 'print(int(true));', 'print(int(nil));',
        'print(upper("aBc1é")); print(lower("ABC")); print(upper(5));', 'print(len("héllo wörld")); print(len([1, [2, 3]])); print(len({"a": 1}));',
    ],
    "scoping": [
        'let x = 1; { let x = 2; print(x); } print(x);', 'let x = 1; { x = 2; } print(x);', 'let x = 1; if (true) { let x = 5; x = 6; print(x); } print(x);',
        'x = 1;', 'print(y);', 'let f = fn() { return z; }; print(f());', 'fn f(a) { let a = 1; } f(2);', 'fn f(a) { { let a = 1; return a; } } print(f(2));',
        'for i in range(2) { let i = 5; print(i); }', 'let i = 0; for i in range(3) { } print(i);', 'for x in [1, 2] { let y = x; } print(y);',
        'let i = 0; while (i < 3) { let t = i * 2; print(t); i = i + 1; }', 'fn f() { return 1; } fn f() { return 2; }', 'fn f() { return 1; } { fn f() { return 2; } print(f()); } print(f());',
        'let print = 5; print("x");', 'let len = fn(x) { return 42; }; print(len("abc"));', 'let g = 10; fn f() { g = g + 1; return g; } print(f()); print(f()); print(g);',
        'fn outer() { let v = 1; fn inner() { v = v + 1; return v; } return inner; } let i = outer(); print(i()); print(i());',
        'fn a() { return b(); } fn b() { return 5; } print(a());', 'fn a() { return b(); } print(a());', 'print(late()); fn late() { return 1; }',
        'fn even(n) { if (n == 0) { return true; } return odd(n - 1); } fn odd(n) { if (n == 0) { return false; } return even(n - 1); } print(even(10)); print(odd(7)); print(even(7));',
        'let a = 1; fn f() { let a = 2; fn g() { return a; } return g(); } print(f()); print(a);',
        'fn f(x) { return x; } print(f(1, 2));', 'fn f(x, y) { return x; } print(f(1));', 'print(len());', 'print(len("a", "b"));', 'print(5());', 'let a = [1]; a();', 'print("s"(1));',
        'fn f() { return; } print(f()); fn g() { } print(g()); fn h() { return nil; } print(h() == g());',
        'fn f() { for i in range(10) { if (i == 3) { return i; } } return -1; } print(f());', 'fn f() { while (true) { return 1; } } print(f());',
        'fn f(n) { let r = 0; for i in range(n) { for j in range(n) { if (j == 2) { break; } r = r + 1; } if (i == 3) { break; } } return r; } print(f(10));',
        'let n = 0; while (true) { n = n + 1; if (n < 5) { continue; } break; } print(n);',
        'let out = []; for i in range(5) { if (i == 1) { continue; } if (i == 4) { break; } push(out, i); } print(out);',
    ],
    "errors": [
        'print("antes"); print(undefined_thing); print("despues");', 'print(1); let a = []; print(a[0]); print(2);', 'print([1, 2, 3][1 / 0]);', 'let x = 5 / (2 - 2);',
        'fn f() { return 1 / 0; } print(f());', 'print(-"a");', 'print(1 < "a");', 'for x in 5 { }', 'for x in nil { }', 'for c in "ab" { print(c); }',
        'let d = {"a": 1}; print(d["a"]); print(d["b"]); print("no");', 'print({}[0]);', 'print(nil[0]);', 'print(f);', 'let a = 1; a.b = 2;',
        'print(1)', 'print(1;', 'print((1);', 'let = 5;', 'let x 5;', 'let x = ;', 'if (true) print(1);', 'if true { print(1); }', 'while (true) print(1);', 'print(1) print(2);',
        '{ print(1); ', 'print(1); }', 'break;', 'continue;', 'return 1;', 'fn f() { break; } f();', 'while (true) { fn g() { break; } }', 'for i in [1] { fn g() { continue; } }',
        'fn f(a, a) { }', 'fn (a) { };', 'let a = [1, 2,];', 'print(1,);', 'fn f(a,) { }', 'let d = {a: 1};', 'let d = {1: 2};', 'let d = {"a": 1,};', 'print("abc);',
        'print("a\nb");', 'print("a\\qb");', 'print(12ab);', 'print(1 $ 2);', 'print(@);', 'print(1.5);', 'let ñ = 1;', ';', 'print(1);;', '1 = 2;', 'f() = 3;', '(a) = 1;', 'let a = 1; a + 1 = 2;',
        'else { }', 'print(not);', 'print(1 +);', 'print(* 2);', 'let x = fn(a) { return a };', 'if (1) { } else print(2);',
        'print(1); # sin salto final', '', '   \n  # solo comentario\n', 'print("ok"); print(1 / 0); print("nunca"); print(undefined);',
    ],
    "deep": [
        'fn sum(n) { if (n == 0) { return 0; } return n + sum(n - 1); } print(sum(2000));',
        'fn d(n) { if (n == 0) { return 0; } let r = d(n - 1); return r + 1; } print(d(2400));',
        'let s = 0; let i = 0; while (i < 60000) { s = s + i % 7; i = i + 1; } print(s);',
        'let s = ""; for i in range(3000) { s = s + str(i % 10); } print(len(s)); print(substr(s, 0, 20));',
        'let g = []; for i in range(120) { let row = []; for j in range(120) { push(row, i * j); } push(g, row); } let t = 0; for r in g { for v in r { t = t + v; } } print(t);',
    ],
}


def build_tests(seed):
    r = rng(seed, "kite-tests")
    tests = []

    def add(cat, src):
        tests.append({"id": f"t{len(tests):03d}", "cat": cat, "src": src if src.endswith("\n") or not src else src + "\n"})

    for cat, progs in HAND.items():
        for p in progs:
            add(cat, p)
    for cat, fn, n in RANDOM_TEMPLATES:
        for _ in range(n):
            add(cat, fn(r))
    for t in tests:
        t["expected"] = ref_run(t["src"])
        if t["cat"] != "errors" and t["expected"] == "error: syntax\n" and t["src"].strip():
            raise AssertionError(f"plantilla con sintaxis inválida: {t['src']!r}")
    return tests


def visible_examples():
    return [{"name": n, "src": s, "expected": ref_run(s)} for n, s in EXAMPLES]
