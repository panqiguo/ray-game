;; EXPORT docks-vars, docks-reacts, 旧码头
;; IMPORT nightingale_first_letter_done, nightingale_trust, nightingale_trust_checked_day, nightingale-trust-loss-text FROM nightingale_story.scm
;; IMPORT gambling_debt, blonde_intro_seen, blonde_drinks_done, blonde_drink_progress, blonde_cold_chatted, blonde_flirted, blonde_customer_chased, blonde_secret_shared, blonde_mary_shared, blonde-cold-text, blonde-flirt-text, blonde-reward-text, blonde-mary-text FROM city_1.scm

(define docks-vars
  (list
    (var 'ryan_docks_unlocked false)
    (var 'ryan_lead (clock :title "莱恩的线索" :desc "在旧码头打听莱恩的过去和现在。" :initial 0 :max 4))
    (var 'ryan_tavern_challenge_unlocked false)
    (var 'ryan_address_found false)
    (var 'ryan_old_shop_unlocked false)
    (var 'ryan_old_shop_checked false)
    (var 'ryan_new_shop_unlocked false)
    (var 'ryan_confronted false)
    (var 'ryan_section_due_day 0)
    (var 'ryan_deadline (clock :title "旧码头调查期限" :desc "警方正在关注旧码头，时间拖得越久夜莺的信任越低。" :initial 5 :max 5))
    (var 'ryan_deadline_checked_day 0)
    (var 'ryan_notice_checked false)
    (var 'helen_boarding_search_unlocked false)
    (var 'helen_boarding_unlocked false)
    (var 'helen_seamen_house_checked false)
    (var 'helen_redbrick_house_checked false)
    (var 'helen_east_warehouse_checked false)
    (var 'helen_seamen_house_progress (clock :title "旧海员寄宿楼" :desc "排查这里是不是老海伦的住处。" :initial 0 :max 6))
    (var 'helen_redbrick_house_progress (clock :title "红砖寄宿公寓" :desc "排查这里是不是老海伦的住处。" :initial 0 :max 6))
    (var 'helen_east_warehouse_progress (clock :title "东栈房出租屋" :desc "排查这里是不是老海伦的住处。" :initial 0 :max 6))
    (var 'helen_met false)
    (var 'helen_loosened (clock :title "老海伦的醉意" :desc "酒精让老海伦的话越来越松，也让房间里的边界越来越模糊。" :initial 0 :max 3))
    (var 'helen_asleep false)
    (var 'helen_room_searched false)
    (var 'helen_photo_found false)
    (var 'helen_photo_damaged false)
    (var 'ryan_old_life_known false)
    (var 'ryan_followed_after_helen false)
    (var 'docks_threat_escalated false)))

(define docks-reacts
  (list
    (react
      :when (and nightingale_first_letter_done (not ryan_docks_unlocked))
      :then (list
        (effect 'set ryan_docks_unlocked true)
        (effect 'set ryan_section_due_day (+ day 5))
        (effect 'set ryan_deadline_checked_day day)
        (effect 'start-quick-dialogue "# 旧码头\n\n# speaker: 科尔\n信纸上的灰和码头泥味拼在一起，把线索推向了旧码头。\n\n莱恩这个名字开始反复出现——醉话、闹事、旧怨，以及一间已经撑不住的新店。\n\n# speaker: 科尔\n该去旧码头看看了。")))
    (react
      :when (and ryan_docks_unlocked
                 (not ryan_confronted)
                 (> day ryan_deadline_checked_day))
      :then (list
        (effect 'clock- ryan_deadline 1)
        (effect 'set ryan_deadline_checked_day day)))
    (react
      :when (and (>= (clock-value ryan_lead) 3)
                 (not ryan_tavern_challenge_unlocked))
      :then (list
        (effect 'set ryan_tavern_challenge_unlocked true)
        (effect 'start-quick-dialogue "# 线索足够了\n\n# speaker: 科尔\n几片碎片拼在一起——莱恩经常出现在码头酒馆。也许该去那里喝一杯。")))
    (react
      :when (and (clock-filled? helen_loosened)
                 (not helen_asleep))
      :then (list
        (effect 'set helen_asleep true)
        (effect 'start-quick-dialogue "# 老海伦睡着了\n\n# speaker: 老海伦\n“莱恩……不是那样的。他以前会修门锁，修水管，什么都修……”\n\n# speaker: 科尔\n她的杯子歪在桌边，话也歪进梦里。可她的眼神最后落向墙角那个铁皮箱。\n\n她没把所有东西说完。也许东西在房间里。")))
    (react
      :when (and ryan_address_found
                 (not helen_boarding_search_unlocked)
                 (not helen_room_searched))
      :then (list
        (effect 'set helen_boarding_search_unlocked true)))
    (react
      :when (and (clock-filled? helen_seamen_house_progress)
                 (not helen_seamen_house_checked)
                 (not helen_boarding_unlocked))
      :then (list
        (effect 'set helen_seamen_house_checked true)
        (effect 'start-quick-dialogue "# 旧海员寄宿楼\n\n# speaker: 科尔\n门牌是真的旧，楼里也确实住过几个认识莱恩的人。\n\n但这里没人叫海伦。一个跛脚房东把我赶下楼，说我来晚了十年。")))
    (react
      :when (and (clock-filled? helen_redbrick_house_progress)
                 (not helen_boarding_unlocked))
      :then (list
        (effect 'set helen_boarding_unlocked true)
        (effect 'start-quick-dialogue "# 找到老海伦\n\n# speaker: 科尔\n红砖楼三层的门缝里有旧酒、潮木头和廉价汤的味道。\n\n门后有人咳了一声。一个女人问我是不是又来找莱恩。\n\n这次找对了。")))
    (react
      :when (and (clock-filled? helen_east_warehouse_progress)
                 (not helen_east_warehouse_checked)
                 (not helen_boarding_unlocked))
      :then (list
        (effect 'set helen_east_warehouse_checked true)
        (effect 'start-quick-dialogue "# 东栈房出租屋\n\n# speaker: 科尔\n这里有海伦这个名字，却不是我要找的人。\n\n登记簿上的海伦已经搬走三年，留下的只有一张欠租单和一个不愿多说的管理员。")))
    (react
      :when (and ryan_docks_unlocked
                 (not ryan_confronted)
                 (> ryan_section_due_day 0)
                 (> day ryan_section_due_day)
                 (> day nightingale_trust_checked_day)
                 (> (clock-value nightingale_trust) 0))
      :then (list
        (effect 'clock- nightingale_trust 1)
        (effect 'set nightingale_trust_checked_day day)
        (when (or (= (clock-value nightingale_trust) 7)
                  (= (clock-value nightingale_trust) 2))
          (effect 'start-quick-dialogue nightingale-trust-loss-text))))))

(define (ryan-tavern-ready?)
  (or ryan_tavern_challenge_unlocked (>= (clock-value ryan_lead) 3)))

(define (ryan-stage)
  (cond
    (ryan_confronted 'done)
    (ryan_old_shop_checked 'old_shop_checked)
    (ryan_old_shop_unlocked 'old_shop)
    (helen_room_searched 'old_shop)
    (helen_boarding_unlocked 'helen_found)
    (ryan_address_found 'helen_boarding_search)
    ((ryan-tavern-ready?) 'tavern_challenge)
    (else 'docks_investigation)))

(define (ryan-docks-investigation-active?)
  (= (ryan-stage) 'docks_investigation))

(define (ryan-tavern-challenge-active?)
  (= (ryan-stage) 'tavern_challenge))

(define (ryan-tavern-open?)
  ryan_address_found)

(define (helen-asleep?)
  (or helen_asleep (clock-filled? helen_loosened)))

(define (ryan-tavern-gate-actions)
  (if (ryan-tavern-challenge-active?)
    (list
      (action
        :title "和码头人喝酒——问出莱恩的地址"
        :desc "你得喝倒他们才能撬开嘴。"
        :effects (list
          (effect 'set ryan_tavern_challenge_unlocked true)
          (effect 'start-encounter '码头酒馆喝酒交锋))))
    (list)))

(define (ryan-tavern-service-actions)
  (if (ryan-tavern-open?)
    (list
      (action
        :title "点一杯酒"
        :desc "八块钱一瓶。你可以自己喝掉，也可以把它带去给更需要酒精开口的人。"
        :inputs (list (item 'money 8 "酒钱"))
          :effects (list
            (effect 'add 'liquor 1)
            (effect 'add energy 2)
            (when (and blonde_intro_seen (not blonde_drinks_done)) (effect 'clock+ blonde_drink_progress 1))))
      (action
        :title "吧台小赌"
        :desc "把十块钱压在一局牌上。酒吧里的赌博更像消遣，但欠账会记在墙后。"
        :conditions (list (field-at-least 'money 10 "需要 10 元赌本"))
        :inputs (list (item 'money 10 "赌本"))
        :check (check
          :suit 敏锐
          :risk 'high
          :ok (outcome (list (effect 'add money 24)) "你读懂了对面那点迟疑，今晚的酒钱有人替你付。")
          :partial (outcome (list (effect 'add money 8) (effect 'add pressure 1)) "你赢回一点，但坐得太久，头也开始发沉。")
          :fail (outcome (list (effect 'clock+ gambling_debt 1) (effect 'add pressure 1)) "牌面翻下去，你只剩下一笔被人记住的小账。"))))
    (list)))

(define (ryan-tavern-blonde-actions)
  (if (ryan-tavern-open?)
    (list
      (when (not blonde_intro_seen)
        (action
          :title "和金发女郎交谈"
          :desc "她人在吧台那一头，还没决定要不要把时间花在你身上。"
          :effects (list
            (effect 'set blonde_intro_seen true)
            (effect 'start-quick-dialogue blonde-cold-text))))
      (when (and blonde_intro_seen (not blonde_drinks_done))
        (action
          :title "和金发女郎交谈"
          :desc "她把你的话当作吧台上的水渍一样擦过去，只丢下一句：“再喝点，侦探。清醒的人都太无聊。”"
          :effects (list
            (effect 'set blonde_cold_chatted true))))
      (when (and blonde_drinks_done (not blonde_flirted))
        (action
          :title "和金发女郎交谈"
          :desc "第八杯之后，她终于主动把身体靠近了一点。她拿你的欲望开玩笑，也在看你是不是会为了她把判断放低。"
          :effects (list
            (effect 'set blonde_flirted true)
            (effect 'add pressure 1)
            (effect 'start-quick-dialogue blonde-flirt-text))))
      (when (and blonde_flirted (not blonde_customer_chased))
        (action
          :title "和金发女郎交谈"
          :desc "她的眼神越过你肩膀，落到那个占便宜的客人身上。她没有开口求你，只是把那一眼停得比平时久。"
          :effects (list (effect 'start-encounter '酒吧赶客人))))
      (when (and blonde_customer_chased (not blonde_secret_shared))
        (action
          :title "和金发女郎交谈"
          :desc "她这次没有立刻把你推回客人的位置。一个吻、一句贴耳的话，或者一张写着地址的酒杯垫，都被她包成同一种暧昧。"
          :effects (list
            (effect 'set blonde_secret_shared true)
            (effect 'start-quick-dialogue blonde-reward-text))))
      (when (and blonde_secret_shared (not blonde_mary_shared))
        (action
          :title "和金发女郎交谈"
          :desc "她故意留了个口子。现在看你敢不敢顺着往里问，问那个她不想完整说出口的旧名字。"
          :effects (list
            (effect 'set blonde_mary_shared true)
            (effect 'start-quick-dialogue blonde-mary-text)))))
    (list)))

(define (ryan-docks-investigation-actions)
  (if (ryan-docks-investigation-active?)
    (list
      (action
        :title "和码头工人搭话"
        :desc "工人休息时最好说话。他们知道莱恩常去的地方，但不会跟陌生人细聊。"
        :check (check
          :suit 敏锐
          :risk 'low
          :ok (outcome (list (effect 'clock+ ryan_lead 1)) "一个老工人朝酒馆方向努了努嘴。")
          :partial (outcome (list (effect 'clock+ ryan_lead 1)) "他没多说，但指了条路。")
          :fail (outcome (list) "工人看了你一眼，转身走了。")))
      (action
        :title "在小店打听莱恩"
        :desc "码头小店老板认识所有人。他愿意说多少取决于你值不值得信任。"
        :check (check
          :suit 魅力
          :risk 'mid
          :ok (outcome (list (effect 'clock+ ryan_lead 1)) "老板低声说：「莱恩以前开过店……后来没了。」")
          :partial (outcome (list (effect 'clock+ ryan_lead 1)) "他话说到一半，被进门的客人打断了。")
          :fail (outcome (list) "老板假装没听见你的问题。")))
      (when (not ryan_notice_checked)
        (action
          :title "查看码头旧公告"
          :desc "告示栏上贴着过期的招租和拆迁通知。莱恩的名字没出现，但店铺转让的日期能拼出一个时间线。"
          :effects (list (effect 'clock+ ryan_lead 1) (effect 'set ryan_notice_checked true)))))
    (list)))

(define (helen-talk-actions)
  (cond
    ((not helen_met)
      (list
        (action
          :title "叫老海伦开门"
          :desc "门缝里有灯光。老海伦认识莱恩，也认识旧码头没被拆掉之前的样子。"
          :effects (list
            (effect 'set helen_met true)
            (effect 'start-quick-dialogue "# 老海伦\n\n# speaker: 老海伦\n门开了一条缝。酒味、旧汤味和潮木头的味道一起挤出来。\n\n# speaker: 老海伦\n“找莱恩？你们不是已经把他写成疯子了吗？”")))))
    ((and (helen-asleep?) (not helen_room_searched))
      (list
        (action
          :title "趁她睡着搜索房间"
          :desc "她没有把全部话说完。墙角的铁皮箱、床头的旧相框和桌底的纸袋都像是在等一个不太体面的侦探。"
          :effects (list (effect 'start-encounter '老海伦房间搜查)))))
    (helen_room_searched
      (list))
    (else
      (list
        (action
          :title "给老海伦带一瓶便宜酒"
          :desc "她不愿意清醒着谈莱恩。你带的酒会让她松口，也会让你离体面远一点。"
          :conditions (list (has-item 'liquor 1 "需要一瓶便宜酒"))
          :inputs (list (item 'liquor 1 "便宜酒"))
          :effects (list (effect 'clock+ helen_loosened 2)))
        (action
          :title "陪她聊莱恩"
          :desc "别急着问威胁信，先让她把莱恩当成一个活过的人，而不是报纸上的疯子。"
          :check (check
            :suit 魅力
            :risk 'low
            :ok (outcome (list (effect 'clock+ helen_loosened 1)) "她骂了莱恩几句，又开始替他说话。")
            :partial (outcome (list (effect 'clock+ helen_loosened 1) (effect 'add pressure 1)) "她说得断断续续，但名字开始从酒气里浮出来。")
            :fail (outcome (list (effect 'add pressure 1)) "她把杯子攥紧，像你也是来抢东西的人。")))
        (action
          :title "顺着她的话问旧码头"
          :desc "她总把莱恩、旧店和一张照片混在一起。你可以不纠正她，只把错乱的地方记下来。"
          :check (check
            :suit 敏锐
            :risk 'mid
            :ok (outcome (list (effect 'clock+ helen_loosened 2)) "她提到一张照片，和一次改造说明会前夜。")
            :partial (outcome (list (effect 'clock+ helen_loosened 1)) "她没有说清楚，但眼神总往墙角飘。")
            :fail (outcome (list (effect 'add pressure 1)) "你问得太直，她忽然开始装糊涂。")))))))

(define (helen-boarding-search-actions progress-clock)
  (list
    (action
      :title "向住客打听老海伦"
      :desc "寄宿公寓里的人不爱回答问题，尤其不爱回答关于邻居的问题。你得好处，就得先担风险。"
      :check (check
        :suit 魅力
        :risk 'high
        :ok (outcome (list (effect 'clock+ progress-clock 3)) "有人终于承认听过这个名字，还把楼层和门牌一起说了。")
        :partial (outcome (list (effect 'clock+ progress-clock 1) (effect 'add pressure 2)) "他们给了你一点口风，也把你的脸记住了。")
        :fail (outcome (list (effect 'add pressure 2)) "门缝一条接一条关上，有人开始大声抱怨有陌生人打听老住户。")))
    (action
      :title "翻看门牌和信箱"
      :desc "旧楼的信箱比人诚实一点，但也更破。"
      :check (check
        :suit 敏锐
        :risk 'low
        :ok (outcome (list (effect 'clock+ progress-clock 2)) "你从褪色标签和旧账单里拼出一段住户变动。")
        :partial (outcome (list (effect 'clock+ progress-clock 1)) "有几个名字对得上，但还不能确定。")
        :fail (outcome (list) "信箱空得像被提前清理过。")))))

(define (ryan-old-shop-check-action)
  (when (not ryan_old_shop_checked)
    (action
      :title "检查店铺内部"
      :desc "柜台被砸过，货架空了。但墙上的痕迹说明这里曾经是正经生意。"
      :effects (list
        (effect 'set ryan_old_shop_checked true)
        (effect 'start-quick-dialogue "# 莱恩的老店铺\n\n# speaker: 科尔\n柜台被砸过，不是普通的偷窃——是被逼走的。\n\n拆迁通知还贴在墙上。发件人的名字和剧院慈善首演的赞助名单有交集。\n\n# speaker: 科尔\n这不是运气不好。有人把莱恩从这片街区清了出去。")))))

(define (ryan-confrontation-action)
  (when (not ryan_confronted)
    (action
      :title "和莱恩对峙"
      :desc "门没锁。莱恩在里面，背对着门口。"
      :effects (list
        (effect 'set ryan_confronted true)
        (effect 'start-quick-dialogue "# 莱恩\n\n# speaker: 莱恩\n他把椅子转过来，先看了你一眼，像在看一件还没决定要不要捡起来的旧工具。\n\n# speaker: 莱恩\n“剧院的人？还是夜莺的人？”\n\n# speaker: 科尔\n“保护她的人。”\n\n# speaker: 莱恩\n他笑了一下，难听，没有温度。\n\n# speaker: 莱恩\n“那你来错地方了。我恨不得她从舞台上摔下来——但我不写恐吓信。”\n\n# speaker: 科尔\n他说这话的时候没有回避目光。没有心虚的人那种闪躲。\n\n# speaker: 莱恩\n“你查清楚那片旧街区是谁拆的，再回来跟我谈威胁信。”")))))

(define (码头酒馆)
  (node
    :title "码头酒馆"
    :desc (if ryan_address_found
      "破旧、吵闹、充满敌意。你已经在这里喝出了一点名声，至少现在有人愿意把你当成牌桌和吧台上的客人。"
      "破旧、吵闹、充满敌意。这里的每个人都认识莱恩，但没人会跟一个陌生人聊他。有人低声笑你像个走错门的娘娘腔。")
    :show-clocks (list
      (when ryan_address_found gambling_debt)
      (when (and ryan_address_found blonde_intro_seen (not blonde_drinks_done)) blonde_drink_progress))
    :actions (append
      (ryan-tavern-gate-actions)
      (ryan-tavern-service-actions)
      (ryan-tavern-blonde-actions))))

(define (莱恩的老店铺)
  (node
    :title "莱恩的老店铺"
    :desc "门板已经卸了，招牌歪挂在雨棚下。莱恩以前的五金店，现在只剩垃圾和老鼠。"
    :actions (list
      (ryan-old-shop-check-action))))

(define (莱恩的新店)
  (node
    :title "莱恩的新店"
    :desc "更小、更偏僻、更破。一块手写的招牌歪在门框上，窗玻璃裂了一条。"
    :actions (list
      (ryan-confrontation-action))))

(define (旧海员寄宿楼)
  (node
    :title "旧海员寄宿楼"
    :desc "一栋靠近水边的长楼，墙上还挂着退色的船员牌。这里看起来像能藏下很多旧名字。"
    :show-clocks (list (when (and (not helen_seamen_house_checked) (not helen_boarding_unlocked)) helen_seamen_house_progress))
    :actions (if (and (not helen_seamen_house_checked) (not helen_boarding_unlocked))
      (helen-boarding-search-actions helen_seamen_house_progress)
      (list))))

(define (红砖寄宿公寓)
  (node
    :title "红砖寄宿公寓"
    :desc (if helen_boarding_unlocked
      "红砖墙被雨泡得发黑。老海伦就住在这里三层楼道尽头——莱恩的老朋友，旧码头的活记忆。"
      "红砖墙被雨泡得发黑，楼梯间有旧酒、潮木头和廉价汤的味道。酒保给的线索在这里变得更像真的。")
    :show-clocks (list (when (not helen_boarding_unlocked) helen_redbrick_house_progress))
    :actions (if (not helen_boarding_unlocked)
      (helen-boarding-search-actions helen_redbrick_house_progress)
      (list))
    :children (list
      (when helen_boarding_unlocked (海伦的房间)))))

(define (东栈房出租屋)
  (node
    :title "东栈房出租屋"
    :desc "旧仓库隔出来的出租屋，一排门后住着临时工、欠租的人和不愿登记的人。这里可能有海伦，也可能只有另一个同名的人。"
    :show-clocks (list (when (and (not helen_east_warehouse_checked) (not helen_boarding_unlocked)) helen_east_warehouse_progress))
    :actions (if (and (not helen_east_warehouse_checked) (not helen_boarding_unlocked))
      (helen-boarding-search-actions helen_east_warehouse_progress)
      (list))))

(define (海伦的房间)
  (node
    :title "海伦的房间"
    :desc (cond
      (helen_photo_found "旧照片已经在你口袋里。老海伦还在睡，像整间房都不愿意醒。")
      (helen_photo_damaged "老海伦醒过一次，照片只剩残片。走廊里已经有人知道你来过。")
      ((helen-asleep?) "老海伦歪在椅子里睡着了。房间里堆满旧物，像一座没人愿意登记的小型废墟。")
      (helen_met "老海伦坐在桌边，酒杯离手很近，话离真相还差一点。")
      (else "门缝里有旧酒、潮木头和廉价汤的味道。这间房像是被城市忘在雨里。"))
    :show-clocks (list (when (and helen_met (not helen_asleep) (not helen_room_searched)) helen_loosened))
    :actions (helen-talk-actions)))

(define (旧码头)
  (node
    :title "旧码头"
    :desc "旧码头不大，但足够藏下不愿被找到的人。莱恩就是其中之一。"
    :position '(900 280)
    :show-clocks (list ryan_lead ryan_deadline nightingale_trust)
    :actions (ryan-docks-investigation-actions)
    :children (list
      (码头酒馆)
      (when (and helen_boarding_search_unlocked (not helen_boarding_unlocked) (not helen_seamen_house_checked)) (旧海员寄宿楼))
      (when helen_boarding_search_unlocked (红砖寄宿公寓))
      (when (and helen_boarding_search_unlocked (not helen_boarding_unlocked) (not helen_east_warehouse_checked)) (东栈房出租屋))
      (when ryan_old_shop_unlocked (莱恩的老店铺)))))
