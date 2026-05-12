from __future__ import annotations

from pathlib import Path

from pyray import *  # type: ignore


PORTRAIT_DIR = Path(__file__).resolve().parents[1] / "assets" / "portraits"
PORTRAIT_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")

_PORTRAIT_CACHE: dict[str, Texture2D | None] = {}


def portrait_for_speaker(speaker: str) -> Texture2D | None:
    if not speaker:
        return None
    assert "/" not in speaker and "\\" not in speaker, f"Speaker name cannot contain a path separator: {speaker}"
    cached = _PORTRAIT_CACHE.get(speaker)
    if speaker in _PORTRAIT_CACHE:
        return cached
    path = _portrait_path(speaker)
    if path is None:
        _PORTRAIT_CACHE[speaker] = None
        return None
    texture = load_texture(str(path))
    assert is_texture_valid(texture), f"Invalid portrait texture: {path}"
    _PORTRAIT_CACHE[speaker] = texture
    return texture


def _portrait_path(speaker: str) -> Path | None:
    for suffix in PORTRAIT_SUFFIXES:
        path = PORTRAIT_DIR / f"{speaker}{suffix}"
        if path.exists():
            return path
    return None
