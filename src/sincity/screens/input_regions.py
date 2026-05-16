from __future__ import annotations

from pyray import Rectangle, get_screen_height, get_screen_width

from sincity.constants import HUD_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH
from sincity.model.state import GameState

from .ui_core import Z_DEBUG, Z_DIALOGUE_MODAL, Z_HAND, Z_HUD, Z_LOCATION_MODAL, Z_PROFILE_MODAL, layout, register_input_region


# --- Panel rect functions (pure, shared between registration and drawing) ---

def debug_panel_rect() -> Rectangle:
    return Rectangle(1080, 92, 330, 340)


def profile_panel_rect() -> Rectangle:
    hud = layout().hud
    return Rectangle(hud.x + hud.width - 500, hud.y + hud.height + 12, 500, 440)


def profile_blocking_rect() -> Rectangle:
    w = get_screen_width() or WINDOW_WIDTH
    h = get_screen_height() or WINDOW_HEIGHT
    return Rectangle(0, HUD_HEIGHT + 8, w, h - HUD_HEIGHT - 8)


def dialogue_blocking_rect() -> Rectangle:
    w = get_screen_width() or WINDOW_WIDTH
    h = get_screen_height() or WINDOW_HEIGHT
    return Rectangle(0, 0, w, h)


# --- Screen-level registration ---

def register_screen_input_regions(state: GameState) -> None:
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    modal_kind = state.modal.kind

    # Location modal: block stage area + HUD (hand stays interactive)
    if modal_kind == "location":
        register_input_region(
            "location_modal_block",
            layout().stage,
            z=Z_LOCATION_MODAL,
            interactive=True,
            blocks_pointer=True,
        )
        register_input_region(
            "hud_block",
            layout().hud,
            z=Z_HUD,
            interactive=False,
            blocks_pointer=True,
        )

    # Profile modal: block everything below HUD (HUD stays interactive)
    if modal_kind == "profile":
        register_input_region(
            "profile_modal_block",
            profile_blocking_rect(),
            z=Z_PROFILE_MODAL,
            interactive=True,
            blocks_pointer=True,
        )

    # Dialogue modal: block everything (full screen, modal=True)
    if modal_kind == "dialogue":
        register_input_region(
            "dialogue_modal_block",
            dialogue_blocking_rect(),
            z=Z_DIALOGUE_MODAL,
            interactive=True,
            modal=True,
            blocks_pointer=True,
        )

    # During resolution, hand should not be interactive
    if resolving:
        register_input_region(
            "hand_block",
            layout().hand,
            z=Z_HAND,
            interactive=False,
            blocks_pointer=True,
        )

    # Debug panel: always sits on top
    if state.debug_open:
        register_input_region(
            "debug_panel",
            debug_panel_rect(),
            z=Z_DEBUG,
            interactive=True,
            blocks_pointer=True,
        )
