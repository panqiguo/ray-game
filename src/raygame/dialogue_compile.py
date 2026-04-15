from __future__ import annotations

from pathlib import Path
from subprocess import run

from raygame.dialogues.registry import ASSET_DIR


def compile_dialogues() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for ink_path in sorted(ASSET_DIR.glob("*.ink")):
        json_path = ink_path.with_suffix(".ink.json")
        if json_path.exists() and json_path.stat().st_mtime >= ink_path.stat().st_mtime:
            continue
        _compile_ink(ink_path, json_path)


def _compile_ink(ink_path: Path, json_path: Path) -> None:
    command_groups = (
        ("inklecate", "-o", str(json_path), str(ink_path)),
        ("npx", "inkjs", "-o", str(json_path), str(ink_path)),
    )
    last_error: Exception | None = None
    for command in command_groups:
        try:
            run(command, check=True, capture_output=True, text=True)
            return
        except FileNotFoundError as exc:
            last_error = exc
        except Exception as exc:
            last_error = exc
    raise RuntimeError(
        f"Failed to compile Ink dialogue {ink_path.name}. Install inklecate or ensure `npx inkjs` is available."
    ) from last_error
