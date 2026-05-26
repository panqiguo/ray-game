from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .defs import ClockTemplate, EncounterModuleError, EncounterReadError, EncounterSchemeError, ObjectValue, RuntimeClockValue, SexpNode, StringAtom


@dataclass(frozen=True)
class Procedure:
    params: tuple[str, ...]
    body: Any
    env: "Environment"


@dataclass(frozen=True)
class SpecialFormProcedure:
    func: Callable[[list[Any], "Environment"], Any]


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    column: int


class Environment:
    def __init__(
        self,
        *,
        parent: Environment | None = None,
        values: dict[str, Any] | None = None,
        resolver: Callable[[str], Any] | None = None,
    ) -> None:
        self.parent = parent
        self.values = {} if values is None else dict(values)
        self.resolver = resolver

    def child(self, values: dict[str, Any] | None = None) -> "Environment":
        return Environment(parent=self, values=values)

    def lookup(self, name: str) -> Any:
        if name.startswith(":"):
            return name
        if name in self.values:
            return self.values[name]
        if self.resolver is not None:
            value = self.resolver(name)
            if value is not _MISSING:
                return value
        if self.parent is not None:
            return self.parent.lookup(name)
        raise EncounterSchemeError(f"Unknown symbol: {name}")


_MISSING = object()


def parse_program(text: str, *, source_path: Path | None = None) -> list[SexpNode]:
    tokens = _tokenize(text, source_path=source_path)
    index = 0
    forms: list[SexpNode] = []
    while index < len(tokens):
        form, index = _parse_form(tokens, index)
        forms.append(form)
    return forms


def expand_includes(source: str, *, source_path: Path | None, include_stack: tuple[Path, ...] = ()) -> list[SexpNode]:
    forms = parse_program(source, source_path=source_path)
    expanded: list[SexpNode] = []
    for form in forms:
        if _is_call(form, "include"):
            assert source_path is not None, "`include` requires a source path."
            target = form[1]
            assert isinstance(target, StringAtom), "`include` path must be a string literal."
            include_path = (source_path.parent / target.value).resolve()
            if not include_path.exists():
                raise EncounterModuleError(f"Included encounter file does not exist: {target.value}")
            if include_path in include_stack:
                raise EncounterModuleError(f"Cyclic include detected: {include_path}")
            nested = expand_includes(
                include_path.read_text(encoding="utf-8"),
                source_path=include_path,
                include_stack=(*include_stack, include_path),
            )
            expanded.extend(nested)
            continue
        expanded.append(form)
    return expanded


def module_dependency_paths(source_path: Path, include_stack: tuple[Path, ...] = ()) -> tuple[Path, ...]:
    source_path = source_path.resolve()
    forms = parse_program(source_path.read_text(encoding="utf-8"), source_path=source_path)
    discovered: list[Path] = [source_path]
    for form in forms:
        if isinstance(form, list) and form and form[0] == "include":
            target = form[1]
            assert isinstance(target, StringAtom), "`include` path must be a string literal."
            include_path = (source_path.parent / target.value).resolve()
            if include_path in include_stack:
                raise EncounterModuleError(f"Cyclic include detected: {include_path}")
            discovered.extend(module_dependency_paths(include_path, include_stack=(*include_stack, include_path)))
    # keep stable order while deduplicating
    return tuple(dict.fromkeys(discovered))


