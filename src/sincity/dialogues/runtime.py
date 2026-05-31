from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sincity.model.state import ActiveDialogueState, DialogueLine, GameState

from .defs import DialogueAsset


@dataclass
class QuickDialogueRuntime:
    blocks: tuple[DialogueLine, ...]
    index: int = 0


def create_dialogue_session(asset: DialogueAsset, state: GameState) -> ActiveDialogueState:
    if not asset.compiled_path.exists():
        error = f"对话资源缺失：{asset.compiled_path.name}"
        return ActiveDialogueState(
            dialogue_id=asset.id,
            title=asset.title,
            history=[DialogueLine(error)],
            finished=True,
            error=error,
        )
    from inkpython import Story

    story = Story(asset.compiled_path.read_text(encoding="utf-8"))
    _bind_story(story, state)
    session = ActiveDialogueState(
        dialogue_id=asset.id,
        title=asset.title,
        runtime=story,
    )
    continue_dialogue_session(session)
    return session


def create_quick_dialogue_session(raw_text: str) -> ActiveDialogueState:
    title, blocks = _parse_quick_dialogue(raw_text)
    session = ActiveDialogueState(
        dialogue_id="__quick__",
        title=title,
        runtime=QuickDialogueRuntime(blocks=blocks),
        auto_close_on_finish=False,
    )
    continue_dialogue_session(session)
    return session


def continue_dialogue_session(session: ActiveDialogueState) -> None:
    if session.runtime is None or session.finished or session.choices:
        return
    if isinstance(session.runtime, QuickDialogueRuntime):
        _continue_quick_dialogue(session.runtime, session)
        return
    story = _story(session)
    while story.canContinue:
        text = story.Continue().strip()
        if text:
            session.history.append(DialogueLine(text=text, speaker=_speaker_from_tags(story.currentTags)))
            break
        if story.currentChoices:
            break
    _refresh_state(session)


def choose_dialogue_option(session: ActiveDialogueState, index: int) -> None:
    assert 0 <= index < len(session.choices), f"Choice index out of range: {index}"
    story = _story(session)
    story.ChooseChoiceIndex(index)
    session.choices = []
    continue_dialogue_session(session)


def _refresh_state(session: ActiveDialogueState) -> None:
    if session.runtime is None:
        session.can_continue = False
        session.choices = []
        session.finished = True
        return
    if isinstance(session.runtime, QuickDialogueRuntime):
        session.choices = []
        session.can_continue = session.runtime.index < len(session.runtime.blocks)
        session.finished = not session.can_continue
        return
    story = _story(session)
    session.choices = [choice.text for choice in story.currentChoices]
    session.can_continue = bool(story.canContinue)
    session.finished = not session.can_continue and not session.choices


def _parse_quick_dialogue(raw_text: str) -> tuple[str, tuple[DialogueLine, ...]]:
    lines = [line.rstrip() for line in raw_text.strip().splitlines()]
    assert lines, "Quick dialogue cannot be empty."
    title = ""
    if lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current.clear()
            continue
        current.append(line.strip())
    if current:
        blocks.append("\n".join(current).strip())
    assert blocks, "Quick dialogue must contain at least one text block."
    return title, tuple(_parse_quick_block(block) for block in blocks)


def _parse_quick_block(block: str) -> DialogueLine:
    lines = block.splitlines()
    speaker = ""
    if lines and lines[0].startswith("# speaker:"):
        speaker = lines[0].partition(":")[2].strip()
        assert speaker, "Quick dialogue speaker tag cannot be empty."
        lines = lines[1:]
    text = "\n".join(line.strip() for line in lines).strip()
    assert text, "Quick dialogue block cannot be empty."
    return DialogueLine(text=text, speaker=speaker)


def _continue_quick_dialogue(runtime: QuickDialogueRuntime, session: ActiveDialogueState) -> None:
    if runtime.index < len(runtime.blocks):
        session.history.append(runtime.blocks[runtime.index])
        runtime.index += 1
    _refresh_state(session)


def _speaker_from_tags(tags: list[str]) -> str:
    for tag in tags:
        key, sep, value = tag.partition(":")
        if sep and key.strip() == "speaker":
            speaker = value.strip()
            assert speaker, "Ink speaker tag cannot be empty."
            return speaker
    return ""


def _bind_story(story: Any, state: GameState) -> None:
    story.BindExternalFunction("give_item", lambda item_id, amount=1: _give_item(state, str(item_id), int(amount)))
    story.BindExternalFunction("remove_item", lambda item_id, amount=1: _remove_item(state, str(item_id), int(amount)))
    story.BindExternalFunction("change_money", lambda amount: _change_money(state, int(amount)))
    story.BindExternalFunction("change_health", lambda amount: _change_health(state, int(amount)))
    story.BindExternalFunction("change_energy", lambda amount: _change_energy(state, int(amount)))
    story.BindExternalFunction("set_value", lambda key, value: _set_value(state, str(key), value))
    story.BindExternalFunction("add_value", lambda key, amount: _add_value(state, str(key), int(amount)))
    story.BindExternalFunction("start_encounter", lambda encounter_id: _start_encounter(state, str(encounter_id)))
    story.BindExternalFunction("finish_encounter", lambda outcome="abort": _finish_encounter(state, str(outcome)))
    story.BindExternalFunction("log", lambda text: state.action_log.append(str(text)))


def _story(session: ActiveDialogueState) -> Any:
    from inkpython import Story

    assert isinstance(session.runtime, Story), "Dialogue runtime is unavailable"
    return session.runtime


def _give_item(state: GameState, item_id: str, amount: int) -> None:
    state.world.inventory[item_id] = state.world.inventory.get(item_id, 0) + amount


def _remove_item(state: GameState, item_id: str, amount: int) -> None:
    current = state.world.inventory.get(item_id, 0)
    next_value = max(0, current - amount)
    if next_value == 0:
        state.world.inventory.pop(item_id, None)
    else:
        state.world.inventory[item_id] = next_value


def _change_money(state: GameState, amount: int) -> None:
    state.world.inventory["money"] = max(0, state.world.inventory.get("money", 0) + amount)
    if state.world.inventory["money"] == 0:
        state.world.inventory.pop("money", None)


def _change_health(state: GameState, amount: int) -> None:
    from sincity.rules.progression import change_health

    change_health(state, amount, [])


def _change_energy(state: GameState, amount: int) -> None:
    from sincity.rules.progression import change_energy

    change_energy(state, amount, [])


def _set_value(state: GameState, key: str, value: Any) -> None:
    from sincity.rules.progression import _set_field

    if isinstance(value, str):
        raw = value.strip()
        if raw == "true":
            parsed: int | bool | str = True
        elif raw == "false":
            parsed = False
        else:
            try:
                parsed = int(raw)
            except ValueError:
                parsed = raw
    elif isinstance(value, bool):
        parsed = value
    else:
        parsed = int(value)
    _set_field(state, key, parsed, [])


def _add_value(state: GameState, key: str, amount: int) -> None:
    from sincity.rules.progression import _add_field

    _add_field(state, key, amount, [])


def _start_encounter(state: GameState, encounter_id: str) -> None:
    from sincity.rules.progression import start_encounter_from_dialogue

    start_encounter_from_dialogue(state, encounter_id)


def _finish_encounter(state: GameState, outcome: str) -> None:
    from sincity.rules.progression import finish_encounter_from_dialogue

    finish_encounter_from_dialogue(state, outcome)
