from __future__ import annotations

from sincity.model.state import GameState, NotificationState

KINDS = frozenset({"info", "success", "warning", "danger"})
MAX_NOTIFICATIONS = 6


def push_notification(
    state: GameState,
    kind: str,
    title: str,
    body: str = "",
    *,
    duration: float = 3.2,
) -> None:
    assert kind in KINDS, f"invalid notification kind: {kind}"
    assert title, "notification title must not be empty"
    assert duration > 0, f"notification duration must be positive: {duration}"

    if state.notifications and state.notifications[-1].kind == kind and state.notifications[-1].title == title and state.notifications[-1].body == body:
        state.notifications[-1].age = 0.0
        return

    state.notifications.append(NotificationState(
        id=state.next_notification_id,
        kind=kind,
        title=title,
        body=body,
        age=0.0,
        duration=duration,
    ))
    state.next_notification_id += 1

    if len(state.notifications) > MAX_NOTIFICATIONS:
        state.notifications.pop(0)


def advance_notifications(state: GameState, dt: float) -> None:
    for item in state.notifications:
        item.age += dt
    state.notifications = [
        item for item in state.notifications
        if item.age < item.duration
    ]
