from __future__ import annotations

import dataclasses
import os
import pickle

from sincity.model.state import GameState, RenderCacheState
from sincity.rules.progression import _mark_content_dirty
from sincity.rules.rng import RandomSource

SAVE_PATH = "debug/debug_save.pkl"


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


def debug_save(state: GameState, rng: RandomSource, path: str = SAVE_PATH) -> None:
    assert state.active_dialogue is None, "不能对话中存档"

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


def debug_load(state: GameState, rng: RandomSource, path: str = SAVE_PATH) -> None:
    with open(path, "rb") as f:
        data = pickle.load(f)

    loaded_state: GameState = data["state"]
    rng_state = data["rng_state"]

    _upgrade_dataclass(loaded_state)
    loaded_state.render_cache = RenderCacheState()

    for f in dataclasses.fields(type(state)):
        setattr(state, f.name, getattr(loaded_state, f.name))

    rng._random.setstate(rng_state)
    _mark_content_dirty(state)
