from __future__ import annotations

from typing import Any

from sincity.content_lang.runtime_core import host_values as _host_values
from sincity.encounters.lispy import Environment, Procedure, StringAtom, base_environment, desugar_define_form, evaluate


def collect_top_level_definitions(forms: list[Any]) -> dict[str, Any]:
    """Collect all define/define-fragment forms, return {name: desugared_expr}.

    Skips content forms. Only processes define/define-fragment at the top level.
    """
    definitions: dict[str, Any] = {}
    for form in forms:
        if not isinstance(form, list) or not form:
            continue
        if form[0] == "content":
            continue
        result = desugar_define_form(form)
        if result is not None:
            name, expr = result
            definitions[name] = expr
    return definitions


def schema_definition_values(definitions: dict[str, Any]) -> dict[str, Any]:
    """Evaluate schema-safe definitions in a minimal env.

    Only evaluates definitions whose expressions are safe
    (literals, quote, lambda, var, or named state lists).
    """
    values: dict[str, Any] = {}
    env = Environment(parent=base_environment(), values={**_host_values(store_specs={}, store={}), **values})
    for name, expr in definitions.items():
        if not _is_schema_definition_expr(name, expr):
            continue
        value = evaluate(expr, env)
        env.values[name] = value
        values[name] = value
    return values


def _is_schema_definition_expr(name: str, expr: Any) -> bool:
    if isinstance(expr, (bool, int, StringAtom)):
        return True
    if not isinstance(expr, list) or not expr:
        return False
    if expr[0] in {"quote", "lambda", "var"}:
        return True
    return expr[0] in {"list", "append"} and (
        name.endswith("-vars") or name.endswith("_vars")
        or name.endswith("-state") or name.endswith("_state")
    )


def resolve_definition_ref(expr: Any, definitions: dict[str, Any]) -> Any:
    """If expr is a symbolic name in definitions, return the stored expression."""
    if isinstance(expr, str) and expr in definitions:
        return definitions[expr]
    return expr


def bind_runtime_definition(value: Any, env: Environment) -> Any:
    """Bind a definition value into runtime env, rebinding Procedure closures."""
    if isinstance(value, Procedure):
        return Procedure(params=value.params, body=value.body, env=env)
    return value
