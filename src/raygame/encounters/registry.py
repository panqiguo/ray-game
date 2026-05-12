from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path

from .defs import CompiledEncounterProgram, EncounterCompileError
from .runtime import compile_encounter_program


ENCOUNTER_DIR = Path(__file__).resolve().parent.parent / "scm" / "encounter"


def _load_program(filename: str) -> CompiledEncounterProgram:
    path = ENCOUNTER_DIR / filename
    try:
        return compile_encounter_program(path.read_text(encoding="utf-8"), source_path=path)
    except EncounterCompileError as exc:
        raise EncounterCompileError(f"{filename}: {exc}") from exc


ENCOUNTER_FILES = (
    "教训小混混.scm",
    "潜入别墅.scm",
    "酒吧艳遇.scm",
    "逃离疗养院.scm",
    "望月旅馆搜寻.scm",
)


def load_encounters() -> dict[str, CompiledEncounterProgram]:
    raw = tuple(_load_program(filename) for filename in ENCOUNTER_FILES)
    return {encounter.id: encounter for encounter in raw}


class EncounterRegistryProxy(Mapping[str, CompiledEncounterProgram]):
    def __init__(self, values: dict[str, CompiledEncounterProgram]) -> None:
        self._values = values

    def set_values(self, values: dict[str, CompiledEncounterProgram]) -> None:
        self._values = values

    def snapshot(self) -> dict[str, CompiledEncounterProgram]:
        return dict(self._values)

    def __getitem__(self, key: str) -> CompiledEncounterProgram:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)


ENCOUNTERS_BY_ID = EncounterRegistryProxy(load_encounters())


def replace_encounters(values: dict[str, CompiledEncounterProgram]) -> None:
    ENCOUNTERS_BY_ID.set_values(values)


def reload_encounters() -> dict[str, CompiledEncounterProgram]:
    values = load_encounters()
    replace_encounters(values)
    return values


def get_encounter(encounter_id: str) -> CompiledEncounterProgram:
    return ENCOUNTERS_BY_ID[encounter_id]
