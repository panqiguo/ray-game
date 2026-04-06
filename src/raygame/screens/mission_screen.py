from __future__ import annotations

from pyray import *  # type: ignore

from raygame.content import MISSION_ACTIONS, MISSION_UTILITY_ACTIONS
from raygame.content.growth import GROWTH_DEFS
from raygame.model.enums import AreaName
from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.rules import action_is_available, action_is_visible, action_ready_to_execute, method_is_available, perform_action, perform_free_action
from raygame.screens.widgets import (
    begin_layer,
    close_modal,
    draw_action_modal,
    draw_frame,
    draw_hand,
    draw_message_feed,
    modal_is_open,
    open_modal,
    draw_profile_modal,
    end_layer,
    layout,
    node_button,
    pill,
)


AREA_META = {
    AreaName.PERIMETER: ("外围", 88),
    AreaName.CORRIDOR: ("走廊", 414),
    AreaName.FREEZER: ("冷库", 740),
}

SIDEBAR_WIDTH = 304


def draw_mission_screen(font: Font | None, state: GameState, rng) -> None:
    if is_key_pressed(KEY_ESCAPE):
        close_modal(state)
    page = layout()
    content_rect = Rectangle(page.stage.x + 20, page.stage.y + 76, page.stage.width - SIDEBAR_WIDTH - 52, page.stage.height - 96)
    side_rect = Rectangle(page.stage.x + page.stage.width - SIDEBAR_WIDTH - 20, page.stage.y + 76, SIDEBAR_WIDTH, page.stage.height - 96)
    draw_frame(page.stage, Color(20, 22, 29, 245))
    draw_text(font, "屠宰场蓝图", int(page.stage.x) + 22, int(page.stage.y) + 18, 30, RAYWHITE)
    draw_text(font, "区域内行动点可自由顺序处理，区域间单向推进。", int(page.stage.x) + 22, int(page.stage.y) + 54, 18, LIGHTGRAY)
    begin_layer("mission_world", interactive=not modal_is_open(state))
    _draw_blueprint(font, state, content_rect)
    _draw_mission_sidebar(font, state, side_rect)
    end_layer("mission_world")
    _draw_alarm_bar(font, state, content_rect)
    if modal_is_open(state, "action"):
        begin_layer("mission_action_modal", interactive=True)
        _draw_action_overlay(font, state, rng)
        end_layer("mission_action_modal")
    if modal_is_open(state, "utility"):
        begin_layer("mission_utility_modal", interactive=True)
        _draw_utility_action_modal(font, state, rng)
        end_layer("mission_utility_modal")
    begin_layer("mission_hand", interactive=(not modal_is_open(state) or modal_is_open(state, "action")))
    draw_hand(font, state, _active_mission_action(state))
    end_layer("mission_hand")
    draw_profile_modal(font, state, GROWTH_DEFS)


def _draw_blueprint(font: Font | None, state: GameState, rect: Rectangle) -> None:
    draw_frame(rect, Color(18, 20, 26, 220))
    base_x = int(rect.x) + 22
    base_y = int(rect.y) + 40
    draw_line(base_x + 210, base_y + 58, base_x + 322, base_y + 58, Color(82, 86, 96, 255))
    draw_line(base_x + 536, base_y + 58, base_x + 648, base_y + 58, Color(82, 86, 96, 255))

    for area, (_, x_offset) in AREA_META.items():
        title, _ = AREA_META[area]
        rect = Rectangle(base_x + x_offset, base_y, 240, 206)
        active = area == state.mission.current_area
        draw_frame(rect, Color(33, 29, 25, 255) if active else Color(24, 27, 34, 255), Color(190, 160, 95, 255) if active else Color(82, 86, 94, 220))
        draw_text(font, title, int(rect.x) + 18, int(rect.y) + 16, 28, RAYWHITE)
        _draw_area_actions(font, rect, state, area)


def _draw_area_actions(font: Font | None, rect: Rectangle, state: GameState, area: AreaName) -> None:
    y = int(rect.y) + 62
    for action in _actions_for_area(state, area):
        if area == state.mission.current_area and node_button(
            font,
            Rectangle(rect.x + 14, y, rect.width - 28, 42),
            action.title,
            "",
            active=modal_is_open(state, "action") and state.selected_action_id == action.id,
            disabled=not action_is_available(action, state),
        ):
            state.selected_action_id = action.id
            state.selected_method_id = None
            state.prepared_costs.clear()
            open_modal(state, "action", action.id)
        else:
            color = Color(170, 210, 170, 255) if action.id in state.mission.completed_actions else LIGHTGRAY
            draw_text(font, f"· {action.title}", int(rect.x) + 18, y + 8, 20, color)
        y += 48


