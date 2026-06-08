from __future__ import annotations

from dataclasses import dataclass

from sincity.model.defs import InputRequirement


@dataclass(frozen=True)
class OpenLocation:
    location_id: str


@dataclass(frozen=True)
class OpenAction:
    action_id: str


@dataclass(frozen=True)
class ExecuteAction:
    pass


@dataclass(frozen=True)
class ContinueDialogue:
    pass


@dataclass(frozen=True)
class ChooseDialogueOption:
    index: int


@dataclass(frozen=True)
class CloseModal:
    pass


@dataclass(frozen=True)
class StartDialogue:
    dialogue_id: str


@dataclass(frozen=True)
class StartQuickDialogue:
    dialogue_id: str


@dataclass(frozen=True)
class SelectCardInput:
    slot_id: str
    slot_index: int


@dataclass(frozen=True)
class ToggleEnergySlot:
    action_id: str


@dataclass(frozen=True)
class ToggleRequirementSlot:
    action_id: str
    requirement_key: str


@dataclass(frozen=True)
class FinishDialogue:
    pass


@dataclass(frozen=True)
class DismissPendingResolution:
    """关闭当前结算动画。仅当 pending 已 settled（effect 已落地）时有效；
    对未 settled 的 pending 调用会 assert（效果尚未应用，不应 dismiss）。"""
    pass


@dataclass(frozen=True)
class FastForwardDialogue:
    pass


@dataclass(frozen=True)
class AdvanceCycle:
    pass


@dataclass(frozen=True)
class EndurePressure:
    pass


GameCommand = (
    OpenLocation
    | OpenAction
    | ExecuteAction
    | ContinueDialogue
    | ChooseDialogueOption
    | CloseModal
    | StartDialogue
    | StartQuickDialogue
    | SelectCardInput
    | ToggleEnergySlot
    | ToggleRequirementSlot
    | FinishDialogue
    | DismissPendingResolution
    | FastForwardDialogue
    | AdvanceCycle
    | EndurePressure
)
