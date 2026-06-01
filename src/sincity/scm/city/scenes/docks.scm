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
    (var 'ryan_notice_checked false)))

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
    (ryan_new_shop_unlocked 'new_shop)
    (ryan_old_shop_checked 'new_shop_unlocking)
    (ryan_old_shop_unlocked 'old_shop)
    (ryan_address_found 'old_shop)
    ((ryan-tavern-ready?) 'tavern_challenge)
    (else 'docks_investigation)))

(define (ryan-docks-investigation-active?)
  (= (ryan-stage) 'docks_investigation))

(define (ryan-tavern-challenge-active?)
  (= (ryan-stage) 'tavern_challenge))

(define (ryan-tavern-open?)
  ryan_address_found)

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
        :desc "八块钱一杯。酒不能解决问题，但能补一点精力。"
        :inputs (list (item 'money 8 "酒钱"))
        :effects (list
          (effect 'add energy 2)
          (when (and blonde_intro_seen (not blonde_drinks_done)) (effect 'clock+ blonde_drink_progress 1))))
      (action
        :title "吧台小赌"
        :desc "把十块钱压在一局牌上。酒吧里的赌博更像消遣，但欠账会记在墙后。"
        :conditions (list (field-at-least 'money 10 "需要 10 元赌本"))
        :inputs (list (item 'money 10 "赌本"))
        :check (check
          :suits (list 敏锐)
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
          :suits (list 敏锐)
          :risk 'low
          :ok (outcome (list (effect 'clock+ ryan_lead 1)) "一个老工人朝酒馆方向努了努嘴。")
          :partial (outcome (list (effect 'clock+ ryan_lead 1)) "他没多说，但指了条路。")
          :fail (outcome (list) "工人看了你一眼，转身走了。")))
      (action
        :title "在小店打听莱恩"
        :desc "码头小店老板认识所有人。他愿意说多少取决于你值不值得信任。"
        :check (check
          :suits (list 魅力)
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

(define (ryan-old-shop-check-action)
  (when (not ryan_old_shop_checked)
    (action
      :title "检查店铺内部"
      :desc "柜台被砸过，货架空了。但墙上的痕迹说明这里曾经是正经生意。"
      :effects (list
        (effect 'set ryan_old_shop_checked true)
        (effect 'set ryan_new_shop_unlocked true)
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

(define (旧码头)
  (node
    :title "旧码头"
    :desc "旧码头不大，但足够藏下不愿被找到的人。莱恩就是其中之一。"
    :position '(900 280)
    :show-clocks (list ryan_lead ryan_deadline nightingale_trust)
    :actions (ryan-docks-investigation-actions)
    :children (list
      (码头酒馆)
      (when ryan_old_shop_unlocked (莱恩的老店铺))
      (when ryan_new_shop_unlocked (莱恩的新店)))))
