from __future__ import annotations

from dataclasses import dataclass, field

from pyray import *  # type: ignore

from raygame.constants import HAND_HEIGHT, HUD_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH
from raygame.content.cards import CARD_DEFS
from raygame.model.defs import ActionCostDef, ActionMethodDef, ActionPointDef
from raygame.model.enums import RISK_LABELS, ResultType, SUIT_LABELS
from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.rules.judgment import RESULT_TABLE, compute_action_value
from raygame.rules.progression import action_costs_ready, action_selection_ready, cost_is_prepared, effective_difficulty, toggle_prepared_cost


RESOURCE_LABELS = {
    "money": "金币",
    "cigarettes": "烟卷",
}

ITEM_PANEL_WIDTH = 224


@dataclass(frozen=True)
class StageLayout:
    hud: Rectangle
    stage: Rectangle
    hand: Rectangle


@dataclass
class UiInputState:
    mouse: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))
    pressed: bool = False
    click_consumed: bool = False
    layers: list["UiLayerState"] = field(default_factory=list)


@dataclass(frozen=True)
class UiLayerState:
    name: str
    interactive: bool


@dataclass(frozen=True)
class ModalShell:
    rect: Rectangle
    body: Rectangle
    close_requested: bool = False


_UI_INPUT = UiInputState()


def begin_ui_frame() -> None:
    _UI_INPUT.mouse = get_mouse_position()
    _UI_INPUT.pressed = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
    _UI_INPUT.click_consumed = False
    _UI_INPUT.layers.clear()


def finish_ui_frame() -> None:
    assert not _UI_INPUT.layers, f"unclosed ui layers: {[layer.name for layer in _UI_INPUT.layers]}"


def begin_layer(name: str, interactive: bool) -> None:
    _UI_INPUT.layers.append(UiLayerState(name=name, interactive=interactive))


def end_layer(name: str) -> None:
    assert _UI_INPUT.layers, f"attempted to end missing ui layer: {name}"
    layer = _UI_INPUT.layers.pop()
    assert layer.name == name, f"ui layer mismatch: expected {name}, got {layer.name}"


def layer_is_interactive() -> bool:
    return _UI_INPUT.layers[-1].interactive if _UI_INPUT.layers else True


def screen_width() -> int:
    width = get_screen_width()
    return width if width > 0 else WINDOW_WIDTH


def screen_height() -> int:
    height = get_screen_height()
    return height if height > 0 else WINDOW_HEIGHT


def mouse_point() -> Vector2:
    return _UI_INPUT.mouse


def layout() -> StageLayout:
    width = screen_width()
    height = screen_height()
    return StageLayout(
        hud=Rectangle(14, 12, width - 28, HUD_HEIGHT - 18),
        stage=Rectangle(14, HUD_HEIGHT + 8, width - 28, height - HUD_HEIGHT - HAND_HEIGHT - 22),
        hand=Rectangle(14, height - HAND_HEIGHT + 6, width - 28, HAND_HEIGHT - 12),
    )


def centered_rect(width: float, height: float, y_offset: float = 0.0) -> Rectangle:
    screen_w = screen_width()
    screen_h = screen_height()
    return Rectangle((screen_w - width) * 0.5, (screen_h - height) * 0.5 + y_offset, width, height)


def screen_rect() -> Rectangle:
    return Rectangle(0, 0, float(screen_width()), float(screen_height()))


def modal_is_open(state: GameState, kind: str | None = None) -> bool:
    if kind is None:
        return bool(state.modal.kind)
    return state.modal.kind == kind


def open_modal(state: GameState, kind: str, primary_id: str | None = None) -> None:
    state.modal.kind = kind
    state.modal.primary_id = primary_id


def close_modal(state: GameState) -> None:
    state.modal.kind = ""
    state.modal.primary_id = None
    state.selected_action_id = None
    state.selected_method_id = None


def modal_blocks_world(state: GameState) -> bool:
    return bool(state.modal.kind)


