from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pyray import *  # type: ignore

from sincity.constants import HAND_HEIGHT, HUD_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH
from sincity.rendering import draw_text, font_cache_key, measure_text_width as render_measure_text_width
from .ui_text import ui_text_size, ui_text_style


@dataclass(frozen=True)
class StageLayout:
    hud: Rectangle
    stage: Rectangle
    hand: Rectangle


@dataclass(frozen=True)
class TableSections:
    shell: Rectangle
    header: Rectangle
    note: Rectangle
    content: Rectangle


# --- Input region system ---

_region_counter: int = 0


@dataclass(frozen=True)
class InputRegion:
    name: str
    rect: Rectangle
    z: int
    order: int
    interactive: bool = True
    modal: bool = False
    blocks_pointer: bool = True


# Z-order constants — higher = more on top
Z_WORLD = 10
Z_HAND = 20
Z_MESSAGE = 25
Z_HUD = 30
Z_LOCATION_MODAL = 50
Z_PROFILE_MODAL = 60
Z_DIALOGUE_MODAL = 70
Z_DEBUG = 90
Z_TOAST = 100


@dataclass
class UiInputState:
    mouse: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))
    pressed: bool = False
    down: bool = False
    released: bool = False
    wheel: float = 0.0
    click_consumed: bool = False
    layers: list[str] = field(default_factory=list)
    layer_zs: list[int] = field(default_factory=list)
    regions: list[InputRegion] = field(default_factory=list)


_UI = UiInputState()
_TEXT_WIDTH_CACHE: dict[tuple[int, str, int], float] = {}
_WRAP_CACHE: dict[tuple[str, int, str, int, int], tuple[str, ...]] = {}
_MAX_TEXT_CACHE_SIZE = 4096


def begin_ui_frame() -> None:
    _UI.mouse = get_mouse_position()
    _UI.pressed = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
    _UI.down = is_mouse_button_down(MOUSE_BUTTON_LEFT)
    _UI.released = is_mouse_button_released(MOUSE_BUTTON_LEFT)
    _UI.wheel = get_mouse_wheel_move()
    _UI.click_consumed = False
    _UI.layers.clear()
    _UI.layer_zs.clear()
    _UI.regions.clear()


def finish_ui_frame() -> None:
    assert not _UI.layers, f"unclosed layers: {_UI.layers}"


def begin_layer(name: str, *, z: int) -> None:
    _UI.layers.append(name)
    _UI.layer_zs.append(z)


def end_layer(name: str) -> None:
    assert _UI.layers, f"missing layer {name}"
    top = _UI.layers.pop()
    _UI.layer_zs.pop()
    assert top == name, f"layer mismatch: expected {name}, got {top}"


def current_layer_z() -> int:
    return _UI.layer_zs[-1] if _UI.layer_zs else 0


# --- Input region registration ---

def register_input_region(
    name: str,
    rect: Rectangle,
    *,
    z: int,
    interactive: bool = True,
    modal: bool = False,
    blocks_pointer: bool = True,
) -> None:
    assert not (modal and not blocks_pointer), f"region {name}: modal=True requires blocks_pointer=True"
    global _region_counter
    _region_counter += 1
    _UI.regions.append(InputRegion(name, rect, z, _region_counter, interactive, modal, blocks_pointer))


def top_region_at(point: Vector2) -> InputRegion | None:
    candidates = [
        region for region in _UI.regions
        if region.blocks_pointer and check_collision_point_rec(point, region.rect)
    ]
    return max(candidates, key=lambda r: (r.z, r.order), default=None)


def highest_modal_z() -> int | None:
    modals = [r.z for r in _UI.regions if r.modal]
    return max(modals, default=None)


def mouse_point() -> Vector2:
    return _UI.mouse


def mouse_wheel() -> float:
    return _UI.wheel


def pointer_available(rect: Rectangle, *, z: int) -> bool:
    modal_z = highest_modal_z()
    if modal_z is not None and z < modal_z:
        return False

    top = top_region_at(mouse_point())
    if top is not None:
        if z < top.z:
            return False
        if z == top.z and not top.interactive:
            return False

    return check_collision_point_rec(mouse_point(), rect)


def scroll_available(rect: Rectangle, *, z: int | None = None) -> bool:
    resolved_z = current_layer_z() if z is None else z
    return pointer_available(rect, z=resolved_z)


def _raw_click_pressed() -> bool:
    return _UI.pressed and not _UI.click_consumed


def pointer_pressed(rect: Rectangle, *, z: int) -> bool:
    if not pointer_available(rect, z=z):
        return False
    if _UI.pressed and not _UI.click_consumed:
        _UI.click_consumed = True
        return True
    return False


def consume_click() -> None:
    _UI.click_consumed = True


