from __future__ import annotations

import math

from pyray import *  # type: ignore

from raygame.labels import ITEM_LABELS
from raygame.model.defs import ActionDef, InputRequirement
from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.rules import get_clock_spec_for_state, get_clock_value

from .ui_core import draw_centered_text, draw_frame, measure_text_width
from .ui_text import ui_text_color, ui_text_style


def draw_clock_badges(
    font: Font | None,
    rect: Rectangle,
    clock_ids: tuple[str, ...],
    state: GameState,
    align: str = "left",
    outside: bool = True,
    scale: float = 1.0,
) -> None:
    visible_clock_ids = tuple(
        clock_id for clock_id in clock_ids if "action_use" not in _clock_spec(state, clock_id).tags
    )
    if not visible_clock_ids:
        return
    total_width = 0.0
    for clock_id in visible_clock_ids:
        spec = _clock_spec(state, clock_id)
        text_style = ui_text_style("body_sm", scale=scale, minimum_size=11)
        text_size = text_style.size
        total_width += max(112.0 * scale, measure_text_width(font, spec.title, text_size) + spec.segments * 18.0 * scale + 42.0 * scale) + 10.0 * scale
    total_width = max(0.0, total_width - 10.0)
    x = rect.x + 8.0 * scale if align == "left" else rect.x + rect.width - total_width - 8.0 * scale
    y = rect.y - 22.0 * scale if outside else rect.y + 6.0 * scale
    for clock_id in visible_clock_ids:
        spec = _clock_spec(state, clock_id)
        text_style = ui_text_style("body_sm", "muted", scale=scale, minimum_size=11)
        text_size = text_style.size
        chip_width = max(112.0 * scale, measure_text_width(font, spec.title, text_size) + spec.segments * 18.0 * scale + 42.0 * scale)
        chip = Rectangle(x, y, chip_width, (18.0 if outside else 20.0) * scale)
        draw_frame(chip, Color(18, 20, 26, 255), Color(90, 94, 100, 220))
        draw_text(font, spec.title, int(chip.x) + int(8.0 * scale), int(chip.y) + (1 if outside else 2), text_style.size - (1 if outside else 0), text_style.color)
        draw_inline_clock(font, chip, spec.segments, _clock_value(state, clock_id), scale=scale)
        x += chip_width + 10.0 * scale


def draw_clock_row(font: Font | None, rect: Rectangle, clock_ids: tuple[str, ...], state: GameState, scale: float = 1.0) -> None:
    x = rect.x
    y = rect.y
    for clock_id in clock_ids:
        spec = _clock_spec(state, clock_id)
        if "action_use" in spec.tags:
            continue
        title_style = ui_text_style("body", "muted", scale=scale, minimum_size=11)
        desc_style = ui_text_style("caption", "subtle", scale=scale, minimum_size=9)
        desc_size = desc_style.size
        desc_width = measure_text_width(font, spec.description, desc_size) if spec.description else 0.0
        width = max(
            156.0 * scale,
            measure_text_width(font, spec.title, title_style.size) + spec.segments * 18.0 * scale + 52.0 * scale,
            desc_width + 8.0 * scale,
        )
        chip = Rectangle(x, y, width, 42.0 * scale if spec.description else 24.0 * scale)
        draw_text(font, spec.title, int(chip.x), int(chip.y) + max(1, int(round(2 * scale))), title_style.size, title_style.color)
        draw_inline_clock(
            font,
            Rectangle(chip.x + 74.0 * scale, chip.y + 1.0 * scale, chip.width - 74.0 * scale, 20.0 * scale),
            spec.segments,
            _clock_value(state, clock_id),
            scale=scale,
        )
        if spec.description:
            draw_text(
                font,
                spec.description,
                int(chip.x),
                int(chip.y + 22.0 * scale),
                desc_style.size,
                desc_style.color,
            )
        x += width + 20.0 * scale


def draw_action_corner_clocks(rect: Rectangle, clock_ids: tuple[str, ...], state: GameState, align: str = "left", scale: float = 1.0) -> None:
    offset = 0.0
    for clock_id in clock_ids:
        spec = _clock_spec(state, clock_id)
        if "action_use" not in spec.tags:
            continue
        center_x = rect.x + offset if align == "left" else rect.x + rect.width - offset
        center = Vector2(center_x, rect.y)
        draw_usage_clock(center, 12.0 * scale, _clock_value(state, clock_id), spec.segments)
        offset += 30.0 * scale


