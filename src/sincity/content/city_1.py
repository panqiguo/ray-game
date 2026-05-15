from __future__ import annotations

from pathlib import Path

from .runtime import CompiledWorldProgram, compile_world_program


def build_city_1() -> CompiledWorldProgram:
    path = Path(__file__).resolve().parent.parent / "scm" / "city_1.scm"
    return compile_world_program(
        path.read_text(encoding="utf-8"),
        source_path=path,
        initial_health=10,
        initial_stress=5,
        initial_money=20,
        initial_cigarettes=0,
        initial_inventory={
            "clothes": 0,
            "gun": 0,
            "hotel_pass": 0,
            "lockpick": 0,
            "fake_id": 0,
            "passage_ticket": 0,
            "first_aid": 0,
            "food": 0,
            "mysterious_item": 0,
            "wounded_man_lead": 0,
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


SCENARIO = ScenarioProxy(build_city_1())


def replace_city_1(program: CompiledWorldProgram) -> None:
    SCENARIO.set_program(program)


def reload_city_1() -> CompiledWorldProgram:
    program = build_city_1()
    replace_city_1(program)
    return program
