(include "helper.scm")
(include "common_clock_macros.scm")
(include "city/bookshop.scm")
(include "city/shared_work.scm")
(include "city/scenes/building.scm")
(include "city/scenes/rich_enclave.scm")
(include "city/scenes/street.scm")
(include "city/scenes/waste.scm")

;; 城市内容现在按“生存底盘 + 主线章节”组织：
;; - 诊所、黑市、书店、摊贩、仓库等长期功能保留。
;; - 第一章围绕中枪男人闯入、警方调查、取回神秘物品。
;; - 送去鉴定后的第二天开启薇拉委托线；鉴定结果稍后并入主线信息。

(define intrusion-intro-text
  "# 雨夜闯入者\n\n# speaker: 科尔\n门被撞开的时候，我正试着让一杯冷咖啡变得像晚饭。\n\n# speaker: 男人\n他捂着腹部，血从指缝里往外冒。枪伤。不是新手打的，也不是警告用的。\n\n# speaker: 男人\n“他们会来找这个。”\n\n# speaker: 科尔\n他把一个包着油纸的小东西塞进抽屉，倒在我的地板上。十分钟后，警笛停在楼下。")

(define police-summons-text
  "# 警方调查\n\n# speaker: 警探\n“一个中枪的男人死在你的办公室里。科尔，你最好让我今天就能把这件事写完。”\n\n# speaker: 科尔\n他要的不是真相，是一份能合上的报告。")

(define wounded-lead-text
  "# 死者线索\n\n# speaker: 科尔\n零碎的话拼在一起：一个外地口音的男人，最近在码头、饭店后门和医院登记处附近出现过。\n\n# speaker: 科尔\n他不是误闯进我的办公室。他是没能跑到下一个地方。")

(define vera-bar-empty-text
  "# 酒吧空回音\n\n# speaker: 科尔\n酒保记得薇拉喝过什么，不记得她跟谁离开。或者说，他不想记得。")

(define vera-waste-empty-text
  "# 废弃区空回音\n\n# speaker: 科尔\n薇拉来过这里。废弃区的人不认脸，只认鞋印和脚步声——而她身后跟着的，不止一个人的脚印。\n\n# speaker: 科尔\n她没有把真正的线索留在这里。但我知道了：她不是唯一一个在这片废墟里走过的人。")

(define vera-street-shoemaker-text
  "# 修鞋铺\n\n# speaker: 修鞋匠\n“她从望月旅馆出来的时候，手里拿着男人的外套。不是她的尺码，也不是她会喜欢的款式。”\n\n# speaker: 科尔\n三个地方都走过了。酒吧在回避，废弃区只剩脚印，老街递出了真正的线头。")

(define hotel-lead-text
  "# 旅馆线索\n\n# speaker: 科尔\n酒吧里的人在回避，废弃区的脚印不止她一个人。但真正把线头递到我手上的，是修鞋匠那句：“她从望月旅馆出来时，手里拿着男人的外套。”\n\n# speaker: 科尔\n旅馆。就是这里了。")

(define hotel-boss-text
  "# 望月旅馆老板\n\n# speaker: 老板\n“我不记客人的脸，也不记客人的名字。”\n\n# speaker: 科尔\n“那你记什么？”\n\n# speaker: 老板\n“谁付钱让我别开门。”")

(define follow-done-text
  "# 跟踪\n\n# speaker: 科尔\n旅馆后门出来的人没有回头。他走过两条街，进了一栋没有门牌的公寓。\n\n# speaker: 科尔\n薇拉，或者知道薇拉在哪的人，就在里面。")

(define auth-ready-text
  "# 雷奥的消息\n\n# speaker: 科尔\n雷奥那边递了话过来。初步结果出来了，要我去把东西领走。")

(define leo-preliminary-text
  "# 雷奥的初步鉴定\n\n# speaker: 雷奥\n“东西是真的旧，不是昨晚才从谁口袋里掉出来的旧。它和某桩更早的事沾着边，但我还没法现在就把整条线说死。”\n\n# speaker: 科尔\n一份不完整的鉴定，有时候比完整的更危险。因为你会忍不住自己把空白补上。")

