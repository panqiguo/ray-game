from __future__ import annotations

from raygame.model.defs import Effect, GrowthDef


GROWTH_DEFS: dict[str, GrowthDef] = {
    "calm_habit": GrowthDef(
        id="calm_habit",
        title="冷静习惯",
        description="Stress 上限 +2。",
        effects=(Effect("increase_stress_cap", 2),),
    ),
    "casebook": GrowthDef(
        id="casebook",
        title="记案本",
        description="每天结束时可保留 1 张手牌到次日。",
        effects=(Effect("enable_casebook", True),),
    ),
    "old_scars": GrowthDef(
        id="old_scars",
        title="老伤钝化",
        description="任务中首次受到 Health 伤害时不塞物理负面牌。",
        effects=(Effect("enable_old_scars", True),),
    ),
    "paranoid_reason": GrowthDef(
        id="paranoid_reason",
        title="偏执专长·理性",
        description="将 1 张理性基础牌永久升级为 1 点。",
        effects=(Effect("upgrade_card", "reason"),),
    ),
}

