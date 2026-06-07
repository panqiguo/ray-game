from __future__ import annotations

from .defs import ActionHandle, CompiledEncounterProgram, EncounterCompileError, RenderedEncounter, RenderedLocation, StoreFieldSpec

__all__ = [
    "ActionHandle",
    "CompiledEncounterProgram",
    "EncounterCompileError",
    "RenderedEncounter",
    "RenderedLocation",
    "StoreFieldSpec",
    "ENCOUNTERS_BY_ID",
    "MAX_REACT_STEPS",
    "get_encounter",
    "initial_store",
    "evaluate_reaction_die",
    "evaluate_effect_expr",
    "evaluate_cycle_start_effects",
    "evaluate_fail_effects",
    "evaluate_react_rules",
    "evaluate_success_effects",
    "next_react_rule",
    "react_rule_matches",
    "render_encounter",
    "validate_encounter_program",
]


def __getattr__(name: str):
    if name in {"ENCOUNTERS_BY_ID", "get_encounter"}:
        from .registry import ENCOUNTERS_BY_ID, get_encounter

        values = {"ENCOUNTERS_BY_ID": ENCOUNTERS_BY_ID, "get_encounter": get_encounter}
        return values[name]
    if name in {
        "MAX_REACT_STEPS",
        "initial_store",
        "evaluate_reaction_die",
        "evaluate_effect_expr",
        "evaluate_cycle_start_effects",
        "evaluate_fail_effects",
        "evaluate_react_rules",
        "evaluate_success_effects",
        "next_react_rule",
        "react_rule_matches",
        "render_encounter",
        "validate_encounter_program",
    }:
        from .runtime import MAX_REACT_STEPS, evaluate_cycle_start_effects, evaluate_effect_expr, evaluate_fail_effects, evaluate_react_rules, evaluate_reaction_die, evaluate_success_effects, initial_store, next_react_rule, react_rule_matches, render_encounter, validate_encounter_program

        values = {
            "MAX_REACT_STEPS": MAX_REACT_STEPS,
            "evaluate_cycle_start_effects": evaluate_cycle_start_effects,
            "evaluate_effect_expr": evaluate_effect_expr,
            "evaluate_fail_effects": evaluate_fail_effects,
            "evaluate_react_rules": evaluate_react_rules,
            "evaluate_reaction_die": evaluate_reaction_die,
            "evaluate_success_effects": evaluate_success_effects,
            "initial_store": initial_store,
            "next_react_rule": next_react_rule,
            "react_rule_matches": react_rule_matches,
            "render_encounter": render_encounter,
            "validate_encounter_program": validate_encounter_program,
        }
        return values[name]
    raise AttributeError(name)