def evaluate(expr: Any, env: Environment) -> Any:
    if isinstance(expr, StringAtom):
        return expr.value
    if isinstance(expr, (bool, int)):
        return expr
    if isinstance(expr, str):
        if expr == "nil":
            return None
        return env.lookup(expr)
    if not isinstance(expr, list):
        return expr
    if not expr:
        return []
    head = expr[0]
    if head == "quote":
        assert len(expr) == 2, "`quote` expects exactly one argument."
        return _quote_value(expr[1])
    if head == "if":
        assert len(expr) == 4, "`if` expects condition, then, else."
        branch = expr[2] if truthy(evaluate(expr[1], env)) else expr[3]
        return evaluate(branch, env)
    if head == "when":
        assert len(expr) == 3, "`when` expects condition and body."
        return evaluate(expr[2], env) if truthy(evaluate(expr[1], env)) else None
    if head == "cond":
        for clause in expr[1:]:
            assert isinstance(clause, list) and len(clause) == 2, "Each cond clause must have condition and body."
            cond_expr, body_expr = clause
            if cond_expr == "else" or truthy(evaluate(cond_expr, env)):
                return evaluate(body_expr, env)
        return None
    if head == "and":
        result: Any = True
        for item in expr[1:]:
            result = evaluate(item, env)
            if not truthy(result):
                return result
        return result
    if head == "or":
        for item in expr[1:]:
            result = evaluate(item, env)
            if truthy(result):
                return result
        return False
    if head == "not":
        assert len(expr) == 2, "`not` expects one operand."
        return not truthy(evaluate(expr[1], env))
    if head == "begin":
        result: Any = None
        for item in expr[1:]:
            result = evaluate(item, env)
        return result
    if head == "let":
        assert len(expr) >= 3 and isinstance(expr[1], list), "`let` expects bindings and body."
        local_values: dict[str, Any] = {}
        for binding in expr[1]:
            assert isinstance(binding, list) and len(binding) == 2, "Each let binding must have name and expr."
            local_values[binding[0]] = evaluate(binding[1], env)
        local_env = env.child(local_values)
        result: Any = None
        for body in expr[2:]:
            result = evaluate(body, local_env)
        return result
    if head == "let*":
        assert len(expr) >= 3 and isinstance(expr[1], list), "`let*` expects bindings and body."
        local_env = env.child({})
        for binding in expr[1]:
            assert isinstance(binding, list) and len(binding) == 2, "Each let binding must have name and expr."
            local_env.values[binding[0]] = evaluate(binding[1], local_env)
        result: Any = None
        for body in expr[2:]:
            result = evaluate(body, local_env)
        return result
    if head == "lambda":
        params = expr[1]
        assert isinstance(params, list), "`lambda` params must be a list."
        assert len(expr) >= 3, "`lambda` needs a body."
        body = expr[2] if len(expr) == 3 else ["begin", *expr[2:]]
        return Procedure(params=tuple(_symbol(item) for item in params), body=body, env=env)
    if head == "define":
        assert len(expr) == 3, "`define` is only valid at module top level."
        raise EncounterSchemeError("`define` must be handled at module load time.")
    proc = evaluate(head, env)
    if isinstance(proc, SpecialFormProcedure):
        return proc.func(expr[1:], env)
    args = [evaluate(item, env) for item in expr[1:]]
    return apply(proc, args)


def apply(proc: Any, args: list[Any]) -> Any:
    if isinstance(proc, Procedure):
        if len(args) != len(proc.params):
            raise EncounterSchemeError(f"Wrong arity: expected {len(proc.params)}, got {len(args)}")
        local_env = proc.env.child(dict(zip(proc.params, args, strict=True)))
        return evaluate(proc.body, local_env)
    if callable(proc):
        try:
            return proc(*args)
        except EncounterSchemeError:
            raise
        except AssertionError as exc:
            raise EncounterSchemeError(str(exc)) from exc
        except TypeError as exc:
            raise EncounterSchemeError(str(exc)) from exc
    raise EncounterSchemeError(f"Attempted to call a non-callable value: {proc!r}")


def truthy(value: Any) -> bool:
    if hasattr(value, "value") and hasattr(value, "name"):
        return truthy(getattr(value, "value"))
    return value is not False and value is not None


