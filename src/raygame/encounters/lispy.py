from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .defs import EncounterModuleError, EncounterReadError, EncounterSchemeError, SexpNode, StringAtom


@dataclass(frozen=True)
class Procedure:
    params: tuple[str, ...]
    body: Any
    env: "Environment"


class Environment:
    def __init__(
        self,
        *,
        parent: Environment | None = None,
        values: dict[str, Any] | None = None,
        lazy_values: dict[str, Any] | None = None,
        resolver: Callable[[str], Any] | None = None,
    ) -> None:
        self.parent = parent
        self.values = {} if values is None else dict(values)
        self.lazy_values = {} if lazy_values is None else dict(lazy_values)
        self.resolver = resolver
        self.cache: dict[str, Any] = {}

    def child(self, values: dict[str, Any] | None = None) -> "Environment":
        return Environment(parent=self, values=values)

    def lookup(self, name: str) -> Any:
        if name.startswith(":"):
            return name
        if name in self.values:
            return self.values[name]
        if name in self.cache:
            return self.cache[name]
        if name in self.lazy_values:
            value = evaluate(self.lazy_values[name], self)
            self.cache[name] = value
            return value
        if self.resolver is not None:
            value = self.resolver(name)
            if value is not _MISSING:
                return value
        if self.parent is not None:
            return self.parent.lookup(name)
        raise EncounterSchemeError(f"Unknown symbol: {name}")


_MISSING = object()


def parse_program(text: str) -> list[SexpNode]:
    tokens = _tokenize(text)
    index = 0
    forms: list[SexpNode] = []
    while index < len(tokens):
        form, index = _parse_form(tokens, index)
        forms.append(form)
    return forms


def expand_includes(source: str, *, source_path: Path | None, include_stack: tuple[Path, ...] = ()) -> list[SexpNode]:
    forms = parse_program(source)
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
        local_env = env.child(local_values)
        for binding in expr[1]:
            assert isinstance(binding, list) and len(binding) == 2, "Each let binding must have name and expr."
            local_values[binding[0]] = evaluate(binding[1], local_env)
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
        return bool(getattr(value, "value"))
    return bool(value)


def base_environment() -> Environment:
    return Environment(
        values={
            "true": True,
            "false": False,
            "nil": None,
            "list": lambda *items: list(items),
            "+": lambda *items: sum(int(_scalar(item)) for item in items),
            "-": _sub,
            "min": lambda *items: min(int(_scalar(item)) for item in items),
            "max": lambda *items: max(int(_scalar(item)) for item in items),
            "=": lambda left, right: _scalar(left) == _scalar(right),
            "<": lambda left, right: _scalar(left) < _scalar(right),
            "<=": lambda left, right: _scalar(left) <= _scalar(right),
            ">": lambda left, right: _scalar(left) > _scalar(right),
            ">=": lambda left, right: _scalar(left) >= _scalar(right),
            "null?": lambda value: value in {None, []},
            "number?": lambda value: isinstance(_scalar(value), int),
            "string?": lambda value: isinstance(_scalar(value), str),
            "boolean?": lambda value: isinstance(_scalar(value), bool),
            "symbol?": lambda value: isinstance(_scalar(value), str),
        }
    )


def _sub(first: Any, *rest: Any) -> int:
    start = int(_scalar(first))
    if not rest:
        return start
    return start - sum(int(_scalar(item)) for item in rest)


def _scalar(value: Any) -> Any:
    if hasattr(value, "value") and hasattr(value, "name"):
        return getattr(value, "value")
    return value


def _quote_value(node: Any) -> Any:
    if isinstance(node, StringAtom):
        return node.value
    if isinstance(node, list):
        return [_quote_value(item) for item in node]
    return None if node == "nil" else node


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch == ";":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if ch in "()":
            tokens.append(ch)
            i += 1
            continue
        if ch == "'":
            tokens.append("'")
            i += 1
            continue
        if ch == '"':
            i += 1
            chars: list[str] = []
            while i < len(text):
                cur = text[i]
                if cur == "\\":
                    i += 1
                    if i >= len(text):
                        raise EncounterReadError("Unterminated string escape.")
                    escaped = text[i]
                    chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
                    i += 1
                    continue
                if cur == '"':
                    i += 1
                    break
                chars.append(cur)
                i += 1
            else:
                raise EncounterReadError("Unterminated string literal.")
            tokens.append(f'"{"".join(chars)}"')
            continue
        start = i
        while i < len(text) and text[i] not in '()"; \t\r\n':
            i += 1
        tokens.append(text[start:i])
    return tokens


def _parse_form(tokens: list[str], index: int) -> tuple[SexpNode, int]:
    token = tokens[index]
    if token == "(":
        items: list[SexpNode] = []
        index += 1
        while index < len(tokens) and tokens[index] != ")":
            item, index = _parse_form(tokens, index)
            items.append(item)
        if index >= len(tokens) or tokens[index] != ")":
            raise EncounterReadError("Missing closing parenthesis.")
        return items, index + 1
    if token == "'":
        quoted, next_index = _parse_form(tokens, index + 1)
        return ["quote", quoted], next_index
    if token == ")":
        raise EncounterReadError("Unexpected closing parenthesis.")
    return _parse_atom(token), index + 1


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
