from __future__ import annotations

from pathlib import Path

from .runtime import CompiledWorldProgram, compile_world_program


def build_escape_scenario() -> CompiledWorldProgram:
    path = Path(__file__).with_name("scenario_escape.scm")
    return compile_world_program(
        path.read_text(encoding="utf-8"),
        source_path=path,
        initial_health=5,
        initial_stress=2,
        initial_money=0,
        initial_cigarettes=0,
        initial_inventory={
            "clothes": 0,
            "gun": 0,
            "hotel_pass": 0,
            "lockpick": 0,
        },
    )


class ScenarioProxy:
    def __init__(self, program: CompiledWorldProgram) -> None:
        self._program = program

    def get_program(self) -> CompiledWorldProgram:
        return self._program

    def set_program(self, program: CompiledWorldProgram) -> None:
        self._program = program

    def __getattr__(self, name: str):
        return getattr(self._program, name)


SCENARIO = ScenarioProxy(build_escape_scenario())


def replace_escape_scenario(program: CompiledWorldProgram) -> None:
    SCENARIO.set_program(program)


def reload_escape_scenario() -> CompiledWorldProgram:
    program = build_escape_scenario()
    replace_escape_scenario(program)
    return program
