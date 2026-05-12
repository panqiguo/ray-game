from __future__ import annotations

from dataclasses import dataclass

from pyray import *  # type: ignore

from sincity.model.state import GameState
from sincity.rendering import draw_text

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
    draw_text(font, "线索与压力", int(rect.x) + 12, int(rect.y) + 10, title_style.size, title_style.color)

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
    values = state.world.values
    old_case_checked = bool(values.get("old_case_checked", False))
    moon_hotel_unlocked = bool(values.get("moon_hotel_unlocked", False))
    hotel_search_done = bool(values.get("hotel_search_done", False))
    red_room_clipping = bool(values.get("red_room_clipping", False))
    tracker_seen = bool(values.get("tracker_seen", False))

    police_fine_active = bool(values.get("police_fine_active", False))
    police_fine_paid = bool(values.get("police_fine_paid", False))
    police_fine_failed = bool(values.get("police_fine_failed", False))
    police_fine_deadline = int(values.get("police_fine_deadline", 0))
    police_fine_amount = int(values.get("police_fine_amount", 60))
    gang_warning_active = bool(values.get("gang_warning_active", False))
    gang_warning_deadline = int(values.get("gang_warning_deadline", 0))
    gang_pressure_forced = bool(values.get("gang_pressure_forced", False))
    pressure_phase = int(values.get("pressure_phase", 0))

    if hotel_search_done:
        main_text = "主线：整理望月旅馆带回的红房间线索"
    elif moon_hotel_unlocked:
        main_text = "主线：前往望月旅馆搜寻 302 房间"
    elif old_case_checked:
        main_text = "主线：在城里打听薇拉的去向"
    else:
        main_text = "主线：去警局查十年前红房间旧案"

    lines: list[TaskLine] = [TaskLine(main_text, active=not hotel_search_done, completed=hotel_search_done and red_room_clipping)]
    lines.append(TaskLine("查阅红房间旧案报告", completed=old_case_checked, active=not old_case_checked))
    lines.append(TaskLine("在酒吧或老街打听薇拉", completed=moon_hotel_unlocked, active=old_case_checked and not moon_hotel_unlocked))
    lines.append(TaskLine("搜寻望月旅馆 302 房间", completed=hotel_search_done, active=moon_hotel_unlocked and not hotel_search_done))
    if tracker_seen:
        lines.append(TaskLine("有人开始跟踪你", active=True, failed=True))

    pressure_lines = _pressure_lines(
        state_day=state.day,
        police_fine_active=police_fine_active,
        police_fine_paid=police_fine_paid,
        police_fine_failed=police_fine_failed,
        police_fine_deadline=police_fine_deadline,
        police_fine_amount=police_fine_amount,
        gang_warning_active=gang_warning_active,
        gang_warning_deadline=gang_warning_deadline,
        gang_pressure_forced=gang_pressure_forced,
        pressure_phase=pressure_phase,
    )
    lines.extend(pressure_lines)
    return tuple(line for line in lines if line.completed or line.active or line is lines[0])


def _pressure_lines(
    *,
    state_day: int,
    police_fine_active: bool,
    police_fine_paid: bool,
    police_fine_failed: bool,
    police_fine_deadline: int,
    police_fine_amount: int,
    gang_warning_active: bool,
    gang_warning_deadline: int,
    gang_pressure_forced: bool,
    pressure_phase: int,
) -> tuple[TaskLine, ...]:
    rows: list[TaskLine] = []
    if police_fine_active:
        days_left = police_fine_deadline - state_day
        if days_left > 0:
            rows.append(TaskLine(f"压力：警察罚单 {police_fine_amount} 元，还剩 {days_left} 天", active=True))
        elif days_left == 0:
            rows.append(TaskLine(f"压力：警察罚单 {police_fine_amount} 元，今天到期", active=True, failed=True))
        else:
            rows.append(TaskLine("压力：警察罚单已经逾期", active=True, failed=True))
    elif police_fine_paid:
        rows.append(TaskLine("压力：警察罚单已缴清", completed=True))
    elif police_fine_failed:
        rows.append(TaskLine("压力：警察已经上门收拾过你", completed=True, failed=True))

    if gang_pressure_forced:
        rows.append(TaskLine("压力：黑帮正在把你拖进巷子", active=True, failed=True))
    elif gang_warning_active:
        days_left = gang_warning_deadline - state_day
        if days_left > 0:
            rows.append(TaskLine(f"压力：黑帮警告，还剩 {days_left} 天", active=True))
        else:
            rows.append(TaskLine("压力：黑帮警告已经到期", active=True, failed=True))
    elif pressure_phase >= 3:
        rows.append(TaskLine("压力：黑帮施压暂时退去", completed=True))
    return tuple(rows)


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
