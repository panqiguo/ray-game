from __future__ import annotations

from pyray import *  # type: ignore

from sincity.model.state import DialogueLine, GameState
from sincity.rendering import draw_text
from sincity.game.flow import dispatch
from sincity.game.commands import ChooseDialogueOption, ContinueDialogue, FinishDialogue

from .dialogue_portraits import portrait_for_speaker
from .ui_core import Z_DIALOGUE_MODAL, begin_layer, clickable, draw_frame, end_layer, layout, mouse_point, scroll_available, text_button, wrap_text_lines_any
from .ui_text import ui_text_size, ui_text_style


def draw_dialogue_overlay(font: Font | None, state: GameState, rng=None) -> None:
    if state.active_dialogue is None:
        return
    begin_layer("dialogue_modal", z=Z_DIALOGUE_MODAL)
    stage = layout().stage
    _draw_dialogue_scrim(stage)
    speaker = _current_speaker(state.active_dialogue.history)
    portrait = portrait_for_speaker(speaker)
    if portrait is not None:
        _draw_portrait(stage, portrait)
    panel = _dialogue_panel_rect(stage, has_portrait=portrait is not None)
    _draw_dialogue_panel(font, state, panel, rng=rng)
    end_layer("dialogue_modal")


def _draw_dialogue_scrim(rect: Rectangle) -> None:
    draw_rectangle_rec(rect, Color(3, 5, 9, 108))
    draw_rectangle_gradient_h(
        int(rect.x),
        int(rect.y),
        int(rect.width),
        int(rect.height),
        Color(3, 5, 9, 186),
        Color(3, 5, 9, 30),
    )


def _dialogue_panel_rect(stage: Rectangle, *, has_portrait: bool) -> Rectangle:
    if stage.width < 980:
        return Rectangle(stage.x + 20, stage.y + 36, stage.width - 40, stage.height - 72)
    width = min(620.0, stage.width * (0.50 if has_portrait else 0.58))
    height = min(520.0, stage.height - 54)
    x = stage.x + stage.width - width - 34
    y = stage.y + max(26.0, (stage.height - height) * 0.5)
    return Rectangle(x, y, width, height)


def _draw_portrait(stage: Rectangle, portrait: Texture2D) -> None:
    if stage.width < 980:
        return
    max_width = stage.width * 0.38
    max_height = stage.height * 0.92
    scale = min(max_width / portrait.width, max_height / portrait.height)
    width = portrait.width * scale
    height = portrait.height * scale
    dest = Rectangle(stage.x + stage.width * 0.09, stage.y + stage.height - height + 16, width, height)
    source = Rectangle(0, 0, float(portrait.width), float(portrait.height))
    draw_texture_pro(portrait, source, dest, Vector2(0, 0), 0.0, Color(255, 255, 255, 235))


def _draw_dialogue_panel(font: Font | None, state: GameState, rect: Rectangle, *, rng=None) -> None:
    assert state.active_dialogue is not None
    draw_frame(rect, Color(13, 16, 22, 236), Color(186, 148, 82, 210))
    title_style = ui_text_style("body_sm", "accent")
    body_style = ui_text_style("body", "default")
    hint_style = ui_text_style("caption", "subtle")
    draw_text(font, state.active_dialogue.title, int(rect.x) + 22, int(rect.y) + 17, title_style.size, title_style.color)
    if text_button(font, Rectangle(rect.x + rect.width - 88, rect.y + 14, 66, 26), "关闭", ui_text_size("body_sm")):
        dispatch(state, FinishDialogue(), rng)
        return
    choices_height = _choices_height(state)
    footer_height = 64 if choices_height == 0 else choices_height + 28
    history_rect = Rectangle(rect.x + 24, rect.y + 52, rect.width - 48, rect.height - footer_height - 68)
    _draw_history(font, state, history_rect, body_style.line_height)
    if state.active_dialogue.history_scroll > 0:
        draw_text(font, "滚轮向下回到最新对白", int(history_rect.x), int(history_rect.y + history_rect.height + 8), hint_style.size, hint_style.color)
    _draw_controls(font, state, rect, footer_height, rng=rng)


def _draw_history(font: Font | None, state: GameState, rect: Rectangle, line_height: int) -> None:
    assert state.active_dialogue is not None
    block_gap = 10
    rendered_lines = _rendered_history(font, state.active_dialogue.history, rect.width)
    max_visible_lines = max(1, int((rect.height + block_gap) // line_height))
    max_scroll = max(0, len(rendered_lines) - max_visible_lines)
    if scroll_available(rect, z=Z_DIALOGUE_MODAL):
        wheel = int(get_mouse_wheel_move())
        if wheel != 0:
            state.active_dialogue.history_scroll = max(0, min(max_scroll, state.active_dialogue.history_scroll - wheel * 3))
    scroll = max(0, min(max_scroll, state.active_dialogue.history_scroll))
    state.active_dialogue.history_scroll = scroll
    start = max(0, len(rendered_lines) - max_visible_lines - scroll)
    visible_lines = rendered_lines[start : start + max_visible_lines]
    y = int(rect.y)
    for text, kind in visible_lines:
        if kind == "spacer":
            y += block_gap
            continue
        style = ui_text_style("body_sm", "accent") if kind == "speaker" else ui_text_style("body", "muted")
        draw_text(font, text, int(rect.x), y, style.size, style.color)
        y += style.line_height


def _rendered_history(font: Font | None, history: list[DialogueLine], width: float) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    previous_speaker = object()
    for block in history:
        if block.speaker and block.speaker != previous_speaker:
            lines.append((block.speaker, "speaker"))
        previous_speaker = block.speaker
        for line in wrap_text_lines_any(font, block.text, width, ui_text_size("body")):
            lines.append((line, "body"))
        lines.append(("", "spacer"))
    if lines and lines[-1][1] == "spacer":
        lines.pop()
    return lines


def _draw_controls(font: Font | None, state: GameState, rect: Rectangle, footer_height: float, *, rng=None) -> None:
    assert state.active_dialogue is not None
    if not state.active_dialogue.choices and not state.active_dialogue.finished and clickable(rect):
        dispatch(state, ContinueDialogue(), rng)
        return
    button_y = rect.y + rect.height - footer_height + 14
    if state.active_dialogue.choices:
        for index, choice in enumerate(state.active_dialogue.choices):
            button = Rectangle(rect.x + 24, button_y, rect.width - 48, 36)
            if text_button(font, button, choice, ui_text_size("body")):
                dispatch(state, ChooseDialogueOption(index), rng)
                return
            button_y += 42
    elif state.active_dialogue.finished:
        if text_button(font, Rectangle(rect.x + rect.width - 120, rect.y + rect.height - 46, 96, 30), "结束", ui_text_size("body")):
            dispatch(state, FinishDialogue(), rng)
            return
    else:
        if text_button(font, Rectangle(rect.x + rect.width - 120, rect.y + rect.height - 46, 96, 30), "继续", ui_text_size("body")):
            dispatch(state, ContinueDialogue(), rng)
            return


def _choices_height(state: GameState) -> float:
    assert state.active_dialogue is not None
    if not state.active_dialogue.choices:
        return 0.0
    return float(len(state.active_dialogue.choices) * 42)


def _current_speaker(history: list[DialogueLine]) -> str:
    return history[-1].speaker if history else ""
