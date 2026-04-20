from __future__ import annotations

from raygame.model.defs import Effect, GrowthDef


GROWTH_DEFS: dict[str, GrowthDef] = {
    "add_logic": GrowthDef(
        id="add_logic",
        title="增加逻辑",
        description="向牌组加入 1 张基础·逻辑。",
        effects=(Effect("add_base_card", "logic"),),
    ),
    "remove_logic": GrowthDef(
        id="remove_logic",
        title="移除逻辑",
        description="从牌组中移除 1 张基础·逻辑。",
        effects=(Effect("remove_base_card", "logic"),),
    ),
    "add_perception": GrowthDef(
        id="add_perception",
        title="增加感知",
        description="向牌组加入 1 张基础·感知。",
        effects=(Effect("add_base_card", "perception"),),
    ),
    "remove_perception": GrowthDef(
        id="remove_perception",
        title="移除感知",
        description="从牌组中移除 1 张基础·感知。",
        effects=(Effect("remove_base_card", "perception"),),
    ),
    "add_willpower": GrowthDef(
        id="add_willpower",
        title="增加意志",
        description="向牌组加入 1 张基础·意志。",
        effects=(Effect("add_base_card", "willpower"),),
    ),
    "remove_willpower": GrowthDef(
        id="remove_willpower",
        title="移除意志",
        description="从牌组中移除 1 张基础·意志。",
        effects=(Effect("remove_base_card", "willpower"),),
    ),
}
