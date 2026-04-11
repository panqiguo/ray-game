from __future__ import annotations

from raygame.content.builders import action, check, clock, effect, location, outcome
from raygame.encounters.defs import EncounterActDef, EncounterDef, EncounterStateDef, EncounterTransitionDef
from raygame.model.enums import Risk, ScreenName, Suit


def encounter_action(**kwargs):
    return action(screen=ScreenName.ENCOUNTER, **kwargs)


def encounter_root(*, id: str, actions=(), children=()):
    return location(id=id, title="", description="", actions=actions, children=children)


def encounter_state(*, id: str, title: str, description: str, root):
    return EncounterStateDef(id=id, title=title, description=description, root=root)


def objective_clock(id: str, title: str, segments: int):
    return clock(id=id, title=title, segments=segments)


def when_clock_full(source: str, *effects):
    return EncounterTransitionDef(kind="clock_full", source=source, effects=effects)


def when_clock_empty(source: str, *effects):
    return EncounterTransitionDef(kind="clock_empty", source=source, effects=effects)


def breathe_action(action_id: str):
    return encounter_action(
        id=action_id,
        title="喘息一下",
        description="你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。",
        effects=(
            effect("reset_hand", True),
            effect("change_health", -1),
        ),
    )


def defend_action(action_id: str, description: str, fail_text: str):
    return encounter_action(
        id=action_id,
        title="防守",
        description=description,
        check=check(
            suits=(Suit.REASON,),
            risk=Risk.LOW,
            success=outcome("你顶住了压制。", effect("advance_encounter_clock", "initiative:1")),
            cost=outcome("你稳住了。", effect("advance_encounter_clock", "initiative:1")),
            fail=outcome(fail_text, effect("change_health", -1)),
        ),
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


PRESSED_ROOT, _ = encounter_root(
    id="pressed_root",
    actions=(
        defend_action(
            "thug_defend_pressed",
            "你先护住头脸，顶住这波压制。",
            "你没有完全挡住。",
        ),
        encounter_action(
            id="thug_elbow_strike",
            title="顶肘反打",
            description="你先护住头脸，顶住这波压制。",
            check=check(
                suits=(Suit.FORCE,),
                risk=Risk.HIGH,
                success=outcome("他被你撞得失衡。", effect("advance_encounter_clock", "initiative:1")),
                cost=outcome("你撞开了一点空隙。", effect("advance_encounter_clock", "initiative:1")),
                fail=outcome("你被他按了回去。", effect("change_health", -1)),
            ),
        ),
        encounter_action(
            id="thug_grab_knife",
            title="抢折刀",
            description="你冒险伸手去拿地上的刀。",
            check=check(
                suits=(Suit.INSTINCT, Suit.FORCE),
                risk=Risk.HIGH,
                success=outcome(
                    "你反手逼退了他。",
                    effect("set_encounter_state", "knife_advantage"),
                    effect("advance_encounter_clock", "initiative:1"),
                ),
                cost=outcome(
                    "你拿到了刀。",
                    effect("set_encounter_state", "knife_advantage"),
                    effect("advance_encounter_clock", "initiative:1"),
                ),
                fail=outcome("你拿到了刀，但没能立刻拉开距离。", effect("set_encounter_state", "knife_advantage")),
            ),
            effects=(effect("change_health", -1),),
        ),
        breathe_action("thug_breathe_pressed"),
    ),
)

KNIFE_ROOT, _ = encounter_root(
    id="knife_root",
    actions=(
        defend_action(
            "thug_defend_knife",
            description="你先护住头脸，稳住局势。",
            fail_text="你还是挨了一下。",
        ),
        encounter_action(
            id="thug_knife_pushback",
            title="持刀逼退",
            description="你挥刀逼退对方，迫使他后撤。",
            check=check(
                suits=(Suit.FORCE, Suit.REASON),
                risk=Risk.MID,
                success=outcome("你完全拿回了主动。", effect("advance_encounter_clock", "initiative:2")),
                cost=outcome("对方被迫后退。", effect("advance_encounter_clock", "initiative:1")),
                fail=outcome("对方看穿了你的虚张声势。", effect("change_health", -1)),
            ),
        ),
        breathe_action("thug_breathe_knife"),
    ),
)

DUEL_ROOT, _ = encounter_root(
    id="duel_root",
    actions=(
        encounter_action(
            id="thug_heavy_punch",
            title="重拳追击",
            description="你不给他喘气空间，直接压上去狠狠干。",
            check=check(
                suits=(Suit.FORCE,),
                risk=Risk.MID,
                success=outcome("你打得他站不稳。", effect("damage_encounter_clock", "enemy_hp:1")),
                cost=outcome("你打实了一拳。", effect("damage_encounter_clock", "enemy_hp:1")),
                fail=outcome("你被他架住了。", effect("change_health", -1)),
            ),
        ),
        encounter_action(
            id="thug_feint",
            title="假动作晃开",
            description="你做一个假动作，骗出他的防守空档。",
            check=check(
                suits=(Suit.EMPATHY, Suit.INSTINCT),
                risk=Risk.MID,
                success=outcome(
                    "他的空门露出来了。",
                    effect("damage_encounter_clock", "enemy_hp:1"),
                    effect("set_encounter_state", "guard_open"),
                ),
                cost=outcome("你撬开了防守。", effect("damage_encounter_clock", "enemy_hp:1")),
                fail=outcome("你没骗到他。"),
            ),
        ),
        knee_kick_action("thug_kick_knee_duel", "你不追求漂亮，而是直接踹他的支撑腿。"),
        breathe_action("thug_breathe_duel"),
    ),
)

OPEN_ROOT, _ = encounter_root(
    id="open_root",
    actions=(
        encounter_action(
            id="thug_finisher",
            title="终结一击",
            description="你抓住对方空门，一击把他放倒。",
            check=check(
                suits=(Suit.FORCE,),
                risk=Risk.LOW,
                success=outcome("你干净利落地结束了这场架。", effect("damage_encounter_clock", "enemy_hp:2")),
                cost=outcome("你一击放倒了他。", effect("damage_encounter_clock", "enemy_hp:2")),
                fail=outcome("没打实，但已经足够。", effect("damage_encounter_clock", "enemy_hp:1")),
            ),
        ),
        knee_kick_action("thug_kick_knee_open", "你直接踹他的支撑腿，狠狠干净利落地结束。"),
        breathe_action("thug_breathe_open"),
    ),
)


ENCOUNTER = EncounterDef(
    id="teach_thug",
    title="教训一个小混混",
    description="拿人钱财，帮人把这件事办干净。",
    initial_act_id="act_1",
    rewards=(effect("change_resource", "money:80"),),
    acts=(
        EncounterActDef(
            id="act_1",
            title="摆脱压制",
            description="先从墙边和压制里脱出来，夺回主动权。",
            objective_clock=objective_clock("initiative", "主动权", 2),
            initial_state_id="pressed_unarmed",
            states=(
                encounter_state(
                    id="pressed_unarmed",
                    title="徒手受压",
                    description="打手把你逼在墙边。地上有一把折刀，但伸手去拿会冒风险。",
                    root=PRESSED_ROOT,
                ),
                encounter_state(
                    id="knife_advantage",
                    title="持刀逼退",
                    description="你已经拿到刀，对方开始后撤。现在你得彻底夺回主动权。",
                    root=KNIFE_ROOT,
                ),
            ),
            transitions=(
                when_clock_full("initiative", effect("set_encounter_act", "act_2"), effect("set_encounter_state", "duel")),
            ),
        ),
        EncounterActDef(
            id="act_2",
            title="拿到优势后终结",
            description="你已经摆脱压制，现在要狠狠干净地收尾。",
            objective_clock=objective_clock("enemy_hp", "敌人血量", 2),
            initial_state_id="duel",
            states=(
                encounter_state(
                    id="duel",
                    title="对峙",
                    description="对方后退半步，准备再扑上来。现在是你拿下这场架的机会。",
                    root=DUEL_ROOT,
                ),
                encounter_state(
                    id="guard_open",
                    title="空门大开",
                    description="他的防守空档已经完全露出来了。狠狠干净地结束这场架。",
                    root=OPEN_ROOT,
                ),
            ),
            transitions=(
                when_clock_empty("enemy_hp", effect("finish_encounter", "success")),
            ),
        ),
    ),
)
