;; Nightingale chapter 1 story state and action helpers.
;; Exports: nightingale-vars, nightingale-reacts, nightingale-tasks,
;;          nightingale-* location action helpers.

(define nightingale-opening-text
  "# 保护夜莺\n\n# speaker: 科尔\n首演前一天，剧院的人把话递到我门口，说夜莺收到了威胁。\n\n# speaker: 科尔\n这座城里会写恐吓信的人不少，真正麻烦的是总有人愿意替他们把信送到地方。\n\n# speaker: 科尔\n先去剧院。别让整座城太早吵起来。")

(define nightingale-guard-text
  "# 剧院前门\n\n# speaker: 保安\n“科尔？里面等你。别到处乱走，今晚每个人都在假装自己没听说那封信。”\n\n# speaker: 科尔\n他说完往舞台方向让开半步。不是欢迎，是把麻烦递给下一个人。")

(define nightingale-stage-text
  "# 排练中的夜莺\n\n（以后这里会播放一段排练动画：舞台空着大半，灯光像一把冷刀落下来。夜莺唱了两句，声音在空剧场里悬住，又忽然停下。）\n\n# speaker: 夜莺\n“你就是科尔？”\n\n# speaker: 科尔\n“如果你收到的是第一封威胁信，我会说先别紧张。”\n\n# speaker: 夜莺\n她把信递过来，指尖很稳。\n\n# speaker: 夜莺\n“那就别这么说。这是第二封，刚刚才送到。”\n\n# speaker: 科尔\n第二封。送信的人还没走远，或者以为自己已经走远。")

(define nightingale-search-half-text
  "# 搜查剧院\n\n# speaker: 科尔\n后台门口有人踩过湿泥。不是演员的鞋，也不像负责搬道具的工人。\n\n# speaker: 科尔\n化妆室那边也许能看见信件经过哪里被交到手上。")

(define nightingale-shadow-text
  "# 可疑人影\n\n# speaker: 科尔\n后巷门缝晃了一下。有人站在雨里，像在确认信已经送到，又像在等另一个信号。\n\n# speaker: 科尔\n这次不能让他慢慢消失。")

(define nightingale-wakeup-text
  "# 醒来\n\n（以后这里会播放一段追逐后的短动画：你追上那个人，手已经碰到面具边缘。下一秒，后脑一阵钝响，剧院灯光像被水冲散。）\n\n# speaker: 夜莺\n“别动。你流了血。”\n\n# speaker: 科尔\n她坐在旁边，妆已经卸了一半，声音比舞台上低得多。\n\n# speaker: 夜莺\n“你追上了他。至少在被人从背后敲倒之前。”\n\n# speaker: 科尔\n这不算安慰，但比谎话好。等她离开，天已经亮了。城市终于重新把门打开。")

(define nightingale-letter-room-text
  "# 第一封威胁信\n\n# speaker: 科尔\n信纸沾着煤灰，折痕像从粗糙口袋里掏出来过不止一次。措辞故意学得像码头人的脾气，可里面有些细节太近后台了。\n\n# speaker: 科尔\n旧码头的味道是真的，剧院内部的眼睛也是真的。问题只是它们谁先动了手。")

(define nightingale-manager-text
  "# 剧院经理\n\n# speaker: 经理\n“首演不是普通演出。赞助、宣传、慈善名单，全都压在这一晚。旧码头那边的人要是闹起来，报纸会先写我们办事不周。”\n\n# speaker: 科尔\n他担心的是场面和票房，不是夜莺。但场面本身就是线索。")

(define nightingale-publicist-text
  "# 宣传口风\n\n# speaker: 宣传人员\n“这场首演是城市更新的招牌。旧码头、慈善晚宴、名人照片，报纸已经排好了版。”\n\n# speaker: 科尔\n把旧码头写进宣传词的人，通常不会去看那地方真正长什么样。")

(define nightingale-stagehand-text
  "# 后台工人\n\n# speaker: 后台工人\n“近两周总有人在后门打听首演流程，像怕错过什么时点。还有人提过莱恩，说他喝醉时什么脏话都敢往夜莺头上砸。”\n\n# speaker: 科尔\n名字终于落地了。莱恩。")

