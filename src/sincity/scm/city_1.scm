(include "helper.scm")
(include "common_clock_macros.scm")

;; 这个文件按“人会怎么理解城市生活”组织：
;; 1. 先放会被触发的叙事文本。
;; 2. 再放反复使用的行动模板。
;; 3. 然后逐个地点写“这个地方能做什么”。
;; 4. 最后集中写世界状态和因果反应 react。

(define case-intro-text
  "# 旧案\n\n# speaker: 科尔\n报纸夹在门缝里，已经被晨雾泡软。版面角落有一行不起眼的小字：红房间旧址将被拆除。\n\n# speaker: 科尔\n十年前，我在那份案卷上签过字。后来有人把案子拿走，把门关上，把所有人的名字从纸上擦掉。\n\n# speaker: 科尔\n我本来不想再管。只是那张照片里，站在红房间门口的女人，长得太像薇拉。")

(define old-case-checked-text
  "# 档案室\n\n# speaker: 科尔\n红房间案卷不在普通柜里。值班警员说它十年前就结了，结案原因写得很干净：证据不足。\n\n# speaker: 科尔\n太干净了。干净得像有人拿漂白水洗过。卷宗最后夹着一份被退回的问询单，签名栏里有一个我认识的姓氏：塞勒。")

(define police-fine-text
  "# 罚单\n\n# speaker: 警员\n“科尔先生，有人说你最近重新开张做生意，却没补齐执照税。”\n\n# speaker: 科尔\n他把罚单放在桌上，手指按住日期。\n\n# speaker: 警员\n“五天。别让我们再跑一趟。我们跑第二趟的时候，通常不带钢笔。”")

(define police-fine-paid-text
  "# 收据\n\n# speaker: 科尔\n钱交出去以后，他们给了我一张收据。纸是真的，理由是假的。\n\n# speaker: 科尔\n柜台后面的警员没有看我，只说：“别再翻旧东西了，科尔。”")

(define police-fine-failed-text
  "# 第二趟\n\n# speaker: 科尔\n他们果然跑了第二趟。没有钢笔，只有两副拳头和一句公事公办。\n\n# speaker: 警员\n“有些案子已经定了。你以前穿过这身皮，应该懂规矩。”")

(define gang-warning-text
  "# 巷口记号\n\n# speaker: 科尔\n楼下墙上多了一个粉笔记号。不是催债的记号，是警告。\n\n# speaker: 打手\n“有人花钱让我们提醒你：别再问红房间。三天后，如果你还没听懂，我们换一种说法。”")

(define gang-pressure-done-text
  "# 警告之后\n\n# speaker: 科尔\n巷子重新安静下来。我还站着，但这座城已经给出了答案：红房间不是旧案，是还在跳的脉搏。")

(define first-tracker-text
  "# 跟踪者\n\n# speaker: 科尔\n傍晚回公寓时，我在橱窗反光里看见同一顶灰帽子第三次停下。\n\n# speaker: 科尔\n警察用罚单，黑帮用拳头。还有人只用眼睛。")

(define enclave-found-text
  "# 飞地深处\n\n# speaker: 科尔\n那片住宅背后的窄路比地图上画得更深。花墙、铁门、无人认领的后巷，一层一层把县城切开。\n\n# speaker: 科尔\n我在尽头找到一间小花店。玻璃上贴着暂停营业，里面却有人浇水。")

(define flower-income-text
  "# 花店分红\n\n# speaker: 科尔\n清晨门缝下塞进一个信封。里面的钱不多，但干净。至少看起来干净。")

(define woman-intro-text
  "# 酒吧里的女人\n\n# speaker: 女人\n“你是科尔？”\n\n# speaker: 科尔\n“看情况。你问的是欠钱的那个，还是能办事的那个？”\n\n# speaker: 女人\n“如果你能办事，欠钱那部分我可以假装没听说。”")

(define woman-done-text
  "# 一笔人情\n\n# speaker: 女人\n“你没有把事情办漂亮。”\n\n# speaker: 科尔\n“但办成了。”\n\n# speaker: 女人\n她笑了一下，把杯子推过来。\n\n# speaker: 女人\n“以后如果你需要有人替你说话，来这里找我。”")

