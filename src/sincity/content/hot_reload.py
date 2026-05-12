from __future__ import annotations

from pathlib import Path
import traceback

from sincity.content.city_1 import SCENARIO, build_city_1, replace_city_1
from sincity.content.validate import validate_content
from sincity.encounters import get_encounter, initial_store
from sincity.encounters.defs import EncounterCompileError
from sincity.encounters.registry import ENCOUNTERS_BY_ID, load_encounters, replace_encounters
from sincity.encounters.lispy import module_dependency_paths
from sincity.model.state import GameState, ProgressClockState


def _is_real_scm_file(path: Path) -> bool:
    name = path.name
    if not name.endswith(".scm"):
        return False
    if name.startswith("."):
        return False
    if name.startswith("#") or name.startswith(".#"):
        return False
    if name.endswith("~") or name.endswith(".swp") or name.endswith(".swo"):
        return False
    return path.is_file()


def _registered_source_paths() -> tuple[Path, ...]:
    sources: list[Path] = []
    world = SCENARIO.get_program()
    if world.source_path is not None:
        sources.append(world.source_path.resolve())
    for encounter in ENCOUNTERS_BY_ID.snapshot().values():
        if encounter.source_path is not None:
            sources.append(encounter.source_path.resolve())
    return tuple(dict.fromkeys(sources))


def _scm_signature() -> tuple[tuple[str, int], ...]:
    files: list[Path] = []
    for source_path in _registered_source_paths():
        if not _is_real_scm_file(source_path):
            continue
        try:
            files.extend(module_dependency_paths(source_path))
        except FileNotFoundError:
            continue
    files = list(dict.fromkeys(path for path in files if _is_real_scm_file(path)))
    signature: list[tuple[str, int]] = []
    for path in files:
        try:
            signature.append((str(path), path.stat().st_mtime_ns))
        except FileNotFoundError:
            continue
    return tuple(signature)


class ScmHotReloader:
    def __init__(self) -> None:
        self._last_signature = _scm_signature()
        self._last_scan_error = ""

    def reload_if_changed(self, state: GameState | None = None) -> bool:
        try:
            signature = _scm_signature()
        except EncounterCompileError as exc:
            message = str(exc)
            if message != self._last_scan_error:
                self._last_scan_error = message
                print("[SCM hot reload] dependency scan failed, keeping previous content")
                traceback.print_exc()
            return False
        self._last_scan_error = ""
        if signature == self._last_signature:
            return False
        self._last_signature = signature
        return self.reload_now(state)

    def reload_now(self, state: GameState | None = None) -> bool:
        old_world = SCENARIO.get_program()
        old_encounters = ENCOUNTERS_BY_ID.snapshot()
        try:
            new_world = build_city_1()
            new_encounters = load_encounters()
            if state is not None and state.active_encounter is not None:
                assert state.active_encounter.encounter_id in new_encounters, (
                    f"Active encounter removed during hot reload: {state.active_encounter.encounter_id}"
                )
            replace_city_1(new_world)
            replace_encounters(new_encounters)
            validate_content()
        except Exception:
            replace_city_1(old_world)
            replace_encounters(old_encounters)
            print("[SCM hot reload] failed, keeping previous content")
            traceback.print_exc()
            return False
        if state is not None:
            _sync_state_to_content(state)
            state.render_cache.revision += 1
            state.action_log.append("内容已热重载。")
            del state.action_log[:-12]
        print("[SCM hot reload] reloaded content")
        return True


def _sync_state_to_content(state: GameState) -> None:
    scenario = SCENARIO.get_program()
    for clock_id in scenario.clocks_by_id:
        state.world.progress_clocks.setdefault(clock_id, ProgressClockState(value=0, visible=True))
    for key, value in scenario.initial_values.items():
        state.world.values.setdefault(key, value)
    for key, value in scenario.initial_inventory.items():
        state.world.inventory.setdefault(key, value)
    if state.active_encounter is None:
        return
    encounter = get_encounter(state.active_encounter.encounter_id)
    for key, value in initial_store(encounter).items():
        state.active_encounter.store.setdefault(key, value)


HOT_RELOADER = ScmHotReloader()