def draw_frame(rect: Rectangle, fill: Color, border: Color = Color(110, 110, 110, 210)) -> None:
    draw_rectangle_rounded(rect, 0.035, 6, fill)
    draw_rectangle_rounded_lines_ex(rect, 0.035, 6, 1.5, border)


def draw_scrim(rect: Rectangle) -> None:
    draw_rectangle_rec(rect, Color(5, 6, 10, 170))


def consume_backdrop_click(scope: Rectangle, content: Rectangle) -> bool:
    if not layer_is_interactive() or not _UI_INPUT.pressed or _UI_INPUT.click_consumed:
        return False
    if not check_collision_point_rec(mouse_point(), scope):
        return False
    if check_collision_point_rec(mouse_point(), content):
        return False
    _UI_INPUT.click_consumed = True
    return True


def draw_modal_shell(
    font: Font | None,
    title: str,
    rect: Rectangle,
    *,
    subtitle: str = "",
    scope: Rectangle | None = None,
    close_on_backdrop: bool = False,
) -> ModalShell:
    close_requested = False
    if scope is not None:
        draw_scrim(scope)
        if consume_backdrop_click(scope, rect) and close_on_backdrop:
            close_requested = True
    draw_frame(rect, Color(17, 18, 24, 248), Color(120, 120, 120, 220))
    draw_text(font, title, int(rect.x) + 24, int(rect.y) + 18, 28 if subtitle else 30, RAYWHITE)
    body_y = rect.y + 70
    if subtitle:
        draw_text(font, subtitle, int(rect.x) + 24, int(rect.y) + 52, 18, LIGHTGRAY)
        body_y = rect.y + 94
    if text_button(font, Rectangle(rect.x + rect.width - 96, rect.y + 18, 72, 28), "关闭", 16):
        close_requested = True
    body = Rectangle(rect.x + 24, body_y, rect.width - 48, rect.height - (body_y - rect.y) - 22)
    return ModalShell(rect=rect, body=body, close_requested=close_requested)


def clickable(rect: Rectangle) -> bool:
    if not layer_is_interactive():
        return False
    hovered = check_collision_point_rec(mouse_point(), rect)
    if hovered:
        draw_rectangle_rounded_lines_ex(rect, 0.035, 6, 2.0, Color(177, 145, 87, 255))
    if hovered and _UI_INPUT.pressed and not _UI_INPUT.click_consumed:
        _UI_INPUT.click_consumed = True
        return True
    return False


def text_button(font: Font | None, rect: Rectangle, label: str, size: int = 20, color: Color = RAYWHITE, disabled: bool = False) -> bool:
    clicked = False if disabled else clickable(rect)
    fill = Color(24, 27, 34, 255) if disabled else Color(28, 32, 40, 255)
    border = Color(70, 72, 78, 180) if disabled else Color(92, 96, 104, 220)
    text_color = Color(118, 118, 118, 255) if disabled else color
    draw_frame(rect, fill, border)
    _draw_centered_text(font, label, rect, size, text_color)
    return clicked


def node_button(font: Font | None, rect: Rectangle, title: str, subtitle: str = "", active: bool = False, disabled: bool = False) -> bool:
    fill = Color(72, 57, 42, 255) if active else Color(28, 32, 40, 255)
    border = Color(191, 157, 96, 255) if active else Color(92, 96, 104, 220)
    if disabled:
        fill = Color(22, 24, 30, 240)
        border = Color(62, 66, 74, 180)
    clicked = False if disabled else clickable(rect)
    draw_frame(rect, fill, border)

    title_size = 22 if subtitle else 24
    title_width = measure_text_ex(font, title, float(title_size), 1.0).x if font is not None else float(measure_text(title, title_size))
    max_title_width = rect.width - 28
    while title_size > 16 and title_width > max_title_width:
        title_size -= 1
        title_width = measure_text_ex(font, title, float(title_size), 1.0).x if font is not None else float(measure_text(title, title_size))

    title_y = int(rect.y) + 10 if subtitle else int(rect.y + (rect.height - title_size) * 0.5)
    draw_text(font, title, int(rect.x) + 14, title_y, title_size, Color(235, 235, 235, 255) if not disabled else Color(120, 120, 120, 255))
    if subtitle:
        subtitle_size = 15
        subtitle_y = int(rect.y) + rect.height - subtitle_size - 10
        draw_text(font, subtitle, int(rect.x) + 14, subtitle_y, subtitle_size, Color(185, 185, 185, 255) if not disabled else Color(100, 100, 100, 255))
    return clicked