def base_environment() -> Environment:
    return Environment(
        values={
            "true": True,
            "false": False,
            "nil": None,
            "list": lambda *items: list(items),
            "car": _car,
            "cdr": _cdr,
            "cons": _cons,
            "append": _append,
            "length": lambda value: len(_list_value(value)),
            "object": SpecialFormProcedure(_object_builtin),
            "object?": lambda value: isinstance(_scalar(value), ObjectValue),
            "get": _object_get,
            "update": SpecialFormProcedure(_object_update_builtin),
            "list?": lambda value: isinstance(_scalar(value), list),
            "pair?": lambda value: isinstance(_scalar(value), list) and len(_scalar(value)) > 0,
            "assoc": _assoc,
            "assoc-ref": _assoc_ref,
            "assoc-set": _assoc_set,
            "assoc-remove": _assoc_remove,
            "map": _map_builtin,
            "filter": _filter_builtin,
            "any": _any_builtin,
            "some": _any_builtin,
            "exists": _any_builtin,
            "all": _all_builtin,
            "member": _member_builtin,
            "reverse": _reverse_builtin,
            "apply": _apply_builtin,
            "+": lambda *items: sum(int(_scalar(item)) for item in items),
            "-": _sub,
            "*": _mul,
            "/": _div,
            "abs": lambda value: abs(int(_scalar(value))),
            "mod": _mod,
            "remainder": _mod,
            "min": lambda *items: min(int(_scalar(item)) for item in items),
            "max": lambda *items: max(int(_scalar(item)) for item in items),
            "=": lambda left, right: _scalar(left) == _scalar(right),
            "eq?": lambda left, right: _scalar(left) == _scalar(right),
            "equal?": lambda left, right: _scalar(left) == _scalar(right),
            "<": lambda left, right: _scalar(left) < _scalar(right),
            "<=": lambda left, right: _scalar(left) <= _scalar(right),
            ">": lambda left, right: _scalar(left) > _scalar(right),
            ">=": lambda left, right: _scalar(left) >= _scalar(right),
            "null?": lambda value: value is None or value == [],
            "number?": lambda value: isinstance(_scalar(value), int),
            "string?": lambda value: isinstance(_scalar(value), str),
            "boolean?": lambda value: isinstance(_scalar(value), bool),
            "symbol?": lambda value: isinstance(_scalar(value), str),
            "zero?": lambda value: int(_scalar(value)) == 0,
            "positive?": lambda value: int(_scalar(value)) > 0,
            "negative?": lambda value: int(_scalar(value)) < 0,
            "console-log": _log_builtin,
        }
    )



def _log_builtin(*items: Any) -> Any:
    message = " ".join(str(_scalar(item)) for item in items)
    print(message, flush=True)
    return items[-1] if items else None

def _sub(first: Any, *rest: Any) -> int:
    start = int(_scalar(first))
    if not rest:
        return -start
    return start - sum(int(_scalar(item)) for item in rest)


def _mul(*items: Any) -> int:
    result = 1
    for item in items:
        result *= int(_scalar(item))
    return result


def _div(first: Any, *rest: Any) -> int:
    start = int(_scalar(first))
    assert rest, "`/` expects at least two operands."
    result = start
    for item in rest:
        divisor = int(_scalar(item))
        assert divisor != 0, "Division by zero."
        result //= divisor
    return result


def _mod(left: Any, right: Any) -> int:
    divisor = int(_scalar(right))
    assert divisor != 0, "Modulo by zero."
    return int(_scalar(left)) % divisor


def _car(value: Any) -> Any:
    items = _list_value(value)
    assert items, "`car` expects a non-empty list."
    return items[0]


def _cdr(value: Any) -> list[Any]:
    items = _list_value(value)
    assert items, "`cdr` expects a non-empty list."
    return items[1:]


def _cons(head: Any, tail: Any) -> list[Any]:
    items = _list_value(tail)
    return [head, *items]


def _append(*values: Any) -> list[Any]:
    result: list[Any] = []
    for value in values:
        result.extend(_list_value(value))
    return result


def _object_builtin(args: list[Any], env: Environment) -> ObjectValue:
    fields: dict[str, Any] = {}
    for item in args:
        assert isinstance(item, list) and len(item) == 2 and isinstance(item[0], str), "`object` fields must be `(name expr)` pairs."
        key = item[0]
        assert not key.startswith(":"), f"`object` field names must be symbols, got: {key}"
        assert key not in fields, f"Duplicate object field: {key}"
        fields[key] = _runtime_value(evaluate(item[1], env))
    return ObjectValue(fields=fields)


def _object_get(obj: Any, key: Any, default: Any | None = None) -> Any:
    raw = _scalar(obj)
    assert isinstance(raw, ObjectValue), f"`get` expects object, got: {raw!r}"
    field = _scalar(key)
    assert isinstance(field, str), f"`get` key must be a symbol/string, got: {field!r}"
    return raw.fields.get(field, default)


def _object_update_builtin(args: list[Any], env: Environment) -> ObjectValue:
    assert args, "`update` expects object plus field updates."
    raw = _scalar(evaluate(args[0], env))
    assert isinstance(raw, ObjectValue), f"`update` expects object, got: {raw!r}"
    fields = dict(raw.fields)
    for item in args[1:]:
        assert isinstance(item, list) and len(item) == 2 and isinstance(item[0], str), "`update` fields must be `(name expr)` pairs."
        fields[item[0]] = _runtime_value(evaluate(item[1], env))
    return ObjectValue(fields=fields)