def _actions_for_area(state: GameState, area: AreaName):
    actions = []
    for action in MISSION_ACTIONS.values():
        if action.area != area:
            continue
        if area == state.mission.current_area:
            if action_is_visible(action, state):
                actions.append(action)
        elif action.id in state.mission.completed_actions:
            actions.append(action)
    return actions


def _draw_alarm_bar(font: Font | None, state: GameState, content_rect: Rectangle) -> None:
    rect = Rectangle(content_rect.x + 22, content_rect.y + 278, content_rect.width - 44, 72)
    draw_frame(rect, Color(18, 20, 26, 250))
    draw_text(font, "屠宰场警报", int(rect.x) + 18, int(rect.y) + 18, 22, RAYWHITE)
    for index in range(state.clocks.alarm_max):
        cell = Rectangle(rect.x + 182 + index * 50, rect.y + 18, 36, 28)
        fill = Color(183, 95, 77, 255) if index < state.clocks.alarm else Color(36, 40, 48, 255)
        draw_frame(cell, fill, Color(90, 94, 100, 220))
    draw_text(font, f"{state.clocks.alarm}/{state.clocks.alarm_max}", int(rect.x) + 402, int(rect.y) + 20, 22, LIGHTGRAY)
    draw_text(font, "警报满时任务失败。", int(rect.x) + 500, int(rect.y) + 20, 18, LIGHTGRAY)


def _draw_action_overlay(font: Font | None, state: GameState, rng) -> None:
    if not modal_is_open(state, "action") or state.selected_action_id is None:
        return
    action = MISSION_ACTIONS[state.selected_action_id]
    methods = [method for method in action.methods if method_is_available(method, state)]
    shell = draw_action_modal(font, state, action, methods)
    if shell.close_requested:
        close_modal(state)
        return
    if state.selected_card_id and state.selected_method_id and pill(font, Rectangle(shell.rect.x + 276, shell.rect.y + 376, 168, 34), "确认行动", False):
        method = next(item for item in methods if item.id == state.selected_method_id)
        perform_action(state, rng, action, method, state.selected_card_id)
    if pill(font, Rectangle(shell.rect.x + 460, shell.rect.y + 376, 168, 34), "取消", False):
        close_modal(state)


def _draw_mission_sidebar(font: Font | None, state: GameState, rect: Rectangle) -> None:
    utility_rect = Rectangle(rect.x, rect.y, rect.width, 174)
    message_rect = Rectangle(rect.x, rect.y + 188, rect.width, rect.height - 188)
    draw_frame(utility_rect, Color(18, 20, 26, 245))
    draw_text(font, "技能", int(utility_rect.x) + 16, int(utility_rect.y) + 14, 24, RAYWHITE)
    y = int(utility_rect.y) + 50
    for action in MISSION_UTILITY_ACTIONS.values():
        disabled = not action_is_available(action, state)
        if node_button(font, Rectangle(utility_rect.x + 16, y, utility_rect.width - 32, 48), action.title, action.description, disabled=disabled):
            open_modal(state, "utility", action.id)
            state.selected_action_id = action.id
            state.selected_method_id = None
            state.prepared_costs.clear()
        y += 58
    draw_message_feed(font, message_rect, state)


def _draw_utility_action_modal(font: Font | None, state: GameState, rng) -> None:
    assert state.modal.primary_id is not None
    action = MISSION_UTILITY_ACTIONS[state.modal.primary_id]
    shell = draw_action_modal(font, state, action, [])
    if shell.close_requested:
        close_modal(state)
        return
    if pill(font, Rectangle(shell.rect.x + 276, shell.rect.y + 376, 168, 34), "执行", False, disabled=not action_ready_to_execute(action, state)):
        perform_free_action(state, rng, action)
        close_modal(state)
    if pill(font, Rectangle(shell.rect.x + 460, shell.rect.y + 376, 168, 34), "取消", False):
        close_modal(state)


def _active_mission_action(state: GameState):
    if modal_is_open(state, "utility") and state.modal.primary_id is not None:
        return MISSION_UTILITY_ACTIONS[state.modal.primary_id]
    if modal_is_open(state, "action") and state.selected_action_id is not None:
        return MISSION_ACTIONS[state.selected_action_id]
    return None