def pill(font: Font | None, rect: Rectangle, label: str, selected: bool = False, disabled: bool = False) -> bool:
    fill = Color(80, 66, 47, 255) if selected else Color(30, 34, 42, 255)
    border = Color(190, 162, 96, 255) if selected else Color(88, 92, 100, 220)
    text_color = RAYWHITE
    if disabled:
        fill = Color(24, 27, 34, 255)
        border = Color(70, 72, 78, 180)
        text_color = Color(118, 118, 118, 255)
    clicked = False if disabled else clickable(rect)
    draw_frame(rect, fill, border)
    _draw_centered_text(font, label, rect, 18, text_color)
    return clicked


def draw_hud(font: Font | None, state: GameState) -> None:
    begin_layer("hud", interactive=(not modal_is_open(state) or modal_is_open(state, "profile")))
    hud = layout().hud
    draw_frame(hud, Color(20, 22, 29, 245))
    _hud_block(font, Rectangle(hud.x + 18, hud.y + 10, 140, 32), "生命", f"{state.resources.health}/{state.resources.max_health}", Color(214, 112, 112, 255))
    _hud_block(font, Rectangle(hud.x + 170, hud.y + 10, 140, 32), "压力", f"{state.resources.stress}/{state.resources.max_stress}", Color(208, 182, 108, 255))
    _clock_block(font, Rectangle(hud.x + 322, hud.y + 10, 250, 36), "Heat", state.clocks.heat, state.clocks.heat_max)
    _clock_block(font, Rectangle(hud.x + 590, hud.y + 10, 250, 36), "乌鸦", state.clocks.crow_time, state.clocks.crow_time_max)
    if state.screen.value == "mission":
        _clock_block(font, Rectangle(hud.x + 858, hud.y + 10, 220, 36), "警报", state.clocks.alarm, state.clocks.alarm_max)
        mode = "任务"
    elif state.screen.value == "ending":
        mode = "结局"
    else:
        mode = "城市"
    draw_text(font, mode, int(hud.x + hud.width - 210), int(hud.y + 18), 22, LIGHTGRAY)
    profile_disabled = modal_is_open(state) and not modal_is_open(state, "profile")
    if text_button(font, Rectangle(hud.x + hud.width - 148, hud.y + 10, 120, 34), f"档案 {state.growth_points}", 18, disabled=profile_disabled):
        if modal_is_open(state, "profile"):
            close_modal(state)
        else:
            open_modal(state, "profile")
    end_layer("hud")


def _hud_block(font: Font | None, rect: Rectangle, label: str, value: str, color: Color) -> None:
    draw_text(font, label, int(rect.x), int(rect.y), 17, Color(170, 170, 170, 255))
    draw_text(font, value, int(rect.x), int(rect.y) + 16, 24, color)


def _clock_block(font: Font | None, rect: Rectangle, label: str, value: int, max_value: int) -> None:
    draw_text(font, label, int(rect.x), int(rect.y), 17, Color(170, 170, 170, 255))
    bar_x = int(rect.x) + 48
    for index in range(max_value):
        cell = Rectangle(bar_x + index * 24, rect.y + 4, 18, 18)
        fill = Color(190, 162, 96, 255) if index < value else Color(44, 48, 56, 255)
        draw_rectangle_rounded(cell, 0.2, 4, fill)
        draw_rectangle_rounded_lines_ex(cell, 0.2, 4, 1.0, Color(96, 96, 96, 200))
    draw_text(font, f"{value}/{max_value}", int(rect.x) + 48 + max_value * 24 + 8, int(rect.y), 18, LIGHTGRAY)


