from __future__ import annotations

from dataclasses import dataclass

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


def local_clock(id: str, title: str, segments: int):
    return clock(id=id, title=title, segments=segments)


def when_clock_full(source: str, *effects):
    return EncounterTransitionDef(kind="clock_full", source=source, effects=effects)


def when_clock_empty(source: str, *effects):
    return EncounterTransitionDef(kind="clock_empty", source=source, effects=effects)


@dataclass(frozen=True)
class StateSpec:
    id: str
    title: str
    description: str
    root_id: str
    action_keys: tuple[str, ...]


def counter_action(action_id: str, description: str, *, reward: int = 1, fail_text: str = "你还是没完全顶住。"):
    return encounter_action(
        id=action_id,
        title="防守反击",
        description=description,
        check=check(
            suits=(Suit.REASON, Suit.EMPATHY),
            risk=Risk.LOW,
            success=outcome("你稳稳顶住了节奏。", effect("advance_encounter_clock", f"initiative:{reward}")),
            cost=outcome("你至少没有继续吃亏。", effect("advance_encounter_clock", "initiative:1")),
            fail=outcome(fail_text, effect("change_health", -1)),
        ),
    )


def punch_action(action_id: str, description: str):
    return encounter_action(
        id=action_id,
        title="直接挥拳",
        description=description,
        check=check(
            suits=(Suit.FORCE,),
            risk=Risk.HIGH,
            success=outcome("你狠狠干出了一步空间。", effect("advance_encounter_clock", "initiative:2")),
            cost=outcome("你砸中了他，但也只是暂时逼开。", effect("advance_encounter_clock", "initiative:1")),
            fail=outcome("你被他顶了回来。", effect("change_health", -1)),
        ),
    )


def rush_knife_action():
    return encounter_action(
        id="thug_rush_knife",
        title="扑向折刀",
        description="你冒险扑向地上的折刀，想先把局势翻过来。",
        effects=(effect("change_health", -1),),
        check=check(
            suits=(Suit.INSTINCT, Suit.FORCE),
            risk=Risk.HIGH,
            success=outcome(
                "你手已经摸到刀柄了。",
                effect("advance_encounter_clock", "knife:1"),
            ),
            cost=outcome(
                "你拖着伤抢到了第一步位置。",
                effect("advance_encounter_clock", "knife:1"),
            ),
            fail=outcome("你扑过去了，但还没真正把刀抢出来。"),
        ),
    )


def knife_press_action():
    return encounter_action(
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
    )


def heavy_punch_action(action_id: str):
    return encounter_action(
        id=action_id,
        title="重拳追击",
        description="你不给他喘气空间，直接压上去狠狠干。",
        check=check(
            suits=(Suit.FORCE,),
            risk=Risk.MID,
            success=outcome("你狠狠干中了一拳。", effect("damage_encounter_clock", "enemy_hp:1")),
            cost=outcome("你打实了一下，但他还撑着。", effect("damage_encounter_clock", "enemy_hp:1")),
            fail=outcome("你被他架住了。", effect("change_health", -1)),
        ),
    )


