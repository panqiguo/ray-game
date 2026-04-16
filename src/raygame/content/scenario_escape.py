from __future__ import annotations

from pathlib import Path

from .runtime import CompiledWorldProgram, compile_world_program


def build_escape_scenario() -> CompiledWorldProgram:
    path = Path(__file__).with_name("scenario_escape.scm")
    return compile_world_program(
        path.read_text(encoding="utf-8"),
        source_path=path,
        initial_health=6,
        initial_stress=4,
        initial_money=0,
        initial_cigarettes=0,
        initial_inventory={
            "clothes": 0,
            "gun": 0,
            "hotel_pass": 0,
            "lockpick": 0,
        },
    )


SCENARIO = build_escape_scenario()