def draw_hand(font: Font | None, state: GameState, action: ActionPointDef | None = None) -> None:
    hand = layout().hand
    draw_frame(hand, Color(18, 20, 26, 250))
    draw_text(font, "手牌", int(hand.x) + 18, int(hand.y) + 14, 22, RAYWHITE)
    draw_text(font, f"牌库:{len(state.deck.draw_pile)}  弃牌:{len(state.deck.discard_pile)}", int(hand.x + hand.width - ITEM_PANEL_WIDTH - 120), int(hand.y) + 14, 20, LIGHTGRAY)
    x = int(hand.x) + 18
    y = int(hand.y) + 48
    card_w = 152
    cards_right = hand.x + hand.width - ITEM_PANEL_WIDTH - 18
    for card_id in state.deck.hand:
        if x + card_w > cards_right:
            break
        rect = Rectangle(x, y, card_w, 106)
        if draw_compact_card(font, rect, card_id, state.selected_card_id == card_id):
            if _card_can_be_slotted(action, card_id):
                state.selected_card_id = None if state.selected_card_id == card_id else card_id
        x += card_w + 12
    inventory_rect = Rectangle(hand.x + hand.width - ITEM_PANEL_WIDTH, hand.y + 10, ITEM_PANEL_WIDTH - 12, hand.height - 20)
    draw_inventory_panel(font, inventory_rect, state, action)


def draw_compact_card(font: Font | None, rect: Rectangle, card_id: str, selected: bool) -> bool:
    card = CARD_DEFS[card_id]
    if card.is_negative:
        fill = Color(62, 43, 40, 255)
        border = Color(146, 86, 78, 255)
    else:
        fill = Color(29, 33, 40, 255)
        border = Color(95, 99, 107, 220)
    if selected:
        border = Color(201, 165, 88, 255)
    clicked = clickable(rect)
    draw_frame(rect, fill, border)
    draw_text(font, card.title, int(rect.x) + 12, int(rect.y) + 12, 22, RAYWHITE)
    draw_text(font, SUIT_LABELS[card.suit], int(rect.x) + 12, int(rect.y) + 44, 18, LIGHTGRAY)
    draw_text(font, f"点数 {card.points}", int(rect.x) + 12, int(rect.y) + 68, 18, Color(212, 196, 132, 255))
    if card.is_negative:
        draw_text(font, "负面", int(rect.x) + 96, int(rect.y) + 68, 18, Color(210, 126, 110, 255))
    return clicked


def draw_action_modal(font: Font | None, state: GameState, action: ActionPointDef, methods: list[ActionMethodDef]) -> ModalShell:
    rect = centered_rect(720, 430, -24)
    shell = draw_modal_shell(font, action.title, rect, subtitle=action.description, scope=layout().stage)

    if not methods:
        draw_text(font, action.free_text or "立即执行该行动。", int(shell.body.x), int(shell.body.y), 19, Color(208, 208, 208, 255))
        _draw_requirement_sheet(font, Rectangle(shell.body.x, shell.body.y + 42, shell.body.width, 160), state, action, None)
        return shell

    mx = shell.body.x
    my = shell.body.y
    for method in methods:
        pill_rect = Rectangle(mx, my, 160, 34)
        if pill(font, pill_rect, method.title, state.selected_method_id == method.id):
            state.selected_method_id = method.id
        mx += 172

    if state.selected_method_id is None and methods:
        state.selected_method_id = methods[0].id

    method = next(item for item in methods if item.id == state.selected_method_id)
    _draw_method_sheet(font, Rectangle(shell.rect.x + 22, shell.rect.y + 152, shell.rect.width - 44, 210), state, method)
    _draw_requirement_sheet(font, Rectangle(shell.rect.x + 22, shell.rect.y + 334, shell.rect.width - 44, 54), state, action, method)
    return shell


