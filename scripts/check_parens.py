"""Quick parenthesis balance checker with location hints.

Usage: uv run python scripts/check_parens.py <file.scm> [file2.scm ...]
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    stack: list[tuple[int, int, str]] = []

    for line_idx, line in enumerate(lines, 1):
        i = 0
        while i < len(line):
            ch = line[i]
            # Skip strings
            if ch == '"':
                i += 1
                while i < len(line):
                    if line[i] == "\\":
                        i += 2
                        continue
                    if line[i] == '"':
                        break
                    i += 1
                i += 1
                continue
            # Skip comments
            if ch == ";" and i + 1 < len(line) and line[i + 1] == ";":
                break
            if ch == "(":
                # Show a bit of context
                context = line[max(0, i - 8) : i + 20]
                stack.append((line_idx, i + 1, context))
            elif ch == ")":
                if not stack:
                    print(
                        f"  ✗ {path.name}:{line_idx}:{i + 1}  "
                        f"Unexpected ')' — no matching '(' open."
                    )
                    return False
                stack.pop()
            i += 1

    if stack:
        print(f"  ✗ {path.name}: unmatched opening parenthesis(es):")
        for lnum, col, ctx in stack:
            print(f"      Line {lnum}:{col}  «{ctx.strip()}»")
        return False

    print(f"  ✓ {path.name}")
    return True


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: uv run python scripts/check_parens.py <file.scm> [...]")
        return 2

    ok = True
    for arg in args:
        path = Path(arg).resolve()
        if not path.exists():
            print(f"  ✗ {path} — file not found")
            ok = False
            continue
        if not check_file(path):
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