def any_input_pressed() -> bool:
    if _UI.pressed:
        return True
    if get_key_pressed() != 0:
        return True
    return (
        is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)
        or is_mouse_button_pressed(MOUSE_BUTTON_MIDDLE)
    )


# --- Layout helpers ---

def layout() -> StageLayout:
    width = get_screen_width() or WINDOW_WIDTH
    height = get_screen_height() or WINDOW_HEIGHT
    return StageLayout(
        hud=Rectangle(14, 12, width - 28, HUD_HEIGHT - 18),
        stage=Rectangle(14, HUD_HEIGHT + 8, width - 28, height - HUD_HEIGHT - HAND_HEIGHT - 22),
        hand=Rectangle(14, height - HAND_HEIGHT + 6, width - 28, HAND_HEIGHT - 12),
    )


def centered_rect(width: float, height: float, y_offset: float = 0.0) -> Rectangle:
    screen_w = get_screen_width() or WINDOW_WIDTH
    screen_h = get_screen_height() or WINDOW_HEIGHT
    return Rectangle((screen_w - width) * 0.5, (screen_h - height) * 0.5 + y_offset, width, height)


def split_table(rect: Rectangle, *, header_height: float = 118.0, note_width: float = 248.0, note_height: float = 92.0) -> TableSections:
    header = Rectangle(rect.x + 14, rect.y + 12, rect.width - 28, header_height)
    note = Rectangle(rect.x + rect.width - note_width - 20, header.y + header.height - note_height, note_width, note_height)
    content = Rectangle(rect.x + 14, header.y + header.height + 12, rect.width - 28, rect.height - header.height - 34)
    return TableSections(shell=rect, header=header, note=note, content=content)


# --- Drawing primitives ---

def draw_frame(rect: Rectangle, fill: Color, border: Color = Color(110, 110, 110, 210)) -> None:
    if rect.width <= 0 or rect.height <= 0:
        return
    draw_rectangle_rounded(rect, 0.035, 6, fill)
    draw_rectangle_rounded_lines_ex(rect, 0.035, 6, 1.5, border)


def draw_scrim(rect: Rectangle) -> None:
    draw_rectangle_rec(rect, Color(5, 6, 10, 170))


def draw_table_shell(
    font: Font | None,
    rect: Rectangle,
    *,
    title: str,
    subtitle: str = "",
    note_title: str = "",
    note_body: str = "",
    close_label: str | None = None,
) -> tuple[TableSections, bool]:
    sections = split_table(rect)
    title_style = ui_text_style("title")
    subtitle_style = ui_text_style("body", "muted")
    note_title_style = ui_text_style("body", "accent")
    note_body_style = ui_text_style("body", "muted")
    draw_frame(rect, Color(18, 20, 26, 246), Color(112, 112, 112, 220))
    draw_text(font, title, int(sections.header.x) + 18, int(sections.header.y) + 14, title_style.size, title_style.color)
    if subtitle:
        draw_text(font, subtitle, int(sections.header.x) + 18, int(sections.header.y) + 50, subtitle_style.size, subtitle_style.color)
    closed = False
    if close_label is not None:
        closed = text_button(font, Rectangle(rect.x + rect.width - 102, rect.y + 18, 78, 28), close_label, ui_text_size("body"))
    if note_title:
        draw_text(font, note_title, int(sections.note.x), int(sections.note.y), note_title_style.size, note_title_style.color)
    if note_body:
        draw_text(font, note_body, int(sections.note.x), int(sections.note.y) + 28, note_body_style.size, note_body_style.color)
    return sections, closed


def draw_note_block(font: Font | None, rect: Rectangle, title: str, body: str) -> None:
    title_style = ui_text_style("subtitle", scale=(20 / 24))
    body_style = ui_text_style("body", "muted")
    draw_frame(rect, Color(22, 25, 32, 255), Color(80, 84, 92, 210))
    if title:
        draw_text(font, title, int(rect.x) + 12, int(rect.y) + 10, title_style.size, title_style.color)
    if body:
        draw_text(font, body, int(rect.x) + 12, int(rect.y) + 38, body_style.size, body_style.color)


# --- Interactive widgets ---

def clickable(rect: Rectangle, *, z: int | None = None) -> bool:
    resolved_z = current_layer_z() if z is None else z
    if not pointer_available(rect, z=resolved_z):
        return False
    draw_rectangle_rounded_lines_ex(rect, 0.035, 6, 2.0, Color(177, 145, 87, 255))
    if _UI.pressed and not _UI.click_consumed:
        _UI.click_consumed = True
        return True
    return False