def _draw_requirement_sheet(font: Font | None, rect: Rectangle, state: GameState, action: ActionPointDef, method: ActionMethodDef | None) -> None:
    draw_frame(rect, Color(25, 28, 34, 255), Color(82, 86, 94, 220))
    draw_text(font, "需求", int(rect.x) + 16, int(rect.y) + 8, 20, RAYWHITE)
    x = int(rect.x) + 76
    requirements: list[tuple[str, bool]] = []
    if method is not None:
        card_ok = state.selected_card_id is not None
        requirements.append((_card_requirement_label(state, method), card_ok))
    elif action.special == "mission_smoke":
        requirements.append((_negative_card_requirement_label(state), action_selection_ready(action, state)))
    for cost in action.costs:
        requirements.append((_cost_requirement_label(cost), cost_is_prepared(state, cost)))
    if not requirements:
        requirements.append(("无需投入", True))
    for label, fulfilled in requirements:
        chip = Rectangle(x, rect.y + 4, 176, 26)
        fill = Color(80, 66, 47, 255) if fulfilled else Color(30, 34, 42, 255)
        border = Color(190, 162, 96, 255) if fulfilled else Color(88, 92, 100, 220)
        draw_frame(chip, fill, border)
        _draw_centered_text(font, label, chip, 16, RAYWHITE if fulfilled else Color(196, 196, 196, 255))
        x += 188
    if rect.height >= 56:
        hint = "在下方手牌区或右下角物品区放入所需内容。"
        draw_text(font, hint, int(rect.x) + 16, int(rect.y) + rect.height - 20, 17, LIGHTGRAY)


def _draw_method_sheet(font: Font | None, rect: Rectangle, state: GameState, method: ActionMethodDef) -> None:
    draw_frame(rect, Color(25, 28, 34, 255), Color(82, 86, 94, 220))
    suits = " / ".join(SUIT_LABELS[suit] for suit in method.suits)
    difficulty = effective_difficulty(method, state)
    preview_method = ActionMethodDef(
        id=method.id,
        title=method.title,
        suits=method.suits,
        difficulty=difficulty,
        risk=method.risk,
        success=method.success,
        cost=method.cost,
        fail=method.fail,
        description=method.description,
        conditions=method.conditions,
        bonus=method.bonus,
    )
    draw_text(font, method.title, int(rect.x) + 16, int(rect.y) + 14, 24, RAYWHITE)
    draw_text(font, f"契合: {suits}    难度: {difficulty}    风险: {RISK_LABELS[method.risk]}", int(rect.x) + 16, int(rect.y) + 46, 18, LIGHTGRAY)
    draw_text(font, method.description, int(rect.x) + 16, int(rect.y) + 74, 18, Color(205, 205, 205, 255))
    if state.selected_card_id is None:
        draw_text(font, "未选手牌", int(rect.x) + 16, int(rect.y) + 116, 20, Color(210, 165, 96, 255))
        return
    value = compute_action_value(state.selected_card_id, preview_method)
    draw_text(font, f"你的行动值: {value}", int(rect.x) + 16, int(rect.y) + 110, 22, Color(224, 192, 112, 255))
    selected_card = CARD_DEFS[state.selected_card_id]
    match_text = "契合花色 +1" if selected_card.suit in method.suits else "非契合花色"
    draw_text(font, match_text, int(rect.x) + 220, int(rect.y) + 112, 18, Color(196, 196, 196, 255))
    draw_result_strip(font, Rectangle(rect.x + 16, rect.y + 144, rect.width - 32, 40), RESULT_TABLE[value])
    fail_count = sum(1 for result in RESULT_TABLE[value] if result == ResultType.FAIL)
    cost_count = sum(1 for result in RESULT_TABLE[value] if result == ResultType.COST)
    success_count = 6 - fail_count - cost_count
    draw_text(font, f"失败 {fail_count * 100 // 6}%   代价 {cost_count * 100 // 6}%   成功 {success_count * 100 // 6}%", int(rect.x) + 16, int(rect.y) + 190, 18, LIGHTGRAY)