(define cases-link-text
  "# 两案关联假设\n\n# speaker: 科尔\n薇拉去过望月旅馆，中枪男人也在替某样不该流出来的东西奔命。\n\n# speaker: 科尔\n它们还不是同一个案子，但已经开始踩进同一条影子里了。")

(define blonde-flirt-text
  "# 调情\n\n# speaker: 金发女郎\n“你看起来不像来喝酒的，科尔。你像来让自己忘掉点什么。”\n\n# speaker: 科尔\n她故意靠得很近，把玩笑贴着耳边说，也顺手量了量我会不会往前走。")

(define blonde-cold-text
  "# 冷淡回应\n\n# speaker: 金发女郎\n她只抬了下眼，手里还在擦杯子。\n\n# speaker: 金发女郎\n“再点一杯。等你真想聊天的时候，再来找我。”\n\n# speaker: 科尔\n她不是不认识我，她只是还没决定要不要把时间花在我身上。")

(define blonde-reward-text
  "# 她给你的奖励\n\n# speaker: 金发女郎\n“今晚你算帮了我一次。”\n\n# speaker: 科尔\n她把一个吻、一句贴耳的话，还有一张写着地址的酒杯垫包成同一种暧昧，像在故意模糊哪样才是真的报酬。")

(define blonde-mary-text
  "# 旧名字\n\n# speaker: 金发女郎\n“你要真在找薇拉，就去问问玛丽。或者至少问问那个和她们都重合过的夜晚。”\n\n# speaker: 科尔\n她说完就不再往下讲，像把名字借给我，却不打算替我承担后果。")

(define gambler-debt-text
  "# 追债人\n\n# speaker: 赌徒\n“老街下面有个只认暗号的局。有人在那里买路，也有人在那里买身份。”\n\n# speaker: 科尔\n他说完，把一张揉皱的下注单塞给我，又说三天后去废弃区钟楼下等他。要是他还能自由走路的话。")

(define gambler-clocktower-text
  "# 钟楼之约\n\n# speaker: 科尔\n三天到了。赌徒没准时出现，但钟楼下压着半张潮湿的票根。")

(define casino-found-text
  "# 赌场入口\n\n# speaker: 老千\n“别在酒吧问地下入口。会显得你太干净。”\n\n# speaker: 科尔\n他把地址写在火柴盒里侧。字很小，赌债很大。")

(define auth-sent-text
  "# 送去鉴定\n\n# speaker: 科尔\n东西已经交给鉴定人。他说需要六天。")

(define auth-result-text
  "# 鉴定结果\n\n# speaker: 鉴定人\n\"这件东西的年代比你想象的久。久到不该出现在这里。\"")

(define blonde-done-text
  "# 金发女郎\n\n# speaker: 科尔\n第八杯酒放在她面前时，她终于没再像之前那样只是接过就放下。她看了我一眼——第一次带着真正的注意，不是调情，而是评估。")

(define item-recovered-text
  "# 取回物品\n\n# speaker: 科尔\n东西拿到了。现在的问题是——该留着它，还是该用它。")

(define rehab-intro-text
  "# 开始康复治疗\n\n# speaker: 科尔\n诊所的大夫看了看我的伤，说没有快速的办法。\"每天来后面的康复室练一练，慢但管用。\"他说。八块钱换一个疗程，算是我在这城里最便宜的交易。")

(define rehab-done-text
  "# 康复训练完成\n\n# speaker: 科尔\n最后一组动作做完，身体终于不再像一台生锈的机器。虽然离痊愈还远，但至少能喘一口顺畅的气了。\n\n恢复了 3 点健康。")

