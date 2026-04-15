from __future__ import annotations

from pathlib import Path

from .defs import CompiledEncounterProgram, EncounterCompileError
from .runtime import compile_encounter_program


def _load_program(filename: str) -> CompiledEncounterProgram:
    path = Path(__file__).with_name(filename)
    try:
        return compile_encounter_program(path.read_text(encoding="utf-8"), source_path=path)
    except EncounterCompileError as exc:
        raise EncounterCompileError(f"{filename}: {exc}") from exc


RAW_ENCOUNTERS = (
    _load_program("teach_thug.scm"),
    _load_program("black_night.scm"),
    _load_program("酒吧艳遇.scm"),
    _load_program("first_scene.scm"),
)
ENCOUNTERS_BY_ID = {encounter.id: encounter for encounter in RAW_ENCOUNTERS}


def get_encounter(encounter_id: str) -> CompiledEncounterProgram:
    return ENCOUNTERS_BY_ID[encounter_id]
