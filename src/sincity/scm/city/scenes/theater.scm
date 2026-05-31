;; EXPORT 剧院, 剧院后巷
;; IMPORT nightingale_*, 夜莺 actions FROM nightingale_story.scm

(define (theater-search-action title desc suit)
  (action
    :title title
    :desc desc
    :check (check
      :suits (list suit)
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
               (when (and nightingale_city_day_started nightingale_second_letter_ready) (剧院后巷)))))
