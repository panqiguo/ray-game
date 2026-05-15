(include "helper.scm")
(include "common_clock_macros.scm")

;; 城市内容现在按“生存底盘 + 主线章节”组织：
;; - 诊所、黑市、书店、摊贩、仓库等长期功能保留。
;; - 第一章围绕中枪男人闯入、警方调查、取回神秘物品。
;; - 送去鉴定后的第二天开启薇拉委托线；鉴定结果稍后并入主线信息。

(define intrusion-intro-text
  "# 雨夜闯入者\n\n# speaker: 科尔\n门被撞开的时候，我正试着让一杯冷咖啡变得像晚饭。\n\n# speaker: 男人\n他捂着腹部，血从指缝里往外冒。枪伤。不是新手打的，也不是警告用的。\n\n# speaker: 男人\n“他们会来找这个。”\n\n# speaker: 科尔\n他把一个包着油纸的小东西塞进抽屉，倒在我的地板上。十分钟后，警笛停在楼下。")

(define police-summons-text
  "# 警方调查\n\n# speaker: 警探\n“一个中枪的男人死在你的办公室里。科尔，你最好让我今天就能把这件事写完。”\n\n# speaker: 科尔\n他要的不是真相，是一份能合上的报告。")

(define vera-commission-text
  "# 薇拉委托\n\n# speaker: 弗雷德里克\n“她不是会突然消失的人。”\n\n# speaker: 科尔\n每个来找侦探的人都会这么说。区别只在于他们是真的相信，还是希望我相信。")

(define vera-thread-text
  "# 薇拉的线索\n\n# speaker: 科尔\n薇拉离开前去过老街的修鞋铺。她留下过一句话：\"如果我不回来，告诉来找我的人——钥匙在窗台第三块砖下面。\"")

(define wounded-lead-text
  "# 死者线索\n\n# speaker: 科尔\n零碎的话拼在一起：一个外地口音的男人，最近在码头、饭店后门和医院登记处附近出现过。\n\n# speaker: 科尔\n他不是误闯进我的办公室。他是没能跑到下一个地方。")

(define frederick-talk-text
  "# 弗雷德里克\n\n# speaker: 弗雷德里克\n“薇拉最近总去老街。她说那里有人欠她一个解释。”\n\n# speaker: 科尔\n他讲得太完整，完整得像提前背过。")

(define hotel-lead-text
  "# 旅馆线索\n\n# speaker: 科尔\n三个地点，两个空回音。真正有用的是老街修鞋匠那句：“她从望月旅馆出来时，手里拿着男人的外套。”")

(define hotel-boss-text
  "# 望月旅馆老板\n\n# speaker: 老板\n“我不记客人的脸，也不记客人的名字。”\n\n# speaker: 科尔\n“那你记什么？”\n\n# speaker: 老板\n“谁付钱让我别开门。”")

(define follow-done-text
  "# 跟踪\n\n# speaker: 科尔\n旅馆后门出来的人没有回头。他走过两条街，进了一栋没有门牌的公寓。\n\n# speaker: 科尔\n薇拉，或者知道薇拉在哪的人，就在里面。")

(define casino-found-text
  "# 赌场入口\n\n# speaker: 老千\n“别在酒吧问地下入口。会显得你太干净。”\n\n# speaker: 科尔\n他把地址写在火柴盒里侧。字很小，赌债很大。")

(define book-logic-text
  "# 读完：《县城账簿与谎言》\n\n# speaker: 科尔\n数字不会说真话，但它们也不擅长撒谎。读完这本书后，我更知道该从哪里看起。")

(define book-perception-text
  "# 读完：《街口观察法》\n\n# speaker: 科尔\n人们总以为自己藏得很好。其实鞋尖、肩膀和停顿，比嘴诚实多了。")

(define book-willpower-text
  "# 读完：《疼痛之后》\n\n# speaker: 科尔\n有些书不教你赢，只教你不要太快倒下。")

(define auth-sent-text
  "# 送去鉴定\n\n# speaker: 科尔\n东西已经交给鉴定人。他说三天后给结果。")

(define auth-result-text
  "# 鉴定结果\n\n# speaker: 鉴定人\n\"这件东西的年代比你想象的久。久到不该出现在这里。\"")

