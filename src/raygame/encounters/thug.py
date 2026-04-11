from __future__ import annotations

from raygame.content.builders import check, effect, outcome
from raygame.encounters.dsl import (
    act,
    compile_encounter_script,
    encounter,
    encounter_action,
    local_clock,
    objective_clock,
    on_clock_empty,
    on_clock_full,
    state,
)
from raygame.model.enums import Risk, Suit


def breathe_action():
    return encounter_action(
        id="thug_breathe",
        title="喘息一下",
        description="你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。",
        effects=(effect("reset_hand", True), effect("change_health", -1)),
    )


def knee_kick_action(action_id: str, description: str):
    return encounter_action(
        id=action_id,
        title="踹膝脱身",
        description=description,
        check=check(
            suits=(Suit.REASON, Suit.FORCE),
            risk=Risk.MID,
            success=outcome("你一下踹垮了他。", effect("damage_encounter_clock", "enemy_hp:2")),
            cost=outcome("你踹实了一下。", effect("damage_encounter_clock", "enemy_hp:1")),
            fail=outcome("你动作慢了。", effect("change_health", -1)),
        ),
    )


ACT_1_ACTIONS = {
    "counter": encounter_action(
        id="thug_counter",
        title="防守反击",
        description="你先稳住头脸和脚步，再找机会把他顶开。",
        check=check(
            suits=(Suit.REASON, Suit.EMPATHY),
            risk=Risk.LOW,
            success=outcome("你稳稳顶住了节奏。", effect("advance_encounter_clock", "initiative:1")),
            cost=outcome("你至少没有继续吃亏。", effect("advance_encounter_clock", "initiative:1")),
            fail=outcome("你还是没完全顶住。", effect("change_health", -1)),
        ),
    ),
    "punch": encounter_action(
        id="thug_punch",
        title="直接挥拳",
        description="你不跟他磨，直接狠狠干出一步空间。",
        check=check(
            suits=(Suit.FORCE,),
            risk=Risk.HIGH,
            success=outcome("你狠狠干出了一步空间。", effect("advance_encounter_clock", "initiative:2")),
            cost=outcome("你砸中了他，但也只是暂时逼开。", effect("advance_encounter_clock", "initiative:1")),
            fail=outcome("你被他顶了回来。", effect("change_health", -1)),
        ),
    ),
    "rush_knife": encounter_action(
        id="thug_rush_knife",
        title="扑向折刀",
        description="你冒险扑向地上的折刀，想先把局势翻过来。",
        effects=(effect("change_health", -1),),
        check=check(
            suits=(Suit.INSTINCT, Suit.FORCE),
            risk=Risk.HIGH,
            success=outcome("你手已经摸到刀柄了。", effect("advance_encounter_clock", "knife:1")),
            cost=outcome("你拖着伤抢到了第一步位置。", effect("advance_encounter_clock", "knife:1")),
            fail=outcome("你扑过去了，但还没真正把刀抢出来。"),
        ),
    ),
    "knife_press": encounter_action(
        id="thug_knife_press",
        title="持刀逼退",
        description="刀一到手，你立刻逼他后撤，把主动权压回来。",
        check=check(
            suits=(Suit.FORCE, Suit.REASON),
            risk=Risk.MID,
            success=outcome("你借着刀势一口气压住了他。", effect("advance_encounter_clock", "initiative:2")),
            cost=outcome("你逼得他后退了一步。", effect("advance_encounter_clock", "initiative:1")),
            fail=outcome("他还是硬顶了上来。", effect("change_health", -1)),
        ),
    ),
    "breathe": breathe_action(),
}


