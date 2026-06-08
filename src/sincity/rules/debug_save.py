from __future__ import annotations

import dataclasses
import os
import pickle

from sincity.model.state import GameState, RenderCacheState
from sincity.game.fields import _mark_content_dirty
from sincity.game.queries import sync_world_progress_clocks
from sincity.rules.rng import RandomSource

SLOT_NAMES: dict[int, str] = {
    1: "quick_save.pkl",
    2: "save_01.pkl",
    3: "save_02.pkl",
    4: "save_03.pkl",
}


def slot_path(slot: int) -> str:
    return os.path.join("debug", SLOT_NAMES[slot])


def _ensure_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _upgrade_dataclass(obj: object, _visited: set[int] | None = None) -> None:
    if _visited is None:
        _visited = set()
    if id(obj) in _visited:
        return
    _visited.add(id(obj))

    for f in dataclasses.fields(obj):
        if f.name not in obj.__dict__:
            if f.default_factory is not dataclasses.MISSING:
                obj.__dict__[f.name] = f.default_factory()
            else:
                obj.__dict__[f.name] = f.default

    for f in dataclasses.fields(obj):
        val = obj.__dict__.get(f.name)
        if dataclasses.is_dataclass(val):
            _upgrade_dataclass(val, _visited)
        elif isinstance(val, (list, tuple, set)):
            for item in val:
                if dataclasses.is_dataclass(item):
                    _upgrade_dataclass(item, _visited)
        elif isinstance(val, dict):
            for v in val.values():
                if dataclasses.is_dataclass(v):
                    _upgrade_dataclass(v, _visited)


def debug_save(state: GameState, rng: RandomSource, slot: int = 1) -> None:
    assert state.active_dialogue is None, "不能对话中存档"
    assert not state.dialogue_queue, "不能在对话队列未清空时存档"
    path = slot_path(slot)
    saved_revision = state.render_cache.revision
    state.render_cache = RenderCacheState()

    try:
        rng_state = rng._random.getstate()
        _ensure_dir(path)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "state": state,
                    "rng_state": rng_state,
                },
                f,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
    finally:
        state.render_cache.revision = saved_revision


def debug_load(state: GameState, rng: RandomSource, slot: int = 1) -> None:
    path = slot_path(slot)
    with open(path, "rb") as f:
        data = pickle.load(f)

    loaded_state: GameState = data["state"]
    rng_state = data["rng_state"]

    _upgrade_dataclass(loaded_state)
    loaded_state.render_cache = RenderCacheState()
    loaded_state.world.seen_items.update(
        k for k, v in loaded_state.world.inventory.items() if v > 0
    )

    for f in dataclasses.fields(type(state)):
        setattr(state, f.name, getattr(loaded_state, f.name))

    sync_world_progress_clocks(state)
    rng._random.setstate(rng_state)
    _mark_content_dirty(state)