(define item-recovered-text
  "# 取回物品\n\n# speaker: 科尔\n东西拿到了。现在的问题是——该留着它，还是该用它。")

(define rehab-intro-text
  "# 开始康复治疗\n\n# speaker: 科尔\n诊所的大夫看了看我的伤，说没有快速的办法。\"每天来后面的康复室练一练，慢但管用。\"他说。八块钱换一个疗程，算是我在这城里最便宜的交易。")

(define rehab-done-text
  "# 康复训练完成\n\n# speaker: 科尔\n最后一组动作做完，身体终于不再像一台生锈的机器。虽然离痊愈还远，但至少能喘一口顺畅的气了。\n\n恢复了 3 点健康。")

(define make-work-action
  (lambda (title desc suit risk ok-money partial-money fail-money fail-health)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk risk
        :ok (outcome (list (effect 'add money ok-money)))
        :partial (outcome (list (effect 'add money partial-money) (effect 'add energy -2)))
        :fail (outcome (list (effect 'add money fail-money) (effect 'add energy -2) (when (> fail-health 0) (effect 'add health (- fail-health)))))))))

(define make-book-action
  (lambda (title desc clock suit)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'low
        :ok (outcome (list (effect 'clock+ clock 2)))
        :partial (outcome (list (effect 'clock+ clock 1) (effect 'add energy -1)))
        :fail (outcome (list (effect 'add energy -1)))))))

(define make-investigate-action
  (lambda (title desc clock suit)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'mid
        :ok (outcome (list (effect 'clock+ clock 2)) "线索露出了一小截。你把它按在纸上。")
        :partial (outcome (list (effect 'clock+ clock 1) (effect 'add energy -1)) "你得到了一点碎片，足够继续往下问。")
        :fail (outcome (list (effect 'add energy -1)) "你问得太快，周围的人开始闭嘴。")))))

(define-node 办公室
  (node
    :desc "办公桌、沙发、电话和一块还没完全褪色的地板。这里既是工作地点，也是你暂时能睡下的地方。"
    :position '(40 280)
    :show-clocks (list (when (not blood_cleaned) blood_clean_progress) (when (and item_recovered item_auth_sent (not auth_done)) auth_wait_progress))
    :actions (list
      (action
        :title "在沙发上睡一晚"
        :desc (if (not blood_cleaned)
          "睡觉 → 天数+1，精力-1，重抽行动卡。地板上有血迹时精力额外减少一点。精力不足时，健康可能受损。"
          "睡觉 → 天数+1，精力-1，重抽行动卡。精力不足时，健康可能受损。")
        :effects (list
          (effect 'advance-day)
          (effect 'reset-hand)
          (effect 'set bookshop_entered_today false)
          (when (not blood_cleaned) (effect 'add energy -1))))
      (action
        :title "吃一包随身干粮"
        :desc "不用找摊贩，也不用花今天的钱。吃掉 1 份干粮，立刻恢复 3 点精力。"
        :conditions (list (has-item 'food 1 "需要干粮"))
        :inputs (list (item 'food 1 "干粮"))
        :effects (list (effect 'add energy 3)))
      (when (and intrusion_seen (not blood_cleaned))
        (action
          :title "清理地板上的血迹"
          :desc "不是为了骗过鉴识科，是为了让自己还能在这里闭眼。"
          :check (check
            :suits (list 意志 感知)
            :risk 'low
            :ok (outcome (list (effect 'clock+ blood_clean_progress 2)))
            :partial (outcome  (list (effect 'clock+ blood_clean_progress 1)))
            :fail (outcome  (list (effect 'add energy -1))))))
      (when (and item_recovered (not item_auth_sent))
        (action
          :title "把神秘物品送去鉴定"
          :desc "这东西被太多人追着找。先弄清它是什么，再决定它值不值得继续拿着。"
          :conditions (list (has-item 'mysterious_item 1 "需要神秘物品") (field-at-least 'money 15 "需要 15 元鉴定费"))
          :inputs (list (item 'money 15 "鉴定费") (item 'mysterious_item 1 "神秘物品"))
          :effects (list
            (effect 'set item_auth_sent true)
            (effect 'set vera_thread_notice_day (+ day 1))
            (effect 'set auth_done_day (+ day 3))
            (effect 'start-quick-dialogue auth-sent-text)))))))

(define-node 街边摊贩
  (node
    :desc "铁锅、热汤、油烟和零钱。这里不问你从哪里来，只问你要不要加辣。"
    :position '(245 280)
    :show-clocks (list (when (and intrusion_seen (not item_recovered) (not wounded_man_lead_obtained)) investigation_progress))
    :actions (list
      (action
        :title "吃一碗热汤"
        :desc "便宜、烫嘴，立刻恢复 3 点精力。"
        :inputs (list (item 'money 6 "饭钱"))
        :effects (list (effect 'add energy 3)))
      (action
        :title "买一包干粮"
        :desc "把 2 点精力恢复存成 1 份干粮，之后可以在办公室里吃掉。"
        :inputs (list (item 'money 10 "干粮钱"))
        :effects (list (effect 'add food 1)))
      (when (and intrusion_seen (not item_recovered) (not stall_investigated))
        (action
          :title "向摊贩打听中枪男人"
          :desc "饭点时人群最杂。有人也许见过那个捂着腹部从雨里穿过去的男人。"
          :check (check
            :suits (list 感知)
            :risk 'mid
            :ok (outcome "你从摊贩的闲谈里拼出了一个方向。" (list (effect 'clock+ investigation_progress 1) (effect 'set stall_investigated true)))
            :partial (outcome "碎片不多，但足够让你继续往前走。" (list (effect 'clock+ investigation_progress 1) (effect 'set stall_investigated true) (effect 'add energy -1)))
            :fail (outcome "他今天不想提中枪的事，你的出现反而让他闭了嘴。" (list (effect 'add energy -1)))))))))

(define-node 黑市
  (node
    :desc "修表铺后门、药味、假章和压低的声音。这里什么都能办，只是从不保证干净。"
    :position '(450 280)
    :show-clocks (list (when (and intrusion_seen (not item_recovered) (not wounded_man_lead_obtained)) investigation_progress))
    :actions (list
      (action
        :title "找黑市医生处理伤口"
        :desc "便宜，不报警。坏处是你最好别仔细看他的器械。"
        :inputs (list (item 'money 12 "诊费"))
        :check (check
          :suits (list 意志)
          :risk 'mid
          :ok (outcome (list (effect 'add health 2)))
          :partial (outcome (list (effect 'add health 2) (effect 'add energy -1)))
          :fail (outcome (list (effect 'add health 1) (effect 'add energy -2) (effect 'set infected true)))))
      (when (and intrusion_seen (not item_recovered) (not market_investigated))
        (action
          :title "问枪伤药品的去向"
          :desc "正规诊所会登记，黑市不会。不会登记的地方，反而更容易留下口风。"
          :check (check
            :suits (list 逻辑)
            :risk 'mid
            :ok (outcome "黑市的人记性比诊所好。他记得那个买绷带的人。" (list (effect 'clock+ investigation_progress 1) (effect 'set market_investigated true)))
            :partial (outcome "他半遮半掩地说了几个细节，够你接着查。" (list (effect 'clock+ investigation_progress 1) (effect 'set market_investigated true) (effect 'add energy -1)))
            :fail (outcome "黑市的人嘴很严，你用错方式了。" (list (effect 'add energy -1)))))))))

(define-node 正规诊所
  (node
    :desc "白墙、玻璃柜、登记表。正规两个字的意思是：他们会救你，也会记住你。"
    :position '(655 280)
    :show-clocks (list (when (and rehab_started (not rehab_done)) rehab_progress) (when (and intrusion_seen (not item_recovered) (not wounded_man_lead_obtained)) investigation_progress))
    :actions (list
      (action
        :title "标准治疗"
        :desc "贵，但稳妥。至少这里的针头来自密封袋。"
        :conditions (list (field-at-least 'money 20 "需要 20 元"))
        :inputs (list (item 'money 20 "诊费"))
        :effects (list (effect 'add health 3)))
      (when (or (not rehab_started) rehab_done)
        (action
          :title "开始康复治疗"
          :desc "八块钱开一个康复疗程。比正规医疗慢，但便宜。"
          :inputs (list (item 'money 8 "疗程费用"))
          :effects (list
            (effect 'set rehab_started true)
            (effect 'set rehab_done false)
            (effect-reset-clock rehab_progress))))
      (when (and rehab_started (not rehab_done) (not (clock-filled? rehab_progress)))
        (action
          :title "进行康复训练"
          :desc "动作不大，但每天坚持会有用。低风险，失败没有惩罚。"
          :check (check
            :suits (list 意志)
            :risk 'low
            :ok (outcome (list (effect 'clock+ rehab_progress 2)))
            :partial (outcome (list (effect 'clock+ rehab_progress 1)))
            :fail (outcome (list)))))
      (when gunshot_wound
        (action
          :title "处理枪伤"
          :desc "他们会处理伤口，也会按规定通知警察。"
          :conditions (list (field-at-least 'money 40 "需要 40 元"))
          :inputs (list (item 'money 40 "枪伤诊费"))
          :effects (list
            (effect 'add health 4)
            (effect 'set gunshot_wound false)
            (effect 'add police_relation -1))))
      (when (and intrusion_seen (not item_recovered) (not clinic_investigated))
        (action
          :title "查急诊登记"
          :desc "中枪的人不一定敢进诊室，但附近总有人看见过他。"
          :check (check
            :suits (list 逻辑)
            :risk 'mid
            :ok (outcome "登记簿上没有他，但护士记得那件血衣。" (list (effect 'clock+ investigation_progress 1) (effect 'set clinic_investigated true)))
            :partial (outcome "你翻到了一些记录，不全，但有用。" (list (effect 'clock+ investigation_progress 1) (effect 'set clinic_investigated true) (effect 'add energy -1)))
            :fail (outcome "护士警惕地看了你一眼，你没敢继续问。" (list (effect 'add energy -1)))))))))

(define-node 书店
  (node
    :desc "书店很小，座位更少。老板不喜欢闲逛的人，但喜欢付过钱后安静的人。"
    :position '(860 280)
    :show-clocks (list logic_book perception_book willpower_book)
    :actions (list
      (when (not bookshop_entered_today)
        (action
          :title "付今天的入场费"
          :desc "五块钱买一张当天的座位。今天之后，你可以在这里自由读书，直到回去睡觉。"
          :conditions (list (field-at-least 'money 5 "需要 5 元"))
          :inputs (list (item 'money 5 "入场费"))
          :effects (list (effect 'set bookshop_entered_today true))))
      (when (and bookshop_entered_today (not logic_book_done))
        (make-book-action "读《县城账簿与谎言》" "一本讲账本、公司壳和人情债的旧书。读完会提升逻辑。" logic_book 逻辑))
      (when (and bookshop_entered_today (not perception_book_done))
        (make-book-action "读《街口观察法》" "一本写给巡警的教材，后来流到旧书架上。读完会提升感知。" perception_book 感知))
      (when (and bookshop_entered_today (not willpower_book_done))
        (make-book-action "读《疼痛之后》" "关于戒断、疼痛和自我约束。读完会提升意志。" willpower_book 意志)))))

(define-node 警局
  (node
    :desc "铁柜、烟味和一排不愿回答问题的人。警察想要报告，不一定想要真相。"
    :position '(1065 280)
    :actions (list
      (when (and intrusion_seen (not police_interview_started))
        (action
          :title "去警局配合调查"
          :desc "他们已经把这件事当成麻烦，而不是案件。你要先把笔录做完。"
          :effects (list
            (effect 'set police_interview_started true)
            (effect 'set police_choice_ready true)
            (effect 'start-dialogue 'police_interview)))))))

(define-node 仓库
  (node
    :desc "仓库按小时结钱，也按小时消耗人。白天搬货，夜里有人谈不该谈的路线。"
    :position '(40 520)
    :show-clocks (list (when (and intrusion_seen (not item_recovered) (not wounded_man_lead_obtained)) investigation_progress))
    :actions (list
      (make-work-action "搬货打散工" "现金来得快，代价也直接。" 意志 'mid 24 16 8 1)
      (when (and intrusion_seen (not item_recovered) (not warehouse_investigated))
        (action
          :title "问码头装卸工"
          :desc "死者鞋底带着码头泥。仓库的人也许见过他从哪条路上来。"
          :check (check
            :suits (list 感知)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ investigation_progress 1) (effect 'set warehouse_investigated true)) "装卸工见过那个方向有车急刹的声音。")
            :partial (outcome (list (effect 'clock+ investigation_progress 1) (effect 'set warehouse_investigated true)) "他不能确定，但给你指了可能的方向。")
            :fail (outcome (list (effect 'add energy -1)) "码头风大，人的记性也容易被吹散。"))))
      (when (and police_investigation_done (not item_recovered) (not item_recovery_started))
        (action
          :title "挑战 - 取回神秘物品"
          :desc "几天后，那东西已经换过手。你必须赶在别人彻底拆开它之前，把它拿回来。"
          :effects (list
            (effect 'set item_recovery_started true)
            (effect 'start-encounter '取回神秘物品)))))))

(define-node 酒吧
  (node
    :desc "酒吧白天像咖啡馆，晚上像供词室。这里没有秘密，只有还没轮到你听见的消息。"
    :position '(245 520)
    :show-clocks (list (when vera_commission_taken frederick_trace_progress) blonde_trust (when gambler_met gambler_debt_progress))
    :actions (list
      (action
        :title "买一杯酒"
        :desc "酒不能解决问题，但能补一点精力。"
        :inputs (list (item 'money 8 "酒钱"))
        :effects (list (effect 'add energy 2)))
      (when (and vera_thread_unlocked (not vera_commission_taken))
        (action
          :title "接下薇拉的委托"
          :desc "弗雷德里克要你找到他的妻子。你还不知道这是不是一件好事。"
          :effects (list
            (effect 'set vera_commission_taken true)
            (effect 'set chapter_2_started true)
            (effect 'start-quick-dialogue vera-commission-text))))
      (when (and vera_commission_taken (not frederick_talk_done))
        (action
          :title "和弗雷德里克谈话"
          :desc "他是薇拉的丈夫，也是最想让你相信自己无辜的人。"
          :effects (list
            (effect 'set frederick_talk_done true)
            (effect 'start-quick-dialogue frederick-talk-text))))
      (when (and frederick_talk_done (not frederick_real_lead_found))
        (make-investigate-action
          "调查弗雷德里克的酒吧踪迹"
          "他来过这里，却没有坐在吧台。有人在角落见过他的影子。"
          frederick_trace_progress
          感知))
      (when (not gambler_met)
        (action
          :title "听绝望的赌徒抱怨"
          :desc "他输了钱，也输掉了保密的能力。"
          :effects (list (effect 'set gambler_met true))))
      (when (and gambler_met (not casino_unlocked))
        (action
          :title "借钱给赌徒"
          :desc "十块钱买不到感激，但能买到他下一句真话。"
          :conditions (list (field-at-least 'money 10 "需要 10 元"))
          :inputs (list (item 'money 10 "借款"))
          :effects (list (effect 'clock+ gambler_debt_progress 1))))
      (when (and gambler_met (not casino_unlocked))
        (action
          :title "赌局 - 老千"
          :desc "他不是好赌，是太相信自己能看穿别人。"
          :check (check
            :suits (list 感知 逻辑)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ gambler_debt_progress 2)) "你看穿了他的手法，也看穿了他的恐惧。")
            :partial (outcome (list (effect 'clock+ gambler_debt_progress 1)) "你没赢漂亮，但逼他说出了地下入口的名字。")
            :fail (outcome (list (effect 'add money -8) (effect 'add energy -1)) "你输了一点钱，也换来一点教训。")))))))

(define-node 老街
  (node
    :desc "旧铺面、窄楼梯、晾衣绳和熟人的眼神。老街没有明确入口，但你总能从这里找到一点活路。"
    :position '(450 520)
    :show-clocks (list (when vera_commission_taken frederick_trace_progress) (when (and hotel_infiltrated (not vera_apartment_found)) vera_follow_progress))
    :actions (list
      (when (and frederick_talk_done (not frederick_real_lead_found))
        (action
          :title "调查弗雷德里克的老街踪迹"
          :desc "三个地点里，只有老街的人真的见过薇拉和弗雷德里克留下的痕迹。"
          :check (check
            :suits (list 感知 逻辑)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ frederick_trace_progress 2)) "你找到了通向望月旅馆的关键证词。")
            :partial (outcome (list (effect 'clock+ frederick_trace_progress 1) (effect 'add energy -1)) "老街给了你半句真话，足够继续追。")
            :fail (outcome (list (effect 'add energy -1)) "老街今天只给你关门声。"))))
      (when (and hotel_infiltrated (not vera_apartment_found))
        (make-investigate-action
          "跟踪旅馆后门的人"
          "不要靠太近，也不要跟丢。真正的地址藏在他以为自己安全的时候。"
          vera_follow_progress
          感知)))))

(define-node 望月旅馆
  (node
    :desc "招牌灯一半亮着，一半像从来没亮过。老板记性很差，收费时除外。"
    :position '(655 520)
    :actions (list
      (when (and frederick_real_lead_found (not hotel_boss_talk_done))
        (action
          :title "和旅馆老板谈"
          :desc "你需要知道薇拉住过哪间房。他需要假装不知道。"
          :effects (list
            (effect 'set hotel_boss_talk_done true)
            (effect 'start-quick-dialogue hotel-boss-text))))
      (when (and hotel_boss_talk_done (not hotel_infiltrated))
        (action
          :title "挑战 - 潜入旅馆"
          :desc "老板不让你进去。那只说明需要换一个入口。"
          :effects (list (effect 'start-encounter '潜入旅馆)))))))

(define-node 公寓
  (node
    :desc "没有门牌的公寓楼，走廊闻起来像潮墙、廉价香水和旧火药。"
    :position '(860 520)
    :actions (list
      (when (and vera_apartment_found (not chapter_2_done))
        (action
          :title "进入公寓"
          :desc "房门没有锁。里面有人等你，枪口先开口。"
          :effects (list
            (effect 'set standoff_started true)
            (effect 'start-encounter '公寓枪对峙)))))))

(define-node 赌场
  (node
    :desc "地下室、绿绒桌、假笑和真债。这里能赢钱，也能把明天提前输掉。"
    :position '(1065 520)
    :actions (list
      (make-work-action "替赌场看一晚场子" "不问问题，只看住门口。" 意志 'mid 30 18 6 1)
      (action
        :title "小赌一局"
        :desc "把十块钱放上桌，试试今晚的手气。"
        :conditions (list (field-at-least 'money 10 "需要 10 元赌本"))
        :inputs (list (item 'money 10 "赌本"))
        :check (check
          :suits (list 感知)
          :risk 'high
          :ok (outcome (list (effect 'add money 30)))
          :partial (outcome (list (effect 'add money 8) (effect 'add energy -1)))
          :fail (outcome (list (effect 'add energy -1))))))))

(define world-state
  (state
    (intro_seen false)
    (intrusion_seen false)
    (chapter_2_started false)
    (main_resolved false)

    (recovery_deadline_day 5)
    (police_interview_started false)
    (police_interview_forced false)
    (police_choice_ready false)
    (police_investigation_done false)
    (police_knows_true_info false)
    (police_got_fake_info false)
    (police_refused_info false)
    (police_suspicious false)
    (police_summons_seen false)
    (blood_clean_progress (clock :title "血迹清理" :desc "清理办公室里的血迹。未清理时休息效果更差。" :initial 0 :max 3))
    (blood_cleaned false)
    (investigation_progress (clock :title "死者线索" :desc "调查3处线索，拼出中枪男人的来路。" :initial 0 :max 3))
    (stall_investigated false)
    (market_investigated false)
    (clinic_investigated false)
    (warehouse_investigated false)
    (wounded_man_lead_obtained false)
    (item_recovery_started false)
    (item_recovery_forced false)
    (item_recovered false)
    (item_recovered_notice_seen false)
    (item_recovery_failed false)
    (item_auth_sent false)
    (vera_thread_notice_day 0)
    (vera_thread_unlocked false)
    (auth_done_day 0)
    (auth_done false)
    (auth_wait_progress (clock :title "鉴定等待" :desc "鉴定人正在检查神秘物品。" :initial 0 :max 3))

    (vera_commission_taken false)
    (frederick_talk_done false)
    (frederick_trace_progress (clock :title "弗雷德里克踪迹" :desc "调查他和薇拉在老街一带的活动。" :initial 0 :max 4))
    (frederick_real_lead_found false)
    (hotel_boss_talk_done false)
    (hotel_infiltrated false)
    (vera_follow_progress (clock :title "跟踪目标" :desc "从旅馆后门跟到真正的公寓。" :initial 0 :max 3))
    (vera_apartment_found false)
    (standoff_started false)
    (chapter_2_done false)

    (gambler_met false)
    (gambler_debt_progress (clock :title "赌徒欠债" :desc "让绝望的赌徒说出地下赌场的位置。" :initial 0 :max 3))
    (casino_unlocked false)
    (blonde_trust (clock :title "金发女郎" :desc "酒吧里另一个知道太多的人。后续支线预留。" :initial 0 :max 3))

    (gang_relation 0)
    (finance_relation 0)
    (police_relation 0)

    (logic_book (clock :title "《县城账簿与谎言》" :desc "读完后逻辑 +1。" :initial 0 :max 3))
    (perception_book (clock :title "《街口观察法》" :desc "读完后感知 +1。" :initial 0 :max 3))
    (willpower_book (clock :title "《疼痛之后》" :desc "读完后意志 +1。" :initial 0 :max 3))
    (logic_book_done false)
    (perception_book_done false)
    (willpower_book_done false)
    (bookshop_entered_today false)

    (infected false)
    (gunshot_wound false)
    (rehab_started false)
    (rehab_done false)
    (rehab_progress (clock :title "康复训练进度" :desc "每次训练进度+1，填满后恢复3点健康。" :initial 0 :max 4))))

(define world-reacts
  (reacts
    (react
      :when (not intro_seen)
      :then (list
        (effect 'set intro_seen true)
        (effect 'set intrusion_seen true)
        (effect 'start-quick-dialogue intrusion-intro-text)))

    (react
      :when (and intrusion_seen (not police_interview_started) (not police_interview_forced) (>= day 2))
      :then (list
        (effect 'set police_interview_started true)
        (effect 'set police_interview_forced true)
        (effect 'set police_choice_ready true)
        (effect 'set police_summons_seen true)
        (effect 'start-dialogue 'forced_police_interview)))

    (react
      :when (and (clock-filled? blood_clean_progress) (not blood_cleaned))
      :then (list
        (effect 'set blood_cleaned true)))

    (react
      :when (and (clock-filled? investigation_progress) (not item_recovered) (not wounded_man_lead_obtained))
      :then (list
        (effect 'set wounded_man_lead_obtained true)
        (effect 'add wounded_man_lead 1)
        (effect 'start-quick-dialogue wounded-lead-text)))

    (react
      :when (and police_investigation_done (not item_recovered) (not item_recovery_started) (not item_recovery_forced) (>= day recovery_deadline_day))
      :then (list
        (effect 'set item_recovery_started true)
        (effect 'set item_recovery_forced true)
        (effect 'start-dialogue 'forced_item_recovery)))

    (react
      :when (and item_recovered (not item_recovered_notice_seen))
      :then (list
        (effect 'set item_recovered_notice_seen true)
        (effect 'start-quick-dialogue item-recovered-text)))

    (react
      :when (and item_auth_sent (not vera_thread_unlocked) (>= day vera_thread_notice_day))
      :then (list
        (effect 'set vera_thread_unlocked true)
        (effect 'start-quick-dialogue vera-thread-text)))

    (react
      :when (and item_auth_sent (not auth_done) (>= day auth_done_day))
      :then (list
        (effect 'set auth_done true)
        (effect 'clock+ auth_wait_progress 3)
        (effect 'start-quick-dialogue auth-result-text)))

    (react
      :when (and (clock-filled? frederick_trace_progress) (not frederick_real_lead_found))
      :then (list
        (effect 'set frederick_real_lead_found true)
        (effect 'start-quick-dialogue hotel-lead-text)))

    (react
      :when (and (clock-filled? vera_follow_progress) (not vera_apartment_found))
      :then (list
        (effect 'set vera_apartment_found true)
        (effect 'start-quick-dialogue follow-done-text)))

    (react
      :when (and (clock-filled? gambler_debt_progress) (not casino_unlocked))
      :then (list
        (effect 'set casino_unlocked true)
        (effect 'start-quick-dialogue casino-found-text)))

    (react
      :when (and (clock-filled? logic_book) (not logic_book_done))
      :then (list
        (effect 'set logic_book_done true)
        (effect 'upgrade-spirit-value 'logic 1)
        (effect 'start-quick-dialogue book-logic-text)))
    (react
      :when (and (clock-filled? perception_book) (not perception_book_done))
      :then (list
        (effect 'set perception_book_done true)
        (effect 'upgrade-spirit-value 'perception 1)
        (effect 'start-quick-dialogue book-perception-text)))
    (react
      :when (and (clock-filled? willpower_book) (not willpower_book_done))
      :then (list
        (effect 'set willpower_book_done true)
        (effect 'upgrade-spirit-value 'willpower 1)
        (effect 'start-quick-dialogue book-willpower-text)))

    (react
      :when (and rehab_started (clock-filled? rehab_progress) (not rehab_done))
      :then (list
        (effect 'set rehab_done true)
        (effect 'add health 3)
        (effect 'start-quick-dialogue rehab-done-text)))))

(define world-tasks
  (list
    (task
      :kind '主线
      :title "几天之后去取东西"
      :desc "那个男人让你第 5 天去取回东西。警察、血迹、死者线索都是你可以提前处理的事。"
      :active (and intrusion_seen (not item_auth_sent))
      :completed item_auth_sent
      :failed item_recovery_failed
      :steps (list))
    (task
      :kind '主线
      :title "等待鉴定结果"
      :desc "神秘物品已经送去鉴定。结果出来之前，你只能继续撑住这座城。"
      :active (and item_auth_sent (not auth_done))
      :completed auth_done
      :failed false
      :steps (list))
    (task
      :kind '主线
      :title "寻找薇拉"
      :desc "弗雷德里克让你找到他的妻子，但这件事从一开始就不太对。"
      :active (and vera_thread_unlocked (not chapter_2_done))
      :completed chapter_2_done
      :failed false
      :steps (list
        (step :title "接下薇拉的委托" :completed vera_commission_taken)
        (step :title "和弗雷德里克谈话" :completed frederick_talk_done)
        (step :title "调查弗雷德里克的踪迹" :completed frederick_real_lead_found)
        (step :title "和旅馆老板谈" :completed hotel_boss_talk_done)
        (step :title "潜入望月旅馆" :completed hotel_infiltrated)
        (step :title "跟踪到公寓" :completed vera_apartment_found)
        (step :title "完成公寓对峙" :completed chapter_2_done)))
    (task
      :kind '支线
      :title "赌徒与赌场"
      :desc "那个绝望的赌徒知道地下入口在哪。借钱、套话，或者让他在赌局里露怯。"
      :active (and gambler_met (not casino_unlocked))
      :completed casino_unlocked
      :failed false
      :steps (list))
    (task
      :kind '压力
      :title "警方调查"
      :desc "警方想尽快结案。你可以主动去警局配合调查；拖到第二天，他们会亲自上门。"
      :active (and intrusion_seen (not police_investigation_done))
      :completed police_investigation_done
      :failed (and police_interview_forced (not police_investigation_done))
      :steps (list))))

(content
  :meta (meta :key 'city_1 :title "贝城县" :desc "雨夜闯入者、警方笔录、薇拉委托，以及被一点点揭开的城市。")
  :state world-state
  :reacts world-reacts
  :tasks world-tasks
  :root
  (node
    :title "贝城县"
    :desc "贝城县不大。办公室、诊所、酒吧、老街和那些没写在地图上的入口，足够装下一个人继续追问的代价。"
    :show-clocks (list (when (and intrusion_seen (not item_recovered) (not wounded_man_lead_obtained)) investigation_progress))
    :children (list
      (办公室)
      (街边摊贩)
      (黑市)
      (正规诊所)
      (书店)
      (警局)
      (仓库)
      (when vera_thread_unlocked (酒吧))
      (when vera_commission_taken (老街))
      (when frederick_real_lead_found (望月旅馆))
      (when vera_apartment_found (公寓))
      (when casino_unlocked (赌场)))))
