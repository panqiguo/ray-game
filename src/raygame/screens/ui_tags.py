from __future__ import annotations

import math

from pyray import *  # type: ignore

from raygame.content import SCENARIO
from raygame.model.defs import ActionDef, InputRequirement
from raygame.model.state import GameState
from raygame.rendering import draw_text

from .ui_core import draw_centered_text, draw_frame, measure_text_width


RESOURCE_LABELS = {
    "money": "金币",
    "cigarettes": "烟卷",
}

ITEM_LABELS = {
    "clothes": "华美衣服",
    "car_key": "车钥匙",
    "repair_case_item": "任务道具",
    "gun": "枪",
}


def draw_clock_badges(
    font: Font | None,
    rect: Rectangle,
    clock_ids: tuple[str, ...],
    state: GameState,
    align: str = "left",
    outside: bool = True,
) -> None:
    visible_clock_ids = tuple(
        clock_id for clock_id in clock_ids if "action_use" not in SCENARIO.clocks_by_id[clock_id].tags
    )
    if not visible_clock_ids:
        return
    total_width = 0.0
    for clock_id in visible_clock_ids:
        spec = SCENARIO.clocks_by_id[clock_id]
        total_width += max(112.0, measure_text_width(font, spec.title, 14) + spec.segments * 16 + 42.0) + 10.0
    total_width = max(0.0, total_width - 10.0)
    x = rect.x + 8 if align == "left" else rect.x + rect.width - total_width - 8
    y = rect.y - 22 if outside else rect.y + 6
    for clock_id in visible_clock_ids:
        spec = SCENARIO.clocks_by_id[clock_id]
        chip_width = max(112.0, measure_text_width(font, spec.title, 14) + spec.segments * 16 + 42.0)
        chip = Rectangle(x, y, chip_width, 18 if outside else 20)
        draw_frame(chip, Color(18, 20, 26, 255), Color(90, 94, 100, 220))
        draw_text(font, spec.title, int(chip.x) + 8, int(chip.y) + (1 if outside else 2), 12 if outside else 13, LIGHTGRAY)
        draw_inline_clock(font, chip, spec.segments, state.world.progress_clocks[clock_id].value)
        x += chip_width + 10


def draw_clock_row(font: Font | None, rect: Rectangle, clock_ids: tuple[str, ...], state: GameState) -> None:
    x = rect.x
    y = rect.y
    for clock_id in clock_ids:
        spec = SCENARIO.clocks_by_id[clock_id]
        if "action_use" in spec.tags:
            continue
        width = max(132.0, measure_text_width(font, spec.title, 16) + spec.segments * 18 + 52.0)
        chip = Rectangle(x, y, width, 24)
        draw_text(font, spec.title, int(chip.x), int(chip.y) + 2, 16, LIGHTGRAY)
        draw_inline_clock(font, Rectangle(chip.x + 74, chip.y + 1, chip.width - 74, 20), spec.segments, state.world.progress_clocks[clock_id].value)
        x += width + 20


def draw_action_corner_clocks(rect: Rectangle, clock_ids: tuple[str, ...], state: GameState, align: str = "left") -> None:
    offset = 0.0
    for clock_id in clock_ids:
        spec = SCENARIO.clocks_by_id[clock_id]
        if "action_use" not in spec.tags:
            continue
        center_x = rect.x + offset if align == "left" else rect.x + rect.width - offset
        center = Vector2(center_x, rect.y)
        draw_usage_clock(center, 12.0, state.world.progress_clocks[clock_id].value, spec.segments)
        offset += 30.0


def draw_corner_labels(font: Font | None, rect: Rectangle, labels: tuple[str, ...], corner: str) -> None:
    offset = 0.0
    for label in labels:
        width = max(54.0, measure_text_width(font, label, 14) + 18.0)
        box_x = rect.x if corner == "left" else rect.x + rect.width - width
        box = Rectangle(box_x, rect.y - 24.0 - offset, width, 20.0)
        if label == "新":
            fill = Color(52, 92, 74, 245)
            border = Color(126, 210, 164, 255)
        else:
            fill = Color(80, 66, 47, 245)
            border = Color(190, 162, 96, 255)
        draw_frame(box, fill, border)
        draw_centered_text(font, label, box, 14, RAYWHITE)
        offset += 24.0


def condition_labels(conditions) -> tuple[str, ...]:
    labels: list[str] = []
    for item in conditions:
        if item.kind == "has_item" and isinstance(item.value, str):
            labels.append(f"需 {ITEM_LABELS.get(item.value, item.value)}")
    return tuple(labels)


def requirement_labels(requirements: tuple[InputRequirement, ...]) -> tuple[str, ...]:
    labels: list[str] = []
    for requirement in requirements:
        if requirement.kind == "item" and not requirement.consume:
            labels.append(f"需 {requirement.label or ITEM_LABELS.get(requirement.key, requirement.key)}")
    return tuple(labels)


def action_corner_labels(action: ActionDef) -> tuple[str, ...]:
    labels = list(condition_labels(action.conditions))
    labels.extend(requirement_labels(action.inputs))
    if is_single_use_action(action) and not labels:
        labels.insert(0, "单次")
    return tuple(labels)


def location_corner_labels(location) -> tuple[str, ...]:
    return condition_labels(location.conditions)


def location_status_labels(location_id: str, location, state: GameState) -> tuple[str, ...]:
    labels = list(location_corner_labels(location))
    if location_id in state.world.fresh_locations:
        labels.insert(0, "新")
    return tuple(labels)


def draw_inline_clock(font: Font | None, rect: Rectangle, segments: int, value: int) -> None:
    chip_size = 10 if rect.height <= 18 else 12
    spacing = chip_size + 4
    start_x = rect.x + rect.width - segments * spacing - 28
    for index in range(segments):
        cell = Rectangle(start_x + index * spacing, rect.y + (2 if rect.height <= 18 else 3), chip_size, chip_size)
        fill = Color(190, 162, 96, 255) if index < value else Color(44, 48, 56, 255)
        draw_rectangle_rounded(cell, 0.2, 4, fill)
        draw_rectangle_rounded_lines_ex(cell, 0.2, 4, 1.0, Color(96, 96, 96, 200))
    draw_text(font, f"{value}/{segments}", int(start_x + segments * spacing + 8), int(rect.y), 12 if rect.height <= 18 else 13, Color(212, 196, 132, 255))


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


def is_single_use_action(action: ActionDef) -> bool:
    return any(item.kind == "hide_action" and item.value == action.id for item in action.effects)
