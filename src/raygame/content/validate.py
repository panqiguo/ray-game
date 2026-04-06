from __future__ import annotations

from raygame.content.cards import CARD_DEFS
from raygame.content.city import CITY_ACTIONS, CITY_LOCATIONS
from raygame.content.endings import ENDING_DEFS
from raygame.content.growth import GROWTH_DEFS
from raygame.content.mission_slaughterhouse import MISSION_ACTIONS
from raygame.content.utility_actions import CITY_UTILITY_ACTIONS, MISSION_UTILITY_ACTIONS
from raygame.model.defs import ActionPointDef, Effect

VALID_CONDITIONS = {
    "has_clue",
    "has_item",
    "clock_at_least",
    "flag_set",
    "flag_not_set",
    "action_done",
    "mode_is",
    "day_at_least",
    "day_at_most",
    "if_clue_reduce",
    "resource_at_most",
}
VALID_EFFECTS = {
    "gain_money",
    "spend_money",
    "spend_all_money",
    "add_stress",
    "lose_health",
    "insert_card",
    "remove_negative",
    "remove_negative_family",
    "advance_clock",
    "freeze_clock",
    "set_flag",
    "give_item",
    "gain_cigarettes",
    "fail_run",
    "increase_stress_cap",
    "enable_casebook",
    "enable_old_scars",
    "upgrade_card",
}


def _validate_effect(effect: Effect) -> None:
    assert effect.kind in VALID_EFFECTS, f"Unknown effect kind: {effect.kind}"
    if effect.kind == "insert_card":
        assert isinstance(effect.value, str) and effect.value in CARD_DEFS, effect


def _validate_action(action: ActionPointDef) -> None:
    for condition in action.conditions:
        assert condition.kind in VALID_CONDITIONS, f"Unknown condition: {condition.kind}"
    for cost in action.costs:
        assert cost.kind in {"resource", "item"}, f"Unknown cost kind: {cost.kind}"
    for effect in action.free_effects:
        _validate_effect(effect)
    for method in action.methods:
        for condition in method.conditions:
            assert condition.kind in VALID_CONDITIONS, f"Unknown condition: {condition.kind}"
        for outcome in (method.success, method.cost, method.fail):
            for effect in outcome.effects:
                _validate_effect(effect)


def validate_content() -> None:
    for card_id, card in CARD_DEFS.items():
        assert card_id == card.id
    for location in CITY_LOCATIONS.values():
        for action_id in location.action_ids:
            assert action_id in CITY_ACTIONS, f"Unknown city action {action_id}"
    for action in CITY_ACTIONS.values():
        _validate_action(action)
    for action in MISSION_ACTIONS.values():
        _validate_action(action)
    for action in CITY_UTILITY_ACTIONS.values():
        _validate_action(action)
    for action in MISSION_UTILITY_ACTIONS.values():
        _validate_action(action)
    for ending in ENDING_DEFS.values():
        for condition in ending.conditions:
            assert condition.kind in VALID_CONDITIONS, f"Unknown ending condition: {condition.kind}"
    for growth in GROWTH_DEFS.values():
        for effect in growth.effects:
            _validate_effect(effect)
