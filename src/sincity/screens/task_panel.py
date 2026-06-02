from __future__ import annotations

from dataclasses import dataclass

from pyray import *  # type: ignore

from sincity.content import SCENARIO
from sincity.content.runtime import RenderedTask, RenderedTaskStep, render_tasks
from sincity.model.state import GameState
from sincity.rendering import draw_text

from .ui_core import Z_MESSAGE, measure_text_width, scroll_available, wrap_text_lines_any
from .ui_text import ui_text_color, ui_text_style


@dataclass(frozen=True)
class TaskRow:
    text: str
    kind: str = "task"
    completed: bool = False
    active: bool = False
    failed: bool = False


GROUP_ORDER = ("主线", "支线", "压力")


def draw_task_panel(font, rect: Rectangle, state: GameState) -> None:
    title_style = ui_text_style("subtitle", scale=(20 / 24))
    draw_text(font, "任务", int(rect.x) + 12, int(rect.y) + 10, title_style.size, title_style.color)

    content_rect = Rectangle(rect.x + 12, rect.y + 38, rect.width - 24, max(0.0, rect.height - 48))
    rows = _task_rows(state)
    content_height = _task_content_height(font, rows, content_rect.width)
    max_scroll = max(0.0, content_height - content_rect.height)
    if max_scroll <= 0:
        state.task_panel_scroll = 0.0
    elif scroll_available(rect, z=Z_MESSAGE):
        state.task_panel_scroll = max(0.0, min(max_scroll, state.task_panel_scroll - get_mouse_wheel_move() * 34.0))
    else:
        state.task_panel_scroll = max(0.0, min(max_scroll, state.task_panel_scroll))

    begin_scissor_mode(int(content_rect.x), int(content_rect.y), int(content_rect.width), int(content_rect.height))
    y = content_rect.y - state.task_panel_scroll
    for row in rows:
        y = _draw_task_row(font, content_rect, y, row)
    end_scissor_mode()

    if max_scroll > 0:
        _draw_scrollbar(rect, state.task_panel_scroll, max_scroll)


def _task_rows(state: GameState) -> tuple[TaskRow, ...]:
    tasks = render_tasks(SCENARIO.get_program(), state)
    rows: list[TaskRow] = []
    for group in GROUP_ORDER:
        group_tasks = tuple(task for task in tasks if task.kind == group and (task.active or task.completed or task.failed))
        if not group_tasks:
            continue
        rows.append(TaskRow(group, kind="group"))
        for task in group_tasks:
            rows.extend(_task_to_rows(task))
    if not rows:
        return (TaskRow("暂无明确任务", kind="empty"),)
    return tuple(rows)


def _task_to_rows(task: RenderedTask) -> tuple[TaskRow, ...]:
    title_row = TaskRow(
        task.title,
        kind="task",
        completed=task.completed,
        active=task.active,
        failed=task.failed,
    )
    if task.completed:
        return (title_row,)
    rows = [title_row]
    if task.description and (task.active or task.failed):
        rows.append(TaskRow(task.description, kind="desc"))
    for step in task.steps:
        if not (step.completed or step.active):
            continue
        rows.append(_step_to_row(step))
    return tuple(rows)


def _step_to_row(step: RenderedTaskStep) -> TaskRow:
    return TaskRow(
        step.title,
        kind="step",
        completed=step.completed,
        active=step.active,
    )


def _draw_task_row(font, content_rect: Rectangle, y: float, row: TaskRow) -> float:
    if row.kind == "group":
        style = ui_text_style("caption", "accent")
        draw_text(font, row.text, int(content_rect.x), int(y), style.size, style.color)
        return y + style.line_height + 2
    if row.kind == "desc":
        style = ui_text_style("caption", "muted")
        return _draw_wrapped(font, row.text, content_rect.x + 10, y, content_rect.width - 10, style, marker="")
    if row.kind == "empty":
        style = ui_text_style("body_sm", "muted")
        draw_text(font, row.text, int(content_rect.x), int(y), style.size, style.color)
        return y + style.line_height

    style = _row_style(row)
    marker = _row_marker(row)
    indent = 16 if row.kind == "step" else 0
    marker_x = content_rect.x + indent + 2
    text_x = content_rect.x + indent + 20
    draw_text(font, marker, int(marker_x), int(y), style.size, style.color)
    next_y = _draw_wrapped(font, row.text, text_x, y, content_rect.width - indent - 20, style, marker=marker)
    if row.completed:
        for index, part in enumerate(wrap_text_lines_any(font, row.text, content_rect.width - indent - 20, style.size)):
            _draw_strike(font, part, text_x, y + index * (style.line_height - 2), style.size, style.color)
    return next_y + (2 if row.kind == "step" else 5)


def _draw_wrapped(font, text: str, x: float, y: float, width: float, style, *, marker: str) -> float:
    del marker
    current_y = y
    for part in wrap_text_lines_any(font, text, width, style.size):
        draw_text(font, part, int(x), int(current_y), style.size, style.color)
        current_y += style.line_height - 2
    return current_y


def _row_style(row: TaskRow):
    if row.failed:
        return ui_text_style("body_sm", "danger")
    if row.completed:
        return ui_text_style("body_sm", "subtle")
    if row.active:
        return ui_text_style("body_sm", "accent")
    return ui_text_style("body_sm", "muted")


def _row_marker(row: TaskRow) -> str:
    if row.failed:
        return "!"
    if row.completed:
        return "✓"
    if row.active:
        return ">"
    return "·"


def _task_content_height(font, rows: tuple[TaskRow, ...], width: float) -> float:
    height = 0.0
    for row in rows:
        if row.kind == "group":
            style = ui_text_style("caption", "accent")
            height += style.line_height + 2
            continue
        if row.kind == "desc":
            style = ui_text_style("caption", "muted")
            height += max(1, len(wrap_text_lines_any(font, row.text, width - 10, style.size))) * (style.line_height - 2)
            continue
        style = ui_text_style("body_sm", "muted")
        indent = 16 if row.kind == "step" else 0
        height += max(1, len(wrap_text_lines_any(font, row.text, width - indent - 20, style.size))) * (style.line_height - 2)
        height += 2 if row.kind == "step" else 5
    return height


def _draw_strike(font, text: str, x: float, y: float, size: int, color: Color) -> None:
    width = measure_text_width(font, text, size)
    line_y = int(y + size * 0.55)
    draw_line_ex(Vector2(float(x), float(line_y)), Vector2(float(x + width), float(line_y)), 1.5, Color(color.r, color.g, color.b, 180))


def _draw_scrollbar(rect: Rectangle, scroll: float, max_scroll: float) -> None:
    track = Rectangle(rect.x + rect.width - 8, rect.y + 38, 3, rect.height - 50)
    if track.height <= 20:
        return
    thumb_h = max(22.0, track.height * 0.55)
    thumb_y = track.y + (track.height - thumb_h) * (scroll / max_scroll)
    draw_rectangle_rounded(track, 0.5, 4, Color(66, 70, 78, 120))
    draw_rectangle_rounded(Rectangle(track.x, thumb_y, track.width, thumb_h), 0.5, 4, Color(155, 130, 80, 190))