ACT_2_ACTIONS = {
    "heavy_punch": encounter_action(
        id="thug_heavy_punch",
        title="重拳追击",
        description="你不给他喘气空间，直接压上去狠狠干。",
        check=check(
            suits=(Suit.FORCE,),
            risk=Risk.MID,
            success=outcome("你狠狠干中了一拳。", effect("damage_encounter_clock", "enemy_hp:1")),
            cost=outcome("你打实了一下，但他还撑着。", effect("damage_encounter_clock", "enemy_hp:1")),
            fail=outcome("你被他架住了。", effect("change_health", -1)),
        ),
    ),
    "feint": encounter_action(
        id="thug_feint",
        title="假动作试探",
        description="你做一个假动作，先试着把他的防守骗开一层。",
        check=check(
            suits=(Suit.EMPATHY, Suit.INSTINCT),
            risk=Risk.MID,
            success=outcome("他的防守被你骗得动了一下。", effect("advance_encounter_clock", "opening:1")),
            cost=outcome("他开始有点被你带着走。", effect("advance_encounter_clock", "opening:1")),
            fail=outcome("他没上当。"),
        ),
    ),
    "kick": knee_kick_action("thug_kick_knee", "你不追求漂亮，而是直接踹他的支撑腿。"),
    "kick_open": knee_kick_action("thug_kick_knee_open", "你直接踹他的支撑腿，狠狠干净利落地结束。"),
    "finisher": encounter_action(
        id="thug_finisher",
        title="终结一击",
        description="你抓住空门，一击把他放倒。",
        check=check(
            suits=(Suit.FORCE,),
            risk=Risk.LOW,
            success=outcome("你干净利落地结束了这场架。", effect("damage_encounter_clock", "enemy_hp:2")),
            cost=outcome("你一击放倒了他。", effect("damage_encounter_clock", "enemy_hp:2")),
            fail=outcome("没打实，但已经足够。", effect("damage_encounter_clock", "enemy_hp:1")),
        ),
    ),
    "breathe": breathe_action(),
}


ENCOUNTER = compile_encounter_script(
    encounter(
        id="teach_thug",
        title="教训一个小混混",
        description="拿人钱财，帮人把这件事办干净。",
        initial_act_id="act_1",
        rewards=(effect("change_resource", "money:80"),),
        acts=(
            act(
                id="act_1",
                title="摆脱压制",
                description="先从墙边和压制里脱出来，夺回主动权。",
                objective_clock=objective_clock("initiative", "主动权", 2),
                initial_state_id="pressed_unarmed",
                action_defs=ACT_1_ACTIONS,
                states=(
                    state(
                        id="pressed_unarmed",
                        title="徒手受压",
                        description="打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干，还是冒险把折刀夺到手。",
                        actions=(
                            "counter",
                            "breathe",
                            "punch",
                            "rush_knife",
                        ),
                    ),
                    state(
                        id="knife_advantage",
                        title="持刀逼退",
                        description="刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。",
                        actions=(
                            "counter",
                            "knife_press",
                            "breathe",
                        ),
                    ),
                ),
                clocks=(local_clock("knife", "夺刀", 2),),
                transitions=(
                    on_clock_full("knife", effect("set_encounter_state", "knife_advantage")),
                    on_clock_full("initiative", effect("set_encounter_act", "act_2"), effect("set_encounter_state", "duel")),
                ),
            ),
            act(
                id="act_2",
                title="拿到优势后终结",
                description="你已经摆脱压制，现在要狠狠干净地收尾。",
                objective_clock=objective_clock("enemy_hp", "敌人血量", 2),
                initial_state_id="duel",
                action_defs=ACT_2_ACTIONS,
                states=(
                    state(
                        id="duel",
                        title="对峙",
                        description="对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。",
                        actions=(
                            "heavy_punch",
                            "breathe",
                            "feint",
                            "kick",
                        ),
                    ),
                    state(
                        id="guard_open",
                        title="空门大开",
                        description="他的防守空档已经完全露出来了。狠狠干净地结束这场架。",
                        actions=(
                            "finisher",
                            "kick_open",
                            "breathe",
                        ),
                    ),
                ),
                clocks=(local_clock("opening", "破绽", 2),),
                transitions=(
                    on_clock_full("opening", effect("set_encounter_state", "guard_open")),
                    on_clock_empty("enemy_hp", effect("finish_encounter", "success")),
                ),
            ),
        ),
    )
)
