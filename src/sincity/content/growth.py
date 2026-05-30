from __future__ import annotations

from sincity.model.defs import Effect, GrowthDef


GROWTH_DEFS: dict[str, GrowthDef] = {
    "upgrade_force": GrowthDef(
        id="upgrade_force",
        title="强化暴力",
        description="暴力基础值 +1。",
        effects=(Effect("upgrade_spirit_value", "force:1"),),
    ),
    "upgrade_charm": GrowthDef(
        id="upgrade_charm",
        title="强化魅力",
        description="魅力基础值 +1。",
        effects=(Effect("upgrade_spirit_value", "charm:1"),),
    ),
    "upgrade_knowledge": GrowthDef(
        id="upgrade_knowledge",
        title="强化知识",
        description="知识基础值 +1。",
        effects=(Effect("upgrade_spirit_value", "knowledge:1"),),
    ),
    "upgrade_sense": GrowthDef(
        id="upgrade_sense",
        title="强化敏锐",
        description="敏锐基础值 +1。",
        effects=(Effect("upgrade_spirit_value", "sense:1"),),
    ),
}
