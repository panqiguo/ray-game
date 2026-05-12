from __future__ import annotations

from dataclasses import dataclass

from pyray import *  # type: ignore

from raygame.model.state import GameState
from raygame.rendering import draw_text

from .ui_core import measure_text_width, wrap_text_lines_any
from .ui_text import ui_text_color, ui_text_style


@dataclass(frozen=True)
class TaskLine:
    text: str
    completed: bool = False
    active: bool = False
    failed: bool = False


def draw_task_panel(font, rect: Rectangle, state: GameState) -> None:
    title_style = ui_text_style("subtitle", scale=(20 / 24))
    main_style = ui_text_style("body", "default")
    active_style = ui_text_style("body_sm", "accent")
    done_style = ui_text_style("body_sm", "subtle")
    future_style = ui_text_style("body_sm", "muted")
    danger_style = ui_text_style("body_sm", "danger")
    draw_text(font, "任务", int(rect.x) + 12, int(rect.y) + 10, title_style.size, title_style.color)

    content_rect = Rectangle(rect.x + 12, rect.y + 38, rect.width - 24, max(0.0, rect.height - 48))
    rows = _chapter_one_tasks(state)
    content_height = _task_content_height(font, rows, content_rect.width)
    max_scroll = max(0.0, content_height - content_rect.height)
    if max_scroll <= 0:
        state.task_panel_scroll = 0.0
    elif check_collision_point_rec(get_mouse_position(), rect):
        state.task_panel_scroll = max(0.0, min(max_scroll, state.task_panel_scroll - get_mouse_wheel_move() * 34.0))
    else:
        state.task_panel_scroll = max(0.0, min(max_scroll, state.task_panel_scroll))

    begin_scissor_mode(int(content_rect.x), int(content_rect.y), int(content_rect.width), int(content_rect.height))
    y = content_rect.y - state.task_panel_scroll
    main = rows[0]
    main_color = ui_text_color("subtle" if main.completed else ("danger" if main.failed else "default"))
    draw_text(font, main.text, int(content_rect.x), int(y), main_style.size, main_color)
    if main.completed:
        _draw_strike(font, main.text, content_rect.x, y, main_style.size, main_color)
    y += main_style.line_height + 5

    for line in rows[1:]:
        style = danger_style if line.failed else done_style if line.completed else active_style if line.active else future_style
        marker = "✓" if line.completed else ">" if line.active else "·"
        marker_x = content_rect.x + 2
        text_x = content_rect.x + 20
        draw_text(font, marker, int(marker_x), int(y), style.size, style.color)
        wrapped = wrap_text_lines_any(font, line.text, content_rect.width - 20, style.size)
        for part in wrapped:
            draw_text(font, part, int(text_x), int(y), style.size, style.color)
            if line.completed:
                _draw_strike(font, part, text_x, y, style.size, style.color)
            y += style.line_height - 2
        y += 3
    end_scissor_mode()

    if max_scroll > 0:
        _draw_scrollbar(rect, state.task_panel_scroll, max_scroll)


def _chapter_one_tasks(state: GameState) -> tuple[TaskLine, ...]:
    phase = str(state.world.values.get("ch1_phase", "waiting_call"))
    values = state.world.values
    hotel_search_done = bool(values.get("hotel_search_done", False))
    failed = phase == "failed" or bool(values.get("ch1_failed", False))
    main_completed = phase == "done"
    phase_step = {
        "waiting_call": 0,
        "visit_frederick": 1,
        "gather_leads": 2,
        "hotel_inquiry": 3,
        "hotel_infiltration": 4,
        "report_frederick": 5,
        "done": 6,
        "failed": 6,
    }.get(phase, 0)
    all_lines = (
        TaskLine("寻找薇拉的踪迹", completed=main_completed, failed=failed),
        TaskLine("接听弗雷德里克的电话", completed=phase_step > 0, active=phase_step == 0),
        TaskLine("去弗雷德里克住宅面谈", completed=phase_step > 1, active=phase_step == 1),
        TaskLine("在警察局、书店和酒馆调查线索", completed=phase_step > 2, active=phase_step == 2),
        TaskLine("在望月旅馆打听薇拉的住处", completed=phase_step > 3, active=phase_step == 3),
        TaskLine("潜入 302 房间搜寻线索", completed=hotel_search_done, active=phase_step == 4 and not hotel_search_done),
        TaskLine("向弗雷德里克报告旅馆线索", completed=phase == "done", active=phase == "report_frederick"),
    )
    visible_lines = [all_lines[0]]
    for line in all_lines[1:]:
        if line.completed or line.active:
            visible_lines.append(line)
    return tuple(visible_lines)


def _task_content_height(font, rows: tuple[TaskLine, ...], width: float) -> float:
    if not rows:
        return 0.0
    main_style = ui_text_style("body", "default")
    item_style = ui_text_style("body_sm", "muted")
    height = main_style.line_height + 5
    for line in rows[1:]:
        height += max(1, len(wrap_text_lines_any(font, line.text, width - 20, item_style.size))) * (item_style.line_height - 2) + 3
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
