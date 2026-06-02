;; EXPORT 剧院, 剧院后巷
;; IMPORT nightingale_*, 夜莺 actions FROM nightingale_story.scm

(define (theater-search-action title desc suit)
  (action
    :title title
    :desc desc
    :check (check
      :suit suit
      :risk 'mid
      :ok (outcome (list (effect 'clock+ nightingale_theater_search 2)) "线索被你按回了正确的位置。")
      :partial (outcome (list (effect 'clock+ nightingale_theater_search 1) (effect 'add pressure 1)) "你找到了点东西，但剧院里的人和声音都在消耗注意力。")
      :fail (outcome (list (effect 'add pressure 1)) "你看见太多无关的脚印，真正的那一条反而混进去了。"))))

;; Scene: 剧院.
;; Exports: 剧院
;;
;; Dependency note:
;; - Story state, texts, and encounter gating live in nightingale_story.scm.
;; - Future old docks content should stay in a separate scene file and only
;;   connect here through chapter vars.

(define (舞台)
  (node
    :title "舞台"
    :desc "排练灯还亮着，空座位像一排排沉默的证人。夜莺站在光里，声音刚刚停下。"
    :show-clocks (list
      (when (and nightingale_commission_taken (not nightingale_shadow_seen)) nightingale_theater_search))
    :actions (list
      (when (and nightingale_commission_taken (not nightingale_manager_talked))
        (action
          :title "和剧院经理谈首演安排"
          :desc "要知道谁最怕这场首演出错，先去找负责出错后擦地的人。"
          :effects (list
            (effect 'set nightingale_manager_talked true)
            (effect 'clock+ nightingale_lore_progress 1)
            (effect 'start-quick-dialogue nightingale-manager-text)))))))

(define (化妆间)
  (node
    :title "化妆间"
    :desc "镜灯把每一张脸照得太清楚，也把不想承认的疲惫照得无处可藏。"
    :show-clocks (list
      (when (and nightingale_commission_taken (not nightingale_shadow_seen)) nightingale_theater_search))
    :actions (list
      (when (and nightingale_commission_taken (not nightingale_letter_checked))
        (action
          :title "检查第二封威胁信"
          :desc "这封信刚刚送到。纸张、折痕和指痕还没完全被剧院里的手弄脏。"
          :effects (list
            (effect 'set nightingale_letter_checked true)
            (effect 'clock+ nightingale_theater_search 1)
            (effect 'start-quick-dialogue nightingale-letter-room-text)))))))

(define (后台通道)
  (node
    :title "后台通道"
    :desc "道具箱、布景板和不停来回的人。这里的秘密通常被称作流程。"
    :show-clocks (list
      (when (and nightingale_commission_taken (not nightingale_shadow_seen)) nightingale_theater_search)
      (when (and nightingale_commission_taken (not nightingale_lore_known)) nightingale_lore_progress))
    :actions (list
      (when (and nightingale_commission_taken (not nightingale_shadow_seen))
        (theater-search-action
          "沿后台门寻找湿脚印"
          "送信的人不一定进了舞台，但一定经过某个没人愿意负责的门。"
          知识))
      (when (and nightingale_commission_taken (not nightingale_publicist_talked))
        (action
          :title "和宣传人员聊首演主题"
          :desc "宣传口的人最懂怎么把一场演出包装成一座城市的脸。"
          :effects (list
            (effect 'set nightingale_publicist_talked true)
            (effect 'clock+ nightingale_lore_progress 1)
            (effect 'start-quick-dialogue nightingale-publicist-text))))
      (when (and nightingale_commission_taken (not nightingale_stagehand_talked))
        (action
          :title "问后台工人最近谁来过后门"
          :desc "工人记不住名字，但会记得那些让人想骂脏话的脸。"
          :effects (list
            (effect 'set nightingale_stagehand_talked true)
            (effect 'clock+ nightingale_lore_progress 1)
            (effect 'start-quick-dialogue nightingale-stagehand-text)))))))

(define (剧院后巷)
  (node
    :title "剧院后巷"
    :desc "后门外的雨棚还在滴水。第一次追逐留下的痕迹淡了，但送信路线还会回到这里。"
    :actions (list
      (when (and nightingale_second_letter_ready
                 (not nightingale_second_letter_intercepted)
                 (not nightingale_second_letter_failed))
        (action
          :title "拦截下一封威胁信"
          :desc (if nightingale_second_letter_harder
            "你没能提前查清送信路线，只能追着线人留下的半个背影跑。"
            "这次你至少知道该往哪里堵。别让剧院先把信交给警方。")
          :effects (list
            (effect 'start-encounter '拦截第二封威胁信)))))))

(define (坠落灯架)
  (node
    :title "坠落灯架"
    :desc "绳索、灯架和碎木还没被清走。每多待一会儿，剧院的人就越急着把现场恢复成一场可以解释的意外。"
    :show-clocks (list
      (when (not theater_accident_clue_found) theater_accident_clue))
    :actions (list
      (when (not theater_accident_clue_found)
        (action
          :title "检查断裂吊绳"
          :desc "绳口像被事故扯断，也像被人提前做过手脚。你得在工人收走它之前看清楚。"
          :check (check
            :suit 敏锐
            :risk 'high
            :ok (outcome (list (effect 'clock+ theater_accident_clue 2)) "你在断口里看见不自然的切痕。")
            :partial (outcome (list (effect 'clock+ theater_accident_clue 1) (effect 'add pressure 1)) "你看出绳子不对，但剧院经理一直催你离开。")
            :fail (outcome (list (effect 'add pressure 2)) "你刚碰到绳子，后台工人就围了上来，没人愿意让外人把事故说复杂。"))))
      (when (not theater_accident_clue_found)
        (action
          :title "取出灯架下的金属楔片"
          :desc "有个小东西卡在灯架和地板之间。它不该出现在这里，也不容易安全拿出来。"
          :check (check
            :suit 知识
            :risk 'high
            :ok (outcome (list (effect 'clock+ theater_accident_clue 2)) "你把楔片取出来，边缘的新痕和剧院的旧固定件对不上。")
            :partial (outcome (list (effect 'clock+ theater_accident_clue 1) (effect 'add health -1)) "楔片被你撬松了，手背也被碎木划开。")
            :fail (outcome (list (effect 'add health -1) (effect 'add pressure 1)) "灯架突然下沉半寸，你只能先抽手，血顺着指节往下滴。")))))))

(define (后台道具间)
  (node
    :title "后台道具间"
    :desc "道具箱翻倒，急救箱半开，备用工具散在地上。这里不一定有真相，但有今晚可能用得上的东西。"
    :show-clocks (list
      (when (not theater_accident_supplies_found) theater_accident_supplies)
      (when (and theater_accident_cleanup_started
                 (not theater_accident_supplies_found)
                 (not (clock-filled? theater_accident_cleanup)))
        theater_accident_cleanup))
    :actions (list
      (when (not theater_accident_supplies_found)
        (action
          :title "翻找散落的急救箱"
          :desc "伤员被带走得太快，急救箱里可能还剩下一点能撑过今晚的东西。"
          :check (check
            :suit 敏锐
            :risk 'mid
            :ok (outcome (list (effect 'clock+ theater_accident_supplies 2)) "你找到绷带、止血粉和一小瓶醒神药。")
            :partial (outcome (list (effect 'clock+ theater_accident_supplies 1) (effect 'add pressure 1)) "你翻到一点有用东西，也引来化妆师一句难听的质问。")
            :fail (outcome (list (effect 'add pressure 1)) "箱子已经被人翻乱，你只听见外面又有人喊夜莺的名字。"))))
      (when (not theater_accident_supplies_found)
        (action
          :title "从工具箱里拿走可用材料"
          :desc "备用钳、细绳和小撬棍都能派上用场。问题是现在每个人都在盯着谁碰了现场。"
          :check (check
            :suit 知识
            :risk 'high
            :ok (outcome (list (effect 'clock+ theater_accident_supplies 2)) "你挑出几件真正能用的工具，动作快到没人来得及拦。")
            :partial (outcome (list (effect 'clock+ theater_accident_supplies 1) (effect 'add pressure 1)) "你拿到一半就被后台工人盯上，只能装作是在帮忙收拾。")
            :fail (outcome (list (effect 'add pressure 2)) "剧院经理看见你打开工具箱，立刻把事故和盗窃两个词放进同一句话里。")))))))

(define (夜莺)
  (node
    :title "夜莺"
    :desc "剧院的台柱。她站在聚光灯下的时间太久，已经不习惯被人绕开说话。"
    :show-clocks (list
      (when nightingale_commission_taken nightingale_trust))
    :actions (list
      (when (and nightingale_front_done (not nightingale_commission_taken))
        (action
          :title "和夜莺谈话"
          :desc "她唱了两句就停下，把刚收到的第二封威胁信递给你。"
          :effects (list
            (effect 'set nightingale_commission_taken true)
            (effect 'start-quick-dialogue nightingale-stage-text)))))))

(define (剧院)
  (node
    :title "剧院"
    :desc "城里最像样的剧院。红绒幕布后面站着夜莺，也站着那些想把她和旧码头一起写进海报的人。"
    :position '(860 500)
    :show-clocks (list
      (when (and nightingale_commission_taken (not nightingale_shadow_seen)) nightingale_theater_search)
      (when (and nightingale_commission_taken (not nightingale_lore_known)) nightingale_lore_progress)
      (when nightingale_commission_taken nightingale_trust))
    :actions (list
      (when (not nightingale_front_done)
        (action
          :title "和前门保安交谈"
          :desc "他知道你是谁，也知道今晚最好别把话说得太大声。"
          :effects (list
            (effect 'set nightingale_front_done true)
            (effect 'start-quick-dialogue nightingale-guard-text))))
      (when (and nightingale_commission_taken (not nightingale_shadow_seen))
        (theater-search-action
          "搜索剧院入口和侧门"
          "送信的人刚离开不久。门口、侧门和工作人员的视线里，应该还留着一条湿漉漉的路线。"
          敏锐))
      (when (and helen_room_searched (not theater_accident_survived))
        (action
          :title "赶回剧院后台"
          :desc "电话里的尖叫还没完全断掉。旧照片在口袋里发硬，后台那边已经有人在喊夜莺的名字。"
          :effects (list
            (effect 'set theater_accident_started true)
            (effect 'start-encounter '后台坠落事故))))
      (when (and theater_accident_clue_found (not theater_photo_discussed))
        (action
          :title "把旧照片和事故线索拿给夜莺看"
          :desc "旧照片、断绳和金属楔片终于能放到同一张桌上。夜莺必须回答的，不只是莱恩是谁。"
          :effects (list
            (effect 'set theater_photo_discussed true)
            (effect 'set press_angle_seen true)
            (effect 'set newspaper_office_unlocked true)
            (effect 'start-quick-dialogue "# 旧照片、断绳和报纸\n\n# speaker: 科尔\n我把照片放到夜莺面前。莱恩的五金店、老海伦、几个码头工人，还有照片边缘那个穿演出服的年轻女人。\n\n# speaker: 夜莺\n她先看照片，再看我手里的楔片。\n\n# speaker: 夜莺\n“你从哪儿弄到这些的？”\n\n# speaker: 科尔\n她问的是来源，不是东西是真是假。后台有人想把断绳收走，经理想让警方接手，记者却已经站在门口，笔记本翻到写好标题的那一页。\n\n# speaker: 科尔\n事故刚发生，报纸却像早就知道该怎么写莱恩、夜莺和旧码头。\n\n# speaker: 科尔\n这不是他来得快。是有人提前把故事喂给了报社。"))))
      (when (and nightingale_shadow_seen (not nightingale_first_confrontation_done))
        (action
         :title "追上那个鬼祟的人"
          :desc "你已经看见他了。接下来不是问话，是先别让他走掉。"
          :effects (list
                    (effect 'start-encounter '剧院后巷交锋)))))
    :children (list
               (when nightingale_front_done (夜莺))
               
               (when nightingale_front_done (舞台))
               (when nightingale_search_half_seen (化妆间))
               (when nightingale_search_half_seen (后台通道))
               (when (and theater_accident_survived (not theater_accident_clue_found)) (坠落灯架))
               (when (and theater_accident_survived
                          (not theater_accident_supplies_found)
                          (or (not theater_accident_cleanup_started)
                              (not (clock-filled? theater_accident_cleanup))))
                 (后台道具间))
               (when (and nightingale_city_day_started nightingale_second_letter_ready) (剧院后巷)))))