(define (make-investigate-action title desc clock suit)
  (action
    :title title
    :desc desc
    :check (check
      :suits (list suit)
      :risk 'mid
      :ok (outcome (list (effect 'clock+ clock 2)) "线索露出了一小截。你把它按在纸上。")
      :partial (outcome (list (effect 'clock+ clock 1) (effect 'add energy -1)) "你得到了一点碎片，足够继续往下问。")
      :fail (outcome (list (effect 'add energy -1)) "你问得太快，周围的人开始闭嘴。"))))

(define (办公室)
  (node
    :title "办公室"
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
          :conditions (list (has-item 'mysterious_item 1 "需要神秘物品") (field-at-least 'money 50 "需要 50 元鉴定费"))
          :inputs (list (item 'money 50 "鉴定费") (item 'mysterious_item 1 "神秘物品"))
          :effects (list
            (effect 'set item_auth_sent true)
            (effect 'set auth_done_day (+ day 6))
            (effect 'start-quick-dialogue auth-sent-text))))
      (when (and auth_done (not leo_report_collected))
        (action
          :title "领取雷奥的初步鉴定"
          :desc "雷奥那边已经有了初步结论。现在去把它拿回来。"
          :effects (list
            (effect 'set leo_report_collected true)
            (effect 'start-quick-dialogue leo-preliminary-text)))))))

(define (街边摊贩)
  (node
    :title "街边摊贩"
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
      (make-work-action "帮摊贩收摊洗碗" "低风险，钱少，但至少不会把腰和命都押在仓库里。" 意志 'low 6 4 2 0)
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

(define (黑市)
  (node
    :title "黑市"
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
          :ok (outcome (list (effect 'add health 3)))
          :partial (outcome (list (effect 'add health 2)))
          :fail (outcome (list (effect 'add health 2) (effect 'add energy -1)))))
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

(define (正规诊所)
  (node
    :title "正规诊所"
    :desc "白墙、玻璃柜、登记表。正规两个字的意思是：他们会救你，也会记住你。"
    :position '(655 280)
    :show-clocks (list (when (and rehab_started (not rehab_done)) rehab_progress) (when (and rehab2_started (not rehab2_done)) rehab2_progress) (when (and intrusion_seen (not item_recovered) (not wounded_man_lead_obtained)) investigation_progress))
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
      (when (or (not rehab2_started) rehab2_done)
        (action
          :title "开始康复治疗（简易）"
          :desc "八块钱开一个简易康复疗程。低配但直接，可用三次。"
          :inputs (list (item 'money 8 "疗程费用"))
          :effects (list
            (effect 'set rehab2_started true)
            (effect 'set rehab2_done false)
            (effect-reset-clock rehab2_progress))))
      (when (and rehab2_started (not rehab2_done) (not (clock-filled? rehab2_progress)))
        (action
          :title "进行简易康复训练"
          :desc "投入行动卡训练一次。效果看发挥，次数用完为止。"
          :check (check
            :suits (list 意志)
            :risk 'low
            :ok (outcome (list (effect 'clock+ rehab2_progress 1) (effect 'add health 1)))
            :partial (outcome (list (effect 'clock+ rehab2_progress 1) (effect 'add energy 1)))
            :fail (outcome (list (effect 'clock+ rehab2_progress 1))))))
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

(define (警局)
  (node
    :title "警局"
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

(define (仓库)
  (node
    :title "仓库"
    :desc "仓库按小时结钱，也按小时消耗人。白天搬货，夜里有人谈不该谈的路线。"
    :position '(40 520)
    :show-clocks (list (when (and intrusion_seen (not item_recovered) (not wounded_man_lead_obtained)) investigation_progress))
    :actions (list
      (make-work-action "搬货打散工" "高风险，现金来得快，代价也直接。坏结果会伤到身体。" 意志 'high 16 11 6 1)
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

(define (酒吧)
  (node
    :title "酒吧"
    :desc "酒吧白天像咖啡馆，晚上像供词室。这里没有秘密，只有还没轮到你听见的消息。"
    :position '(245 520)
    :show-clocks (list gambling_debt (when (and blonde_intro_seen (not blonde_drinks_done)) blonde_drink_progress))
    :actions (list
      (action
        :title "点一杯酒"
        :desc (if (not vera_thread_unlocked)
          "八块钱一杯。酒不能解决问题，但能补一点精力。"
          "八块钱一杯。她还在吧台的那一头，但现在只是忙着招呼别的客人。")
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
          :suits (list 感知)
          :risk 'high
          :ok (outcome (list (effect 'add money 24)) "你读懂了对面那点迟疑，今晚的酒钱有人替你付。")
          :partial (outcome (list (effect 'add money 8) (effect 'add energy -1)) "你赢回一点，但坐得太久，头也开始发沉。")
          :fail (outcome (list (effect 'clock+ gambling_debt 1) (effect 'add energy -1)) "牌面翻下去，你只剩下一笔被人记住的小账。")))
      ;; 薇拉主线 — 电话中已接下委托，直接去三个地方打听
      (when (and vera_thread_unlocked (not vera_bar_checked))
        (action
          :title "在酒吧问薇拉最近的消息"
          :desc "先从最容易开口的地方问起。这里的人通常先记得酒，再记得脸。"
          :effects (list
            (effect 'set vera_bar_checked true)
            (effect 'set vera_bar_clue true)
            (effect 'start-quick-dialogue vera-bar-empty-text))))
      (when (and vera_thread_unlocked (not blonde_intro_seen))
        (action
          :title "和金发女郎交谈"
          :desc "她人在那里，但还不打算把注意力真正放到你身上。也许多点几杯酒，她会愿意多看你一眼。"
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
            (effect 'add energy -1)
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
            (effect 'start-quick-dialogue blonde-mary-text)))))))

(define (望月旅馆)
  (node
    :title "望月旅馆"
    :desc "招牌灯一半亮着，一半像从来没亮过。老板记性很差，收费时除外。"
    :position '(860 520)
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

(define (公寓)
  (node
    :title "公寓"
    :desc "没有门牌的公寓楼，走廊闻起来像潮墙、廉价香水和旧火药。"
    :position '(1065 520)
    :actions (list
      (when (and vera_apartment_found (not chapter_2_done))
        (action
          :title "进入公寓"
          :desc "房门没有锁。里面有人等你，枪口先开口。"
          :effects (list
            (effect 'set standoff_started true)
            (effect 'start-encounter '公寓枪对峙))))
      (when (and vera_apartment_found (not chapter_2_done))
        (action
          :title "进入公寓（反应骰测试）"
          :desc "同一个房间，同一把枪。测试薇拉在休整时也会反应的版本。"
          :effects (list
            (effect 'set standoff_started true)
            (effect 'start-encounter '公寓枪对峙2))))
      (when (and vera_apartment_found (not chapter_2_done))
        (action
          :title "进入公寓（Claude 版）"
          :desc "测试 Claude 写的三时钟版本：缓和、危险、距离。"
          :effects (list
            (effect 'set standoff_started true)
            (effect 'start-encounter '公寓对峙))))
      (when (and vera_apartment_found (not chapter_2_done))
        (action
          :title "进入公寓（关系版测试）"
          :desc "测试枪、情绪、距离三条关系轴的版本；夺枪失败后会关闭夺枪路线。"
          :effects (list
            (effect 'set standoff_started true)
            (effect 'start-encounter '公寓对峙3关系版)))))))

(define (赌场)
  (node
    :title "赌场"
    :desc "地下室、绿绒桌、假笑和真债。这里能赢钱，也能把明天提前输掉。"
    :position '(1270 520)
    :actions (list
      (make-work-action "替赌场看一晚场子" "不问问题，只看住门口。" 意志 'high 18 12 6 1))))

(define (情景测试C)
  (node
    :title "情景测试C"
    :desc "临时测试入口。这里不接主线，只用来快速比较几个情景模型的手感。"
    :position '(1460 520)
    :actions (list
      ;; 不错, 但是数值还是单人的, 一旦加了一个队友, 情况就不同了
      (action
        :title "测试：仓库撤退"
        :desc "持续涌现敌人、通道和出口推进之间的分诊。"
        :effects (list (effect 'start-encounter '测试仓库撤退)))
      (action
        :title "测试：切断与潜入"
        :desc "操作区域改变环境状态，再反过来影响保险箱难度。"
        :effects (list (effect 'start-encounter '测试切断潜入)))
      (action
        :title "测试：关系平衡"
        :desc "在获取情报时维持安全关系区间，避免冷掉或越界。"
        :effects (list (effect 'start-encounter '测试关系平衡)))
      (action
        :title "测试：关系效率"
        :desc "关系决定情报开采效率，比较先投资关系与直接追问的收益。"
        :effects (list (effect 'start-encounter '关系平衡-效率)))
      (action
        :title "测试：意愿话题"
        :desc "反应骰表示她当前想聊什么，顺势攒筹码或强行引向情报。"
        :effects (list (effect 'start-encounter '关系平衡-意愿骰)))
      (action
        :title "测试：茶楼搜刮"
        :desc "三处区域警惕重新分布，每个 cycle 两个行动，测试干扰与搜刮路线。"
        :effects (list (effect 'start-encounter '测试茶楼三处搜刮)))

      ;; 如果是多人, 那么需求三个线索的不同性质的行为就变得有趣了
      (action
        :title "测试：档案室拼图"
        :desc "线索越多分析越简单，但总时间不够。"
        :effects (list (effect 'start-encounter '测试档案室拼图)))
      
      (action
        :title "投资降低风险-翻看账本"
        :desc "制造混乱打开短窗口，或直接偷看承担暴露。"
        :effects (list (effect 'start-encounter '投资降低风险-翻看账本)))

      ;; 感觉不太对劲, 这个就是感觉摸不到头脑, 不知道该有什么策略
      (action
        :title "测试：姿态对抗"
        :desc "固定姿态循环、反应骰和针对性破绽行动。"
        :effects (list (effect 'start-encounter '测试姿态对抗)))

      ;; 这是一个时间/精力投资, 适合当做其中一个机制, 但不适合全部
      (action
        :title "投资机制-赌场后台"
        :desc "代币、准备时间、负期望裸赌与正期望规则赌博。"
        :effects (list (effect 'start-encounter '投资机制-赌场后台)))
      )))

(define world-vars
  (append
    bookshop-vars
    building-vars
    rich-enclave-vars
    waste-vars
    (list
      (var 'intro_seen false)
      (var 'intrusion_seen false)
      (var 'chapter_2_started false)
      (var 'main_resolved false)

      (var 'recovery_deadline_day 5)
      (var 'police_interview_started false)
      (var 'police_interview_forced false)
      (var 'police_choice_ready false)
      (var 'police_investigation_done false)
      (var 'police_knows_true_info false)
      (var 'police_got_fake_info false)
      (var 'police_refused_info false)
      (var 'police_suspicious false)
      (var 'police_summons_seen false)
      (var 'blood_clean_progress (clock :title "血迹清理" :desc "清理办公室里的血迹。未清理时休息效果更差。" :initial 0 :max 3))
      (var 'blood_cleaned false)
      (var 'investigation_progress (clock :title "死者线索" :desc "调查3处线索，拼出中枪男人的来路。" :initial 0 :max 3))
      (var 'stall_investigated false)
      (var 'market_investigated false)
      (var 'clinic_investigated false)
      (var 'warehouse_investigated false)
      (var 'wounded_man_lead_obtained false)
      (var 'item_recovery_started false)
      (var 'item_recovery_forced false)
      (var 'item_recovered false)
      (var 'item_recovered_notice_seen false)
      (var 'item_recovery_failed false)
      (var 'item_auth_sent false)
      (var 'vera_thread_notice_day 0)
      (var 'vera_thread_unlocked false)
      (var 'vera_unlock_timer (clock :title "" :desc "" :initial 0 :max 2))
      (var 'auth_done_day 0)
      (var 'auth_done false)
      (var 'leo_report_collected false)
      (var 'cases_link_hypothesis_done false)
      (var 'auth_wait_progress (clock :title "鉴定等待" :desc "鉴定人正在检查神秘物品。" :initial 0 :max 6))

      (var 'vera_commission_taken false)
      (var 'frederick_talk_done false)
      (var 'vera_bar_checked false)
      (var 'vera_bar_clue false)
      (var 'vera_street_checked false)
      (var 'vera_waste_checked false)
      (var 'frederick_real_lead_found false)
      (var 'hotel_boss_talk_done false)
      (var 'hotel_infiltrated false)
      (var 'vera_follow_progress (clock :title "跟踪目标" :desc "从旅馆后门跟到真正的公寓。" :initial 0 :max 3))
      (var 'vera_apartment_found false)
      (var 'standoff_started false)
      (var 'chapter_2_done false)

      (var 'gambler_met false)
      (var 'gambler_debt_choice_done false)
      (var 'gambler_return_day 0)
      (var 'gambler_clocktower_ready false)
      (var 'casino_unlocked false)
      (var 'blonde_intro_seen false)
      (var 'blonde_cold_chatted false)
      (var 'blonde_flirted false)
      (var 'blonde_customer_chased false)
      (var 'blonde_secret_shared false)
      (var 'blonde_mary_shared false)
      (var 'blonde_drink_progress (clock :title "金发女郎·好感" :desc "给她点酒累计好感。填满后可以和她调情。" :initial 0 :max 8))
      (var 'blonde_drinks_done false)

      (var 'gang_relation 0)
      (var 'finance_relation 0)
      (var 'police_relation 0)

      (var 'infected false)
      (var 'gunshot_wound false)
      (var 'rehab_started false)
      (var 'rehab_done false)
      (var 'rehab_progress (clock :title "康复训练进度" :desc "每次训练进度+1，填满后恢复3点健康。" :initial 0 :max 4))
      (var 'rehab2_started false)
      (var 'rehab2_done false)
      (var 'rehab2_progress (clock :title "简易康复训练" :desc "每次训练恢复少量体力，可用3次。" :initial 0 :max 3)))))

(define world-reacts
  (append
    (list
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
      :when (and item_auth_sent (= vera_thread_notice_day 0))
      :then (list
        (effect 'set vera_thread_notice_day (+ day 1))))

    (react
      :when (and item_auth_sent (not vera_thread_unlocked) (>= day vera_thread_notice_day) (> vera_thread_notice_day 0))
      :then (list
        (effect 'set vera_thread_unlocked true)
        (effect 'set frederick_talk_done true)
        (effect 'set vera_commission_taken true)
        (effect 'set chapter_2_started true)
        (effect 'start-dialogue 'frederick_phone_intro)))

    (react
      :when (and item_auth_sent (not auth_done) (>= day auth_done_day))
      :then (list
        (effect 'set auth_done true)
        (effect 'clock+ auth_wait_progress 6)
        (effect 'start-quick-dialogue auth-ready-text)))

    (react
      :when (and leo_report_collected hotel_infiltrated (not cases_link_hypothesis_done))
      :then (list
        (effect 'set cases_link_hypothesis_done true)
        (effect 'start-quick-dialogue cases-link-text)))

    (react
      :when (and vera_bar_checked vera_waste_checked vera_street_checked (not frederick_real_lead_found))
      :then (list
        (effect 'set frederick_real_lead_found true)
        (effect 'start-quick-dialogue hotel-lead-text)))

    (react
      :when (and (clock-filled? vera_follow_progress) (not vera_apartment_found))
      :then (list
        (effect 'set vera_apartment_found true)
        (effect 'start-quick-dialogue follow-done-text)))

    (react
      :when (and gambler_debt_choice_done (not gambler_clocktower_ready) (>= day gambler_return_day) (> gambler_return_day 0))
      :then (list
        (effect 'set gambler_clocktower_ready true)
        (effect 'start-quick-dialogue gambler-clocktower-text)))

    (react
      :when (and rehab_started (clock-filled? rehab_progress) (not rehab_done))
      :then (list
        (effect 'set rehab_done true)
        (effect 'add health 3)))
    (react
      :when (and rehab2_started (clock-filled? rehab2_progress) (not rehab2_done))
      :then (list
        (effect 'set rehab2_done true)))
    (react
      :when (and chapter_2_started (clock-filled? blonde_drink_progress) (not blonde_drinks_done))
      :then (list
        (effect 'set blonde_drinks_done true)
        (effect 'start-quick-dialogue blonde-done-text))))
    bookshop-reacts
    building-reacts
    rich-enclave-reacts
    waste-reacts))

(define world-tasks
  (list
    (task
      :kind '主线
      :title "几天之后去取东西"
      :desc "那个男人让你第 5 天去取回东西。警察、血迹、死者线索都是你可以提前处理的事。"
      :active (and intrusion_seen (not item_recovered))
      :completed item_recovered
      :failed item_recovery_failed
      :steps (list))
    (task
      :kind '主线
      :title "处理神秘物品的鉴定"
      :desc "东西已经拿回来了。把它送去雷奥那里，等六天，拿回初步结论。等薇拉那条线也走到旅馆，再看看这两案是不是踩进了同一片影子。"
      :active (and item_recovered (not cases_link_hypothesis_done))
      :completed cases_link_hypothesis_done
      :failed false
      :steps (list
        (step :title "把东西送去鉴定" :completed item_auth_sent)
        (step :title "等待鉴定，需要 6 天" :completed auth_done)
        (step :title "领取雷奥的初步鉴定" :completed leo_report_collected)
        (step :title "提出两案关联假设" :completed cases_link_hypothesis_done)))
    (task
      :kind '主线
      :title "寻找薇拉"
      :desc "德雷福雷在电话里给了三个方向：酒吧、老街、废弃区。至少有一个会留下她的痕迹。"
      :active (and vera_thread_unlocked (not chapter_2_done))
      :completed chapter_2_done
      :failed false
      :steps (list
        (step :title "在老街三个地方打听薇拉的消息" :completed frederick_real_lead_found)
        (step :title "和旅馆老板谈判" :completed hotel_boss_talk_done)
        (step :title "潜入望月旅馆" :completed hotel_infiltrated)
        (step :title "跟踪得到的线索" :completed vera_apartment_found)
        (step :title "持枪对峙" :completed chapter_2_done)))
    (task
      :kind '支线
      :title "酒吧金发女郎"
      :desc "她看起来放荡、轻佻、主动引诱，但这也是她在老街活下来的方式。"
      :active (and blonde_intro_seen (not blonde_mary_shared))
      :completed blonde_mary_shared
      :failed false
      :steps (list
        (step :title "点满八杯酒，让她注意到你" :completed blonde_drinks_done)
        (step :title "和金发女郎交谈：她开始认真看你" :completed blonde_flirted)
        (step :title "和金发女郎交谈：替她处理占便宜的客人" :completed blonde_customer_chased)
        (step :title "和金发女郎交谈：收下暧昧奖励" :completed blonde_secret_shared)
        (step :title "和金发女郎交谈：听她提起旧名字和重合的夜晚" :completed blonde_mary_shared)))
    (task
      :kind '支线
      :title "赌徒与赌场"
      :desc "赌徒知道老街下面那个只认暗号的局。先把他从巷口的麻烦里拖出来——剩下的会回来。"
      :active (and gambler_met (not casino_unlocked))
      :completed casino_unlocked
      :failed false
      :steps (list
        (step :title "碰上被按在巷口的赌徒" :completed gambler_met)
        (step :title "处理追债人留下的麻烦" :completed gambler_debt_choice_done)
        (step :title "检查下注单上的暗号" :completed casino_unlocked)))
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
  :state world-vars
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
      (酒吧)
      (when (or vera_thread_unlocked (and exploitation_incident_active (= exploitation_incident_location 'street))) (老街))
      (废弃区)
      (大厦)
      (富人飞地)
      (when frederick_real_lead_found (望月旅馆))
      (when vera_apartment_found (公寓))
      (when casino_unlocked (赌场))
      (情景测试C))))
