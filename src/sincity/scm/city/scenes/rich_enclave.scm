;; Scene: 富人飞地.
;; Exports: rich-enclave-vars, rich-enclave-reacts, exploitation-incident-action, 富人飞地
;;
;; Dependency note:
;; - 富人飞地 creates `exploitation_incident_location` values that 老街 and
;;   废弃区 consume to show incident-resolution actions. Without a real
;;   provide/require system, this contract is documented here and enforced by
;;   full content validation.

(define exploitation-incident-desc
  (lambda (location)
    (if (= location 'street)
      "富人飞地的催租把老街逼出了事。三天内不解决，会伤到你的关系和钱包。"
      "富人飞地压低工钱的后果回到了废弃区。三天内不解决，会伤到你的关系和钱包。")))

(define exploitation-incident-fail-text
  (lambda (location)
    (if (= location 'street)
      "他们不再只骂业主，也开始认你的脸。"
      "他们不再只骂包工头，也开始认你的脸。")))

(define exploitation-incident-action
  (lambda (location)
    (when (and exploitation_incident_active (= exploitation_incident_location location))
      (action
        :title "处理民怨事端"
        :desc (exploitation-incident-desc location)
        :check (check
          :suits (list 魅力)
          :risk 'high
          :ok (outcome (list (effect 'clock+ exploitation_incident_resolution 2)) "你把几个带头的人压了下去，局面开始松动。")
          :partial (outcome (list (effect 'clock+ exploitation_incident_resolution 1) (effect 'add pressure 1)) "你暂时压住了事，但火还在下面烧。")
          :fail (outcome (list (effect 'add health -1) (effect 'add pressure 1)) (exploitation-incident-fail-text location)))))))

(define rich-enclave-vars
  (list
    (var 'exploitation_unrest (clock :title "民怨" :desc "压榨型工作会增加民怨，满格后生成事端。" :initial 0 :max 6))
    (var 'exploitation_incident_active false)
    (var 'exploitation_incident_location 'none)
    (var 'exploitation_incident_checked_day 1)
    (var 'exploitation_incident_timer (clock :title "事端倒计时" :desc "事端出现后每天推进；满 3 后造成关系和金钱损失。" :initial 0 :max 3))
    (var 'exploitation_incident_resolution (clock :title "平息事端" :desc "填满后摆平当前民怨事端。" :initial 0 :max 3))))

(define rich-enclave-reacts
  (list
    (react
      :when (and (clock-filled? exploitation_unrest) (not exploitation_incident_active))
      :then (list
        (effect 'set exploitation_incident_active true)
        (effect 'set exploitation_incident_checked_day day)
        (effect-reset-clock exploitation_unrest)
        (effect-reset-clock exploitation_incident_timer)
        (effect-reset-clock exploitation_incident_resolution)
        (effect 'start-quick-dialogue "# 民怨事端\n\n# speaker: 科尔\n钱从富人飞地流进我的口袋，怒气从老街和废弃区冒出来。现在它终于变成了一件必须处理的事。")))
    (react
      :when (and exploitation_incident_active (> day exploitation_incident_checked_day))
      :then (list
        (effect 'clock+ exploitation_incident_timer 1)
        (effect 'set exploitation_incident_checked_day day)))
    (react
      :when (and exploitation_incident_active (clock-filled? exploitation_incident_resolution))
      :then (list
        (effect 'set exploitation_incident_active false)
        (effect 'set exploitation_incident_location 'none)
        (effect-reset-clock exploitation_incident_timer)
        (effect-reset-clock exploitation_incident_resolution)
        (effect 'start-quick-dialogue "# 事端平息\n\n# speaker: 科尔\n事情被压下去了。不是解决，只是这座城又一次学会了把声音吞回去。")))
    (react
      :when (and exploitation_incident_active (clock-filled? exploitation_incident_timer))
      :then (list
        (effect 'set exploitation_incident_active false)
        (effect 'set exploitation_incident_location 'none)
        (effect-reset-clock exploitation_incident_timer)
        (effect-reset-clock exploitation_incident_resolution)
        (effect 'add money -40)
        (effect 'add finance_relation -1)
        (effect 'start-quick-dialogue "# 事端失控\n\n# speaker: 科尔\n三天足够让一桩麻烦从街角长成传闻。钱赔出去了，富人飞地的人也开始怀疑我是不是不够干净。")))))

(define (富人飞地)
  (node
    :title "富人飞地"
    :desc "铁门、花墙和不需要解释来源的钱。这里的工作很轻，代价常常先落在别人身上。"
    :position '(1475 280)
    :show-clocks (list exploitation_unrest)
    :actions (list
      (action
        :title "代业主催租"
        :desc "收益高，耗力少。你把压力转嫁给租客，钱立刻回来，民怨也会积起来。"
        :check (check
          :suits (list 魅力)
          :risk 'low
          :ok (outcome (list (effect 'set exploitation_incident_location 'street) (effect 'add money 35) (effect 'clock+ exploitation_unrest 2)) "你说的是规矩，听起来像威胁。业主很满意。")
          :partial (outcome (list (effect 'set exploitation_incident_location 'street) (effect 'add money 25) (effect 'clock+ exploitation_unrest 1)) "钱收回来一部分，楼下的怨声也多了一点。")
          :fail (outcome (list (effect 'set exploitation_incident_location 'street) (effect 'add money 12) (effect 'clock+ exploitation_unrest 2) (effect 'add pressure 1)) "租客没有钱，只有愤怒。你带走一点现金，留下更多火星。")))
      (action
        :title "压低工钱"
        :desc "替包工头砍掉尾款。轻松、体面、来钱快，但每一次都在废弃区和老街积一层火。"
        :check (check
          :suits (list 知识)
          :risk 'mid
          :ok (outcome (list (effect 'set exploitation_incident_location 'waste) (effect 'add money 45) (effect 'clock+ exploitation_unrest 2)) "合同上的小字替你完成了大部分暴力。")
          :partial (outcome (list (effect 'set exploitation_incident_location 'waste) (effect 'add money 30) (effect 'clock+ exploitation_unrest 2) (effect 'add pressure 1)) "账压下去了，但有人记住了你的脸。")
          :fail (outcome (list (effect 'set exploitation_incident_location 'waste) (effect 'add money 15) (effect 'clock+ exploitation_unrest 3) (effect 'add pressure 1)) "你没压住场面，只压出了更难收拾的怒气。"))))))
