(include "helper.scm")
(include "common_clock_macros.scm")

(define quick-phone-text
  "# 弗雷德里克的电话\n\n# speaker: 科尔\n电话铃响到第三声时，我才把听筒拿起来。窗外的雨贴着玻璃往下爬，像一张没写完的供词。\n\n# speaker: 弗雷德里克\n“科尔先生？我是弗雷德里克·塞勒。县检察官办公室的弗雷德里克·塞勒。”\n\n# speaker: 科尔\n“检察官通常不在这个钟点给我打电话。除非他们想让我离某件事远一点。”\n\n# speaker: 弗雷德里克\n“我希望你靠近一点。是关于我的妻子，薇拉。她离家已经两周。我不想把事情闹大，但我需要一个不会把话带到报社的人。”\n\n# speaker: 科尔\n“你要我找人？”\n\n# speaker: 弗雷德里克\n“我要你来我家一趟。照片、时间线、报酬，我都会准备好。请尽快。”")

(define frederick-visit-text
  "# 塞勒家的客厅\n\n# speaker: 科尔\n塞勒家的客厅干净得像一间没人真正生活过的展示屋。弗雷德里克把一张照片放到茶几中央，动作轻得像怕惊醒什么。\n\n# speaker: 弗雷德里克\n“这是薇拉。我的妻子。她最近状态很不好，情绪、判断力，都出了问题。两周前，她离开了家。”\n\n# speaker: 科尔\n“你报了警。”\n\n# speaker: 弗雷德里克\n“报了。但失踪人口流程很慢。她是成年人，他们总觉得成年人有权消失。”\n\n# speaker: 科尔\n“你不这么觉得？”\n\n# speaker: 弗雷德里克\n“她需要治疗。她可能会伤害自己，也可能被别人利用。”\n\n# speaker: 科尔\n他说了很多“需要帮助”，却没有说一次“我想她”。那句话没从他嘴里出来，像一枚扣错的扣子。\n\n# speaker: 弗雷德里克\n“还有一件事。另一伙人也在找她。我不知道他们是谁，但他们不是为了帮她。你必须赶在他们之前。”\n\n# speaker: 科尔\n“我接这个委托。先从她最后出现过的地方查起。”")

(define police-result-text
  "# 警察局线索\n\n# speaker: 值班警员\n“塞勒太太？报告在这儿。丈夫来得很体面，话说得也清楚。我们这边能做的都做了。”\n\n# speaker: 科尔\n“体面的人最擅长让别人觉得事情已经被处理过了。”\n\n# speaker: 值班警员\n“你这话我没听见。还有一页附注，别问我怎么夹进去的。”\n\n# speaker: 科尔\n那页纸上写着一家私人精神病院的名字。预约入院评估，申请人弗雷德里克·塞勒，时间在薇拉失踪前两周。\n\n# speaker: 科尔\n“他早就准备好了病房。”\n\n# speaker: 值班警员\n“也可能只是早就担心她。你要是想把好丈夫和坏丈夫分开，最好别指望表格替你做。”")

(define bar-result-text
  "# 酒馆线索\n\n# speaker: 酒保\n“找女人的人多了。找妻子的，找情人的，找欠债跑掉的。你说的这个有什么特别？”\n\n# speaker: 科尔\n“问话的人不像家属。”\n\n# speaker: 酒保\n“那倒有。两个人，西装不合身，鞋太干净。问过一个深色头发的女人，拿着照片，不说名字。”\n\n# speaker: 科尔\n“他们给钱了吗？”\n\n# speaker: 酒保\n“给了。但不是让人想帮忙的那种给法，是让人想赶快忘掉他们来过。”\n\n# speaker: 科尔\n弗雷德里克说的另一伙人不是吓唬人的。他们已经进了县城，而且比我更不在乎敲门的方式。")

(define bookshop-result-text
  "# 书店线索\n\n# speaker: 多琳\n“你找的女人，薇拉。她来过这里。”\n\n# speaker: 科尔\n“你刚才说不确定。”\n\n# speaker: 多琳\n“刚才我是不想确定。她问过旧城区的便宜住处，还问哪里不会检查太多证件。”\n\n# speaker: 科尔\n“她像是在躲谁？”\n\n# speaker: 多琳\n“她像是在确认自己还能不能躲。那不一样。”\n\n# speaker: 科尔\n多琳把一张旧便笺推过来，上面写着一个名字：望月旅馆。\n\n# speaker: 多琳\n“别白天去问太直。老板胆子小，胆子小的人会把门关得特别快。”")

