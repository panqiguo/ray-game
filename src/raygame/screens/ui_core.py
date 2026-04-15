from __future__ import annotations

from dataclasses import dataclass, field

from pyray import *  # type: ignore

from raygame.constants import HAND_HEIGHT, HUD_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH
from raygame.rendering import draw_text


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


@dataclass
class UiInputState:
    mouse: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))
    pressed: bool = False
    click_consumed: bool = False
    layers: list[str] = field(default_factory=list)


_UI = UiInputState()


def begin_ui_frame() -> None:
    _UI.mouse = get_mouse_position()
    _UI.pressed = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
    _UI.click_consumed = False
    _UI.layers.clear()


def finish_ui_frame() -> None:
    assert not _UI.layers, f"unclosed layers: {_UI.layers}"


def begin_layer(name: str, interactive: bool) -> None:
    _UI.layers.append(name if interactive else f"!{name}")


def end_layer(name: str) -> None:
    assert _UI.layers, f"missing layer {name}"
    top = _UI.layers.pop()
    assert top.removeprefix("!") == name, f"layer mismatch: expected {name}, got {top}"


def layer_interactive() -> bool:
    return not _UI.layers[-1].startswith("!") if _UI.layers else True


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


def mouse_point() -> Vector2:
    return _UI.mouse


def click_pressed() -> bool:
    return _UI.pressed and not _UI.click_consumed


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
    draw_frame(rect, Color(18, 20, 26, 246), Color(112, 112, 112, 220))
    draw_text(font, title, int(sections.header.x) + 18, int(sections.header.y) + 14, 28, RAYWHITE)
    if subtitle:
        draw_text(font, subtitle, int(sections.header.x) + 18, int(sections.header.y) + 50, 17, LIGHTGRAY)
    closed = False
    if close_label is not None:
        closed = text_button(font, Rectangle(rect.x + rect.width - 102, rect.y + 18, 78, 28), close_label, 16)
    if note_title:
        draw_text(font, note_title, int(sections.note.x), int(sections.note.y), 18, Color(212, 196, 132, 255))
    if note_body:
        draw_text(font, note_body, int(sections.note.x), int(sections.note.y) + 28, 16, LIGHTGRAY)
    return sections, closed


def draw_note_block(font: Font | None, rect: Rectangle, title: str, body: str) -> None:
    draw_frame(rect, Color(22, 25, 32, 255), Color(80, 84, 92, 210))
    if title:
        draw_text(font, title, int(rect.x) + 12, int(rect.y) + 10, 18, RAYWHITE)
    if body:
        draw_text(font, body, int(rect.x) + 12, int(rect.y) + 38, 16, LIGHTGRAY)


def clickable(rect: Rectangle) -> bool:
    if not layer_interactive():
        return False
    hovered = check_collision_point_rec(mouse_point(), rect)
    if hovered:
        draw_rectangle_rounded_lines_ex(rect, 0.035, 6, 2.0, Color(177, 145, 87, 255))
    if hovered and _UI.pressed and not _UI.click_consumed:
        _UI.click_consumed = True
        return True
    return False


def text_button(font: Font | None, rect: Rectangle, label: str, size: int = 20, disabled: bool = False) -> bool:
    clicked = False if disabled else clickable(rect)
    fill = Color(24, 27, 34, 255) if disabled else Color(28, 32, 40, 255)
    border = Color(70, 72, 78, 180) if disabled else Color(92, 96, 104, 220)
    draw_frame(rect, fill, border)
    draw_centered_text(font, label, rect, size, Color(118, 118, 118, 255) if disabled else RAYWHITE)
    return clicked


def pill(font: Font | None, rect: Rectangle, label: str, selected: bool = False, disabled: bool = False, scale: float = 1.0) -> bool:
    fill = Color(80, 66, 47, 255) if selected else Color(30, 34, 42, 255)
    border = Color(190, 162, 96, 255) if selected else Color(88, 92, 100, 220)
    if disabled:
        fill = Color(24, 27, 34, 255)
        border = Color(70, 72, 78, 180)
    clicked = False if disabled else clickable(rect)
    draw_frame(rect, fill, border)
    draw_centered_text(font, label, rect, max(11, int(round(18 * scale))), Color(118, 118, 118, 255) if disabled else RAYWHITE)
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
    draw_centered_text(font, label, rect, max(10, int(round(15 * scale))), RAYWHITE if not disabled else Color(110, 110, 110, 255))
    return clicked


def draw_centered_text(font: Font | None, text: str, rect: Rectangle, size: int, color: Color) -> None:
    width = measure_text_width(font, text, size)
    x = int(rect.x + (rect.width - width) * 0.5)
    y = int(rect.y + (rect.height - size) * 0.5) - 1
    draw_text(font, text, x, y, size, color)


def measure_text_width(font: Font | None, text: str, size: int) -> float:
    return measure_text_ex(font, text, float(size), 1.0).x if font is not None else float(measure_text(text, size))


def wrap_text_lines(font: Font | None, text: str, max_width: float, size: int) -> tuple[str, ...]:
    words = text.split()
    if not words:
        return (text,) if text else ()
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
    return tuple(lines)


def wrap_text_lines_any(font: Font | None, text: str, max_width: float, size: int) -> tuple[str, ...]:
    if not text:
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
    return tuple(lines)
