from __future__ import annotations

import sys
from pathlib import Path

from sincity.encounters.lispy import expand_includes, parse_program


def lint_scm_file(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    parse_program(source, source_path=path)
    expand_includes(source, source_path=path, include_stack=(path.resolve(),))


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
