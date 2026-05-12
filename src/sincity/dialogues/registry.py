from __future__ import annotations

from pathlib import Path

from .defs import DialogueAsset


ASSET_DIR = Path(__file__).resolve().parent / "assets"


DIALOGUES_BY_ID: dict[str, DialogueAsset] = {}


def _register_defaults() -> dict[str, DialogueAsset]:
    return {
        "bar_bartender_intro": DialogueAsset(
            id="bar_bartender_intro",
            title="和酒保聊聊",
            compiled_path=ASSET_DIR / "bar_bartender_intro.ink.json",
        ),
        "开篇": DialogueAsset(
            id="开篇",
            title="开篇",
            compiled_path=ASSET_DIR / "开篇.ink.json",
        ),
        "first_scene_doctor_office": DialogueAsset(
            id="first_scene_doctor_office",
            title="主治医师办公室",
            compiled_path=ASSET_DIR / "first_scene_doctor_office.ink.json",
        ),
        "frederick_phone_intro": DialogueAsset(
            id="frederick_phone_intro",
            title="弗雷德里克的电话",
            compiled_path=ASSET_DIR / "frederick_phone_intro.ink.json",
        ),
    }


DIALOGUES_BY_ID.update(_register_defaults())


def get_dialogue(dialogue_id: str) -> DialogueAsset:
    assert dialogue_id in DIALOGUES_BY_ID, f"Unknown dialogue: {dialogue_id}"
    return DIALOGUES_BY_ID[dialogue_id]
