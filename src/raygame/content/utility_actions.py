from __future__ import annotations

from raygame.model.defs import ActionCostDef, ActionPointDef
from raygame.model.enums import ScreenName


CITY_UTILITY_ACTIONS: dict[str, ActionPointDef] = {
    "city_smoke": ActionPointDef(
        id="city_smoke",
        title="抽烟",
        description="让脑子暂时安静一点。",
        screen=ScreenName.CITY,
        costs=(ActionCostDef("resource", "cigarettes", 1, "烟卷"),),
        free_text="投入 1 根烟卷，Stress -2，并塞入疲惫。",
        special="city_smoke",
    ),
    "end_day": ActionPointDef(
        id="end_day",
        title="结束今天",
        description="收起线索和烟灰，准备迎接下一天。",
        screen=ScreenName.CITY,
        free_text="结束整备阶段并推进到下一天。",
        special="end_day",
    ),
}


MISSION_UTILITY_ACTIONS: dict[str, ActionPointDef] = {
    "mission_smoke": ActionPointDef(
        id="mission_smoke",
        title="抽烟",
        description="拿一口烟，换一次重新整理手牌的机会。",
        screen=ScreenName.MISSION,
        costs=(ActionCostDef("resource", "cigarettes", 1, "烟卷"),),
        free_text="投入 1 根烟卷，并选 1 张负面手牌弃掉后重整手牌。",
        special="mission_smoke",
    ),
    "push_through": ActionPointDef(
        id="push_through",
        title="硬撑",
        description="当手里什么都不剩时，硬把自己往前推一把。",
        screen=ScreenName.MISSION,
        free_text="在空手时强行续行动，抽牌并增加 Stress。",
        special="push_through",
    ),
}