(define nightingale-stall-text
  "# 街头跑腿\n\n# speaker: 摊贩\n“有个湿透的小子拿着封信跑过这条街，像赶着把自己卖掉一样。往剧院那边去的，鞋底全是黑泥。”\n\n# speaker: 科尔\n不是剧院里的人自己送的。但信是被城市的手转过去的。")

(define nightingale-market-text
  "# 买来的线索\n\n# speaker: 黑市掌柜\n“钱给够，我就多想起来一点。那小子不是一个人跑的，背后有人按段付钱，信纸和煤灰也不是剧院自己的东西。”\n\n# speaker: 科尔\n消息被他切成几片卖。难看，但有用。")

(define nightingale-restaurant-done-text
  "# 饭摊老板终于说完\n\n# speaker: 摊贩\n“送信的小孩在我这儿吃过两回。他每次都坐边上，像怕有人从巷口出来认出他。最后一次，他提到剧院后巷，还提到旧码头那边有人给钱。”\n\n# speaker: 科尔\n老板把这句话拆成六顿饭。现在它终于能连起来。")

(define nightingale-bar-text
  "# 小报记者\n\n# speaker: 小报记者\n“首演、慈善、旧码头改造，这三个词绑在一起卖得最好。夜莺唱得越高，下面的人看起来就越像被踩在舞台灯底下。”\n\n# speaker: 科尔\n他还提到了莱恩。像提一个已经被写进草稿、只等警方盖章的名字。")

(define nightingale-waste-text
  "# 底层传递链\n\n# speaker: 跑腿少年\n“有人给钱，让我去认认路，别真去敲门。我只知道信最后会到剧院后巷，拿钱的人口音像码头那边。”\n\n# speaker: 科尔\n送信人不是主谋，只是这条链上最便宜的一节。")

(define nightingale-first-letter-done-text
  "# 第一封信的方向\n\n# speaker: 科尔\n纸、灰、递送方式都把线头往旧码头推，可那份对后台节奏的熟悉又不像外人能随手编出来的。\n\n# speaker: 科尔\n威胁不是凭空写出来的。它长了两张脸：一张朝着旧码头，一张看着剧院里面。")

(define nightingale-trust-loss-text
  "# 夜莺的信任\n\n# speaker: 科尔\n时间拖得太久，剧院那边开始怀疑我是不是还能控制局面。夜莺没有催促，但沉默本身已经是一种回答。")

(define nightingale-trust-fail-text
  "# 委托失败\n\n# speaker: 科尔\n夜莺不再等我。剧院把材料交给警方，把门也一并关上。\n\n# speaker: 科尔\n这座城市里，失去信任有时候比失去线索更快。")

(define nightingale-lore-text
  "# 莱恩这个名字\n\n# speaker: 科尔\n经理怕丑闻，宣传怕掉版面，后台工人怕出人命。三种怕拼在一起，只留下同一个名字：莱恩。\n\n# speaker: 科尔\n到目前为止，他更像个被推到台前的嫌疑人，而不是全部答案。")

(define nightingale-second-letter-alert-text
  "# 第二封信的踪迹\n\n# speaker: 剧院代理人\n“刚有人来报，第二封信已经在路上。你之前安插的线人盯到了送信的影子，就在剧院后巷附近。”\n\n# speaker: 科尔\n信终于从纸上站起来了。")

(define nightingale-second-letter-fail-text
  "# 剧院绕过你\n\n# speaker: 剧院经理\n“信已经进来了，我们只能先交给警方。”\n\n# speaker: 科尔\n我慢了一步。现在剧院和警局之间，又多了一份不经过我的材料。")

