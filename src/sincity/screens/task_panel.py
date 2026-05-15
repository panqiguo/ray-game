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
    police_interview_started = bool(values.get("police_interview_started", False))
    police_choice_ready = bool(values.get("police_choice_ready", False))
    police_investigation_done = bool(values.get("police_investigation_done", False))
    blood_cleaned = bool(values.get("blood_cleaned", False))
    wounded_man_lead_obtained = bool(values.get("wounded_man_lead_obtained", False))
    item_recovery_started = bool(values.get("item_recovery_started", False))
    item_recovered = bool(values.get("item_recovered", False))
    item_recovery_failed = bool(values.get("item_recovery_failed", False))
    item_auth_sent = bool(values.get("item_auth_sent", False))
    vera_thread_unlocked = bool(values.get("vera_thread_unlocked", False))
    auth_done = bool(values.get("auth_done", False))
    vera_commission_taken = bool(values.get("vera_commission_taken", False))
    frederick_talk_done = bool(values.get("frederick_talk_done", False))
    frederick_real_lead_found = bool(values.get("frederick_real_lead_found", False))
    hotel_boss_talk_done = bool(values.get("hotel_boss_talk_done", False))
    hotel_infiltrated = bool(values.get("hotel_infiltrated", False))
    vera_apartment_found = bool(values.get("vera_apartment_found", False))
    chapter_2_done = bool(values.get("chapter_2_done", False))
    recovery_deadline_day = int(values.get("recovery_deadline_day", 5))
    vera_thread_notice_day = int(values.get("vera_thread_notice_day", 0))
    auth_done_day = int(values.get("auth_done_day", 0))

    police_interview_forced = bool(values.get("police_interview_forced", False))

    if not item_recovered:
        days_left = recovery_deadline_day - state.day
        if days_left > 1:
            main_text = f"主线：{days_left} 天之后去取东西"
        elif days_left == 1:
            main_text = "主线：明天去取东西"
        elif days_left == 0:
            main_text = "主线：今天去取东西"
        else:
            main_text = "主线：立刻去取东西"
    elif chapter_2_done:
        main_text = "主线：整理公寓对峙后的真相"
    elif vera_apartment_found:
        main_text = "主线：进入无门牌公寓"
    elif hotel_infiltrated:
        main_text = "主线：跟踪旅馆后门的人"
    elif hotel_boss_talk_done:
        main_text = "主线：潜入望月旅馆"
    elif frederick_real_lead_found:
        main_text = "主线：和望月旅馆老板谈"
    elif frederick_talk_done:
        main_text = "主线：调查弗雷德里克的踪迹"
    elif vera_commission_taken:
        main_text = "主线：和弗雷德里克谈话"
    elif vera_thread_unlocked:
        main_text = "主线：去酒吧接下薇拉委托"
    elif item_auth_sent:
        main_text = "主线：等待薇拉线索出现"
    elif item_recovered:
        main_text = "主线：把神秘物品送去鉴定"
    elif item_recovery_started:
        main_text = "主线：取回神秘物品"
    elif police_investigation_done:
        main_text = "主线：在第 5 天前取回神秘物品"
    elif police_interview_started:
        main_text = "主线：在警方笔录中处理纸条信息"
    else:
        main_text = "主线：去警局配合调查"

    lines: list[TaskLine] = [TaskLine(main_text, active=not chapter_2_done, completed=chapter_2_done)]
    police_task_failed = police_interview_forced and not police_investigation_done
    police_task_text = "一天之内去警局配合调查"
    if police_interview_forced:
        police_task_text = "警方已经上门强制审问"
    lines.append(TaskLine(police_task_text, completed=police_investigation_done, active=not police_investigation_done, failed=police_task_failed))
    lines.append(TaskLine("在笔录中决定纸条信息怎么处理", completed=police_investigation_done, active=police_interview_started and not police_investigation_done))
    lines.append(TaskLine("取回神秘物品", completed=item_recovered, active=police_investigation_done and not item_recovered, failed=item_recovery_failed))
    lines.append(TaskLine("送去鉴定", completed=item_auth_sent, active=item_recovered and not item_auth_sent))
    lines.append(TaskLine("接下薇拉委托", completed=vera_commission_taken, active=vera_thread_unlocked and not vera_commission_taken))
    lines.append(TaskLine("和弗雷德里克谈话", completed=frederick_talk_done, active=vera_commission_taken and not frederick_talk_done))
    lines.append(TaskLine("调查弗雷德里克踪迹", completed=frederick_real_lead_found, active=frederick_talk_done and not frederick_real_lead_found))
    lines.append(TaskLine("潜入旅馆并跟踪到公寓", completed=vera_apartment_found, active=frederick_real_lead_found and not vera_apartment_found))
    lines.append(TaskLine("完成公寓枪对峙", completed=chapter_2_done, active=vera_apartment_found and not chapter_2_done))

    if not wounded_man_lead_obtained:
        lines.append(TaskLine("可选：调查中枪男人，取回东西时会更有把握", active=True))
    if item_auth_sent and not vera_thread_unlocked:
        days_left = vera_thread_notice_day - state.day
        text = "薇拉线索：明天会有人联系你" if days_left > 0 else "薇拉线索：今天应该出现"
        lines.append(TaskLine(text, active=True))
    if item_auth_sent and not auth_done:
        days_left = auth_done_day - state.day
        if days_left > 0:
            lines.append(TaskLine(f"鉴定结果：还需等待 {days_left} 天", active=True))
        else:
            lines.append(TaskLine("鉴定结果：今天应该送到", active=True))
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