def draw_result_strip(font: Font | None, rect: Rectangle, result_row: tuple[ResultType, ...]) -> None:
    cell_w = (rect.width - 20) / 6.0
    x = rect.x
    for result in result_row:
        if result == ResultType.FAIL:
            fill = Color(124, 66, 66, 255)
            label = "失"
        elif result == ResultType.COST:
            fill = Color(144, 126, 70, 255)
            label = "代"
        else:
            fill = Color(74, 134, 92, 255)
            label = "成"
        cell = Rectangle(x, rect.y, cell_w - 4, rect.height)
        draw_frame(cell, fill, Color(22, 22, 22, 180))
        _draw_centered_text(font, label, cell, 18, RAYWHITE)
        x += cell_w


def draw_casebook_hint(font: Font | None, state: GameState) -> None:
    if "enable_casebook" not in state.flags:
        return
    hand = layout().hand
    draw_text(font, "记案本已解锁，可保留当前选中手牌过夜。", int(hand.x) + 18, int(hand.y) + 116, 18, Color(194, 164, 104, 255))


def draw_profile_modal(font: Font | None, state: GameState, growth_defs) -> None:
    if not modal_is_open(state, "profile"):
        return
    begin_layer("profile_modal", interactive=True)
    try:
        page = layout()
        rect = Rectangle(page.hud.x + page.hud.width - 470, page.hud.y + page.hud.height + 12, 470, 420)
        shell = draw_modal_shell(font, "个人档案", rect, scope=screen_rect())
        draw_text(font, f"成长点数: {state.growth_points}", int(rect.x) + 20, int(rect.y) + 58, 20, Color(208, 182, 108, 255))
        draw_text(font, f"已解锁: {len(state.unlocked_growths)}", int(rect.x) + 190, int(rect.y) + 58, 20, LIGHTGRAY)
        if shell.close_requested:
            close_modal(state)
            return

        y = int(rect.y) + 102
        draw_text(font, "成长", int(rect.x) + 20, y, 18, Color(202, 180, 124, 255))
        y += 28
        for growth_id in state.pending_growth_choices:
            growth = growth_defs[growth_id]
            locked = state.growth_points <= 0
            button_rect = Rectangle(rect.x + 20, y, 188, 32)
            if locked:
                draw_frame(button_rect, Color(22, 24, 30, 255), Color(70, 72, 78, 180))
                _draw_centered_text(font, growth.title, button_rect, 18, Color(118, 118, 118, 255))
            else:
                if pill(font, button_rect, growth.title, False):
                    from raygame.rules import claim_growth

                    claim_growth(state, growth_id)
                    return
            draw_text(font, growth.description, int(rect.x) + 20, y + 40, 17, LIGHTGRAY)
            y += 82

        if state.unlocked_growths:
            draw_text(font, "已拥有", int(rect.x) + 236, int(rect.y) + 130, 18, Color(202, 180, 124, 255))
            yy = int(rect.y) + 160
            for growth_id in sorted(state.unlocked_growths):
                title = growth_defs[growth_id].title
                draw_text(font, f"· {title}", int(rect.x) + 236, yy, 18, LIGHTGRAY)
                yy += 26
    finally:
        end_layer("profile_modal")


def draw_message_feed(font: Font | None, rect: Rectangle, state: GameState) -> None:
    draw_frame(rect, Color(18, 20, 26, 245))
    draw_text(font, "消息", int(rect.x) + 16, int(rect.y) + 14, 24, RAYWHITE)
    y = int(rect.y) + 50
    if state.last_resolution is not None:
        resolution = state.last_resolution
        draw_text(font, f"{resolution.result.value} | 骰 {resolution.die_roll} | 值 {resolution.value}", int(rect.x) + 16, y, 18, Color(225, 205, 130, 255))
        y += 24
        draw_text(font, resolution.text, int(rect.x) + 16, y, 18, LIGHTGRAY)
        y += 40
    for entry in reversed(state.action_log[-5:]):
        draw_text(font, f"· {entry}", int(rect.x) + 16, y, 18, Color(196, 196, 196, 255))
        y += 26


def _cost_label(cost: ActionCostDef) -> str:
    if cost.label:
        return f"{cost.label} x{cost.amount}"
    if cost.kind == "resource":
        return f"{RESOURCE_LABELS.get(cost.key, cost.key)} x{cost.amount}"
    return f"{cost.key} x{cost.amount}"


