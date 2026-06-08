from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

from typing import TYPE_CHECKING

from .defs import Effect
from .enums import ResultType, ScreenName

if TYPE_CHECKING:
    from sincity.encounters.defs import ActionTemplate, LocationTemplate


@dataclass
class DeckState:  # runtime state
    extra_slots: dict[str, int] = field(default_factory=dict)
    action_card_values: dict[str, int] = field(default_factory=dict)
    action_card_bonuses: dict[str, int] = field(default_factory=dict)
    action_card_penalties: dict[str, int] = field(default_factory=dict)
    action_card_labels: dict[str, str] = field(default_factory=dict)
    action_card_owners: dict[str, str] = field(default_factory=dict)
    available_slots: list[str] = field(default_factory=list)
    exhausted_slots: list[str] = field(default_factory=list)
    locked_slots: list[str] = field(default_factory=list)
    trauma_by_slot: dict[str, int] = field(default_factory=dict)


@dataclass
class AttributeState:  # runtime state
    health: int = 10
    max_health: int = 10
    energy: int = 5
    max_energy: int = 5


@dataclass
class ActorStatusState:  # runtime state
    id: str
    cycles: int


@dataclass
class PartyActorState:  # runtime state
    id: str
    name: str
    health: int
    max_health: int
    energy: int
    max_energy: int
    force: int = 0
    charm: int = 0
    knowledge: int = 0
    sense: int = 0
    is_player: bool = False
    pressure: int = 0
    max_pressure: int = 5
    pressure_locked: bool = False
    stress_location: str = ""
    statuses: list[ActorStatusState] = field(default_factory=list)

    @property
    def can_act(self) -> bool:
        if self.health <= 0:
            return False
        if self.is_player:
            return True
        return not self.pressure_locked


@dataclass
class ProgressClockState:  # runtime state
    value: int = 0
    visible: bool = False  # UI state
    disabled: bool = False


@dataclass
class WorldState:  # runtime state
    fresh_locations: set[str] = field(default_factory=set)
    progress_clocks: dict[str, ProgressClockState] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)
    seen_items: set[str] = field(default_factory=set)
    values: dict[str, int | bool | str] = field(default_factory=dict)
    rewarded_tasks: set[str] = field(default_factory=set)
    mounted_locations: dict[str, tuple["LocationTemplate", ...]] = field(default_factory=dict)
    mounted_actions: dict[str, tuple["ActionTemplate", ...]] = field(default_factory=dict)


@dataclass
class ActionAssemblyState:  # UI state container
    action_id: str | None = None
    slotted_card_id: str | None = None
    slotted_card_index: int | None = None
    slotted_items: dict[str, int] = field(default_factory=dict)


@dataclass
class SelectedInputState:  # UI state container
    kind: str = ""
    key: str = ""
    index: int | None = None


@dataclass
class ActionResolution:  # UI state (result display)
    action_id: str
    card_id: str | None
    result: ResultType | None
    die_roll: int | None
    value: int | None
    text: str
    effect_lines: tuple[str, ...] = ()


@dataclass
class PendingResolutionState:  # transitional (holds pending effects)
    resolution: ActionResolution
    effects: tuple[Effect, ...]
    log_text: str
    location_id: str
    acting_actor_id: str = ""
    completion_kind: str = ""
    reveal_title: str = ""
    reveal_text: str = ""
    reveal_duration: float = 0.0
    progress: float = 0.0
    settled: bool = False


@dataclass
class ModalFrame:  # UI state container
    kind: str
    primary_id: str | None = None


@dataclass
class ModalState:  # UI state container
    kind: str = ""
    primary_id: str | None = None
    return_kind: str = ""
    return_primary_id: str | None = None
    stacked_frames: list[ModalFrame] = field(default_factory=list)


@dataclass
class ActiveEncounterState:  # runtime state
    encounter_id: str
    store: dict[str, int | bool | str] = field(default_factory=dict)


@dataclass
class DialogueLine:  # runtime state
    text: str
    speaker: str = ""


@dataclass
class ActiveDialogueState:  # runtime state (fields marked # UI state are UI-only)
    dialogue_id: str
    title: str
    runtime: Any | None = None
    history: list[DialogueLine] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    can_continue: bool = False
    finished: bool = False
    auto_close_on_finish: bool = True  # UI state
    history_scroll: int = 0  # UI state
    error: str = ""  # UI state


@dataclass
class RenderCacheState:  # UI state container
    revision: int = 0
    world_revision: int = -1
    world_snapshot: Any | None = None
    encounter_revision: int = -1
    encounter_id: str = ""
    encounter_snapshot: Any | None = None


@dataclass
class ActiveActionRevealState:  # UI state container
    action_id: str
    title: str
    text: str
    elapsed: float = 0.0
    duration: float = 0.0


@dataclass
class NotificationState:  # UI state container
    id: int
    kind: str
    title: str
    body: str = ""
    age: float = 0.0
    duration: float = 3.2


@dataclass
class CardHintFlashState:  # UI state container
    action_id: str = ""
    until_monotonic: float = 0.0


@dataclass
class GameState:  # runtime state + UI state containers
    deck: DeckState
    attributes: AttributeState = field(default_factory=AttributeState)
    party: dict[str, PartyActorState] = field(default_factory=dict)
    player_actor_id: str = "cole"
    companion_actor_ids: list[str] = field(default_factory=list)
    world: WorldState = field(default_factory=WorldState)
    screen: ScreenName = ScreenName.CITY
    day: int = 1
    assembly: ActionAssemblyState = field(default_factory=ActionAssemblyState)  # UI state
    selected_input: SelectedInputState = field(default_factory=SelectedInputState)  # UI state
    pending_growth_choices: list[str] = field(default_factory=list)
    growth_points: int = 0
    unlocked_growths: set[str] = field(default_factory=set)
    modal: ModalState = field(default_factory=ModalState)  # UI state
    active_encounter: ActiveEncounterState | None = None
    active_dialogue: ActiveDialogueState | None = None
    dialogue_queue: list[ActiveDialogueState] = field(default_factory=list)
    last_resolution: ActionResolution | None = None  # UI state
    pending_resolution: PendingResolutionState | None = None  # transitional
    action_reveal: ActiveActionRevealState | None = None  # UI state
    action_log: list[str] = field(default_factory=list)  # UI state
    ending_id: str | None = None
    ending_title: str = ""  # UI state
    ending_body: str = ""  # UI state
    pending_game_over: bool = False
    pending_game_over_title: str = ""  # UI state
    pending_game_over_body: str = ""  # UI state
    debug_open: bool = False  # UI state
    pending_restart: bool = False
    seed: int = 0
    render_cache: RenderCacheState = field(default_factory=RenderCacheState)  # UI state
    card_hint_flash: CardHintFlashState = field(default_factory=CardHintFlashState)  # UI state
    acting_actor_id: str = ""
    encounter_pressure_used: bool = False
    encounter_resource_root_id: str = ""
    task_panel_scroll: float = 0.0  # UI state
    notifications: list[NotificationState] = field(default_factory=list)  # UI state
    next_notification_id: int = 1  # UI state
    pending_events: list["GameEvent"] = field(default_factory=list)  # transient: ResolutionSettled etc from game.resolution
