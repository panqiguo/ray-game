from __future__ import annotations

from pyray import *  # type: ignore

from raygame.content import CITY_ACTIONS, CITY_LOCATIONS, CITY_UTILITY_ACTIONS, GROWTH_DEFS
from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.rules import action_is_available, action_is_visible, action_ready_to_execute, method_is_available, perform_action, perform_free_action
from raygame.screens.widgets import (
    begin_layer,
    centered_rect,
    close_modal,
    draw_action_modal,
    draw_casebook_hint,
    draw_frame,
    draw_hand,
    draw_message_feed,
    draw_modal_shell,
    modal_blocks_world,
    modal_is_open,
    draw_profile_modal,
    end_layer,
    layout,
    node_button,
    pill,
    open_modal,
)


LOCATION_LAYOUT = {
    "office": ((96, 92), "办公桌 / 案卷"),
    "red_light": ((420, 92), "暗巷 / 酒吧"),
    "docks": ((744, 92), "集装箱区 / 走私商"),
    "black_market": ((258, 312), "街边摊"),
    "clinic": ((582, 312), "包扎"),
    "slaughterhouse": ((906, 312), "潜入入口"),
}

SIDEBAR_WIDTH = 304


def draw_city_screen(font: Font | None, state: GameState, rng) -> None:
    if is_key_pressed(KEY_ESCAPE):
        if state.selected_action_id is not None:
            state.selected_action_id = None
            state.selected_method_id = None
            state.prepared_costs.clear()
            if modal_is_open(state, "utility"):
                close_modal(state)
        else:
            close_modal(state)
    page = layout()
    content_rect = Rectangle(page.stage.x + 20, page.stage.y + 76, page.stage.width - SIDEBAR_WIDTH - 52, page.stage.height - 96)
    side_rect = Rectangle(page.stage.x + page.stage.width - SIDEBAR_WIDTH - 20, page.stage.y + 76, SIDEBAR_WIDTH, page.stage.height - 96)
    draw_frame(page.stage, Color(21, 24, 31, 245))
    draw_text(font, f"第 {state.day} 天：城市整备", int(page.stage.x) + 22, int(page.stage.y) + 18, 30, RAYWHITE)
    draw_text(font, "城区地图", int(page.stage.x) + 22, int(page.stage.y) + 56, 18, LIGHTGRAY)
    begin_layer("city_world", interactive=not modal_is_open(state))
    _draw_city_map(font, state, content_rect)
    _draw_city_sidebar(font, state, side_rect)
    end_layer("city_world")
    if modal_is_open(state, "location"):
        begin_layer("city_location_modal", interactive=state.selected_action_id is None)
        _draw_location_modal(font, state)
        end_layer("city_location_modal")
        if state.selected_action_id is not None:
            begin_layer("city_action_modal", interactive=True)
            _draw_location_action_modal(font, state, rng)
            end_layer("city_action_modal")
    if modal_is_open(state, "utility"):
        begin_layer("city_utility_modal", interactive=True)
        _draw_utility_action_modal(font, state, rng)
        end_layer("city_utility_modal")
    begin_layer("city_hand", interactive=(not modal_blocks_world(state) or state.selected_action_id is not None))
    draw_hand(font, state, _active_city_action(state))
    end_layer("city_hand")
    draw_casebook_hint(font, state)
    draw_profile_modal(font, state, GROWTH_DEFS)


def _draw_city_map(font: Font | None, state: GameState, rect: Rectangle) -> None:
    draw_frame(rect, Color(18, 20, 26, 220))
    map_origin_x = int(rect.x) + 28
    map_origin_y = int(rect.y) + 26
    line_color = Color(66, 70, 82, 255)

    draw_line(map_origin_x + 140, map_origin_y + 76, map_origin_x + 360, map_origin_y + 76, line_color)
    draw_line(map_origin_x + 466, map_origin_y + 76, map_origin_x + 682, map_origin_y + 76, line_color)
    draw_line(map_origin_x + 358, map_origin_y + 146, map_origin_x + 358, map_origin_y + 254, line_color)
    draw_line(map_origin_x + 682, map_origin_y + 254, map_origin_x + 842, map_origin_y + 254, line_color)

    for location_id, location in CITY_LOCATIONS.items():
        if location_id == "slaughterhouse" and "clue_a" not in state.clues and state.day < 3:
            continue
        offset, subtitle = LOCATION_LAYOUT[location_id]
        rect = Rectangle(map_origin_x + offset[0], map_origin_y + offset[1], 224, 82)
        active = modal_is_open(state, "location") and state.modal.primary_id == location_id
        if node_button(font, rect, location.title, subtitle, active=active):
            open_modal(state, "location", location_id)
            state.selected_action_id = None
            state.selected_method_id = None
            state.prepared_costs.clear()