def draw_inventory_panel(font: Font | None, rect: Rectangle, state: GameState, action: ActionPointDef | None) -> None:
    draw_frame(rect, Color(16, 18, 24, 255), Color(76, 82, 96, 220))
    draw_text(font, "物品", int(rect.x) + 14, int(rect.y) + 10, 22, RAYWHITE)
    cell_w = (rect.width - 32) * 0.5
    cell_h = 54
    row_gap = 6
    grid_top = 40
    slots = [
        ("money", "金币", getattr(state.resources, "money")),
        ("cigarettes", "烟卷", getattr(state.resources, "cigarettes")),
        ("ledger", "账本", 1 if "ledger" in state.items else 0),
        ("guard_key", "钥匙", 1 if "guard_key" in state.items else 0),
    ]
    for index, (key, label, amount) in enumerate(slots):
        col = index % 2
        row = index // 2
        cell = Rectangle(rect.x + 12 + col * (cell_w + 8), rect.y + grid_top + row * (cell_h + row_gap), cell_w, cell_h)
        cost = _find_slot_cost(action, key)
        selected = cost is not None and cost_is_prepared(state, cost)
        available = amount > 0 or cost is None or cost.kind == "resource"
        disabled = cost is None or not available
        fill = Color(84, 68, 46, 255) if selected else Color(24, 27, 34, 255)
        border = Color(190, 162, 96, 255) if selected else Color(82, 88, 102, 220)
        if disabled:
            fill = Color(20, 22, 28, 255)
            border = Color(60, 64, 74, 180)
        draw_frame(cell, fill, border)
        if not disabled and clickable(cell):
            assert cost is not None
            toggle_prepared_cost(state, action, cost)

        label_color = RAYWHITE if not disabled else Color(110, 110, 110, 255)
        value_color = Color(212, 196, 132, 255) if not disabled else Color(100, 100, 100, 255)

        draw_text(font, label, int(cell.x) + 10, int(cell.y) + 8, 16, label_color)
        draw_text(font, str(amount), int(cell.x) + 10, int(cell.y) + 30, 19, value_color)
        if cost is not None:
            need = f"x{cost.amount}"
            draw_text(font, need, int(cell.x + cell.width - measure_text_ex(font, need, 15, 1.0).x - 10), int(cell.y) + 30, 15, LIGHTGRAY if not disabled else Color(96, 96, 96, 255))


def _find_slot_cost(action: ActionPointDef | None, key: str) -> ActionCostDef | None:
    if action is None:
        return None
    for cost in action.costs:
        if cost.key == key:
            return cost
    return None


def _card_can_be_slotted(action: ActionPointDef | None, card_id: str) -> bool:
    if action is None:
        return True
    if action.methods:
        return True
    if action.special == "mission_smoke":
        return CARD_DEFS[card_id].is_negative
    return False


def _card_requirement_label(state: GameState, method: ActionMethodDef) -> str:
    if state.selected_card_id is None:
        return "1 张手牌"
    card = CARD_DEFS[state.selected_card_id]
    suffix = "契合" if card.suit in method.suits else "非契合"
    return f"已放入 {card.title} ({suffix})"


def _negative_card_requirement_label(state: GameState) -> str:
    if state.selected_card_id is None:
        return "1 张负面牌"
    card = CARD_DEFS[state.selected_card_id]
    return f"已放入 {card.title}" if card.is_negative else f"{card.title} 不是负面牌"


def _cost_requirement_label(cost: ActionCostDef) -> str:
    return _cost_label(cost)


def _draw_centered_text(font: Font | None, text: str, rect: Rectangle, size: int, color: Color) -> None:
    width = measure_text_ex(font, text, float(size), 1.0).x if font is not None else float(measure_text(text, size))
    x = int(rect.x + (rect.width - width) * 0.5)
    y = int(rect.y + (rect.height - size) * 0.5) - 1
    draw_text(font, text, x, y, size, color)
