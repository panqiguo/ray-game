from __future__ import annotations

from dataclasses import dataclass, field

from sincity.presentation.typography import ui_text_size


@dataclass(frozen=True)
class TableCardStyle:
    width: float
    height: float
    title_size: int
    body_size: int


@dataclass(frozen=True)
class TableCardModel:
    title: str
    body: str
    labels: tuple[str, ...] = ()
    clock_ids: tuple[str, ...] = ()
    metadata: tuple[str, ...] = ()
    active: bool = False
    disabled: bool = False
    interactive: bool = True
    style: TableCardStyle = field(default_factory=lambda: TABLE_CARD)


WORLD_CARD = TableCardStyle(width=188.0, height=96.0, title_size=ui_text_size("subtitle"), body_size=ui_text_size("body"))
TABLE_CARD = TableCardStyle(width=188.0, height=96.0, title_size=ui_text_size("subtitle"), body_size=ui_text_size("body"))
ACTION_CARD = TableCardStyle(width=232.0, height=224.0, title_size=ui_text_size("subtitle"), body_size=ui_text_size("body") + 2)
