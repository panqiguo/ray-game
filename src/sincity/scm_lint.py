from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from sincity.encounters.lispy import desugar_define_form, expand_includes, parse_program

_DANGEROUS_HEADS = frozenset({
    "action", "location",
    "when", "if", "cond",
    "clock-value", "clock-filled?",
    "world-attr", "world-value", "world-item",
    "store-get", "get-field",
})


def check_dangerous_defines(forms: list[Any], path: Path) -> list[str]:
    warnings: list[str] = []
    for form in forms:
        if not isinstance(form, list) or not form:
            continue
        head = form[0]
        if head == "define-fragment":
            continue
        if head != "define":
            continue
        # (define name expr) — not function define
        if isinstance(form[1], list):
            continue  # function define: (define (fn ...) ...)
        name = form[1]
        if not isinstance(name, str):
            continue
        assert len(form) == 3, f"`define` with a symbol expects exactly one expression: {form}"
        expr = form[2]
        if isinstance(expr, list) and expr and expr[0] in _DANGEROUS_HEADS:
            rel = path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path
            warnings.append(
                f"  {rel}: define `{name}` uses `({expr[0]} ...)` at top level "
                f"— may depend on runtime state.\n"
                f"    Suggestion: use `(define-fragment {name} ...)` or `(define ({name}) ...)` instead."
            )
    return warnings


def lint_scm_file(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    parse_program(source, source_path=path)
    expanded_forms = expand_includes(source, source_path=path, include_stack=(path.resolve(),))
    warnings = check_dangerous_defines(expanded_forms, path)
    for w in warnings:
        print(f"warning: {w}")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python -m sincity.scm_lint <path/to/file.scm>")
        return 2
    path = Path(args[0]).resolve()
    lint_scm_file(path)
    print(f"ok: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
