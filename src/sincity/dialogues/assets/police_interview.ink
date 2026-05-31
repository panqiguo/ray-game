INCLUDE ./external.ink

-> start

=== start ===
# 警方调查
警局的问询室比走廊更冷。桌上有一杯没人喝的水，一支铅笔，和一份已经写好一半的笔录。

# speaker: 警探
“姓名、时间、他怎么进来的。按顺序说，别加你那些侦探味的修辞。”

# speaker: 科尔
你告诉他男人撞进办公室时已经中枪，告诉他楼下警笛来得太快，告诉他你没有见过开枪的人。

~ change_health(-2)

# speaker: 警探
“所以一个快死的人，专门挑了你的办公室当终点。真巧。”

# speaker: 科尔
他要的不是真相，是一份能合上的报告。每个字都像在把责任钉到你桌上。

~ change_energy(-2)

# speaker: 警探
“最后一个问题。他有没有留下什么东西？纸条、名字、地址，任何能让我们少跑几步的东西。”

~ change_health(-2)

+ [告诉警察纸条的内容]
    # speaker: 科尔
    你把纸条推过去。它离开手指的一瞬间，你知道自己把下一步路也交出去了一半。

    # speaker: 警探
    “很好。至少这次你没有浪费我们的时间。”

    # speaker: 科尔
    他说得像夸奖，听起来像威胁。

    ~ set_value("police_investigation_done", "true")
    ~ set_value("police_knows_true_info", "true")
    ~ set_value("police_choice_ready", "false")
    ~ add_value("police_relation", 1)
    -> END

+ [给出一条假线索]
    # speaker: 科尔
    你说了一个地址，一个够真实、够麻烦，也够偏离纸条的地址。

    # speaker: 警探
    “你最好不是在浪费警力，科尔。”

    # speaker: 科尔
    他没有完全相信，但他写下来了。今天，这就够了。

    ~ set_value("police_investigation_done", "true")
    ~ set_value("police_got_fake_info", "true")
    ~ set_value("police_choice_ready", "false")
    ~ add_value("police_relation", -1)
    -> END

+ [隐瞒纸条]
    # speaker: 科尔
    “没有。”你说。

    # speaker: 警探
    他盯着你看了几秒，像在等你自己把谎话咽回去。

    # speaker: 警探
    “你以前穿过这身皮，科尔。你知道沉默不是免费的。”

    ~ set_value("police_investigation_done", "true")
    ~ set_value("police_refused_info", "true")
    ~ set_value("police_choice_ready", "false")
    ~ add_value("police_relation", -1)
    -> END