(define hotel-ready-text
  "# 望月旅馆\n\n# speaker: 旅馆老板\n“302 没空。客人走了，房间也没空。钱还在付，我就照规矩留着。”\n\n# speaker: 科尔\n“谁付的钱？”\n\n# speaker: 旅馆老板\n“规矩没让我回答这个。”\n\n# speaker: 科尔\n“薇拉·塞勒住过那里。”\n\n# speaker: 旅馆老板\n老板的眼神动了一下，很快又落回账本上。\n\n# speaker: 旅馆老板\n“我这儿住过很多人。有些人想被记住，有些人不想。你最好学会分清。”\n\n# speaker: 科尔\n他不会把钥匙交出来。但他已经告诉了我足够多：302 还保留着，有人替她续房，而薇拉本人已经离开。今晚，我得自己进去。")

(define case-failed-text
  "# 迟了一步\n\n# speaker: 科尔\n第三天过去后，县城忽然安静下来。不是没人见过薇拉，而是每个见过她的人都开始说自己记错了。\n\n# speaker: 多琳\n“有人比你快。他们问过之后，没人愿意再讲第二遍。”\n\n# speaker: 科尔\n“他们带走了什么？”\n\n# speaker: 多琳\n“线头。也许还有人。”\n\n# speaker: 科尔\n弗雷德里克的委托还挂在那里，但“寻找薇拉的踪迹”这件事已经失败。剩下的，只会更难看。")

(define hotel-search-complete-text
  "# 302 房间留下的东西\n\n# speaker: 科尔\n我从望月旅馆出来时，街上的灯已经亮了。302 房间还在身后，像一只被人故意留开的抽屉。\n\n# speaker: 科尔\n垃圾桶里的纸条写着一个街道名和模糊的时间；床底的小布袋里有几粒白色药片，还有一张关于“红房间”的旧剪报；窗台背面刻着一行字：M.B. knows.\n\n# speaker: 科尔\n这些东西说明薇拉不是毫无目的地消失。她留过痕迹，也许是给自己，也许是给后来的人。\n\n# speaker: 科尔\n第一条路已经找到了尽头：薇拉确实来过望月旅馆，又从这里继续往更深的地方走了。现在该去见弗雷德里克，看看他听到这些东西时，会先问什么。")

(define report-frederick-text
  "# 回报弗雷德里克\n\n# speaker: 科尔\n“薇拉住过望月旅馆。302 房间被人继续付钱保留。她离开之后，房间里还有东西。”\n\n# speaker: 弗雷德里克\n“东西？”\n\n# speaker: 科尔\n“药片，一张旧剪报，还有刻在窗台背面的字。她不是随便离家的。”\n\n# speaker: 弗雷德里克\n他沉默了很久。没有问薇拉有没有提到他，也没有问她看起来怕不怕。\n\n# speaker: 弗雷德里克\n“你还找到了什么？”\n\n# speaker: 科尔\n“足够让我知道这不是一桩普通寻人。”\n\n# speaker: 弗雷德里克\n“那就继续。报酬会照付。只要你把她带回来。”")

