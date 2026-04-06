from __future__ import annotations

from raygame.model.defs import ActionCostDef, ActionMethodDef, ActionPointDef, Condition, Effect, LocationDef, OutcomeDef
from raygame.model.enums import Risk, ScreenName, Suit


CITY_LOCATIONS: dict[str, LocationDef] = {
    "office": LocationDef("office", "事务所", "桌上的信纸和灰烬都还没冷。", ("clear_mind",)),
    "red_light": LocationDef("red_light", "红灯区", "每个消息都有价格。", ("thug_talk", "thug_threat", "informant", "drink_out")),
    "docks": LocationDef("docks", "码头", "风里都是铁锈味。", ("dock_work", "smuggler_tip")),
    "black_market": LocationDef("black_market", "黑市", "缺的东西在这里都有价。", ("buy_cigarettes",)),
    "clinic": LocationDef("clinic", "诊所", "白灯亮得叫人心烦。", ("bandage",)),
    "slaughterhouse": LocationDef("slaughterhouse", "屠宰场", "雨里的门牌像一张还没翻开的底牌。", ("enter_slaughterhouse",)),
}


CITY_ACTIONS: dict[str, ActionPointDef] = {
    "dock_work": ActionPointDef(
        id="dock_work",
        title="搬货打工",
        description="先把今晚的饭钱挣出来。",
        screen=ScreenName.CITY,
        conditions=(Condition("day_at_most", 2),),
        methods=(
            ActionMethodDef(
                id="dock_work_force",
                title="扛起箱子",
                suits=(Suit.FORCE,),
                difficulty=1,
                risk=Risk.LOW,
                description="粗活不需要解释。",
                success=OutcomeDef("这一班干得像台机器。", (Effect("gain_money", 15),)),
                cost=OutcomeDef("挣到了钱，但手臂发酸。", (Effect("gain_money", 10), Effect("add_stress", 1))),
                fail=OutcomeDef("动作慢了半拍，只拿到一点零钱。", (Effect("gain_money", 5),)),
            ),
        ),
    ),
    "thug_talk": ActionPointDef(
        id="thug_talk",
        title="堵路混混·套话",
        description="让他以为你只是来关心人的。",
        screen=ScreenName.CITY,
        conditions=(Condition("day_at_most", 2), Condition("flag_not_set", "clue_a")), 
        methods=(
            ActionMethodDef(
                id="thug_talk_empathy",
                title="好声套话",
                suits=(Suit.EMPATHY,),
                difficulty=2,
                risk=Risk.MID,
                description="让他觉得你真在乎乌鸦的死活。",
                success=OutcomeDef("他吐出一个地名。屠宰场。", (Effect("set_flag", "clue_a"),)),
                cost=OutcomeDef("他松口了，但你也留下了印象。", (Effect("set_flag", "clue_a"), Effect("advance_clock", "heat:1"))),
                fail=OutcomeDef("他嘲笑你，转身就走。", (Effect("add_stress", 2), Effect("insert_card", "panic"))),
            ),
        ),
    ),
    "thug_threat": ActionPointDef(
        id="thug_threat",
        title="堵路混混·威吓",
        description="直接逼他说点有用的。",
        screen=ScreenName.CITY,
        conditions=(Condition("day_at_most", 2), Condition("flag_not_set", "clue_a")),
        methods=(
            ActionMethodDef(
                id="thug_threat_force",
                title="顶到墙上",
                suits=(Suit.FORCE,),
                difficulty=2,
                risk=Risk.MID,
                description="今天没空慢慢谈。",
                success=OutcomeDef("对方怕了，地点到手。", (Effect("set_flag", "clue_a"), Effect("advance_clock", "heat:1"))),
                cost=OutcomeDef("地点是问出来了，街角的人也都记住了你。", (Effect("set_flag", "clue_a"), Effect("advance_clock", "heat:2"))),
                fail=OutcomeDef("动静太大，消息没问到。", (Effect("advance_clock", "heat:2"), Effect("add_stress", 1))),
            ),
        ),
    ),
    "buy_cigarettes": ActionPointDef(
        id="buy_cigarettes",
        title="买烟卷",
        description="黑市小摊总能救急。",
        screen=ScreenName.CITY,
        costs=(ActionCostDef("resource", "money", 10, "金币"),),
        free_text="投入 10 金币，买两根烟卷。",
        free_effects=(Effect("gain_cigarettes", 2),),
    ),
    "informant": ActionPointDef(
        id="informant",
        title="找线人喝酒",
        description="消息总要沾一点酒味。",
        screen=ScreenName.CITY,
        conditions=(Condition("day_at_least", 2), Condition("flag_not_set", "clue_b")),
        methods=(
            ActionMethodDef(
                id="informant_empathy",
                title="陪一杯",
                suits=(Suit.EMPATHY,),
                difficulty=2,
                risk=Risk.MID,
                description="让对方自己把布局说出来。",
                success=OutcomeDef("他在桌面上画出了屠宰场的走廊。", (Effect("set_flag", "clue_b"), Effect("advance_clock", "heat:1"))),
                cost=OutcomeDef("图拿到了，但有人注意到你们聊了什么。", (Effect("set_flag", "clue_b"), Effect("advance_clock", "heat:2"))),
                fail=OutcomeDef("只喝进了劣酒。", (Effect("add_stress", 1),)),
            ),
        ),
    ),
    "drink_out": ActionPointDef(
        id="drink_out",
        title="买醉",
        description="不是解决办法，只是把声音压下去。",
        screen=ScreenName.CITY,
        conditions=(Condition("day_at_least", 2),),
        free_text="移除至多 2 张负面牌，次日少抽 1 张。",
        free_effects=(Effect("remove_negative", 2), Effect("set_flag", "hungover")),
    ),
    "smuggler_tip": ActionPointDef(
        id="smuggler_tip",
        title="打听屠宰场",
        description="看谁会在换班前离岗。",
        screen=ScreenName.CITY,
        conditions=(Condition("day_at_least", 2), Condition("flag_not_set", "clue_c")),
        methods=(
            ActionMethodDef(
                id="smuggler_instinct",
                title="听风向",
                suits=(Suit.INSTINCT,),
                difficulty=3,
                risk=Risk.MID,
                description="码头的风比人更早知道班次。",
                success=OutcomeDef("你摸清了守卫换班，还替乌鸦多争到一点时间。", (Effect("set_flag", "clue_c"), Effect("freeze_clock", 1))),
                cost=OutcomeDef("换班时间问出来了，但要价不低。", (Effect("set_flag", "clue_c"), Effect("spend_money", 10))),
                fail=OutcomeDef("白跑一趟，还被绕得脑袋发紧。", (Effect("add_stress", 2),)),
            ),
        ),
    ),
    "bandage": ActionPointDef(
        id="bandage",
        title="包扎",
        description="把最碍事的伤处理掉。",
        screen=ScreenName.CITY,
        costs=(ActionCostDef("resource", "money", 15, "金币"),),
        free_text="投入 15 金币，移除 1 张物理负面牌。",
        free_effects=(Effect("remove_negative_family", "physical"),),
    ),
    "clear_mind": ActionPointDef(
        id="clear_mind",
        title="整理思绪",
        description="把噪音一张张掀开。",
        screen=ScreenName.CITY,
        free_text="移除 1 张心理负面牌。",
        free_effects=(Effect("remove_negative_family", "mental"),),
    ),
    "enter_slaughterhouse": ActionPointDef(
        id="enter_slaughterhouse",
        title="潜入屠宰场",
        description="不再继续整备，今晚就动手。",
        screen=ScreenName.CITY,
        free_text="直接开始屠宰场任务。",
        special="enter_mission",
    ),
}