(define escape-intro-text
  "# 仓库里的男人\n\n# speaker: 男人\n“这城不会放过欠账的人，也不会放过知道太多的人。”\n\n# speaker: 科尔\n“你是哪一种？”\n\n# speaker: 男人\n“准备离开的那一种。缺证件，缺船票，缺钱。你要是也想走，就别把警察引到我身上。”")

(define fake-id-intro-text
  "# 假证件\n\n# speaker: 接头人\n“证件不是商品，科尔。至少不是卖给你这种人的商品。”\n\n# speaker: 科尔\n“那它是什么？”\n\n# speaker: 接头人\n“人情。你替我把一本账册拿回来，我替你弄一个不会在码头第一眼就露馅的名字。”")

(define escape-done-text
  "# 离开贝城县\n\n# speaker: 科尔\n夜里的货车没有开灯。男人坐在驾驶室里，假证件压在仪表盘下，船票贴着我的胸口。\n\n# speaker: 男人\n“上车以后就别回头。”\n\n# speaker: 科尔\n我没有回头。")

(define book-logic-text
  "# 读完：《县城账簿与谎言》\n\n# speaker: 科尔\n数字不会说真话，但它们也不擅长撒谎。读完这本书后，我更知道该从哪里看起。")

(define book-perception-text
  "# 读完：《街口观察法》\n\n# speaker: 科尔\n人们总以为自己藏得很好。其实鞋尖、肩膀和停顿，比嘴诚实多了。")

(define book-willpower-text
  "# 读完：《疼痛之后》\n\n# speaker: 科尔\n有些书不教你赢，只教你不要太快倒下。")

(define rehab-intro-text
  "# 开始康复治疗\n\n# speaker: 科尔\n诊所的大夫看了看我的伤，说没有快速的办法。\"每天来后面的康复室练一练，慢但管用。\"他说。八块钱换一个疗程，算是我在这城里最便宜的交易。")

(define rehab-done-text
  "# 康复训练完成\n\n# speaker: 科尔\n最后一组动作做完，身体终于不再像一台生锈的机器。虽然离痊愈还远，但至少能喘一口顺畅的气了。\n\n恢复了 3 点健康。")

(define gang-liaison-text
  "# 黑帮联络处\n\n# speaker: 科尔\n巷口拐角那面墙上的粉笔记号每天都在变。黑帮的人说，有事会在这里留信。如果赶在期限前想先把事情办了，也可以在这里留一个记号，他们自然会派人来找我。")

