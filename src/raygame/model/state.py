from __future__ import annotations

from dataclasses import dataclass, field

from .defs import Effect
from .enums import ResultType, ScreenName


@dataclass
class DeckState:
    draw_pile: list[str]
    discard_pile: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    retained_card_id: str | None = None


@dataclass
class AttributeState:
    health: int = 10
    max_health: int = 10
    stress: int = 0
    max_stress: int = 8


@dataclass
class ResourceState:
    money: int = 0
    cigarettes: int = 0


@dataclass
class ProgressClockState:
    value: int = 0
    visible: bool = False
    disabled: bool = False


@dataclass
class WorldState:
    visible_locations: set[str] = field(default_factory=set)
    fresh_locations: set[str] = field(default_factory=set)
    hidden_actions: set[str] = field(default_factory=set)
    progress_clocks: dict[str, ProgressClockState] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)


@dataclass
class ActionAssemblyState:
    action_id: str | None = None
    slotted_card_id: str | None = None
    slotted_resources: dict[str, int] = field(default_factory=dict)
    slotted_items: dict[str, int] = field(default_factory=dict)


@dataclass
class SelectedInputState:
    kind: str = ""
    key: str = ""


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
    progress: float = 0.0
    settled: bool = False


@dataclass
class ModalState:
    kind: str = ""
    primary_id: str | None = None
    return_kind: str = ""
    return_primary_id: str | None = None


@dataclass
class GameState:
    deck: DeckState
    attributes: AttributeState = field(default_factory=AttributeState)
    resources: ResourceState = field(default_factory=ResourceState)
    world: WorldState = field(default_factory=WorldState)
    screen: ScreenName = ScreenName.CITY
    day: int = 1
    assembly: ActionAssemblyState = field(default_factory=ActionAssemblyState)
    selected_input: SelectedInputState = field(default_factory=SelectedInputState)
    pending_growth_choices: list[str] = field(default_factory=list)
    growth_points: int = 0
    unlocked_growths: set[str] = field(default_factory=set)
    modal: ModalState = field(default_factory=ModalState)
    last_resolution: ActionResolution | None = None
    pending_resolution: PendingResolutionState | None = None
    action_log: list[str] = field(default_factory=list)
    ending_id: str | None = None
    ending_title: str = ""
    ending_body: str = ""
    debug_open: bool = False
    seed: int = 0