def _runtime_value(value: Any) -> Any:
    if isinstance(value, ClockTemplate):
        return RuntimeClockValue(title=value.title, description=value.description, value=value.initial, maximum=value.maximum)
    if isinstance(value, ObjectValue):
        return ObjectValue(fields={key: _runtime_value(item) for key, item in value.fields.items()})
    if isinstance(value, list):
        return [_runtime_value(item) for item in value]
    return value


def _assoc(key: Any, alist: Any) -> Any:
    needle = _scalar(key)
    for entry in _list_value(alist):
        pair = _list_value(entry)
        assert len(pair) >= 2, "`assoc` expects an alist of `(key value ...)` entries."
        if _scalar(pair[0]) == needle:
            return pair
    return None


def _assoc_ref(alist: Any, key: Any, default: Any | None = None) -> Any:
    entry = _assoc(key, alist)
    if entry is None:
        return default
    assert len(entry) >= 2, "`assoc-ref` expects alist entries with at least key and value."
    return entry[1]


def _assoc_set(alist: Any, key: Any, value: Any) -> list[Any]:
    needle = _scalar(key)
    result: list[Any] = []
    replaced = False
    for entry in _list_value(alist):
        pair = _list_value(entry)
        assert len(pair) >= 2, "`assoc-set` expects an alist of `(key value ...)` entries."
        if _scalar(pair[0]) == needle:
            result.append([pair[0], value, *pair[2:]])
            replaced = True
        else:
            result.append(pair)
    if not replaced:
        result.append([key, value])
    return result


def _assoc_remove(alist: Any, key: Any) -> list[Any]:
    needle = _scalar(key)
    result: list[Any] = []
    for entry in _list_value(alist):
        pair = _list_value(entry)
        assert len(pair) >= 2, "`assoc-remove` expects an alist of `(key value ...)` entries."
        if _scalar(pair[0]) != needle:
            result.append(pair)
    return result


def _map_builtin(first: Any, second: Any) -> list[Any]:
    if callable(first) or isinstance(first, Procedure):
        proc, values = first, second
    else:
        values, proc = first, second
    return [apply(proc, [item]) for item in _list_value(values)]


def _filter_builtin(first: Any, second: Any) -> list[Any]:
    if callable(first) or isinstance(first, Procedure):
        proc, values = first, second
    else:
        values, proc = first, second
    return [item for item in _list_value(values) if truthy(apply(proc, [item]))]


def _any_builtin(first: Any, second: Any) -> bool:
    if callable(first) or isinstance(first, Procedure):
        proc, values = first, second
    else:
        values, proc = first, second
    return any(truthy(apply(proc, [item])) for item in _list_value(values))


def _all_builtin(first: Any, second: Any) -> bool:
    if callable(first) or isinstance(first, Procedure):
        proc, values = first, second
    else:
        values, proc = first, second
    return all(truthy(apply(proc, [item])) for item in _list_value(values))


def _member_builtin(value: Any, values: Any) -> Any:
    needle = _scalar(value)
    items = _list_value(values)
    for index, item in enumerate(items):
        if _scalar(item) == needle:
            return items[index:]
    return None


def _reverse_builtin(values: Any) -> list[Any]:
    return list(reversed(_list_value(values)))


def _apply_builtin(proc: Any, values: Any) -> Any:
    return apply(proc, list(_list_value(values)))


def _scalar(value: Any) -> Any:
    if hasattr(value, "value") and hasattr(value, "name"):
        raw = getattr(value, "value")
        if hasattr(raw, "maximum") and hasattr(raw, "value"):
            return getattr(raw, "value")
        return raw
    if hasattr(value, "maximum") and hasattr(value, "value"):
        return getattr(value, "value")
    return value


def _list_value(value: Any) -> list[Any]:
    raw = _scalar(value)
    assert isinstance(raw, list), f"Expected list, got: {raw!r}"
    return raw


def _quote_value(node: Any) -> Any:
    if isinstance(node, StringAtom):
        return node.value
    if isinstance(node, list):
        return [_quote_value(item) for item in node]
    return None if node == "nil" else node


