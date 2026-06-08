# game/session.py — 新开局和 session 初始化
#
# 权威入口:
#   state, rng = start_new_run(seed)
#
# 当前依赖: progression._active_card_actors, progression._reset_action_cycle_from_deck
# 后续可迁入 game/ 后消除.

from sincity.constants import HAND_SIZE
from sincity.content import ACTOR_STATUS_DEFS, INITIAL_COMPANION_ID, PARTY_ACTOR_DEFS, PLAYER_ACTOR_ID, SCENARIO, build_initial_party
from sincity.model.enums import ScreenName
from sincity.model.state import AttributeState, GameState, ProgressClockState, WorldState
from sincity.game.deck import make_starting_deck, start_city_day
from sincity.game.rng import RandomSource


def start_new_run(seed: int) -> tuple[GameState, RandomSource]:
    rng = RandomSource(seed)
    deck = make_starting_deck(rng)
    initial_inventory = {
        **dict(SCENARIO.initial_inventory),
        "money": SCENARIO.initial_money,
        "cigarettes": SCENARIO.initial_cigarettes,
    }
    seen_items = {k for k, v in initial_inventory.items() if v > 0}
    world = WorldState(
        progress_clocks={
            clock_id: ProgressClockState(
                value=spec.initial,
                visible=True,
            )
            for clock_id, spec in SCENARIO.clocks_by_id.items()
        },
        inventory=initial_inventory,
        seen_items=seen_items,
        values=dict(SCENARIO.initial_values),
    )
    state = GameState(
        deck=deck,
        attributes=AttributeState(
            health=SCENARIO.initial_health,
            max_health=10,
            energy=SCENARIO.initial_energy,
            max_energy=5,
        ),
        world=world,
        screen=ScreenName.CITY,
        pending_growth_choices=list(SCENARIO.initial_growth_choices),
        growth_points=0,
        seed=seed,
    )
    state.player_actor_id = PLAYER_ACTOR_ID
    state.party = build_initial_party(player_health=state.attributes.health, player_energy=state.attributes.energy)
    state.companion_actor_ids = [INITIAL_COMPANION_ID] if INITIAL_COMPANION_ID and INITIAL_COMPANION_ID in state.party else []
    from sincity.game.fields import sync_trauma_cards_with_health as _sync_trauma
    _sync_trauma(state)
    start_city_day(state.deck, rng, HAND_SIZE, actors=_active_card_actors(state), status_defs=ACTOR_STATUS_DEFS)
    _reset_action_cycle_from_deck(state)
    from sincity.game.queries import sync_world_progress_clocks
    sync_world_progress_clocks(state)
    from sincity.game.reacts import resolve_world_reacts
    resolve_world_reacts(state, rng, [])
    return state, rng


def _active_card_actors(state: GameState) -> tuple:
    if state.screen == ScreenName.ENCOUNTER:
        ids = [state.player_actor_id]
    else:
        ids = [state.player_actor_id, *state.companion_actor_ids]
    return tuple(actor for actor_id in ids if (actor := state.party.get(actor_id)) is not None and actor.can_act)


def _reset_action_cycle_from_deck(state: GameState) -> None:
    state.encounter_pressure_used = False
    state.deck.action_card_bonuses.clear()


# ── Debug helpers ──────────────────────────────────────────────────────

def _refresh_cards_after_party_change(state: GameState, rng: RandomSource | None = None) -> None:
    if rng is None:
        from sincity.game.rng import RandomSource as _RS
        rng = _RS(state.seed)
    from sincity.game.actions import clear_assembly, clear_selected_input
    from sincity.game.clocks import reset_hand
    clear_assembly(state)
    clear_selected_input(state)
    reset_hand(state, rng)


def add_next_companion_for_debug(state: GameState, rng: RandomSource | None = None) -> str | None:
    from sincity.content import DEBUG_COMPANION_ORDER
    from sincity.game.fields import _mark_content_dirty, actor_name
    for actor_id in DEBUG_COMPANION_ORDER:
        if actor_id not in state.companion_actor_ids:
            state.companion_actor_ids.append(actor_id)
            _refresh_cards_after_party_change(state, rng)
            _mark_content_dirty(state)
            return actor_name(state, actor_id)
    return None


def remove_companions_for_debug(state: GameState, rng: RandomSource | None = None) -> tuple[str, ...]:
    from sincity.game.fields import _mark_content_dirty, actor_name
    removed = tuple(actor_name(state, actor_id) for actor_id in state.companion_actor_ids)
    state.companion_actor_ids.clear()
    _refresh_cards_after_party_change(state, rng)
    _mark_content_dirty(state)
    return removed


# ── Growth (shared with UI) ───────────────────────────────────────────

def claim_growth(state: GameState, growth_id: str) -> None:
    from sincity.content import GROWTH_DEFS
    from sincity.game.conditions import all_met
    from sincity.game.effects import apply_effects
    from sincity.game.notifications import push_notification
    from sincity.game.fields import _push_log
    from sincity.game.actions import close_modal
    if state.growth_points <= 0:
        return
    growth = GROWTH_DEFS[growth_id]
    if not all_met(growth.conditions, state):
        return
    apply_effects(growth.effects, state, RandomSource(state.seed))
    state.growth_points = max(0, state.growth_points - 1)
    _push_log(state, f"成长调整：{growth.title}")
    push_notification(state, "success", "成长已确认", growth.title)
    close_modal(state)