(define nightingale-vars
  (list
    (var 'nightingale_theater_unlocked true)
    (var 'nightingale_front_done false)
    (var 'nightingale_commission_taken false)
    (var 'nightingale_theater_search (clock :title "剧院搜查" :desc "在剧院里追查第二封威胁信刚刚经过的路线。" :initial 0 :max 4))
    (var 'nightingale_search_half_seen false)
    (var 'nightingale_shadow_seen false)
    (var 'nightingale_first_confrontation_done false)
    (var 'nightingale_city_day_started false)
    (var 'nightingale_clinic_unlocked false)
    (var 'nightingale_stall_unlocked false)
    (var 'nightingale_market_unlocked false)
    (var 'nightingale_bar_unlocked false)
    (var 'nightingale_waste_unlocked false)
    (var 'nightingale_letter_checked false)
    (var 'nightingale_stall_checked false)
    (var 'nightingale_market_checked false)
    (var 'nightingale_restaurant_talk (clock :title "饭摊老板的半句话" :desc "老板每次只肯多说一点。多吃几顿饭，他才会把送信人的路线讲完整。" :initial 0 :max 6))
    (var 'nightingale_restaurant_done false)
    (var 'nightingale_bar_checked false)
    (var 'nightingale_waste_checked false)
    (var 'nightingale_manager_talked false)
    (var 'nightingale_publicist_talked false)
    (var 'nightingale_stagehand_talked false)
    (var 'nightingale_first_letter_progress (clock :title "威胁信调查" :desc "顺着纸张、递送链和口风，查清第一封信背后的方向。" :initial 0 :max 4))
    (var 'nightingale_first_letter_done false)
    (var 'nightingale_first_letter_due_day 0)
    (var 'nightingale_trust (clock :title "夜莺的信任" :desc "拖得越久，夜莺和剧院越会怀疑你是否还能保护她。降到 0 时委托失败。" :initial 8 :max 8))
    (var 'nightingale_trust_initialized false)
    (var 'nightingale_trust_checked_day 0)
    (var 'nightingale_trust_failed false)
    (var 'nightingale_lore_progress (clock :title "夜莺的传说" :desc "经理、宣传、工人——每个人都记得一部分关于夜莺的传闻。拼起来就是一个完整的故事。" :initial 0 :max 3))
    (var 'nightingale_lore_known false)
    (var 'nightingale_docks_direction_known false)
    (var 'nightingale_second_letter_ready false)
    (var 'nightingale_second_letter_trigger_day 0)
    (var 'nightingale_second_letter_harder false)
    (var 'nightingale_second_letter_intercepted false)
    (var 'nightingale_second_letter_failed false)
    (var 'nightingale_second_letter_delivered false)))

(define nightingale-reacts
  (list
    (react
      :when (and (>= (clock-value nightingale_theater_search) 2) (not nightingale_search_half_seen))
      :then (list
        (effect 'set nightingale_search_half_seen true)
        (effect 'start-quick-dialogue nightingale-search-half-text)))
    (react
      :when (and (clock-filled? nightingale_theater_search) (not nightingale_shadow_seen))
      :then (list
        (effect 'set nightingale_shadow_seen true)
        (effect 'start-quick-dialogue nightingale-shadow-text)))
    (react
      :when (and nightingale_first_confrontation_done (not nightingale_city_day_started))
      :then (list
        (effect 'set nightingale_city_day_started true)
        (effect 'set nightingale_clinic_unlocked true)
        (effect 'set nightingale_stall_unlocked true)
        (effect 'start-quick-dialogue nightingale-wakeup-text)))
    (react
      :when (and nightingale_stall_checked (not nightingale_market_unlocked))
      :then (list
        (effect 'set nightingale_market_unlocked true)))
    (react
      :when (and (clock-filled? nightingale_restaurant_talk) (not nightingale_restaurant_done))
      :then (list
        (effect 'set nightingale_restaurant_done true)
        (effect 'clock+ nightingale_first_letter_progress 1)
        (effect 'start-quick-dialogue nightingale-restaurant-done-text)))
    (react
      :when (and nightingale_market_checked (not nightingale_bar_unlocked))
      :then (list
        (effect 'set nightingale_bar_unlocked true)))
    (react
      :when (and (or nightingale_bar_checked nightingale_first_letter_done) (not nightingale_waste_unlocked))
      :then (list
        (effect 'set nightingale_waste_unlocked true)))
    (react
      :when (and nightingale_commission_taken (= nightingale_first_letter_due_day 0))
      :then (list
        (effect 'set nightingale_first_letter_due_day (+ day 3))
        (effect 'set nightingale_trust_checked_day day)))
    (react
      :when (and nightingale_city_day_started (not nightingale_trust_initialized))
      :then (list
        (effect 'set nightingale_trust_initialized true)
        (effect 'clock+ nightingale_trust 8)))
    (react
      :when (and nightingale_city_day_started
                 (not nightingale_first_letter_done)
                 (> nightingale_first_letter_due_day 0)
                 (> day nightingale_first_letter_due_day)
                 (> day nightingale_trust_checked_day)
                 (> (clock-value nightingale_trust) 0))
      :then (list
        (effect 'clock- nightingale_trust 1)
        (effect 'set nightingale_trust_checked_day day)
        (effect 'start-quick-dialogue nightingale-trust-loss-text)))
    (react
      :when (and nightingale_city_day_started
                 (not nightingale_first_letter_done)
                 (clock-empty? nightingale_trust)
                 (not nightingale_trust_failed))
      :then (list
        (effect 'set nightingale_trust_failed true)
        (effect 'end-game "委托失败" "夜莺不再信任你，剧院把威胁信交给警方。保护夜莺的委托到此结束。")))
    (react
      :when (and nightingale_stall_checked nightingale_market_checked nightingale_restaurant_done (not nightingale_first_letter_done))
      :then (list
        (effect 'set nightingale_first_letter_done true)
        (effect 'set nightingale_docks_direction_known true)
        (effect 'clock+ nightingale_trust 3)
        (effect 'start-quick-dialogue nightingale-first-letter-done-text)))
    (react
      :when (and (clock-filled? nightingale_lore_progress) (not nightingale_lore_known))
      :then (list
        (effect 'set nightingale_lore_known true)
        (effect 'start-quick-dialogue nightingale-lore-text)))
    (react
      :when (and nightingale_commission_taken
                 (not nightingale_second_letter_ready)
                 (> nightingale_first_letter_due_day 0)
                 (>= day nightingale_first_letter_due_day))
      :then (append
        (list
          (effect 'set nightingale_second_letter_ready true)
          (effect 'set nightingale_second_letter_trigger_day day)
          (effect 'start-quick-dialogue nightingale-second-letter-alert-text))
        (if (not nightingale_first_letter_done)
          (list (effect 'set nightingale_second_letter_harder true))
          (list))))
    (react
      :when (and nightingale_second_letter_ready
                 (not nightingale_second_letter_intercepted)
                 (not nightingale_second_letter_failed)
                 (> day nightingale_second_letter_trigger_day))
      :then (list
        (effect 'set nightingale_second_letter_failed true)
        (effect 'set nightingale_second_letter_delivered true)
        (effect 'add police_relation -1)
        (effect 'start-quick-dialogue nightingale-second-letter-fail-text)))
  ))

(define nightingale-tasks
  (list
    (task
      :kind '主线
      :title "保护夜莺：剧院里的第二封信"
      :desc "去剧院见夜莺。第二封威胁信刚刚送到，送信的人可能还在附近。"
      :active nightingale_theater_unlocked
      :completed nightingale_city_day_started
      :failed false
      :steps (list
        (step :title "和前门保安交谈" :completed nightingale_front_done)
        (step :title "在舞台见到夜莺" :completed nightingale_commission_taken)
        (step :title "搜查剧院里的送信路线" :completed nightingale_shadow_seen)
        (step :title "追上可疑人影" :completed nightingale_first_confrontation_done)))
    (task
      :kind '主线
      :title "三天内追查送信路线"
      :desc "你被打昏后醒来，身体状态很差。先找医生和食物撑住，再顺着城市里的线索追查下一次送信。"
      :active (and nightingale_city_day_started (not nightingale_second_letter_ready))
      :completed nightingale_first_letter_done
      :failed nightingale_trust_failed
      :steps (list
        (step :title "去诊所处理伤势" :completed nightingale_clinic_unlocked)
        (step :title "从摊贩处打听街头跑腿" :completed nightingale_stall_checked)
        (step :title "凑钱从黑市买到送信线索" :completed nightingale_market_checked)
        (step :title "在饭摊吃几顿饭，让老板说完" :completed nightingale_restaurant_done)
        (step :title "拼出下一次送信路线" :completed nightingale_first_letter_done)))
    (task
      :kind '主线
      :title "拦截第二封威胁信"
      :desc "线人已经盯到送信人的影子。你只有当天这一点时间，赶在信件进剧院之前拦下它。"
      :active (and nightingale_second_letter_ready
                   (not nightingale_second_letter_intercepted)
                   (not nightingale_second_letter_failed))
      :completed nightingale_second_letter_intercepted
      :failed nightingale_second_letter_failed
      :steps (list
        (step :title "赶到剧院后巷" :completed nightingale_second_letter_ready)
        (step :title "拦下递信人" :completed nightingale_second_letter_intercepted)))
    (task
      :kind '主线
      :title "了解首演与旧码头的关系"
      :desc "首演不是单纯的一场演出。经理、宣传人员、后台工人都在回避某些名字，而莱恩开始越来越像被推向前台的替身。"
      :active (and nightingale_commission_taken (not nightingale_lore_known))
      :completed nightingale_lore_known
      :failed false
      :steps (list
        (step :title "和剧院经理谈谈首演" :completed nightingale_manager_talked)
        (step :title "听宣传口的人解释旧码头主题" :completed nightingale_publicist_talked)
        (step :title "问后台工人最近谁在打听流程" :completed nightingale_stagehand_talked)
        (step :title "收集夜莺的传说" :completed nightingale_lore_known)))))

(define (nightingale-stall-investigation-action)
  (when (and nightingale_commission_taken
             (not nightingale_second_letter_ready)
             (not nightingale_stall_checked))
    (action
      :title "打听谁替剧院跑过信"
      :desc "摊贩看街的时间比警察还久。送信的人如果匆忙经过，这里最容易留下口风。"
      :check (check
        :suits (list 敏锐)
        :risk 'low
        :ok (outcome (list
          (effect 'set nightingale_stall_checked true)
          (effect 'clock+ nightingale_first_letter_progress 1)
          (effect 'start-quick-dialogue nightingale-stall-text)))
        :partial (outcome (list
          (effect 'set nightingale_stall_checked true)
          (effect 'clock+ nightingale_first_letter_progress 1)
          (effect 'add energy -1)
          (effect 'start-quick-dialogue nightingale-stall-text)))
        :fail (outcome (list (effect 'add energy -1)) "摊贩先顾着手里的热汤，不想把你的问题也一起端起来。")))))

(define (nightingale-blackmarket-investigation-action)
  (when (and nightingale_commission_taken
             (not nightingale_second_letter_ready)
             (not nightingale_market_checked))
    (action
      :title "花钱买送信人的来路"
      :desc "黑市掌柜把消息切成几段卖。十块钱，他就把送信人的关键名字吐出来。"
      :conditions (list (field-at-least 'money 100 "需要 10 元"))
      :inputs (list (item 'money 100 "消息费"))
      :effects (list
        (effect 'set nightingale_market_checked true)
        (effect 'clock+ nightingale_first_letter_progress 1)
        (effect 'start-quick-dialogue nightingale-market-text)))))

(define (nightingale-bar-context-action)
  (when (and nightingale_commission_taken
             (not nightingale_lore_known)
             (not nightingale_bar_checked))
    (action
      :title "和小报记者聊夜莺的首演"
      :desc "酒吧里总有人比报纸更早拿到草稿。问题只是你愿意让谁记住你在问。"
      :effects (list
        (effect 'set nightingale_bar_checked true)
        (effect 'clock+ nightingale_lore_progress 1)
        (effect 'start-quick-dialogue nightingale-bar-text)))))

(define (nightingale-waste-investigation-action)
  (when (and nightingale_commission_taken
             (not nightingale_second_letter_ready)
             (not nightingale_waste_checked))
    (action
      :title "问底层跑腿有没有人替剧院送过信"
      :desc "如果威胁信是花钱一层层递过去的，最便宜的那一层通常站在这里。"
      :check (check
        :suits (list 魅力)
        :risk 'mid
        :ok (outcome (list
          (effect 'set nightingale_waste_checked true)
          (effect 'clock+ nightingale_first_letter_progress 1)
          (effect 'start-quick-dialogue nightingale-waste-text)))
        :partial (outcome (list
          (effect 'set nightingale_waste_checked true)
          (effect 'clock+ nightingale_first_letter_progress 1)
          (effect 'add health -1)
          (effect 'start-quick-dialogue nightingale-waste-text)))
        :fail (outcome (list (effect 'add health -1)) "你逼得太近了，他们先让你记住谁的地盘不能白问。")))))
