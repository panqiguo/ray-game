from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from raylib import ffi
from pyray import *  # type: ignore
from pyray import measure_text as rl_measure_text
from pyray import measure_text_ex as rl_measure_text_ex
from pyray import draw_text as rl_draw_text
from pyray import draw_text_ex as rl_draw_text_ex


DEFAULT_FONT_SIZE = 18
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_FONT_FILE = PROJECT_ROOT / "font.ttf"
TEXT_SOURCE_SUFFIXES = {".py", ".scm", ".ink", ".json"}
TEXT_SPACING = 1.0


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
        (0x4E00, 0x7FFF),  # CJK Unified Ideographs: common Chinese chars (练 etc.)
        (0xFF00, 0xFFEF),  # Halfwidth and Fullwidth Forms
    )
    codepoints: set[int] = set()
    for start, end in ranges:
        codepoints.update(range(start, end + 1))
    for text in _iter_project_text():
        codepoints.update(ord(char) for char in text)
    return sorted(codepoints)


def _iter_project_text():
    roots = (PROJECT_ROOT / "main.py", PROJECT_ROOT / "src" / "sincity")
    for root in roots:
        if root.is_file():
            yield root.read_text(encoding="utf-8")
            continue
        if root.is_dir():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix in TEXT_SOURCE_SUFFIXES:
                    yield path.read_text(encoding="utf-8")


@dataclass
class UIFont:
    source_path: Path
    codepoints: tuple[int, ...]
    default_size: int = DEFAULT_FONT_SIZE
    _fonts: dict[int, Font] = field(default_factory=dict)

    def font_for_size(self, size: int) -> Font:
        normalized_size = int(round(size))
        assert normalized_size > 0, f"Font size must be positive: {size}"
        font = self._fonts.get(normalized_size)
        if font is None:
            font = _load_font_at_size(self.source_path, normalized_size, self.codepoints)
            self._fonts[normalized_size] = font
        return font

    def default_font(self) -> Font:
        return self.font_for_size(self.default_size)

    def unload(self) -> None:
        for font in self._fonts.values():
            unload_font(font)
        self._fonts.clear()


def load_ui_font() -> UIFont:
    assert LOCAL_FONT_FILE.exists(), f"Missing required font file: {LOCAL_FONT_FILE}"
    font = UIFont(LOCAL_FONT_FILE, tuple(_build_codepoints()))
    gui_set_font(font.default_font())
    return font


def unload_ui_font(font: UIFont | Font | None) -> None:
    if font is None:
        return
    if isinstance(font, UIFont):
        font.unload()
        return
    unload_font(font)


def draw_text(font: UIFont | Font | None, text: str, x: int, y: int, size: int, color: Color) -> None:
    if font is None:
        rl_draw_text(text, x, y, size, color)
        return
    selected_font = _select_font(font, size)
    rl_draw_text_ex(selected_font, text, Vector2(float(x), float(y)), float(size), TEXT_SPACING, color)


def measure_text_width(font: UIFont | Font | None, text: str, size: int) -> float:
    if font is None:
        return float(rl_measure_text(text, size))
    selected_font = _select_font(font, size)
    return float(rl_measure_text_ex(selected_font, text, float(size), TEXT_SPACING).x)


def font_cache_key(font: UIFont | Font | None, size: int) -> int:
    if font is None:
        return 0
    if isinstance(font, UIFont):
        return (id(font) << 16) ^ int(round(size))
    return _font_texture_id(font)


def _load_font_at_size(source_path: Path, size: int, codepoints_tuple: tuple[int, ...]) -> Font:
    codepoints_array = ffi.new("int[]", codepoints_tuple)
    codepoints = ffi.cast("int *", codepoints_array)
    try:
        font = load_font_ex(str(source_path), size, codepoints, len(codepoints_array))
    except Exception as exc:
        raise RuntimeError(f"Failed to load font from {source_path} at {size}px") from exc
    assert is_font_valid(font), f"Invalid font loaded from {source_path} at {size}px"
    set_texture_filter(font.texture, TEXTURE_FILTER_POINT)
    return font


def _select_font(font: UIFont | Font, size: int) -> Font:
    if isinstance(font, UIFont):
        return font.font_for_size(size)
    return font


def _font_texture_id(font: Font) -> int:
    texture = getattr(font, "texture", None)
    texture_id = getattr(texture, "id", None)
    if isinstance(texture_id, int):
        return texture_id
    return id(font)
