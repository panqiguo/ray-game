INCLUDE ./external.ink

-> start

=== start ===
# 强制审问
门不是被敲开的。

# speaker: 警探
“科尔，你让我们等了一整天。”

# speaker: 科尔
他们没有给你穿外套的时间。一个人按住你的肩膀，另一个人把你从办公室的椅子上拽起来。楼梯扶手撞在肋骨上，疼痛比清晨更早醒来。

~ change_health(-1)

# speaker: 警探
“一个中枪的人死在你这里，你却觉得自己可以睡到自然醒？”

# speaker: 科尔
问询室比昨天更冷。桌上没有水，只有一支铅笔，和一份已经写好结论的笔录。

# speaker: 警探
“姓名、时间、他怎么进来的。按顺序说。还有，别再试着替自己省麻烦。”

# speaker: 科尔
你告诉他男人撞进办公室时已经中枪，告诉他楼下警笛来得太快，告诉他你没有见过开枪的人。

# speaker: 警探
“最后一个问题。他有没有留下什么东西？纸条、名字、地址，任何能让我们少跑几步的东西。”

+ [告诉警察纸条的内容]
    # speaker: 科尔
    你把纸条推过去。它离开手指的一瞬间，你知道自己把下一步路也交出去了一半。

    # speaker: 警探
    “看吧。早这样，你还能少挨一下。”

    ~ set_value("police_investigation_done", "true")
    ~ set_value("police_knows_true_info", "true")
    ~ set_value("police_choice_ready", "false")
    ~ add_value("police_relation", -1)
    -> END

+ [给出一条假线索]
    # speaker: 科尔
    你说了一个地址，一个够真实、够麻烦，也够偏离纸条的地址。

    # speaker: 警探
    “你最好不是在浪费警力，科尔。今天我没什么耐心。”

    ~ set_value("police_investigation_done", "true")
    ~ set_value("police_got_fake_info", "true")
    ~ set_value("police_choice_ready", "false")
    ~ set_value("police_suspicious", "true")
    ~ add_value("police_relation", -1)
    -> END

+ [隐瞒纸条]
    # speaker: 科尔
    “没有。”你说。

    # speaker: 警探
    他笑了一下，没有温度。

    # speaker: 警探
    “你以前穿过这身皮，科尔。你知道沉默不是免费的。今天尤其不是。”

    ~ set_value("police_investigation_done", "true")
    ~ set_value("police_refused_info", "true")
    ~ set_value("police_choice_ready", "false")
    ~ add_value("police_relation", -2)
    -> END