def _tokenize(text: str, *, source_path: Path | None = None) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    line = 1
    column = 1

    def advance_char(ch: str) -> None:
        nonlocal line, column
        if ch == "\n":
            line += 1
            column = 1
        else:
            column += 1

    def read_while(predicate: Callable[[str], bool]) -> tuple[str, int, int]:
        nonlocal i, line, column
        start_line = line
        start_column = column
        chars: list[str] = []
        while i < len(text) and predicate(text[i]):
            chars.append(text[i])
            advance_char(text[i])
            i += 1
        return "".join(chars), start_line, start_column

    paren_stack: list[tuple[int, int]] = []
    while i < len(text):
        ch = text[i]
        if ch in " \t\r\n":
            advance_char(ch)
            i += 1
            continue
        if ch == ";":
            while i < len(text) and text[i] != "\n":
                advance_char(text[i])
                i += 1
            continue
        if ch in "()":
            if ch == "(":
                paren_stack.append((line, column))
            else:
                if not paren_stack:
                    raise EncounterReadError(
                        _format_read_error(
                            "Unexpected closing parenthesis.",
                            source_path=source_path,
                            line=line,
                            column=column,
                        )
                    )
                paren_stack.pop()
            tokens.append(Token(ch, line, column))
            advance_char(ch)
            i += 1
            continue
        if ch == "'":
            tokens.append(Token("'", line, column))
            advance_char(ch)
            i += 1
            continue
        if ch == '"':
            start_line = line
            start_column = column
            advance_char(ch)
            i += 1
            chars: list[str] = []
            while i < len(text):
                cur = text[i]
                if cur == "\\":
                    advance_char(cur)
                    i += 1
                    if i >= len(text):
                        raise EncounterReadError(
                            _format_read_error(
                                "Unterminated string escape.",
                                source_path=source_path,
                                line=start_line,
                                column=start_column,
                            )
                        )
                    escaped = text[i]
                    chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
                    advance_char(escaped)
                    i += 1
                    continue
                if cur == '"':
                    advance_char(cur)
                    i += 1
                    break
                chars.append(cur)
                advance_char(cur)
                i += 1
            else:
                raise EncounterReadError(
                    _format_read_error(
                        "Unterminated string literal.",
                        source_path=source_path,
                        line=start_line,
                        column=start_column,
                    )
                )
            tokens.append(Token(f'"{"".join(chars)}"', start_line, start_column))
            continue
        token_text, token_line, token_column = read_while(lambda cur: cur not in '()"; \t\r\n')
        tokens.append(Token(token_text, token_line, token_column))
    if paren_stack:
        missing_line, missing_column = paren_stack[-1]
        raise EncounterReadError(
            _format_read_error(
                "Missing closing parenthesis.",
                source_path=source_path,
                line=missing_line,
                column=missing_column,
            )
        )
    return tokens


def _parse_form(tokens: list[Token], index: int) -> tuple[SexpNode, int]:
    token = tokens[index]
    if token.text == "(":
        items: list[SexpNode] = []
        index += 1
        while index < len(tokens) and tokens[index].text != ")":
            item, index = _parse_form(tokens, index)
            items.append(item)
        if index >= len(tokens) or tokens[index].text != ")":
            raise EncounterReadError("Missing closing parenthesis.")
        return items, index + 1
    if token.text == "'":
        quoted, next_index = _parse_form(tokens, index + 1)
        return ["quote", quoted], next_index
    if token.text == ")":
        raise EncounterReadError("Unexpected closing parenthesis.")
    return _parse_atom(token.text), index + 1


def _format_read_error(message: str, *, source_path: Path | None, line: int, column: int) -> str:
    location = f"{line}:{column}"
    if source_path is not None:
        return f"{source_path}:{location} {message}"
    return f"{location} {message}"


def _parse_atom(token: str) -> SexpNode:
    if token.startswith('"'):
        return StringAtom(token[1:-1])
    if token == "true":
        return True
    if token == "false":
        return False
    if token.lstrip("-+").isdigit():
        return int(token)
    return token


def _is_call(node: Any, name: str) -> bool:
    return isinstance(node, list) and bool(node) and node[0] == name


def _symbol(value: Any) -> str:
    if isinstance(value, str):
        return value
    raise EncounterSchemeError(f"Expected symbol, got: {value!r}")
