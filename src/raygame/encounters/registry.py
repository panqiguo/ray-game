from __future__ import annotations

from pathlib import Path

from .defs import CompiledEncounterProgram
from .runtime import compile_encounter_program


def _load_program(filename: str) -> CompiledEncounterProgram:
    path = Path(__file__).with_name(filename)
    return compile_encounter_program(path.read_text(encoding="utf-8"))


RAW_ENCOUNTERS = (_load_program("teach_thug.enc"),)
ENCOUNTERS_BY_ID = {encounter.id: encounter for encounter in RAW_ENCOUNTERS}


def get_encounter(encounter_id: str) -> CompiledEncounterProgram:
    return ENCOUNTERS_BY_ID[encounter_id]
