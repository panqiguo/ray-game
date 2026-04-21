from __future__ import annotations

from raygame.model.defs import Condition, Effect, GrowthDef


GROWTH_DEFS: dict[str, GrowthDef] = {
    "upgrade_logic": GrowthDef(
        id="upgrade_logic",
        title="强化逻辑",
        description="逻辑基础值 +1。",
        effects=(Effect("upgrade_spirit_value", "logic:1"),),
    ),
    "upgrade_perception": GrowthDef(
        id="upgrade_perception",
        title="强化感知",
        description="感知基础值 +1。",
        effects=(Effect("upgrade_spirit_value", "perception:1"),),
    ),
    "upgrade_willpower": GrowthDef(
        id="upgrade_willpower",
        title="强化意志",
        description="意志基础值 +1。",
        effects=(Effect("upgrade_spirit_value", "willpower:1"),),
    ),
    "major_logic_slot": GrowthDef(
        id="major_logic_slot",
        title="重大升级：逻辑额外槽位",
        description="需要逻辑至少 3。获得一个额外的逻辑槽位。",
        effects=(Effect("add_spirit_slot", "logic"),),
        conditions=(Condition("field_at_least", "logic:3", "需要逻辑至少 3"),),
    ),
    "major_perception_slot": GrowthDef(
        id="major_perception_slot",
        title="重大升级：感知额外槽位",
        description="需要感知至少 3。获得一个额外的感知槽位。",
        effects=(Effect("add_spirit_slot", "perception"),),
        conditions=(Condition("field_at_least", "perception:3", "需要感知至少 3"),),
    ),
    "major_willpower_slot": GrowthDef(
        id="major_willpower_slot",
        title="重大升级：意志额外槽位",
        description="需要意志至少 3。获得一个额外的意志槽位。",
        effects=(Effect("add_spirit_slot", "willpower"),),
        conditions=(Condition("field_at_least", "willpower:3", "需要意志至少 3"),),
    ),
}