def text_button(font: Font | None, rect: Rectangle, label: str, size: int | None = None, disabled: bool = False) -> bool:
    clicked = False if disabled else clickable(rect)
    fill = Color(24, 27, 34, 255) if disabled else Color(28, 32, 40, 255)
    border = Color(70, 72, 78, 180) if disabled else Color(92, 96, 104, 220)
    draw_frame(rect, fill, border)
    resolved_size = size if size is not None else ui_text_size("body")
    draw_centered_text(font, label, rect, resolved_size, ui_text_style("body", "disabled" if disabled else "default").color)
    return clicked


def pill(font: Font | None, rect: Rectangle, label: str, selected: bool = False, disabled: bool = False, scale: float = 1.0) -> bool:
    fill = Color(80, 66, 47, 255) if selected else Color(30, 34, 42, 255)
    border = Color(190, 162, 96, 255) if selected else Color(88, 92, 100, 220)
    if disabled:
        fill = Color(24, 27, 34, 255)
        border = Color(70, 72, 78, 180)
    clicked = False if disabled else clickable(rect)
    draw_frame(rect, fill, border)
    label_style = ui_text_style("body", "disabled" if disabled else "default", scale=scale, minimum_size=11)
    draw_centered_text(font, label, rect, label_style.size, label_style.color)
    return clicked


def draw_slot_chip(font: Font | None, rect: Rectangle, label: str, *, filled: bool = False, receptive: bool = False, disabled: bool = False, scale: float = 1.0) -> bool:
    fill = Color(84, 68, 46, 255) if filled else Color(18, 21, 27, 255)
    border = Color(190, 162, 96, 255) if filled else Color(64, 70, 82, 220)
    inner = Rectangle(rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6)
    if disabled:
        fill = Color(20, 22, 28, 255)
        border = Color(60, 64, 74, 180)
    clicked = False if disabled else clickable(rect)
    draw_frame(rect, fill, border)
    if not filled:
        draw_frame(inner, Color(12, 14, 18, 210), Color(34, 38, 46, 160))
    elif receptive:
        draw_frame(inner, Color(56, 46, 30, 150), Color(118, 100, 62, 160))
    label_style = ui_text_style("body_sm", "disabled" if disabled else "default", scale=scale, minimum_size=10)
    draw_centered_text(font, label, rect, label_style.size, label_style.color)
    return clicked


# --- Text helpers ---

def draw_centered_text(font: Font | None, text: str, rect: Rectangle, size: int, color: Color) -> None:
    width = measure_text_width(font, text, size)
    x = int(rect.x + (rect.width - width) * 0.5)
    y = int(rect.y + (rect.height - size) * 0.5) - 1
    draw_text(font, text, x, y, size, color)


def measure_text_width(font: Font | None, text: str, size: int) -> float:
    key = (_font_cache_key(font, size), text, size)
    cached = _TEXT_WIDTH_CACHE.get(key)
    if cached is not None:
        return cached
    width = render_measure_text_width(font, text, size)
    _bounded_cache_store(_TEXT_WIDTH_CACHE, key, width)
    return width


def wrap_text_lines(font: Font | None, text: str, max_width: float, size: int) -> tuple[str, ...]:
    key = _wrap_cache_key("words", font, text, max_width, size)
    cached = _WRAP_CACHE.get(key)
    if cached is not None:
        return cached
    words = text.split()
    if not words:
        lines = (text,) if text else ()
        _bounded_cache_store(_WRAP_CACHE, key, lines)
        return lines
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if measure_text_width(font, candidate, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    wrapped = tuple(lines)
    _bounded_cache_store(_WRAP_CACHE, key, wrapped)
    return wrapped


def wrap_text_lines_any(font: Font | None, text: str, max_width: float, size: int) -> tuple[str, ...]:
    key = _wrap_cache_key("chars", font, text, max_width, size)
    cached = _WRAP_CACHE.get(key)
    if cached is not None:
        return cached
    if not text:
        _bounded_cache_store(_WRAP_CACHE, key, ())
        return ()
    lines: list[str] = []
    for paragraph in text.splitlines() or ("",):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for ch in paragraph:
            candidate = f"{current}{ch}"
            if current and measure_text_width(font, candidate, size) > max_width:
                lines.append(current)
                current = ch.lstrip()
            else:
                current = candidate
        if current:
            lines.append(current)
    wrapped = tuple(lines)
    _bounded_cache_store(_WRAP_CACHE, key, wrapped)
    return wrapped


def _font_cache_key(font: Font | None, size: int) -> int:
    return font_cache_key(font, size)


def _wrap_cache_key(mode: Literal["words", "chars"], font: Font | None, text: str, max_width: float, size: int) -> tuple[str, int, str, int, int]:
    return (mode, _font_cache_key(font, size), text, int(round(max_width * 100.0)), size)


def _bounded_cache_store(cache: dict, key, value) -> None:
    if len(cache) >= _MAX_TEXT_CACHE_SIZE:
        cache.clear()
    cache[key] = value
