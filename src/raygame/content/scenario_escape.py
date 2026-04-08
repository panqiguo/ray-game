from __future__ import annotations

from raygame.content.builders import (
    action,
    compile_scenario,
    clock,
    condition,
    resource,
    delivery_action,
    effect,
    explore_action,
    item_input,
    location,
    outcome,
    rest_action,
    scenario,
    shop_purchase,
    single_use_action,
    threshold,
    check,
    limited_use_action,
)
from raygame.model.defs import CompiledScenario
from raygame.model.enums import Risk, ScreenName, Suit


def build_escape_scenario() -> CompiledScenario:
    inn, inn_clocks = location(
        id="inn",
        title="旅社",
        description="床垫薄得像在提醒你别睡太死。",
        position=(28, 12),
        actions=(
            rest_action(
                id="inn_sleep",
                title="住一晚",
                description="花钱买一点真正的休息。",
                screen=ScreenName.CITY,
                inputs=(resource("money", 20, "金币"),),
                effects=(effect("change_health", 2),),
            ),
        ),
    )

    bridge, bridge_clocks = location(
        id="bridge",
        title="桥洞",
        description="挡风不挡潮，也挡不住梦里的脚步声。",
        position=(242, 34),
        actions=(
            rest_action(
                id="bridge_sleep",
                title="蜷着睡",
                description="不用花钱，但心会越睡越绷。",
                screen=ScreenName.CITY,
                effects=(effect("change_stress", 2),),
            ),
        ),
    )

    clinic, clinic_clocks = location(
        id="clinic",
        title="诊所",
        description="医生不问太多，只看你有没有钱。",
        position=(468, 18),
        actions=(
            delivery_action(
                id="clinic_treat",
                title="缝合伤口",
                description="花钱处理伤和创伤。",
                screen=ScreenName.CITY,
                inputs=(resource("money", 30, "金币"),),
                effects=(effect("change_health", 2),),
            ),
        ),
    )

    bar, bar_clocks = location(
        id="bar",
        title="酒吧",
        description="消息和劳力都能在这里兑成现钱。",
        position=(690, 42),
        actions=(
            limited_use_action(
                id="bar_work",
                title="做服务生",
                description="挤在噪音里赚一点钱。",
                screen=ScreenName.CITY,
                uses=3,
                check=check(
                    suits=(Suit.EMPATHY, Suit.REASON),
                    difficulty=2,
                    risk=Risk.LOW,
                    success=outcome("今晚还算顺利。", effect("change_resource", "money:20")),
                    cost=outcome("钱拿到了，但耳朵还在嗡。", effect("change_resource", "money:15"), effect("change_stress", 1)),
                    fail=outcome("被人呼来喝去了一整晚。", effect("change_resource", "money:10"), effect("change_stress", 2)),
                ),
            ),
            delivery_action(
                id="bar_drink",
                title="喝两杯",
                description="把脑子里的声音压低一点。",
                screen=ScreenName.CITY,
                inputs=(resource("money", 15, "金币"),),
                effects=(effect("change_stress", -2),),
            ),
        ),
    )

    slum, slum_clocks = location(
        id="slum_street",
        title="贫民窟街道",
        description="想活下去，先得弄清这里谁在说话。",
        position=(52, 144),
        actions=(
            explore_action(
                id="slum_explore",
                title="打听这里",
                description="一点点摸熟这片街区。",
                screen=ScreenName.CITY,
                clock_id="slum_knowledge",
                clock_title="贫民窟了解",
                segments=4,
                check=check(
                    suits=(Suit.EMPATHY, Suit.INSTINCT),
                    difficulty=2,
                    risk=Risk.MID,
                    success=outcome("你摸到了一条新路。"),
                    cost=outcome("知道了点东西，也被人记住了。", effect("change_stress", 1)),
                    fail=outcome("这里还不认你。", effect("change_stress", 1)),
                ),
                thresholds=(
                    threshold(2, effect("reveal_location", "warehouse"), effect("reveal_location", "repair_shop")),
                    threshold(4, effect("reveal_location", "black_market_doctor"), effect("hide_location", "slum_street")),
                ),
            ),
            action(
                id="slum_watch",
                title="盯住巷口",
                description="不问人，只记住谁在什么时候出现。",
                screen=ScreenName.CITY,
                check=check(
                    suits=(Suit.INSTINCT, Suit.REASON),
                    difficulty=2,
                    risk=Risk.MID,
                    success=outcome("你摸清了几条出入的路。"),
                    cost=outcome("你等到了点东西，也让自己更紧绷。", effect("change_stress", 1)),
                    fail=outcome("你只看见雨水和关上的门。"),
                ),
                effects=(effect("advance_clock", "slum_knowledge:1"),),
                linked_clock_ids=("slum_knowledge",),
            ),
        ),
    )

    residential, residential_clocks = location(
        id="residential",
        title="居民区",
        description="这里白天安静，夜里却什么都可能卖。",
        position=(286, 126),
        actions=(
            explore_action(
                id="residential_explore",
                title="观察这里",
                description="看看哪些门会在合适的时候打开。",
                screen=ScreenName.CITY,
                clock_id="residential_knowledge",
                clock_title="居民区了解",
                segments=4,
                check=check(
                    suits=(Suit.REASON, Suit.INSTINCT),
                    difficulty=2,
                    risk=Risk.LOW,
                    success=outcome("你记住了这里的节奏。"),
                    cost=outcome("你看见了点门道，但也更累了。", effect("change_stress", 1)),
                    fail=outcome("这片地方还没把你算成自己人。"),
                ),
                thresholds=(
                    threshold(2, effect("reveal_location", "restaurant"), effect("reveal_location", "trading_center")),
                    threshold(4, effect("hide_location", "residential")),
                ),
            ),
            action(
                id="residential_chat",
                title="和街坊套近乎",
                description="换一种更柔和的方式摸清这里的人情。",
                screen=ScreenName.CITY,
                check=check(
                    suits=(Suit.EMPATHY, Suit.REASON),
                    difficulty=2,
                    risk=Risk.LOW,
                    success=outcome("你从闲聊里拼出了新的门路。"),
                    cost=outcome("消息到手了，但也欠下了点人情。", effect("change_stress", 1)),
                    fail=outcome("他们礼貌地看着你，却什么都没说。"),
                ),
                effects=(effect("advance_clock", "residential_knowledge:1"),),
                linked_clock_ids=("residential_knowledge",),
            ),
        ),
    )

    hotel, hotel_clocks = location(
        id="hotel",
        title="酒店",
        description="门童先看衣料，再决定你是不是个人。",
        position=(916, 20),
        actions=(
            single_use_action(
                id="hotel_entry",
                title="取得许可",
                description="至少得看起来像个客人。",
                screen=ScreenName.CITY,
                inputs=(item_input("clothes", 1, "华美的衣服", consume=False),),
                effects=(effect("reveal_location", "grand_hotel"),),
            ),
        ),
    )

    warehouse, warehouse_clocks = location(
        id="warehouse",
        title="仓库",
        description="有活就代表有钱，只是钱总比力气轻。",
        position=(510, 152),
        actions=(
            limited_use_action(
                id="warehouse_shift",
                title="扛包裹",
                description="靠旧伤去换眼前这顿饭。",
                screen=ScreenName.CITY,
                uses=3,
                check=check(
                    suits=(Suit.FORCE,),
                    difficulty=2,
                    risk=Risk.MID,
                    success=outcome("你把活干完了。", effect("change_resource", "money:35")),
                    cost=outcome("钱到手了，伤口也跟着开口。", effect("change_resource", "money:25"), effect("change_health", -1)),
                    fail=outcome("你差点把人和货一起砸了。", effect("change_stress", 1)),
                ),
            ),
        ),
        conditions=(condition("location_visible", "warehouse"),),
    )

    repair_shop, repair_clocks = location(
        id="repair_shop",
        title="机械修理厂",
        description="老板不会白借车，也不会白相信人。",
        position=(744, 132),
        actions=(
            single_use_action(
                id="repair_request",
                title="说想离开这里",
                description="老板给了你两个选择：押金，或者替他解决麻烦。",
                screen=ScreenName.CITY,
                effects=(effect("reveal_location", "repair_job_scene"),),
            ),
            delivery_action(
                id="repair_deposit",
                title="交 300 块押金",
                description="用现钱买一次机会。",
                screen=ScreenName.CITY,
                inputs=(resource("money", 300, "金币"),),
                effects=(effect("give_item", "car_key:1"), effect("hide_action", "repair_deposit"), effect("hide_action", "repair_handover")),
            ),
            delivery_action(
                id="repair_handover",
                title="交还任务东西",
                description="把老板要的东西带回来。",
                screen=ScreenName.CITY,
                inputs=(item_input("repair_case_item", 1, "任务道具"),),
                effects=(effect("give_item", "car_key:1"), effect("hide_action", "repair_deposit"), effect("hide_action", "repair_handover")),
            ),
            delivery_action(
                id="leave_town",
                title="开车离开",
                description="钥匙已经在你手里，再不走就太晚了。",
                screen=ScreenName.CITY,
                inputs=(item_input("car_key", 1, "车钥匙", consume=False),),
                effects=(effect("end_run", "escape_success"),),
                conditions=(condition("has_item", "car_key"),),
            ),
        ),
        conditions=(condition("location_visible", "repair_shop"),),
    )

    black_market_doctor, black_market_clocks = location(
        id="black_market_doctor",
        title="黑市医生",
        description="他下手更狠，也更便宜。",
        position=(84, 272),
        actions=(
            delivery_action(
                id="black_market_patch",
                title="便宜处理一下",
                description="花更少的钱，但过程一点都不好看。",
                screen=ScreenName.CITY,
                inputs=(resource("money", 15, "金币"),),
                effects=(effect("change_health", 1), effect("change_stress", 1)),
            ),
        ),
        conditions=(condition("location_visible", "black_market_doctor"),),
    )

    restaurant, restaurant_clocks = location(
        id="restaurant",
        title="餐厅",
        description="热汤不一定能救命，但能让手别抖得那么厉害。",
        position=(332, 258),
        actions=(
            delivery_action(
                id="restaurant_meal",
                title="吃一顿热饭",
                description="让人先像个人一会儿。",
                screen=ScreenName.CITY,
                inputs=(resource("money", 18, "金币"),),
                effects=(effect("change_stress", -2),),
            ),
        ),
        conditions=(condition("location_visible", "restaurant"),),
    )

    trading_center, trading_clocks = location(
        id="trading_center",
        title="交易中心",
        description="什么都能买到，前提是你有钱。",
        position=(588, 282),
        actions=(
            shop_purchase(
                id="buy_clothes",
                title="买华美的衣服",
                description="先把自己包装得像能进门的人。",
                screen=ScreenName.CITY,
                price=80,
                item_id="clothes",
                item_label="华美的衣服",
            ),
            shop_purchase(
                id="buy_gun",
                title="买枪",
                description="有些门开不开，和手里有没有响的东西有关。",
                screen=ScreenName.CITY,
                price=120,
                item_id="gun",
                item_label="枪",
            ),
        ),
        conditions=(condition("location_visible", "trading_center"),),
    )

    grand_hotel_private_room, grand_hotel_private_room_clocks = location(
        id="grand_hotel_private_room",
        title="包间",
        description="厚门一关，谈价和求人的声音都会变得更低。",
        actions=(
            single_use_action(
                id="grand_hotel_client",
                title="接一桩委托",
                description="有人愿意花钱让你找回丢掉的东西。",
                screen=ScreenName.CITY,
                effects=(effect("reveal_location", "client_case_scene"),),
            ),
        ),
        conditions=(condition("has_item", "clothes"),),
    )

    grand_hotel, grand_hotel_clocks = location(
        id="grand_hotel",
        title="高档酒店",
        description="这里的人不会自己说真话，但会花钱让别人替他们找。",
        position=(962, 146),
        children=(grand_hotel_private_room,),
        conditions=(condition("location_visible", "grand_hotel"),),
    )

    repair_job_scene, repair_job_clocks = location(
        id="repair_job_scene",
        title="修理厂委托现场",
        description="老板说的麻烦就在这儿。",
        position=(824, 264),
        actions=(
            single_use_action(
                id="solve_repair_case",
                title="处理麻烦",
                description="把事办妥，再把东西带回去。",
                screen=ScreenName.CITY,
                check=check(
                    suits=(Suit.REASON, Suit.FORCE),
                    difficulty=3,
                    risk=Risk.MID,
                    success=outcome("你把麻烦处理干净了。", effect("give_item", "repair_case_item:1")),
                    cost=outcome("东西拿到了，但你也挂了彩。", effect("give_item", "repair_case_item:1"), effect("change_health", -1)),
                    fail=outcome("你被赶了出来。", effect("change_stress", 2)),
                ),
                effects=(effect("hide_location", "repair_job_scene"),),
            ),
        ),
        conditions=(condition("location_visible", "repair_job_scene"),),
    )

    client_case_scene, client_case_clocks = location(
        id="client_case_scene",
        title="酒店委托现场",
        description="富人的麻烦通常只是更贵一点。",
        position=(1048, 276),
        actions=(
            single_use_action(
                id="solve_client_case",
                title="完成委托",
                description="把丢掉的东西带回去。",
                screen=ScreenName.CITY,
                check=check(
                    suits=(Suit.EMPATHY, Suit.REASON),
                    difficulty=3,
                    risk=Risk.LOW,
                    success=outcome("委托办成了。", effect("change_resource", "money:180")),
                    cost=outcome("事情办成了，但你几乎榨干了自己。", effect("change_resource", "money:140"), effect("change_stress", 1)),
                    fail=outcome("你空手而归。", effect("change_stress", 2)),
                ),
                effects=(effect("hide_location", "client_case_scene"),),
            ),
        ),
        conditions=(condition("location_visible", "client_case_scene"),),
    )

    clocks = (
        clock(id="pursuit", title="被追击", segments=6, thresholds=(threshold(6, effect("end_run", "caught")),)),
        *inn_clocks,
        *bridge_clocks,
        *clinic_clocks,
        *bar_clocks,
        *slum_clocks,
        *residential_clocks,
        *hotel_clocks,
        *warehouse_clocks,
        *repair_clocks,
        *black_market_clocks,
        *restaurant_clocks,
        *trading_clocks,
        *grand_hotel_clocks,
        *grand_hotel_private_room_clocks,
        *repair_job_clocks,
        *client_case_clocks,
    )

    scenario_def = scenario(
        id="escape",
        title="逃离这里",
        screen=ScreenName.CITY,
        roots=(
            inn,
            bridge,
            clinic,
            bar,
            slum,
            residential,
            hotel,
            warehouse,
            repair_shop,
            black_market_doctor,
            restaurant,
            trading_center,
            grand_hotel,
            repair_job_scene,
            client_case_scene,
        ),
        clocks=clocks,
        initial_visible_locations=("inn", "bridge", "clinic", "bar", "slum_street", "residential", "hotel"),
        initial_visible_clocks=("pursuit", "slum_knowledge", "residential_knowledge"),
        initial_health=6,
        initial_stress=4,
        initial_money=0,
        initial_cigarettes=0,
        initial_inventory={},
        initial_growth_choices=(),
    )
    return compile_scenario(scenario_def)


SCENARIO = build_escape_scenario()
