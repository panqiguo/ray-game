from __future__ import annotations

from sincity.dialogues import (
    choose_dialogue_option as choose_runtime_dialogue_option,
    continue_dialogue_session,
    create_dialogue_session,
    create_quick_dialogue_session,
    get_dialogue,
)
from sincity.model.enums import ScreenName
from sincity.model.state import GameState, ModalState

from sincity.game.actions import clear_assembly, clear_selected_input
from sincity.game.fields import _mark_content_dirty


def _push_log(state: GameState, text: str) -> None:
    from sincity.constants import MAX_LOG_LINES
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


def _apply_game_over(state: GameState, *, title: str, body: str) -> None:
    state.pending_game_over = False
    state.pending_game_over_title = ""
    state.pending_game_over_body = ""
    state.ending_id = "game_over"
    state.ending_title = title
    state.ending_body = body
    state.screen = ScreenName.ENDING
    state.active_encounter = None
    state.active_dialogue = None
    state.dialogue_queue.clear()
    state.pending_resolution = None
    state.modal = ModalState()
    clear_assembly(state)
    clear_selected_input(state)
    _mark_content_dirty(state)


# ── Dialogue lifecycle ─────────────────────────────────────────────

def start_dialogue(state: GameState, dialogue_id: str) -> None:
    asset = get_dialogue(dialogue_id)
    _open_dialogue_session(state, create_dialogue_session(asset, state), primary_id=dialogue_id)
    _push_log(state, f"进入对话：{asset.title}")


def start_quick_dialogue(state: GameState, raw_text: str) -> None:
    session = create_quick_dialogue_session(raw_text)
    _open_dialogue_session(state, session, primary_id="__quick__")
    _push_log(state, f"进入对话：{session.title}")


def _open_dialogue_session(state: GameState, session, *, primary_id: str) -> None:
    del primary_id
    if state.active_dialogue is not None:
        state.dialogue_queue.append(session)
        return
    state.active_dialogue = session
    clear_assembly(state)
    clear_selected_input(state)


def continue_dialogue(state: GameState) -> None:
    if state.active_dialogue is None:
        return
    keep_pinned = state.active_dialogue.history_scroll == 0
    continue_dialogue_session(state.active_dialogue)
    if keep_pinned and state.active_dialogue is not None:
        state.active_dialogue.history_scroll = 0
    if state.active_dialogue.finished and state.active_dialogue.auto_close_on_finish:
        finish_dialogue(state)


def fast_forward_dialogue(state: GameState) -> bool:
    if state.active_dialogue is None:
        return False
    initial_dialogue = state.active_dialogue
    while state.active_dialogue is initial_dialogue and state.active_dialogue.can_continue and not state.active_dialogue.choices:
        continue_dialogue(state)
    if state.active_dialogue is None:
        return True
    if state.active_dialogue is not initial_dialogue:
        return True
    if state.active_dialogue.choices:
        return True
    if state.active_dialogue.finished:
        finish_dialogue(state)
        return True
    raise AssertionError(f"Dialogue cannot be advanced or finished: {state.active_dialogue.dialogue_id}")


def choose_dialogue_option(state: GameState, index: int) -> None:
    if state.active_dialogue is None:
        return
    keep_pinned = state.active_dialogue.history_scroll == 0
    choose_runtime_dialogue_option(state.active_dialogue, index)
    if state.active_dialogue is None:
        return
    if keep_pinned and state.active_dialogue is not None:
        state.active_dialogue.history_scroll = 0
    if state.active_dialogue.finished and state.active_dialogue.auto_close_on_finish:
        finish_dialogue(state)


def finish_dialogue(state: GameState) -> None:
    if state.active_dialogue is None:
        return
    _clear_dialogue_modal(state)
    if state.pending_game_over:
        _apply_game_over(
            state,
            title=state.pending_game_over_title,
            body=state.pending_game_over_body,
        )


def _clear_dialogue_modal(state: GameState) -> None:
    state.active_dialogue = None
    if state.dialogue_queue:
        state.active_dialogue = state.dialogue_queue.pop(0)
        clear_assembly(state)
        clear_selected_input(state)
        return
    clear_assembly(state)
    clear_selected_input(state)


def end_game(state: GameState, *, title: str = "游戏结束", body: str = "") -> None:
    if state.active_dialogue is not None:
        state.pending_game_over = True
        state.pending_game_over_title = title
        state.pending_game_over_body = body
        return
    _apply_game_over(state, title=title, body=body)
