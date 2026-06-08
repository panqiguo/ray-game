from __future__ import annotations

# 事件系统设计约束（过渡期）:
#   事件有两个出口：
#   1. dispatch() 返回值 — 同步事件（ActionStarted、DialogueStarted 等）
#   2. state.pending_events 队列 — 异步结算事件（ResolutionSettled）
#      由 advance_pending_resolution() 在帧更新中写入，调用方需轮询消费
#
#   这是过渡设计：ResolutionSettled 依赖时间驱动（0.7s animation）无法同步返回。
#   后续应统一：全走 pending_events，或 dispatch 返回 Future/Promise。

from dataclasses import dataclass

from sincity.model.enums import ResultType
from sincity.model.state import GameState


@dataclass(frozen=True)
class ActionStarted:
    """ExecuteAction 时发出——此时只创建了 PendingResolution，effect 尚未真正结算。"""
    action_id: str
    result: ResultType | None


@dataclass(frozen=True)
class ResolutionSettled:
    """advance_pending_resolution 中 effect 已应用、last_resolution 已写入后发出。
    这是 effects / reacts / screen 切换已经落地的信号。"""
    action_id: str


@dataclass(frozen=True)
class EncounterStarted:
    encounter_id: str


@dataclass(frozen=True)
class DialogueStarted:
    dialogue_id: str


@dataclass(frozen=True)
class GameEnded:
    ending_id: str | None


@dataclass(frozen=True)
class DialogueFastForwarded:
    pass


GameEvent = ActionStarted | ResolutionSettled | EncounterStarted | DialogueStarted | DialogueFastForwarded | GameEnded


def drain_pending_events(state: GameState) -> list[GameEvent]:
    events = state.pending_events
    state.pending_events = []
    return events
