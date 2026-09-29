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
{examples}