(define make-lead-action
  (lambda (title desc clock suits risk ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suits suits
        :risk risk
        :ok (outcome ok-text (list (effect 'clock+ clock 2)))
        :partial (outcome partial-text (list (effect 'clock+ clock 1)))
        :fail (outcome fail-text (list (effect 'add stress 1)))))))

(define make-work-action
  (lambda (title desc reward stress-cost clock)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list 意志)
        :risk 'mid
        :ok (outcome "活儿办得利落，钱也来得干净一点。" (list (effect 'add money reward) (effect 'clock+ clock 1)))
        :partial (outcome "钱到手了，但你也被这一天磨得有点烦。" (list (effect 'add money reward) (effect 'add stress stress-cost) (effect 'clock+ clock 1)))
        :fail (outcome "事情不顺，你只拿到一点钱，还惹了一身疲惫。" (list (effect 'add money 10) (effect 'add stress stress-cost)))))))

(define-node 新区·科尔办公室
  (node
    :desc "新区的租金还没涨到离谱，楼下有打字社和咖啡摊。科尔的办公室不大，但电话线还通，门牌也还挂着。"
    :position '(20 280)
    :actions (list
      (when (= ch1_phase 'waiting_call)
        (action
          :title "接听弗雷德里克的电话"
          :desc "电话那头是县里的检察官弗雷德里克·塞勒。他请你去家里谈一件关于妻子的事。"
          :effects (list
            (effect 'set ch1_phase 'visit_frederick)
            (effect 'start-quick-dialogue quick-phone-text))))
      (when (and (= ch1_phase 'gather_leads) (not case_notes_reviewed))
        (action
          :title "整理主线任务"
          :desc "你把弗雷德里克的话写在便笺上：薇拉离家两周，可能需要治疗，还有另一伙人也在找她。"
          :effects (list
            (effect 'set case_notes_reviewed true))))
      (action
        :title "在办公室沙发上睡一晚"
        :desc "省钱，但睡得不舒服。天亮以后手牌会回来，另一伙人也更近了一步。"
        :effects (list
          (effect 'reset-hand)
          (effect 'advance-day)
          (when
            (or (= ch1_phase 'gather_leads) (= ch1_phase 'hotel_inquiry) (= ch1_phase 'hotel_infiltration) (= ch1_phase 'report_frederick))
            (effect 'clock+ other_seekers 1))
          (effect 'add stress -1))))))

(define-node 新区·弗雷德里克住宅
  (node
   :desc "塞勒家的窗帘、银器和草坪都被照料得很稳妥。这里没有慌乱，只有被压低的声音和摆放得过分整齐的照片。"
   :position '(225 280)
   :actions (list
             (when (= ch1_phase 'visit_frederick)
               (action
                :title "拜访弗雷德里克"
                :desc "弗雷德里克把薇拉的照片放在桌上，说明委托内容和三天内必须找到她的压力。"
                :effects (list
                          (effect 'set ch1_phase 'gather_leads)
                          (effect 'set frederick_visited true)
                          (effect 'start-quick-dialogue frederick-visit-text))))
             (when (= ch1_phase 'report_frederick)
               (action
                :title "向弗雷德里克回报"
                :desc "你已经找到薇拉在旅馆留下的痕迹。现在该告诉委托人，第一条路已经被你挖开了。"
                :effects (list
                          (effect 'set ch1_phase 'done)
                          (effect 'start-quick-dialogue report-frederick-text)))))))

(define-node 新区·书店
  (node
    :desc "多琳的书店夹在外滩和百货商店之间，卖新书，也收旧书。书页、灰尘和邻里闲话在这里存得一样久。"
    :position '(430 280)
    :show-clocks (list (when (= ch1_phase 'gather_leads) bookshop_leads))
    :actions (list
      (when (= ch1_phase 'gather_leads)
        (make-lead-action
          "翻旧报和借阅记录"
          "薇拉如果来过这里，未必会留下名字，但会留下她关心过的东西。"
          bookshop_leads
          (list 逻辑)
          'low
          "你从旧报边角和借阅记录里找到了方向。"
          "你找到了一些可能有用的边角。"
          "你看得眼睛发酸，还是没能把线索接上。"))
      (when (= ch1_phase 'gather_leads)
        (action
          :title "帮多琳整理书箱"
          :desc "把后屋的旧书搬出来，顺便听她讲几句旧城区的事。"
          :effects (list
            (effect 'add money 15)
            (effect 'clock+ bookshop_leads 1))))
      (when (not (= ch1_phase 'waiting_call))
        (action
          :title "在书店安静读一会儿"
          :desc "不一定有用，但至少这里没人催你。"
          :check (check
                  :suits (list 感知)
                  :risk 'low
                  :ok (outcome "" (list ))
                  :partial (outcome "" (list))
                  :fail (outcome "" (list)))
          :always (list
            (effect 'add stress -1)
            (when (= ch1_phase 'gather_leads) (effect 'clock+ bookshop_leads 1))))))))

(define-node 新区·酒馆
  (node
    :desc "这里白天卖咖啡，晚上卖酒。镇上的司机、店员和县政府文书都会在这里把真话说成玩笑。"
    :position '(635 280)
    :show-clocks (list (when (= ch1_phase 'gather_leads) bar_leads))
    :actions (list
      (when (= ch1_phase 'gather_leads)
        (make-lead-action
          "听吧台闲话"
          "你不直接问薇拉，只问最近谁在找人。"
          bar_leads
          (list 感知)
          'low
          "你听到几个名字和一辆陌生车。"
          "你听到一点风声，但还拼不成完整图案。"
          "今晚大家的嘴都像杯底一样干。"))
      (action
        :title "买一杯酒放松"
        :desc "酒不解决问题，但能让问题暂时小声一点。"
        :inputs (list (item 'money 8))
        :effects (list
          (effect 'add stress -2)
          (when (= ch1_phase 'gather_leads) (effect 'clock+ bar_leads 1))))
      (when (= ch1_phase 'gather_leads)
        (make-work-action
          "临时帮酒保收桌"
          "端盘子、擦桌子、听客人把半句真话漏出来。"
          20
          1
          bar_leads)))))

(define-node 新区·百货商店
  (node
    :desc "玻璃柜台、成排货架和过分明亮的灯。这里买不到真相，但买得到让你接近真相的工具。"
    :position '(840 280)
    :actions (list
      (action
        :title "买一套开锁工具"
        :desc "旅馆门锁不一定用得上，但有工具总比用指甲和运气强。"
        :conditions (list (field-at-least 'money 45 "需要 45 元"))
        :inputs (list (item 'money 45))
        :effects (list (effect 'add lockpick 1)))
      (action
        :title "买止痛药和绷带"
        :desc "不算治疗，只是让身体别在关键时刻拖后腿。"
        :conditions (list (field-at-least 'money 20 "需要 20 元"))
        :inputs (list (item 'money 20))
        :effects (list (effect 'add first_aid 1))))))

(define-node 新区·外滩
  (node
    :desc "河面不宽，风倒是很硬。新修的步道还没完全把泥味盖住，傍晚时适合假装自己不是在被时间追着跑。"
    :position '(1045 280)
    :actions (list
      (action
        :title "沿河走一圈"
        :desc "不推进一天，只是让脑子里的噪音稍微散开。"
        :effects (list (effect 'add stress -1))))))

(define-node 旧城区·警察局
  (node
    :desc "旧城区的行政中心还保留着厚墙和旧木窗。警察局的人不一定愿意帮你，但他们的柜子里有纸面上的过去。"
    :position '(20 60)
    :show-clocks (list (when (= ch1_phase 'gather_leads) police_leads))
    :actions (list
      (when (= ch1_phase 'gather_leads)
        (make-lead-action
          "翻失踪报告和旧档案"
          "薇拉的名字、弗雷德里克的签名、医院的联系记录，它们应该能在某个抽屉里对上。"
          police_leads
          (list 逻辑)
          'mid
          "你从档案缝里抠出了一条时间不太对的记录。"
          "你找到一点记录，但还缺能让它发亮的那一页。"
          "档案员盯上了你，你只能先合上抽屉。"))
      (when (= ch1_phase 'gather_leads)
        (make-work-action
          "替档案员跑腿"
          "给楼上楼下送文件，换一点零钱，也换一点开柜子的机会。"
          15
          1
          police_leads)))))

(define-node 旧城区·老旅舍
  (node
    :desc "楼梯会响，床单发硬，但门能锁上。对科尔来说，这已经算一种体面。"
    :position '(225 60)
    :actions (list
      (action
        :title "住一晚"
        :desc "花钱睡一张真正的床。天亮以后手牌恢复，另一伙人也更近一步。"
        :inputs (list (item 'money 12))
        :effects (list
          (effect 'reset-hand)
          (effect 'advance-day)
          (when
            (or (= ch1_phase 'gather_leads) (= ch1_phase 'hotel_inquiry) (= ch1_phase 'hotel_infiltration) (= ch1_phase 'report_frederick))
            (effect 'clock+ other_seekers 1))
          (effect 'add stress -2))))))

(define-node 旧城区·诊所
  (node
    :desc "医生话不多，账也算得清。镇上很多人不想去医院时，都会先来这里。"
    :position '(430 60)
    :actions (list
      (action
        :title "处理伤口"
        :desc "花钱换药、缝合、打一针。"
        :inputs (list (item 'money 20))
        :effects (list (effect 'add health 2)))
      (action
        :title "用随身药品顶一下"
        :desc "用之前买来的药和绷带处理一下。效果有限，但不用再掏钱。"
        :conditions (list (has-item 'first_aid 1 "需要药品"))
        :inputs (list (item 'first_aid 1 "药品"))
        :effects (list (effect 'add health 1))))))

(define-node 旧城区·旧街零工
  (node
    :desc "老街上总有活：搬货、送信、修门锁、替人排队。钱不多，但比坐在办公室里等电话强。"
    :position '(635 60)
    :actions (list
      (action
        :title "接半天零工"
        :desc "安全、琐碎、便宜。你赚不到大钱，但也不太会惹麻烦。"
        :check (check
          :suits (list 意志)
          :risk 'low
          :ok (outcome "活儿干得利索，钱也来得干净。" (list (effect 'add money 15)))
          :partial (outcome "活儿勉强算完成了，钱也来得有点勉强。" (list (effect 'add money 10) (effect 'add stress 1)))
          :fail (outcome "活儿没干完，钱也没拿到。" (list (effect 'add stress 1))))
          
          ))))

(define-node 旧城区·旅馆
  (node
    :desc "望月旅馆的招牌白天也像没睡醒。老板站在柜台后面，像一把拒绝打开的旧锁。"
    :position '(840 60)
    :show-clocks (list (when (= ch1_phase 'hotel_inquiry) hotel_inquiry))
    :actions (list
      (when (= ch1_phase 'hotel_inquiry)
        (action
          :title "付钱问老板"
          :desc "钱不能买到真话，但能买到老板多说两句。"
          :inputs (list (item 'money 15))
          :effects (list
            (effect 'clock+ hotel_inquiry 2))))
      (when (= ch1_phase 'hotel_inquiry)
        (make-lead-action
          "和住客聊天"
          "住在这里的人不喜欢被问问题，但他们也不喜欢旅馆老板。"
          hotel_inquiry
          (list 感知)
          'low
          "有人见过薇拉，也见过替她续房的人。"
          "你套出一点住客闲话。"
          "对方把门关上了。"))
      (when (= ch1_phase 'hotel_inquiry)
        (make-lead-action
          "偷偷翻登记簿"
          "老板转身的时候，柜台后面的登记簿露出一角。"
          hotel_inquiry
          (list 逻辑)
          'high
          "你看到了 302 房间和一笔奇怪的续费。"
          "你看清了一半，够继续追。"
          "老板差点抓到你的手，气氛立刻冷了。"))
      (when (= ch1_phase 'hotel_infiltration)
        (action
          :title "偷偷溜进 302"
          :desc "老板已经把门关死了。你知道 302 还保留着，也知道再问下去只会让人起疑。该从侧楼梯进去看看了。"
          :effects (list
            (effect 'start-encounter '望月旅馆搜寻)))))))

(define-node 工业园区·仓库
  (node
    :desc "工业园区白天有机器声，晚上只剩风从铁皮缝里钻。仓库活给现金，也拿身体换。"
    :position '(20 500)
    :actions (list
      (action
        :title "搬货打工"
        :desc "钱来得快，代价也直接。睡眠、体力和心情都会被压出一点响声。"
        :check (check
          :suits (list 意志)
          :risk 'mid
          :ok (outcome "你撑完一整轮，领到一叠现金。" (list (effect 'add money 4) (effect 'add stress 1)))
          :partial (outcome "钱拿到了，但腰背像被铁钩扯过。" (list (effect 'add money 8) (effect 'add stress 2)))
          :fail (outcome "你被货箱砸了一下，工头只给了半份钱。" (list (effect 'add money 10) (effect 'add stress 2) (effect 'add health -1))))))))

(define-node 工业园区·修车行
  (node
    :desc "机油、焊花和旧发动机的味道混在一起。这里的人不太问来路，只问你手稳不稳。"
    :position '(225 500)
    :actions (list
      (action
        :title "修车打工"
        :desc "比仓库轻一点，也更需要眼力。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (outcome "你把故障找得很准，老板按完整工钱结账。" (list (effect 'add money 10)))
          :partial (outcome "活干完了，手上多了几道油口子。" (list (effect 'add money 6) (effect 'add stress 1)))
          :fail (outcome "你弄坏了一个小零件，只拿到一点跑腿钱。" (list (effect 'add money 4) (effect 'add stress 1)))))
      (action
        :title "买一支旧手电"
        :desc "旅馆、仓库、黑暗楼道。手电总会派上用场。"
        :conditions (list (field-at-least 'money 25 "需要 25 元"))
        :inputs (list (item 'money 25))
        :effects (list (effect 'add flashlight 1))))))

(define world-state
  (state
    (first-happened false)
    (ch1_phase 'waiting_call)

    (other_seekers (clock :title "另一伙人的追踪" :desc "每过一天 +1。填满后，他们会抢在科尔前面收走薇拉的踪迹。" :initial 0 :max 3))
    (police_leads (clock :title "警察局情报" :desc "警察局档案里关于薇拉和弗雷德里克的纸面痕迹。" :initial 0 :max 3))
    (bookshop_leads (clock :title "书店情报" :desc "书店里积攒的旧城区记忆和薇拉留下的方向。" :initial 0 :max 3))
    (bar_leads (clock :title "酒馆情报" :desc "酒馆里关于另一伙找人者的闲话。" :initial 0 :max 3))
    (hotel_inquiry (clock :title "旅馆老板的口风" :desc "望月旅馆老板越说越多，但仍然不肯把 302 房间交出来。" :initial 0 :max 4))

    (frederick_visited false)
    (case_notes_reviewed false)
    (asylum_eval_found false)
    (people_asking_woman false)
    (hotel_area_known false)
    (hotel_ready_to_infiltrate false)
    (hotel_search_done false)
    (hotel_search_reported false)
    (ch1_failed false)
    (ch1_done false)

    (note_street_time false)
    (pills_found false)
    (red_room_clipping false)
    (mb_knows false)
    (corridor_man_seen false)
    (lockpick 0)
    (first_aid 0)
    (flashlight 0)))

(define world-reacts
  (reacts
   ;; (react-once-until first-happened (effect 'start-encounter '教训小混混))
   (react
    :when (and (= ch1_phase 'gather_leads) (clock-filled? police_leads) (not asylum_eval_found))
    :then (list
           (effect 'set asylum_eval_found true)
           (effect 'start-quick-dialogue police-result-text)))
   (react
    :when (and (= ch1_phase 'gather_leads) (clock-filled? bar_leads) (not people_asking_woman))
    :then (list
           (effect 'set people_asking_woman true)
           (effect 'start-quick-dialogue bar-result-text)))
   (react
    :when (and (= ch1_phase 'gather_leads) (clock-filled? bookshop_leads) (not hotel_area_known))
    :then (list
           (effect 'set hotel_area_known true)
           (effect 'set ch1_phase 'hotel_inquiry)
           (effect 'start-quick-dialogue bookshop-result-text)))
   (react
    :when (and (= ch1_phase 'hotel_inquiry) (clock-filled? hotel_inquiry) (not hotel_ready_to_infiltrate))
    :then (list
           (effect 'set hotel_ready_to_infiltrate true)
           (effect 'set ch1_phase 'hotel_infiltration)
           (effect 'start-quick-dialogue hotel-ready-text)))
   (react
    :when (and hotel_search_done (not hotel_search_reported))
    :then (list
           (effect 'set hotel_search_reported true)
           (effect 'set ch1_phase 'report_frederick)
           (effect 'start-quick-dialogue hotel-search-complete-text)))
   (react
    :when (and (= ch1_phase 'done) (not ch1_done))
    :then (list
           (effect 'set ch1_done true)))
   (react
    :when (and (clock-filled? other_seekers) (not hotel_search_done) (not ch1_failed))
    :then (list
           (effect 'set ch1_failed true)
           (effect 'set ch1_phase 'failed)
           (effect 'start-quick-dialogue case-failed-text)))))

(content
 :meta (meta :key 'city_1 :title "贝城县" :desc "第一章：寻找失踪的妻子。")
 :state world-state
 :reacts world-reacts
 :root
 (node
  :title "贝城县"
  :desc "贝城县不大，旧城区、新区和工业园区三片地方就装下了大多数人的生活。今天的电话还没响完，事情已经在门外等着。"
  :show-clocks (list
                (when
                    (or (= ch1_phase 'gather_leads) (= ch1_phase 'hotel_inquiry) (= ch1_phase 'hotel_infiltration) (= ch1_phase 'report_frederick))
                  other_seekers))
  :children (list
             (旧城区·警察局)
             (旧城区·老旅舍)
             (旧城区·诊所)
             ;; (旧城区·旧街零工)
             (when (or (= ch1_phase 'hotel_inquiry) (= ch1_phase 'hotel_infiltration)) (旧城区·旅馆))
             
             (新区·科尔办公室)
             (when (or (= ch1_phase 'visit_frederick) (= ch1_phase 'report_frederick)) (新区·弗雷德里克住宅))
             (when (not (= ch1_phase 'waiting_call)) (新区·书店))
             (when (not (= ch1_phase 'waiting_call)) (新区·酒馆))
             (新区·百货商店)
             (新区·外滩)

      (工业园区·仓库)
      (工业园区·修车行))))
