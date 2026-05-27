;; Scene: 废弃区.
;; Exports: waste-vars, waste-reacts, 废弃区
;;
;; Dependency note:
;; - Uses `exploitation-incident-action` from 富人飞地 scene when an incident
;;   lands in waste. This location also hosts Vera and gambler actions, so the
;;   scene naturally depends on those thread states/texts in city_1.scm.

(define piecework-desc
  (lambda ()
    (cond
      ((= piecework_bad_halves 0) "废弃区的小工厂按件结钱。当前零件还算完整；两半都做完后按正常品付钱。")
      ((= piecework_bad_halves 1) "废弃区的小工厂按件结钱。当前零件已有一半残次；做完后只能按三分之一价格结算。")
      (else "废弃区的小工厂按件结钱。当前零件已经是废品；做完也拿不到钱。"))))

(define piecework-action
  (lambda ()
    (action
      :title "工厂计件：组装螺丝"
      :desc (piecework-desc)
      :check (check
        :suits (list 逻辑)
        :risk 'mid
        :ok (outcome (list (effect 'clock+ piecework_part 1)) "这一半零件咬合得很顺，像是机器也终于肯帮你一次。")
        :partial (outcome (list (effect 'clock+ piecework_part 1) (effect 'add piecework_bad_halves 1) (effect 'add energy -1)) "这一半勉强装上了，但已经算残次。")
        :fail (outcome (list (effect 'clock+ piecework_part 1) (effect 'add piecework_bad_halves 1) (effect 'add energy -1)) "这一半坏了。工头没说话，只把账记在你这件零件上。")))))

(define waste-vars
  (list
    (var 'piecework_part (clock :title "组装零件" :desc "每格代表零件的一半。两半都完成后按品质结算。" :initial 0 :max 2))
    (var 'piecework_bad_halves 0)
    (var 'gambling_debt (clock :title "赌债" :desc "酒吧小赌欠下的账。满格后会伤到健康。" :initial 0 :max 4))))

(define waste-reacts
  (list
    (react
      :when (clock-filled? piecework_part)
      :then (list
        (cond
          ((= piecework_bad_halves 0) (effect 'add money 14))
          ((= piecework_bad_halves 1) (effect 'add money 5))
          (else nil))
        (cond
          ((= piecework_bad_halves 0) (effect 'start-quick-dialogue "# 计件工资\n\n# speaker: 工头\n“正常品。十四块。”"))
          ((= piecework_bad_halves 1) (effect 'start-quick-dialogue "# 计件工资\n\n# speaker: 工头\n“残次品。只能按三分之一算。”"))
          (else (effect 'start-quick-dialogue "# 计件工资\n\n# speaker: 工头\n“废品。这个不给钱。”")))
        (effect-reset-clock piecework_part)
        (effect 'set piecework_bad_halves 0)))
    (react
      :when (clock-filled? gambling_debt)
      :then (list
        (effect-reset-clock gambling_debt)
        (effect 'add health -1)
        (effect 'start-quick-dialogue "# 酒吧赌债\n\n# speaker: 科尔\n酒吧里欠下的小账不会永远小下去。今晚有人在后巷提醒了我这一点。")))))

(define (废弃区)
  (node
    :title "废弃区"
    :desc "倒塌的围墙、被水泡坏的广告牌，还有那些不愿意白天提起的交易。"
    :position '(655 520)
    :show-clocks (list
      piecework_part
      (when (and exploitation_incident_active (= exploitation_incident_location 'waste)) exploitation_incident_timer)
      (when (and exploitation_incident_active (= exploitation_incident_location 'waste)) exploitation_incident_resolution))
    :actions (list
      (exploitation-incident-action 'waste)
      (piecework-action)
      (when (and vera_thread_unlocked (not vera_waste_checked))
        (action
          :title "搜索废弃区"
          :desc "这里有人见过她——但大多只承认看见了影子。你低下头看地面：脚印不止一个人的，有人在她后面。"
          :effects (list
            (effect 'set vera_waste_checked true)
            (effect 'start-quick-dialogue vera-waste-empty-text))))
      (when (and chapter_2_started (not gambler_met))
        (action
          :title "挑战 - 碰撞：赌徒被人按在巷口"
          :desc "有人把一个赌徒按在墙上搜身。他看见你时，像看见一条还没来得及用掉的命。"
          :effects (list (effect 'start-encounter '巷口赌徒))))
      (when (and gambler_met (not gambler_debt_choice_done))
        (action
          :title "处理追债人留下的麻烦"
          :desc "帮他、卖他，或者两边套话。反正你得先决定这张下注单要替谁留着。"
          :effects (list
            (effect 'set gambler_debt_choice_done true)
            (effect 'set gambler_return_day (+ day 3))
            (effect 'start-quick-dialogue gambler-debt-text))))
      (when (and gambler_clocktower_ready (not casino_unlocked))
        (action
          :title "赴废弃区钟楼下的约"
          :desc "赌徒本人没出现，但他把路已经留给你了。"
          :effects (list
            (effect 'set casino_unlocked true)
            (effect 'start-quick-dialogue casino-found-text)))))))