def draw_corner_labels(font: Font | None, rect: Rectangle, labels: tuple[str, ...], corner: str, scale: float = 1.0) -> None:
    offset = 0.0
    label_style = ui_text_style("body_sm", scale=scale, minimum_size=11)
    for label in labels:
        width = max(54.0 * scale, measure_text_width(font, label, label_style.size) + 18.0 * scale)
        box_x = rect.x if corner == "left" else rect.x + rect.width - width
        box = Rectangle(box_x, rect.y - 24.0 * scale - offset, width, 20.0 * scale)
        if label == "新":
            fill = Color(52, 92, 74, 245)
            border = Color(126, 210, 164, 255)
        else:
            fill = Color(80, 66, 47, 245)
            border = Color(190, 162, 96, 255)
        draw_frame(box, fill, border)
        draw_centered_text(font, label, box, label_style.size, ui_text_color("default"))
        offset += 24.0 * scale


def condition_labels(conditions) -> tuple[str, ...]:
    labels: list[str] = []
    for item in conditions:
        if item.label:
            labels.append(item.label)
            continue
        if item.kind == "has_item" and isinstance(item.value, str):
            key, _, raw_amount = item.value.partition(":")
            amount = int(raw_amount) if raw_amount else 1
            title = ITEM_LABELS.get(key, key)
            labels.append(f"需要 {title}" if amount == 1 else f"需要 {title} x{amount}")
        elif item.kind == "field_at_least" and isinstance(item.value, str):
            key, raw = item.value.split(":", 1)
            title = ITEM_LABELS.get(key, key)
            labels.append(f"需要 {title} {raw}")
    return tuple(labels)


def requirement_labels(requirements: tuple[InputRequirement, ...]) -> tuple[str, ...]:
    labels: list[str] = []
    for requirement in requirements:
        if requirement.kind == "item" and not requirement.consume:
            labels.append(f"需要 {requirement.label or ITEM_LABELS.get(requirement.key, requirement.key)}")
    return tuple(labels)


def action_corner_labels(action: ActionDef) -> tuple[str, ...]:
    labels = list(condition_labels(action.conditions))
    if action_starts_encounter(action):
        labels.append("外出")
    labels.extend(requirement_labels(action.inputs))
    return tuple(labels)


def action_starts_encounter(action: ActionDef) -> bool:
    effects = list(action.effects)
    if action.check is not None:
        effects.extend(action.check.success.effects)
        effects.extend(action.check.cost.effects)
        effects.extend(action.check.fail.effects)
    return any(effect.kind == "start_encounter" for effect in effects)


def location_corner_labels(location) -> tuple[str, ...]:
    return condition_labels(location.conditions)


def location_status_labels(location_id: str, location, state: GameState) -> tuple[str, ...]:
    labels = list(location_corner_labels(location))
    if location_id in state.world.fresh_locations:
        labels.insert(0, "新")
    return tuple(labels)


def draw_inline_clock(font: Font | None, rect: Rectangle, segments: int, value: int, scale: float = 1.0) -> None:
    chip_size = max(7, int(round((10 if rect.height <= 18 else 12) * scale)))
    spacing = chip_size + max(4, int(round(6 * scale)))
    start_x = rect.x + rect.width - segments * spacing - max(16.0, 30.0 * scale)
    for index in range(segments):
        cell = Rectangle(start_x + index * spacing, rect.y + (2 if rect.height <= 18 else 3) * scale, chip_size, chip_size)
        fill = Color(190, 162, 96, 255) if index < value else Color(44, 48, 56, 255)
        draw_rectangle_rounded(cell, 0.2, 4, fill)
        draw_rectangle_rounded_lines_ex(cell, 0.2, 4, 1.0, Color(96, 96, 96, 200))
    value_style = ui_text_style("caption", "accent", scale=scale, minimum_size=10)
    draw_text(font, f"{value}/{segments}", int(start_x + segments * spacing + max(6.0, 8.0 * scale)), int(rect.y), value_style.size + (1 if rect.height > 18 else 0), value_style.color)


def draw_usage_clock(center: Vector2, radius: float, value: int, segments: int) -> None:
    draw_circle_v(center, radius + 2.0, Color(12, 14, 18, 240))
    step = 360.0 / segments
    start = -90.0
    for index in range(segments):
        sector_start = start + index * step + 2.0
        sector_end = start + (index + 1) * step - 2.0
        fill = Color(190, 162, 96, 255) if index < value else Color(44, 48, 56, 255)
        draw_circle_sector(center, radius, sector_start, sector_end, 12, fill)
    draw_circle_lines(int(center.x), int(center.y), radius, Color(112, 112, 112, 220))
    for index in range(segments):
        angle = math.radians(start + index * step)
        tip = Vector2(center.x + math.cos(angle) * radius, center.y + math.sin(angle) * radius)
        draw_line_ex(center, tip, 1.0, Color(18, 18, 18, 210))
def _clock_spec(state: GameState, clock_id: str):
    return get_clock_spec_for_state(state, clock_id)


def _clock_value(state: GameState, clock_id: str) -> int:
    return get_clock_value(state, clock_id)
