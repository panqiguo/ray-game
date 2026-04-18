from __future__ import annotations

from pathlib import Path

from raylib import ffi
from pyray import *  # type: ignore
from pyray import draw_text as rl_draw_text
from pyray import draw_text_ex as rl_draw_text_ex


FONT_SIZE = 36
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_FONT_FILE = PROJECT_ROOT / "font.ttf"
TEXT_SOURCE_SUFFIXES = {".py", ".scm", ".ink", ".json"}


def _color_u32(color: Color) -> int:
    return int(color_to_int(color)) & 0xFFFFFFFF


def configure_gui_theme() -> None:
    bg = _color_u32(Color(14, 17, 23, 255))
    panel = _color_u32(Color(27, 31, 39, 255))
    focus = _color_u32(Color(184, 147, 84, 255))
    text = _color_u32(RAYWHITE)
    dim = _color_u32(Color(190, 190, 190, 255))
    gui_set_style(DEFAULT, BACKGROUND_COLOR, bg)
    gui_set_style(DEFAULT, TEXT_COLOR_NORMAL, text)
    gui_set_style(DEFAULT, TEXT_COLOR_FOCUSED, text)
    gui_set_style(DEFAULT, BORDER_COLOR_NORMAL, _color_u32(Color(90, 90, 90, 255)))
    gui_set_style(DEFAULT, BASE_COLOR_NORMAL, panel)
    gui_set_style(DEFAULT, BASE_COLOR_FOCUSED, focus)
    gui_set_style(DEFAULT, BASE_COLOR_PRESSED, _color_u32(Color(214, 174, 96, 255)))
    gui_set_style(BUTTON, TEXT_PADDING, 10)
    gui_set_style(LABEL, TEXT_COLOR_NORMAL, dim)
    gui_set_style(PROGRESSBAR, BASE_COLOR_NORMAL, panel)
    gui_set_style(PROGRESSBAR, BASE_COLOR_PRESSED, focus)


def _build_codepoints() -> list[int]:
    ranges = (
        (0x0020, 0x007E),  # Basic Latin: English letters, digits, punctuation
        (0x00A0, 0x00FF),  # Latin-1 Supplement: ·, accents, common Western symbols
        (0x2000, 0x206F),  # General Punctuation: … — • “ ” and similar marks
        (0x20A0, 0x20CF),  # Currency Symbols: €, ¥ and related signs
        (0x2100, 0x214F),  # Letterlike Symbols: ™, №, ℡ and related signs
        (0x2190, 0x21FF),  # Arrows: useful for UI and logs
        (0x2200, 0x22FF),  # Mathematical Operators: ∞, ≈, ± and similar signs
        (0x25A0, 0x25FF),  # Geometric Shapes: UI glyphs and bullets
        (0x3000, 0x303F),  # CJK Symbols and Punctuation
        (0xFF00, 0xFFEF),  # Halfwidth and Fullwidth Forms
    )
    codepoints: set[int] = set()
    for start, end in ranges:
        codepoints.update(range(start, end + 1))
    for text in _iter_project_text():
        codepoints.update(ord(char) for char in text)
    return sorted(codepoints)


def _iter_project_text():
    roots = (PROJECT_ROOT / "main.py", PROJECT_ROOT / "src" / "raygame")
    for root in roots:
        if root.is_file():
            yield root.read_text(encoding="utf-8")
            continue
        if root.is_dir():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix in TEXT_SOURCE_SUFFIXES:
                    yield path.read_text(encoding="utf-8")


def load_ui_font() -> Font | None:
    assert LOCAL_FONT_FILE.exists(), f"Missing required font file: {LOCAL_FONT_FILE}"
    codepoints_array = ffi.new("int[]", _build_codepoints())
    codepoints = ffi.cast("int *", codepoints_array)
    try:
        font = load_font_ex(str(LOCAL_FONT_FILE), FONT_SIZE, codepoints, len(codepoints_array))
    except Exception as exc:
        raise RuntimeError(f"Failed to load font from {LOCAL_FONT_FILE}") from exc
    gui_set_font(font)
    return font


def draw_text(font: Font | None, text: str, x: int, y: int, size: int, color: Color) -> None:
    if font is None:
        rl_draw_text(text, x, y, size, color)
        return
    rl_draw_text_ex(font, text, Vector2(float(x), float(y)), float(size), 1.0, color)