def feint_probe_action(action_id: str, description: str, *, next_state: str | None):
    effects = [effect("advance_encounter_clock", "opening:1")]
    if next_state is not None:
        effects.append(effect("set_encounter_state", next_state))
    return encounter_action(
        id=action_id,
        title="假动作试探",
        description=description,
        check=check(
            suits=(Suit.EMPATHY, Suit.INSTINCT),
            risk=Risk.MID,
            success=outcome("他的防守被你骗得动了一下。", *effects),
            cost=outcome("他开始有点被你带着走。", *effects),
            fail=outcome("他没上当。"),
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


def finisher_action():
    return encounter_action(
        id="thug_finisher_open",
        title="终结一击",
        description="你抓住空门，一击把他放倒。",
        check=check(
            suits=(Suit.FORCE,),
            risk=Risk.LOW,
            success=outcome("你干净利落地结束了这场架。", effect("damage_encounter_clock", "enemy_hp:2")),
            cost=outcome("你一击放倒了他。", effect("damage_encounter_clock", "enemy_hp:2")),
            fail=outcome("没打实，但已经足够。", effect("damage_encounter_clock", "enemy_hp:1")),
        ),
    )


def breathe_action(action_id: str):
    return encounter_action(
        id=action_id,
        title="喘息一下",
        description="你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。",
        effects=(effect("reset_hand", True), effect("change_health", -1)),
    )


def build_shared_action(key: str, state_id: str):
    if key == "breathe":
        return breathe_action(f"thug_breathe_{state_id}")
    raise AssertionError(f"Unknown shared thug action: {key}")


ACT_1_ACTIONS = {
    "counter_pressed": counter_action("thug_counter_pressed", "你先稳住头脸和脚步，再找机会把他顶开。"),
    "punch_pressed": punch_action("thug_punch_pressed", "你不跟他磨，直接狠狠干出一步空间。"),
    "rush_knife": rush_knife_action(),
    "counter_knife": counter_action("thug_counter_knife", "你先稳住刀势和身位，再找机会彻底压住他。"),
    "knife_press": knife_press_action(),
}


ACT_1_STATES = (
    StateSpec(
        id="pressed_unarmed",
        title="徒手受压",
        description="打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干，还是冒险把折刀夺到手。",
        root_id="pressed_root",
        action_keys=("counter_pressed", "punch_pressed", "rush_knife", "breathe"),
    ),
    StateSpec(
        id="knife_advantage",
        title="持刀逼退",
        description="刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。",
        root_id="knife_advantage_root",
        action_keys=("counter_knife", "knife_press", "breathe"),
    ),
)


ACT_2_ACTIONS = {
    "heavy_punch_duel": heavy_punch_action("thug_heavy_punch_duel"),
    "feint_duel": feint_probe_action("thug_feint_duel", "你做一个假动作，先试着把他的防守骗开一层。", next_state=None),
    "kick_duel": knee_kick_action("thug_kick_knee_duel", "你不追求漂亮，而是直接踹他的支撑腿。"),
    "finisher": finisher_action(),
    "kick_open": knee_kick_action("thug_kick_knee_open", "你直接踹他的支撑腿，狠狠干净利落地结束。"),
}


ACT_2_STATES = (
    StateSpec(
        id="duel",
        title="对峙",
        description="对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。",
        root_id="duel_root",
        action_keys=("heavy_punch_duel", "feint_duel", "kick_duel", "breathe"),
    ),
    StateSpec(
        id="guard_open",
        title="空门大开",
        description="他的防守空档已经完全露出来了。狠狠干净地结束这场架。",
        root_id="open_root",
        action_keys=("finisher", "kick_open", "breathe"),
    ),
)


def build_state(spec: StateSpec, action_defs: dict[str, object]) -> EncounterStateDef:
    actions = []
    for key in spec.action_keys:
        if key in action_defs:
            actions.append(action_defs[key])
            continue
        actions.append(build_shared_action(key, spec.id))
    root, _ = encounter_root(
        id=spec.root_id,
        actions=tuple(actions),
    )
    return encounter_state(
        id=spec.id,
        title=spec.title,
        description=spec.description,
        root=root,
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
            states=tuple(build_state(spec, ACT_1_ACTIONS) for spec in ACT_1_STATES),
            clocks=(local_clock("knife", "夺刀", 2),),
            transitions=(
                when_clock_full("knife", effect("set_encounter_state", "knife_advantage")),
                when_clock_full("initiative", effect("set_encounter_act", "act_2"), effect("set_encounter_state", "duel")),
            ),
        ),
        EncounterActDef(
            id="act_2",
            title="拿到优势后终结",
            description="你已经摆脱压制，现在要狠狠干净地收尾。",
            objective_clock=objective_clock("enemy_hp", "敌人血量", 2),
            initial_state_id="duel",
            states=tuple(build_state(spec, ACT_2_ACTIONS) for spec in ACT_2_STATES),
            clocks=(local_clock("opening", "破绽", 2),),
            transitions=(
                when_clock_full("opening", effect("set_encounter_state", "guard_open")),
                when_clock_empty("enemy_hp", effect("finish_encounter", "success")),
            ),
        ),
    ),
)
