from __future__ import annotations

from sincity.constants import MAX_LOG_LINES
from sincity.content import ACTOR_STATUS_DEFS, PARTY_ACTOR_DEFS
from sincity.encounters import get_encounter
from sincity.model.enums import ScreenName
from sincity.model.state import (
    ActorStatusState,
    GameState,
    PartyActorState,
)
from sincity.game.notifications import push_notification


def _mark_content_dirty(state: GameState) -> None:
    state.render_cache.revision += 1


# ── Log ────────────────────────────────────────────────────────────────

def _push_log(state: GameState, text: str) -> None:
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


# ── Actor queries ──────────────────────────────────────────────────

def player_actor(state: GameState):
    actor = state.party.get(state.player_actor_id)
    assert actor is not None, f"Missing player actor: {state.player_actor_id}"
    return actor


def party_actor(state: GameState, actor_id: str):
    actor = state.party.get(actor_id)
    assert actor is not None, f"Unknown party actor: {actor_id}"
    return actor


def actor_name(state: GameState, actor_id: str) -> str:
    return party_actor(state, actor_id).name


def world_attr_value(state: GameState, key: str) -> int:
    actor = player_actor(state)
    if key == "energy":
        return actor.energy
    if key == "health":
        return actor.health
    if key == "pressure":
        return actor.pressure
    if key == "force":
        return actor.force
    if key == "charm":
        return actor.charm
    if key == "knowledge":
        return actor.knowledge
    if key == "sense":
        return actor.sense
    raise AssertionError(f"Unknown world attr: {key}")


# ── Field reads ───────────────────────────────────────────────────

def field_value(state: GameState, key: str) -> int | bool | str:
    if key == "day":
        return state.day
    if state.active_encounter is not None and key in state.active_encounter.store:
        encounter = get_encounter(state.active_encounter.encounter_id)
        spec = encounter.store_specs[key]
        if spec.persist == "encounter":
            return state.active_encounter.store[key]
        if spec.persist == "world_attr":
            return world_attr_value(state, key)
        if spec.persist == "world_value":
            return state.world.values.get(key, spec.initial)
        if spec.persist == "world_inventory":
            return state.world.inventory.get(key, int(spec.initial))
    if key in {"energy", "health", "force", "charm", "knowledge", "sense", "pressure"}:
        return world_attr_value(state, key)
    if key in state.world.values:
        return state.world.values[key]
    return state.world.inventory.get(key, 0)


# ── Health / trauma helpers ────────────────────────────────────────────

def sync_trauma_cards_with_health(state: GameState) -> None:
    state.deck.trauma_by_slot.clear()


