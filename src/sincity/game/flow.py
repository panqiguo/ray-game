from __future__ import annotations

from sincity.model.enums import ScreenName
from sincity.model.state import GameState
from sincity.rules.rng import RandomSource

from sincity.game.commands import (
    AdvanceCycle,
    ChooseDialogueOption,
    CloseModal,
    ContinueDialogue,
    DismissPendingResolution,
    EndurePressure,
    ExecuteAction,
    FastForwardDialogue,
    FinishDialogue,
    GameCommand,
    OpenAction,
    OpenLocation,
    SelectCardInput,
    StartDialogue,
    StartQuickDialogue,
    ToggleEnergySlot,
    ToggleRequirementSlot,
)
from sincity.game.events import (
    ActionStarted,
    DialogueFastForwarded,
    DialogueStarted,
    EncounterStarted,
    GameEnded,
    GameEvent,
)
from sincity.game.actions import open_action, select_card_input, close_modal
from sincity.game.dialogues import (
    continue_dialogue,
    choose_dialogue_option,
    start_dialogue,
    start_quick_dialogue,
    finish_dialogue,
    fast_forward_dialogue,
)
from sincity.game.resolution import perform_current_action, dismiss_pending_resolution
from sincity.game.clocks import advance_cycle
from sincity.game.encounters import endure_pressure_during_encounter


def dispatch(state: GameState, command: GameCommand, rng: RandomSource | None = None) -> tuple[GameEvent, ...]:
    if rng is None:
        rng = RandomSource(state.seed)

    events: list[GameEvent] = []

    screen_before = state.screen
    encounter_before = state.active_encounter

    match command:
        case OpenLocation(location_id):
            from sincity.game.actions import open_modal
            open_modal(state, "location", location_id)

        case OpenAction(action_id):
            open_action(state, action_id)

        case ExecuteAction():
            perform_current_action(state, rng)
            pending = state.pending_resolution
            if pending is not None:
                events.append(ActionStarted(
                    action_id=pending.resolution.action_id,
                    result=pending.resolution.result,
                ))

        case ContinueDialogue():
            continue_dialogue(state)

        case ChooseDialogueOption(index):
            choose_dialogue_option(state, index)

        case CloseModal():
            close_modal(state)

        case StartDialogue(dialogue_id):
            start_dialogue(state, dialogue_id)
            events.append(DialogueStarted(dialogue_id))

        case StartQuickDialogue(dialogue_id):
            start_quick_dialogue(state, dialogue_id)
            events.append(DialogueStarted(dialogue_id))

        case SelectCardInput(slot_id, slot_index):
            select_card_input(state, slot_id, slot_index)

        case ToggleEnergySlot(action_id):
            from sincity.game.actions import toggle_action_energy_slot
            from sincity.game.queries import get_action_for_state
            action = get_action_for_state(state, action_id)
            if action is not None:
                toggle_action_energy_slot(state, action)

        case ToggleRequirementSlot(action_id, requirement_key):
            from sincity.game.actions import toggle_action_requirement_slot, current_action
            action = current_action(state)
            if action is not None and action.id == action_id:
                for req in action.inputs:
                    if req.key == requirement_key:
                        toggle_action_requirement_slot(state, action, req)
                        break

        case FinishDialogue():
            finish_dialogue(state)

        case DismissPendingResolution():
            dismiss_pending_resolution(state)

        case FastForwardDialogue():
            if fast_forward_dialogue(state):
                events.append(DialogueFastForwarded())

        case AdvanceCycle():
            advance_cycle(state, rng)

        case EndurePressure():
            endure_pressure_during_encounter(state, rng)

    # 检测状态转换以构造事件
    if state.active_encounter is not None and encounter_before is None:
        events.append(EncounterStarted(state.active_encounter.encounter_id))
    if state.screen == ScreenName.ENDING and screen_before != ScreenName.ENDING:
        events.append(GameEnded(state.ending_id))

    return tuple(events)