(define make-work-action
  (lambda (title desc suit risk ok-money partial-money fail-money fail-health)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk risk
        :ok (outcome "活儿完成得干净。钱到手，身体还能撑。" (list (effect 'add money ok-money) (effect 'add energy -1)))
        :partial (outcome "钱拿到了，但这一天把你磨得发紧。" (list (effect 'add money partial-money) (effect 'add energy -2)))
        :fail (outcome "事情不顺。你拿到一点钱，也付了一点身体的账。" (list (effect 'add money fail-money) (effect 'add energy -2) (when (> fail-health 0) (effect 'add health (- fail-health)))))))))

(define make-book-action
  (lambda (title desc clock suit)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'low
        :ok (outcome "你读进去了，页边的字开始连成路。" (list (effect 'clock+ clock 2)))
        :partial (outcome "你读得慢，但今天没有白坐。" (list (effect 'clock+ clock 1) (effect 'add energy -1)))
        :fail (outcome "纸上的字浮起来，脑子却沉下去。" (list (effect 'add energy -1)))))))

(define make-explore-action
  (lambda (title desc clock suit)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'mid
        :ok (outcome "你把这片地方又摸清了一层。" (list (effect 'clock+ clock 2) (effect 'add energy -1)))
        :partial (outcome "你没有完全迷路，也没有完全找到路。" (list (effect 'clock+ clock 1) (effect 'add energy -1)))
        :fail (outcome "这片地方今天不接纳你。" (list (effect 'add energy -2)))))))

(define make-investigate-action
  (lambda (title desc clock suit)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'mid
        :ok (outcome "线索露出了一小截。你把它按在纸上。" (list (effect 'clock+ clock 2) (effect 'add energy -1)))
        :partial (outcome "你得到了一点碎片，足够继续往下问。" (list (effect 'clock+ clock 1) (effect 'add energy -1)))
        :fail (outcome "你问得太快，周围的人开始闭嘴。" (list (effect 'add energy -1)))))))

(define-node 科尔公寓
  (node
    :desc "一张沙发，一部电话，一只永远没洗干净的杯子。公寓不安全，但至少门锁认识你。"
    :position '(40 280)
    :actions (list
      (action
        :title "在沙发上睡一晚"
        :desc "睡眠会把今天结束掉。醒来时精力少一点，行动卡重新抽取，期限也更近。"
        :effects (list
          (effect 'advance-day)
          (effect 'reset-hand)
          (effect 'set bookshop_entered_today false)
          (when flower_invested (effect 'add money 10))))
      (action
        :title "吃一包随身干粮"
        :desc "不用找摊贩，也不用花今天的钱。吃掉 1 份干粮，立刻恢复 2 点精力。"
        :conditions (list (has-item 'food 1 "需要干粮"))
        :inputs (list (item 'food 1 "干粮"))
        :effects (list (effect 'add energy 2)))
      )))

(define-node 街边摊贩
  (node
    :desc "铁锅、热汤、油烟和零钱。这里不问你从哪里来，只问你要不要加辣。"
    :position '(245 280)
    :actions (list
      (action
        :title "吃一碗热汤"
        :desc "便宜、烫嘴，立刻恢复 2 点精力。"
        :inputs (list (item 'money 6 "饭钱"))
        :effects (list (effect 'add energy 2)))
      (action
        :title "买一包干粮"
        :desc "把 2 点精力恢复存成 1 份干粮，之后可以在公寓里吃掉。贵一点，换的是不用当场吃。"
        :inputs (list (item 'money 10 "干粮钱"))
        :effects (list (effect 'add food 1))))))

(define-node 黑市
  (node
    :desc "修表铺后门、药味、假章和压低的声音。这里什么都能办，只是从不保证干净。"
    :position '(450 280)
    :actions (list
      (when (and (not fake_id_job_done) (not fake_id_job_started))
        (action
          :title "向接头人打听假证件"
          :desc "他能做证件，但他不缺钱。他缺一个愿意替他处理麻烦的人。"
          :effects (list
            (effect 'set fake_id_job_started true)
            (effect 'start-quick-dialogue fake-id-intro-text))))
      (when (and fake_id_job_started (not fake_id_job_done))
        (action
          :title "替接头人拿回账册"
          :desc "这不是购买，是交换。你替他处理一件棘手事，他替你做证件。"
          :effects (list
            (effect 'start-encounter '黑市证件人情))))
      (action
        :title "找黑市医生处理伤口"
        :desc "便宜，不报警。坏处是你最好别仔细看他的器械。"
        :inputs (list (item 'money 12 "诊费"))
        :check (check
          :suits (list 意志)
          :risk 'mid
          :ok (outcome "他手很快，针脚也还算直。" (list (effect 'add health 2)))
          :partial (outcome "伤口处理好了，但你开始发冷。" (list (effect 'add health 2) (effect 'add energy -1)))
          :fail (outcome "处理得太脏。你活下来了，但身体记了一笔账。" (list (effect 'add health 1) (effect 'add energy -2) (effect 'set infected true))))))))

(define-node 正规诊所
  (node
    :desc "白墙、玻璃柜、登记表。正规两个字的意思是：他们会救你，也会记住你。"
    :position '(655 280)
    :show-clocks (list (when (and rehab_started (not rehab_done)) rehab_progress))
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
            (effect-reset-clock rehab_progress)
            (effect 'start-quick-dialogue rehab-intro-text))))
      (when (and rehab_started (not rehab_done) (not (clock-filled? rehab_progress)))
        (action
          :title "进行康复训练"
          :desc "动作不大，但每天坚持会有用。低风险，失败没有惩罚。"
          :check (check
            :suits (list 意志)
            :risk 'low
            :ok (outcome "你今天的状态不错，训练效果很好。" (list (effect 'clock+ rehab_progress 2)))
            :partial (outcome "你坚持完成了训练，虽然有些吃力。" (list (effect 'clock+ rehab_progress 1)))
            :fail (outcome "今天身体不太配合，但至少没有更糟。" (list)))))
      (when gunshot_wound
        (action
          :title "处理枪伤"
          :desc "他们会处理伤口，也会按规定通知警察。"
          :conditions (list (field-at-least 'money 40 "需要 40 元"))
          :inputs (list (item 'money 40 "枪伤诊费"))
          :effects (list
            (effect 'add health 4)
            (effect 'set gunshot_wound false)
            (effect 'add police_relation -1)))))))

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
        (make-book-action
          "读《县城账簿与谎言》"
          "一本讲账本、公司壳和人情债的旧书。读完会提升逻辑。"
          logic_book
          逻辑))
      (when (and bookshop_entered_today (not perception_book_done))
        (make-book-action
          "读《街口观察法》"
          "一本写给巡警的教材，后来流到旧书架上。读完会提升感知。"
          perception_book
          感知))
      (when (and bookshop_entered_today (not willpower_book_done))
        (make-book-action
          "读《疼痛之后》"
          "关于戒断、疼痛和自我约束。读完会提升意志。"
          willpower_book
          意志)))))

(define-node 警局档案室
  (node
    :desc "铁柜、烟味和一排不愿回答问题的人。旧案不会自己开口，尤其是被人关过一次的旧案。"
    :position '(1065 520)
    :actions (list
      (when (not old_case_checked)
        (action
          :title "查十年前红房间旧案"
          :desc "红房间死亡事件的案卷早就结了。你只是想确认它到底怎么结的。"
          :check (check
            :suits (list 逻辑 感知)
            :risk 'mid
            :ok (outcome "你找到了被抽走后又塞回来的几页。" (list (effect 'set old_case_checked true) (effect 'set pressure_started true) (effect 'set pressure_phase 1) (effect 'set police_fine_notice_day (+ day 1)) (effect 'start-quick-dialogue old-case-checked-text) (effect 'add energy -1)))
            :partial (outcome "你没拿到完整卷宗，但看见了足够奇怪的空白。" (list (effect 'set old_case_checked true) (effect 'set pressure_started true) (effect 'set pressure_phase 1) (effect 'set police_fine_notice_day (+ day 1)) (effect 'start-quick-dialogue old-case-checked-text) (effect 'add energy -1)))
            :fail (outcome "档案员不肯放行，但你的老关系还够撬开一道缝。" (list (effect 'set old_case_checked true) (effect 'set pressure_started true) (effect 'set pressure_phase 1) (effect 'set police_fine_notice_day (+ day 1)) (effect 'start-quick-dialogue old-case-checked-text) (effect 'add energy -2) (effect 'add police_relation -1))))))
      (when (and police_fine_active (not police_fine_paid))
        (action
          :title "缴纳执照罚金"
          :desc "这不是罚款，是他们给你开的第一道价码。"
          :conditions (list (field-at-least 'money police_fine_amount "需要缴纳罚金"))
          :inputs (list (item 'money police_fine_amount "执照罚金"))
          :effects (list
            (effect 'set police_fine_paid true)
            (effect 'set police_fine_active false)
            (effect 'set pressure_phase 2)
            (effect 'set gang_warning_notice_day (+ day 2))
            (effect 'start-quick-dialogue police-fine-paid-text)))))))

(define-node 酒吧
  (node
    :desc "酒吧白天像咖啡馆，晚上像供词室。这里没有秘密，只有还没轮到你听见的消息。"
    :position '(1065 280)
    :show-clocks (list woman_trust (when (and old_case_checked (not moon_hotel_unlocked)) city_lead_progress))
    :actions (list
      (action
        :title "买一杯酒"
        :desc "酒不能解决问题，但能补一点精力。"
        :inputs (list (item 'money 8 "酒钱"))
        :effects (list (effect 'add energy 2)))
      (when (= woman_phase 0)
        (action
          :title "和吧台边的女人说话"
          :desc "她先叫出了你的名字。那通常不是好事。"
          :effects (list
            (effect 'set woman_phase 1)
            (effect 'start-quick-dialogue woman-intro-text))))
      (when (= woman_phase 1)
        (action
          :title "替她打听一个名字"
          :desc "她要找的人欠她一句话，也可能欠她一条命。"
          :check (check
            :suits (list 感知)
            :risk 'mid
            :ok (outcome "你在几张桌子之间听到了那个名字。" (list (effect 'clock+ woman_trust 2) (effect 'add energy -1)))
            :partial (outcome "你听到一点线索，她愿意继续相信你。" (list (effect 'clock+ woman_trust 1) (effect 'add energy -1)))
            :fail (outcome "你问得太直，今晚没人再接你的话。" (list (effect 'add energy -1))))))
      (when (and old_case_checked (not moon_hotel_unlocked))
        (make-investigate-action
          "打听薇拉的去向"
          "弗雷德里克的妻子在旧城区出现过。酒吧里总有人见过不该见的人。"
          city_lead_progress
          感知)))))

(define-node 仓库
  (node
    :desc "仓库按小时结钱，也按小时消耗人。白天搬货，夜里有人谈离开的路。"
    :position '(40 520)
    :actions (list
      (make-work-action
        "搬货打散工"
        "现金来得快，代价也直接。"
        意志
        'mid
        24
        16
        8
        1)
      (when (not escape_contact)
        (action
          :title "听仓库男人谈离城"
          :desc "他知道一条离开贝城县的路，但那条路不收空手的人。"
          :effects (list
            (effect 'set escape_contact true)
            (effect 'start-quick-dialogue escape-intro-text))))
      (when (and escape_contact (not passage_known))
        (action
          :title "帮男人处理一件小麻烦"
          :desc "有个装卸工知道得太多。你不必伤人，只要让他闭嘴。"
          :check (check
            :suits (list 意志)
            :risk 'mid
            :ok (outcome "事情压下去了。男人把一张船票交给你。" (list (effect 'set passage_known true) (effect 'add passage_ticket 1) (effect 'add energy -1)))
            :partial (outcome "事情勉强压住，代价是你欠了一个人情。" (list (effect 'set passage_known true) (effect 'add passage_ticket 1) (effect 'add gang_relation -1) (effect 'add energy -1)))
            :fail (outcome "那人跑去找警察。男人很不高兴。" (list (effect 'add police_relation -1) (effect 'add energy -2))))))
      (when (and escape_contact (not main_resolved))
        (action
          :title "和男人一起离开城市"
          :desc "假证件、船票、现金，还有别把警察带到码头的好运气。"
          :conditions (list
            (has-item 'fake_id 1 "需要假证件")
            (has-item 'passage_ticket 1 "需要船票")
            (field-at-least 'money 50 "需要 50 元")
            (field-at-least 'police_relation -1 "警察关系不能太差"))
          :inputs (list
            (item 'money 50 "离城现金")
            (item 'fake_id 1 "假证件")
            (item 'passage_ticket 1 "船票"))
          :effects (list
            (effect 'set escaped_city true)
            (effect 'set main_resolved true)
            (effect 'start-quick-dialogue escape-done-text)
            (effect 'end-game "离开城市" "科尔没有还清所有账，但他让账本留在了贝城县。")))))))

(define-node 飞地区域
  (node
    :desc "县城边缘新修的富人飞地。铁门后面有草坪，铁门外面有被忘掉的小路。"
    :position '(245 520)
    :show-clocks (list enclave_search)
    :actions (list
      (make-explore-action
        "沿着飞地外围探索"
        "你从保安看不见的地方走，试着弄清这片新钱修出来的迷宫。"
        enclave_search
        感知))))

(define-node 花店
  (node
    :desc "花店藏在飞地背面。老板不解释为什么暂停营业，也不解释为什么需要现金。"
    :position '(245 520)
    :actions (list
      (when (not flower_invested)
        (action
          :title "投资花店"
          :desc "一百元买不到一间店，但能买到一个每天清晨都会送来信封的人。"
          :conditions (list (field-at-least 'money 50 "需要 50 元"))
          :inputs (list (item 'money 50 "投资款"))
          :effects (list
            (effect 'set flower_invested true))))
      (when flower_invested
        (action
          :title "查看花店账本"
          :desc "账本不厚，但每一页都说明这笔钱正在慢慢回来。"
          :effects (list
            (effect 'start-quick-dialogue "# 花店账本\n\n# speaker: 科尔\n花店每天清晨结一次账。数字不大，但它们很稳定。")))))))

(define-node 老街
  (node
    :desc "旧铺面、窄楼梯、晾衣绳和熟人的眼神。老街没有明确入口，但你总能从这里找到一点活路。"
    :position '(450 520)
    :show-clocks (list old_street_search (when (and old_case_checked (not moon_hotel_unlocked)) city_lead_progress))
    :actions (list
      (make-explore-action
        "在老街摸路"
        "你问修鞋匠、报童和楼下晒太阳的人，慢慢把老街的关系图拼出来。"
        old_street_search
        感知)
      (when (and old_case_checked (not moon_hotel_unlocked))
        (make-investigate-action
          "追问望月旅馆"
          "有人见过薇拉从一辆灰色轿车旁边走开。线索指向老街尽头的廉价旅馆。"
          city_lead_progress
          逻辑))
      (when (and moon_hotel_unlocked (not hotel_search_done))
        (action
          :title "前往望月旅馆搜寻"
          :desc "薇拉住过的 302 房间还没有被清空。有人付了钱，让它保持原样。"
          :effects (list (effect 'start-encounter '望月旅馆搜寻))))
      (when (clock-filled? old_street_search)
        (action
          :title "从老街人情里拿一张票"
          :desc "有些票不卖给陌生人。幸好你已经不是完全的陌生人。"
          :conditions (list (field-at-least 'money 40 "需要 40 元"))
          :inputs (list (item 'money 40 "打点费用"))
          :effects (list (effect 'add passage_ticket 1)))))))

(define-node 黑帮联络处
  (node
    :desc "巷口拐角有一面用粉笔画记号的墙。黑帮的人说他们会在这里留信。如果想提前把事情办了，也可以在这里等他们的人。"
    :position '(40 420)
    :show-clocks (list gang_countdown_clock)
    :actions (list
      (when (and intro_seen (not main_resolved) (= gang_phase 1) (not gang_task_forced) (not gang_task_result_pending))
        (action
          :title "去处理黑帮的第一件事"
          :desc "教训那几个欠教训的小混混。早办完早了结。"
          :effects (list
            (effect 'set gang_task_forced true)
            (effect 'start-encounter '教训小混混))))
      (when (and intro_seen (not main_resolved) (= gang_phase 2) (not gang_task_forced) (not gang_task_result_pending))
        (action
          :title "去处理黑帮的第二件事"
          :desc "黑帮又找上门了。这次的事更麻烦一点。"
          :effects (list
            (effect 'set gang_task_forced true)
            (effect 'start-encounter '教训小混混))))
      (when (and intro_seen (not main_resolved) (= gang_phase 3) (not gang_task_forced) (not gang_task_result_pending))
        (action
          :title "去处理黑帮的第三件事"
          :desc "最后一件事。办完这桩，账本就暂时能合上。"
          :effects (list
            (effect 'set gang_task_forced true)
            (effect 'start-encounter '教训小混混))))
      (when (not main_resolved)
        (action
          :title "把钱交给黑帮"
          :desc "最直接、也最疼的一种自由：把钱装进信封，送到他们桌上。"
          :conditions (list (field-at-least 'money 100 "需要 100 元"))
          :inputs (list (item 'money 100 "还债现金"))
          :effects (list
            (effect 'set debt_paid true)
            (effect 'set main_resolved true)
            (effect 'end-game "债务结清" "科尔用现金买回了十五天后的早晨。黑帮不再敲门，至少暂时如此。")))))))

(define world-state
  (state
    (intro_seen false)
    (main_resolved false)

    (debt_amount 100)
    (gang_phase 1)
    (gang_days_remaining 5)
    (gang_task_forced false)
    (gang_task_result_pending false)
    (debt_paid false)
    (escaped_city false)

    (case_intro_seen false)
    (old_case_checked false)
    (city_lead_progress (clock :title "薇拉线索" :desc "把红房间旧案和薇拉最近的行踪连起来。" :initial 0 :max 4))
    (moon_hotel_unlocked false)
    (hotel_search_done false)
    (note_street_time false)
    (pills_found false)
    (red_room_clipping false)
    (mb_knows false)
    (corridor_man_seen false)

    (pressure_started false)
    (pressure_phase 0)
    (police_fine_notice_day 0)
    (police_fine_active false)
    (police_fine_deadline 0)
    (police_fine_amount 60)
    (police_fine_paid false)
    (police_fine_failed false)
    (gang_warning_notice_day 0)
    (gang_warning_active false)
    (gang_warning_deadline 0)
    (gang_pressure_forced false)
    (gang_pressure_result_pending false)
    (tracker_seen false)

    (gang_relation 0)
    (finance_relation 0)
    (police_relation 0)

    (logic_book (clock :title "《县城账簿与谎言》" :desc "读完后逻辑 +1。" :initial 0 :max 3))
    (perception_book (clock :title "《街口观察法》" :desc "读完后感知 +1。" :initial 0 :max 3))
    (willpower_book (clock :title "《疼痛之后》" :desc "读完后意志 +1。" :initial 0 :max 3))
    (woman_trust (clock :title "女人的信任" :desc "她会先看你能不能把小事办成。" :initial 0 :max 3))
    (enclave_search (clock :title "飞地探索" :desc "摸清飞地背后的路，可能发现新的地点。" :initial 0 :max 4))
    (old_street_search (clock :title "老街探索" :desc "老街的人情和暗门。" :initial 0 :max 3))
    (gang_countdown_clock (clock :title "剩余天数" :desc "还剩几天截止。" :initial 0 :max 5))

    (logic_book_done false)
    (perception_book_done false)
    (willpower_book_done false)
    (bookshop_entered_today false)
    (woman_phase 0)
    (woman_done false)
    (escape_contact false)
    (fake_id_job_started false)
    (fake_id_job_done false)
    (fake_id_job_failed false)
    (passage_known false)
    (flower_found false)
    (flower_invested false)
    (infected false)
    (gunshot_wound false)
    (rehab_started false)
    (rehab_done false)
    (rehab_progress (clock :title "康复训练进度" :desc "每次训练进度+1，填满后恢复3点健康。" :initial 0 :max 4))))

(define world-reacts
  (reacts
    ;; 开场：先把红房间旧案放到玩家面前，但压力要等玩家真正去查后才启动。
    (react
      :when (not case_intro_seen)
      :then (list
        (effect 'set case_intro_seen true)
        (effect 'set intro_seen true)
        (effect 'start-quick-dialogue case-intro-text)))

    ;; 查旧案后的第二天，警察用执照罚单把压力具体化。
    (react
      :when (and old_case_checked (= pressure_phase 1) (not police_fine_active) (not police_fine_paid) (>= day police_fine_notice_day))
      :then (list
        (effect 'set police_fine_active true)
        (effect 'set police_fine_deadline (+ day 5))
        (effect 'start-quick-dialogue police-fine-text)))

    ;; 罚单逾期后，警察亲自上门。失败也会推动压力链进入下一段。
    (react
      :when (and police_fine_active (not police_fine_paid) (> day police_fine_deadline))
      :then (list
        (effect 'set police_fine_active false)
        (effect 'set police_fine_failed true)
        (effect 'set pressure_phase 2)
        (effect 'set gang_warning_notice_day (+ day 1))
        (effect 'add health -2)
        (effect 'add energy -2)
        (effect 'add police_relation -1)
        (effect 'start-quick-dialogue police-fine-failed-text)))

    ;; 罚单之后，黑帮开始接手施压。
    (react
      :when (and (= pressure_phase 2) (not gang_warning_active) (not gang_pressure_result_pending) (>= day gang_warning_notice_day))
      :then (list
        (effect 'set gang_warning_active true)
        (effect 'set gang_warning_deadline (+ day 3))
        (effect 'start-quick-dialogue gang-warning-text)))

    ;; 黑帮警告不是交钱能解决的，时间到了就强制进入外出事件。
    (react
      :when (and gang_warning_active (not gang_pressure_forced) (> day gang_warning_deadline))
      :then (list
        (effect 'set gang_pressure_forced true)
        (effect 'start-encounter '教训小混混)))

    ;; 黑帮施压结束后，压力暂时退到暗处。
    (react
      :when gang_pressure_result_pending
      :then (list
        (effect 'set gang_pressure_result_pending false)
        (effect 'set gang_pressure_forced false)
        (effect 'set gang_warning_active false)
        (effect 'set pressure_phase 3)
        (effect 'add gang_relation -1)
        (effect 'start-quick-dialogue gang-pressure-done-text)))

    ;; 城市调查填满后，解锁第一个外出调查目标。
    (react
      :when (and (clock-filled? city_lead_progress) (not moon_hotel_unlocked))
      :then (list
        (effect 'set moon_hotel_unlocked true)
        (effect 'start-quick-dialogue "# 望月旅馆\n\n# speaker: 科尔\n薇拉在望月旅馆住过三晚。老板说她走得很急，但房间一直没人清。有人替她续了钱。")))

    ;; 旅馆线索把红房间从旧案变成现在正在发生的事。
    (react
      :when (and hotel_search_done red_room_clipping (not tracker_seen))
      :then (list
        (effect 'set tracker_seen true)
        (effect 'start-quick-dialogue first-tracker-text)))

    ;; 读书的结果放在这里：clock 满了，人的能力发生改变。
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

    ;; 酒吧女人的短链先在城市层闭合。队友行动卡以后再接。
    (react
      :when (and (= woman_phase 1) (clock-filled? woman_trust) (not woman_done))
      :then (list
        (effect 'set woman_done true)
        (effect 'set woman_phase 2)
        (effect 'add finance_relation 1)
        (effect 'start-quick-dialogue woman-done-text)))

    ;; 探索区域是“虚地点”：探索满了，虚地点消失，真实地点出现。
    (react
      :when (and (clock-filled? enclave_search) (not flower_found))
      :then (list
        (effect 'set flower_found true)
        (effect 'start-quick-dialogue enclave-found-text)))

    ;; 投资项目的收益在“休息醒来”时结算，见公寓的休息行动。这里不写成 react，
    ;; 是为了避免每帧重复触发，也让“醒来收到信封”的语义更直接。

    ;; 康复训练完成：进度填满后恢复健康。
    (react
      :when (and rehab_started (clock-filled? rehab_progress) (not rehab_done))
      :then (list
        (effect 'set rehab_done true)
        (effect 'add health 3)
        (effect 'start-quick-dialogue rehab-done-text)))

    ))

(content
  :meta (meta :key 'city_1 :title "贝城县" :desc "旧案、线索，以及不想让你继续追问的人。")
  :state world-state
  :reacts world-reacts
  :root
  (node
    :title "贝城县"
    :desc "贝城县不大。旧案、工作、诊所、酒吧和那些没写在地图上的小路，足够装下一个人继续追问的代价。"
    :children (list
      (科尔公寓)
      (街边摊贩)
      (黑市)
      (正规诊所)
      (书店)
      (酒吧)
      (仓库)
      (if flower_found (花店) (飞地区域))
      (老街)
      (警局档案室))))