def change_health(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    actor = player_actor(state)
    actor.health = max(0, min(actor.max_health, actor.health + amount))
    state.attributes.health = actor.health
    sync_trauma_cards_with_health(state)
    _mark_content_dirty(state)
    if actor.health <= 0:
        state.ending_id = "collapse"
        state.ending_title = "倒下了"
        state.ending_body = "你最终还是没能撑住。"
        state.screen = ScreenName.ENDING


# ── Pressure helpers ───────────────────────────────────────────────────

def pressure_recovery_threshold(actor: PartyActorState) -> int:
    return max(0, actor.max_pressure - 3)


def add_actor_status(actor: PartyActorState, status_id: str) -> None:
    status_def = ACTOR_STATUS_DEFS.get(status_id)
    assert status_def is not None, f"Unknown actor status: {status_id}"
    for status in actor.statuses:
        if status.id == status_id:
            status.cycles = max(status.cycles, status_def.cycles)
            return
    actor.statuses.append(ActorStatusState(id=status_id, cycles=status_def.cycles))


def change_actor_pressure(state: GameState, amount: int, actor_id: str, extra_lines: list[str] | None = None) -> None:
    actor = party_actor(state, actor_id)
    old = actor.pressure
    was_locked = actor.pressure_locked
    actor.pressure = max(0, min(actor.max_pressure, actor.pressure + amount))
    delta = actor.pressure - old
    overflow = (old + amount) - actor.max_pressure
    if overflow > 0 and actor.is_player:
        change_health(state, -overflow, extra_lines)
        if extra_lines is not None:
            extra_lines.append(f"压力爆表，生命 -{overflow}")
    if delta > 0 and actor.pressure >= actor.max_pressure and not actor.is_player:
        actor.pressure_locked = True
        if not was_locked:
            actor_def = PARTY_ACTOR_DEFS.get(actor.id)
            actor.stress_location = actor_def.stress_location if actor_def is not None else ""
            location_text = actor.stress_location or "别处"
            _push_log(state, f"{actor.name} 压力太大，去了{location_text}。")
            push_notification(state, "warning", "同伴离开行动", f"{actor.name} 在{location_text}释放压力。")
    if delta < 0 and actor.pressure <= pressure_recovery_threshold(actor):
        actor.pressure_locked = False
        if was_locked:
            actor.stress_location = ""
            actor_def = PARTY_ACTOR_DEFS.get(actor.id)
            if actor_def is not None and actor_def.stress_return_status:
                add_actor_status(actor, actor_def.stress_return_status)
            _push_log(state, f"{actor.name} 压力降到安全线以下，回到了行动中。")
            push_notification(state, "success", "同伴回归", f"{actor.name} 可以再次行动。")
    _mark_content_dirty(state)
    if extra_lines is not None and delta != 0 and overflow <= 0:
        label = "压力" if delta > 0 else "压力恢复"
        extra_lines.append(f"{actor.name} {label} {abs(delta)}")


# ── Energy helper ──────────────────────────────────────────────────────

def change_energy(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    actor = player_actor(state)
    if amount >= 0:
        actor.energy = min(actor.max_energy, actor.energy + amount)
        state.attributes.energy = actor.energy
        _mark_content_dirty(state)
        return
    loss = -amount
    absorbed = min(actor.energy, loss)
    actor.energy -= absorbed
    state.attributes.energy = actor.energy
    overflow = loss - absorbed
    _mark_content_dirty(state)
    if overflow > 0:
        change_actor_pressure(state, overflow, state.player_actor_id, extra_lines)


# ── Field writes ───────────────────────────────────────────────────

def _coerce_like(current: int | bool | str, value: int | bool | str) -> int | bool | str:
    if isinstance(current, bool):
        return bool(value)
    if isinstance(current, int):
        return int(value)
    return str(value)


def set_world_attr(state: GameState, key: str, value: int) -> None:
    actor = player_actor(state)
    if key == "energy":
        actor.energy = max(0, min(actor.max_energy, value))
        state.attributes.energy = actor.energy
        return
    if key == "pressure":
        delta = value - actor.pressure
        change_actor_pressure(state, delta, state.player_actor_id)
        return
    if key == "health":
        actor.health = max(0, min(actor.max_health, value))
        state.attributes.health = actor.health
        sync_trauma_cards_with_health(state)
        _mark_content_dirty(state)
        return
    assert key in {"force", "charm", "knowledge", "sense"}, f"Unknown world attr: {key}"
    setattr(actor, key, value)


def set_field(state: GameState, key: str, value: int | bool | str, extra_lines: list[str] | None = None) -> None:
    if state.active_encounter is not None and key in state.active_encounter.store:
        encounter = get_encounter(state.active_encounter.encounter_id)
        spec = encounter.store_specs[key]
        if spec.persist == "encounter":
            current = state.active_encounter.store[key]
            state.active_encounter.store[key] = _coerce_like(current, value)
            _mark_content_dirty(state)
            return
        if spec.persist == "world_attr":
            set_world_attr(state, key, int(value))
            state.active_encounter.store[key] = field_value(state, key)
            _mark_content_dirty(state)
            return
        if spec.persist == "world_value":
            current = state.world.values.get(key, spec.initial)
            parsed = _coerce_like(current, value)
            state.world.values[key] = parsed
            state.active_encounter.store[key] = parsed
            _mark_content_dirty(state)
            return
        if spec.persist == "world_inventory":
            count = max(0, int(value))
            if count > 0:
                state.world.seen_items.add(key)
            state.world.inventory[key] = count
            state.active_encounter.store[key] = count
            _mark_content_dirty(state)
            return
    if key == "energy":
        set_world_attr(state, key, int(value))
        _mark_content_dirty(state)
        return
    if key == "pressure":
        set_world_attr(state, key, int(value))
        _mark_content_dirty(state)
        return
    if hasattr(state.attributes, key):
        if key == "health":
            set_world_attr(state, key, int(value))
        else:
            setattr(state.attributes, key, int(value))
        _mark_content_dirty(state)
        return
    if key in {"gang_relation", "finance_relation", "police_relation"}:
        state.world.values[key] = max(-3, min(3, int(value)))
        _mark_content_dirty(state)
        return
    if isinstance(value, bool) or key in state.world.values:
        state.world.values[key] = value
        _mark_content_dirty(state)
        return
    count = max(0, int(value))
    if count > 0:
        state.world.seen_items.add(key)
    state.world.inventory[key] = count
    _mark_content_dirty(state)


# ── Actor attribute helpers ────────────────────────────────────────────

def _actor_attribute_value(state: GameState, owner_id: str, suit) -> int:
    from sincity.model.enums import Suit
    actor = party_actor(state, owner_id)
    if suit == Suit.FORCE:
        return actor.force
    if suit == Suit.CHARM:
        return actor.charm
    if suit == Suit.KNOWLEDGE:
        return actor.knowledge
    if suit == Suit.SENSE:
        return actor.sense
    return 0


def tick_actor_statuses_after_draw(state: GameState) -> None:
    for actor in state.party.values():
        if not actor.statuses:
            continue
        next_statuses: list = []
        for status in actor.statuses:
            status.cycles -= 1
            if status.cycles > 0:
                next_statuses.append(status)
        actor.statuses = next_statuses


# ── Spirit helpers ───────────────────────────────────────────────────

def upgrade_spirit_value(state: GameState, spirit: str, amount: int, extra_lines: list[str] | None = None) -> None:
    actor = player_actor(state)
    assert spirit in {"force", "charm", "knowledge", "sense"}, f"Unknown spirit: {spirit}"
    setattr(actor, spirit, getattr(actor, spirit) + amount)
    sync_trauma_cards_with_health(state)
    _mark_content_dirty(state)
    if extra_lines is not None:
        from sincity.game.effects import _field_label
        extra_lines.append(f"{_field_label(spirit)} +{amount}")


def add_spirit_slot(state: GameState, spirit: str, extra_lines: list[str] | None = None) -> None:
    from sincity.game.deck import refresh_spirit_slots
    from sincity.game.session import _active_card_actors
    state.deck.extra_slots[spirit] = state.deck.extra_slots.get(spirit, 0) + 1
    refresh_spirit_slots(state.deck, rng=None, actors=_active_card_actors(state), screen=state.screen)
    sync_trauma_cards_with_health(state)
    _mark_content_dirty(state)
    if extra_lines is not None:
        from sincity.game.effects import _field_label
        extra_lines.append(f"{_field_label(spirit)} 获得额外槽位")


def add_field(state: GameState, key: str, amount: int, extra_lines: list[str] | None = None) -> None:
    if state.active_encounter is not None and key in state.active_encounter.store:
        current = field_value(state, key)
        assert isinstance(current, int), f"Cannot add to non-number field `{key}`"
        set_field(state, key, current + amount, extra_lines)
        return
    if key == "health":
        change_health(state, amount, extra_lines)
        return
    if key == "energy":
        change_energy(state, amount, extra_lines)
        return
    if key == "pressure":
        change_actor_pressure(state, amount, state.acting_actor_id or state.player_actor_id, extra_lines)
        return
    current = field_value(state, key)
    set_field(state, key, int(current) + amount, extra_lines)