def _draw_city_sidebar(font: Font | None, state: GameState, rect: Rectangle) -> None:
    utility_rect = Rectangle(rect.x, rect.y, rect.width, 174)
    message_rect = Rectangle(rect.x, rect.y + 188, rect.width, rect.height - 188)
    draw_frame(utility_rect, Color(18, 20, 26, 245))
    draw_text(font, "技能", int(utility_rect.x) + 16, int(utility_rect.y) + 14, 24, RAYWHITE)
    y = int(utility_rect.y) + 50
    for action in CITY_UTILITY_ACTIONS.values():
        disabled = not action_is_available(action, state)
        if node_button(font, Rectangle(utility_rect.x + 16, y, utility_rect.width - 32, 48), action.title, action.description, disabled=disabled):
            open_modal(state, "utility", action.id)
            state.selected_action_id = action.id
            state.selected_method_id = None
            state.prepared_costs.clear()
        y += 58
    draw_message_feed(font, message_rect, state)


def _draw_location_modal(font: Font | None, state: GameState) -> None:
    if state.modal.primary_id is None:
        return
    location = CITY_LOCATIONS[state.modal.primary_id]
    modal = centered_rect(760, 320, -40)
    shell = draw_modal_shell(font, location.title, modal, subtitle=location.description, scope=layout().stage)
    if shell.close_requested:
        close_modal(state)
        return

    x = int(shell.body.x)
    y = int(shell.body.y)
    visible_actions = [CITY_ACTIONS[action_id] for action_id in location.action_ids if action_is_visible(CITY_ACTIONS[action_id], state)]
    for action in visible_actions:
        rect = Rectangle(x, y, 220, 56)
        active = state.selected_action_id == action.id
        if node_button(font, rect, action.title, action.description, active=active, disabled=not action_is_available(action, state)):
            state.selected_action_id = action.id
            state.selected_method_id = None
            state.prepared_costs.clear()
            state.modal.primary_id = location.id
        x += 236
        if x + 220 > shell.rect.x + shell.rect.width - 20:
            x = int(shell.body.x)
            y += 72

    if not visible_actions:
        draw_text(font, "此处今天没有可用行动。", int(shell.body.x), int(shell.body.y), 18, LIGHTGRAY)


def _draw_location_action_modal(font: Font | None, state: GameState, rng) -> None:
    assert state.modal.primary_id is not None
    assert state.selected_action_id is not None
    action = CITY_ACTIONS[state.selected_action_id]
    methods = [method for method in action.methods if method_is_available(method, state)]
    shell = draw_action_modal(font, state, action, methods)
    if shell.close_requested:
        state.selected_action_id = None
        state.selected_method_id = None
        state.prepared_costs.clear()
        return
    if not action.methods:
        if pill(font, Rectangle(shell.rect.x + 276, shell.rect.y + 376, 168, 34), "执行", False, disabled=not action_ready_to_execute(action, state)):
            perform_free_action(state, rng, action)
            close_modal(state)
        if pill(font, Rectangle(shell.rect.x + 460, shell.rect.y + 376, 168, 34), "取消", False):
            state.selected_action_id = None
            state.selected_method_id = None
            state.prepared_costs.clear()
        return
    if state.selected_card_id and state.selected_method_id and pill(font, Rectangle(shell.rect.x + 276, shell.rect.y + 376, 168, 34), "确认行动", False):
        method = next(item for item in methods if item.id == state.selected_method_id)
        perform_action(state, rng, action, method, state.selected_card_id)
    if pill(font, Rectangle(shell.rect.x + 460, shell.rect.y + 376, 168, 34), "取消", False):
        state.selected_action_id = None
        state.selected_method_id = None
        state.prepared_costs.clear()


def _draw_utility_action_modal(font: Font | None, state: GameState, rng) -> None:
    assert state.modal.primary_id is not None
    action = CITY_UTILITY_ACTIONS[state.modal.primary_id]
    shell = draw_action_modal(font, state, action, [])
    if shell.close_requested:
        close_modal(state)
        return
    if pill(font, Rectangle(shell.rect.x + 276, shell.rect.y + 376, 168, 34), "执行", False, disabled=not action_ready_to_execute(action, state)):
        perform_free_action(state, rng, action)
        close_modal(state)
    if pill(font, Rectangle(shell.rect.x + 460, shell.rect.y + 376, 168, 34), "取消", False):
        close_modal(state)


def _active_city_action(state: GameState):
    if modal_is_open(state, "utility") and state.modal.primary_id is not None:
        return CITY_UTILITY_ACTIONS[state.modal.primary_id]
    if modal_is_open(state, "location") and state.selected_action_id is not None:
        return CITY_ACTIONS[state.selected_action_id]
    return None
