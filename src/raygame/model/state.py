from __future__ import annotations

from dataclasses import dataclass, field

from .enums import AreaName, ResultType, ScreenName


@dataclass
class DeckState:
    draw_pile: list[str]
    discard_pile: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    retained_card_id: str | None = None
    push_through_count: int = 0


@dataclass
class ResourceState:
    health: int = 5
    max_health: int = 5
    stress: int = 0
    max_stress: int = 8
    money: int = 30
    cigarettes: int = 0


@dataclass
class ClockState:
    heat: int = 0
    heat_max: int = 6
    crow_time: int = 6
    crow_time_max: int = 6
    alarm: int = 0
    alarm_max: int = 4
    freeze_crow_time_once: bool = False


@dataclass
class MissionState:
    current_area: AreaName = AreaName.PERIMETER
    completed_actions: set[str] = field(default_factory=set)
    skipped_guard: bool = False
    freezer_shortcut: bool = False
    lights_off: bool = False
    evidence_unlocked: bool = False
    crow_rescued: bool = False
    crow_talked: bool = False
    boss_resolution: str | None = None
    ledger_found: bool = False
    failed: bool = False


@dataclass
class ActionResolution:
    action_id: str
    method_id: str
    card_id: str | None
    result: ResultType
    die_roll: int
    value: int
    text: str


@dataclass
class ModalState:
    kind: str = ""
    primary_id: str | None = None


@dataclass
class GameState:
    deck: DeckState
    resources: ResourceState = field(default_factory=ResourceState)
    clocks: ClockState = field(default_factory=ClockState)
    mission: MissionState = field(default_factory=MissionState)
    screen: ScreenName = ScreenName.CITY
    day: int = 1
    clues: set[str] = field(default_factory=set)
    items: set[str] = field(default_factory=set)
    flags: set[str] = field(default_factory=set)
    unlocked_growths: set[str] = field(default_factory=set)
    pending_growth_choices: list[str] = field(default_factory=list)
    growth_points: int = 0
    selected_action_id: str | None = None
    selected_method_id: str | None = None
    selected_card_id: str | None = None
    prepared_costs: set[str] = field(default_factory=set)
    modal: ModalState = field(default_factory=ModalState)
    last_resolution: ActionResolution | None = None
    action_log: list[str] = field(default_factory=list)
    ending_id: str | None = None
    ending_title: str = ""
    ending_body: str = ""
    debug_open: bool = False
    seed: int = 0
    used_old_wound_buffer: bool = False
