from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

from typing import TYPE_CHECKING

from .defs import Effect
from .enums import ResultType, ScreenName

if TYPE_CHECKING:
    from sincity.encounters.defs import ActionTemplate, LocationTemplate


@dataclass
class DeckState:
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
class AttributeState:
    health: int = 10
    max_health: int = 10
    energy: int = 5
    max_energy: int = 5


@dataclass
class ActorStatusState:
    id: str
    cycles: int


@dataclass
class PartyActorState:
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
class ProgressClockState:
    value: int = 0
    visible: bool = False
    disabled: bool = False


@dataclass
class WorldState:
    fresh_locations: set[str] = field(default_factory=set)
    progress_clocks: dict[str, ProgressClockState] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)
    seen_items: set[str] = field(default_factory=set)
    values: dict[str, int | bool | str] = field(default_factory=dict)
    rewarded_tasks: set[str] = field(default_factory=set)
    mounted_locations: dict[str, tuple["LocationTemplate", ...]] = field(default_factory=dict)
    mounted_actions: dict[str, tuple["ActionTemplate", ...]] = field(default_factory=dict)


@dataclass
class ActionAssemblyState:
    action_id: str | None = None
    slotted_card_id: str | None = None
    slotted_card_index: int | None = None
    slotted_items: dict[str, int] = field(default_factory=dict)


@dataclass
class SelectedInputState:
    kind: str = ""
    key: str = ""
    index: int | None = None


@dataclass
class ActionResolution:
    action_id: str
    card_id: str | None
    result: ResultType | None
    die_roll: int | None
    value: int | None
    text: str
    effect_lines: tuple[str, ...] = ()


@dataclass
class PendingResolutionState:
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
class ModalFrame:
    kind: str
    primary_id: str | None = None


@dataclass
class ModalState:
    kind: str = ""
    primary_id: str | None = None
    return_kind: str = ""
    return_primary_id: str | None = None
    stacked_frames: list[ModalFrame] = field(default_factory=list)


@dataclass
class ActiveEncounterState:
    encounter_id: str
    store: dict[str, int | bool | str] = field(default_factory=dict)


@dataclass
class DialogueLine:
    text: str
    speaker: str = ""


@dataclass
class ActiveDialogueState:
    dialogue_id: str
    title: str
    runtime: Any | None = None
    history: list[DialogueLine] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    can_continue: bool = False
    finished: bool = False
    auto_close_on_finish: bool = True
    history_scroll: int = 0
    error: str = ""


@dataclass
class RenderCacheState:
    revision: int = 0
    world_revision: int = -1
    world_snapshot: Any | None = None
    encounter_revision: int = -1
    encounter_id: str = ""
    encounter_snapshot: Any | None = None


@dataclass
class ActiveActionRevealState:
    action_id: str
    title: str
    text: str
    elapsed: float = 0.0
    duration: float = 0.0


@dataclass
class NotificationState:
    id: int
    kind: str
    title: str
    body: str = ""
    age: float = 0.0
    duration: float = 3.2


@dataclass
class CardHintFlashState:
    action_id: str = ""
    until_monotonic: float = 0.0


@dataclass
class GameState:
    deck: DeckState
    attributes: AttributeState = field(default_factory=AttributeState)
    party: dict[str, PartyActorState] = field(default_factory=dict)
    player_actor_id: str = "cole"
    companion_actor_ids: list[str] = field(default_factory=list)
    world: WorldState = field(default_factory=WorldState)
    screen: ScreenName = ScreenName.CITY
    day: int = 1
    assembly: ActionAssemblyState = field(default_factory=ActionAssemblyState)
    selected_input: SelectedInputState = field(default_factory=SelectedInputState)
    pending_growth_choices: list[str] = field(default_factory=list)
    growth_points: int = 0
    unlocked_growths: set[str] = field(default_factory=set)
    modal: ModalState = field(default_factory=ModalState)
    active_encounter: ActiveEncounterState | None = None
    active_dialogue: ActiveDialogueState | None = None
    dialogue_queue: list[ActiveDialogueState] = field(default_factory=list)
    last_resolution: ActionResolution | None = None
    pending_resolution: PendingResolutionState | None = None
    action_reveal: ActiveActionRevealState | None = None
    action_log: list[str] = field(default_factory=list)
    ending_id: str | None = None
    ending_title: str = ""
    ending_body: str = ""
    pending_game_over: bool = False
    pending_game_over_title: str = ""
    pending_game_over_body: str = ""
    debug_open: bool = False
    pending_restart: bool = False
    seed: int = 0
    render_cache: RenderCacheState = field(default_factory=RenderCacheState)
    card_hint_flash: CardHintFlashState = field(default_factory=CardHintFlashState)
    acting_actor_id: str = ""
    encounter_pressure_used: bool = False
    encounter_resource_root_id: str = ""
    task_panel_scroll: float = 0.0
    notifications: list[NotificationState] = field(default_factory=list)
    next_notification_id: int = 1
