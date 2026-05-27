;; Scene: 大厦.
;; Exports: building-state, building-reacts, 大厦

(define office-salary
  (lambda ()
    (+ 18 (* (clock-value office_rank) 8))))

(define office-overtime-pay
  (lambda ()
    (+ 6 (* (clock-value office_rank) 2))))

(define office-overtime-fail-pay
  (lambda ()
    (+ 3 (clock-value office_rank))))

(define office-performance-clock
  (lambda ()
    (cond
      ((= (clock-value office_rank) 0) office_performance_rank0)
      ((= (clock-value office_rank) 1) office_performance_rank1)
      (else office_performance_rank2))))

(define office-performance-effect
  (lambda (amount)
    (effect 'clock+ (office-performance-clock) amount)))

(define office-action-desc
  (lambda ()
    (cond
      ((= (clock-value office_rank) 0)
        "日薪 18 元。每天出勤满 3 格会立刻结算当天工资；如果没即时结算，第二天也会补结。职级 0 晋升需要 8 点绩效。满勤后继续工作视为加班，立刻给少量加班费。")
      ((= (clock-value office_rank) 1)
        "日薪 26 元。每天出勤满 3 格会立刻结算当天工资；如果没即时结算，第二天也会补结。职级 1 晋升需要 12 点绩效。满勤后继续工作视为加班，立刻给少量加班费。")
      (else
        "日薪 34 元。每天出勤满 3 格会立刻结算当天工资；如果没即时结算，第二天也会补结。职级 2 的绩效要求为 16 点，填满后发绩效奖金。满勤后继续工作视为加班，立刻给少量加班费。"))))

(define office-desc
  (lambda ()
    (if office_demoted_notice
      "玻璃门、打卡机和永远亮着的走廊灯。昨天出勤没满，职级已经被扣了；今天仍然要把三段出勤凑齐。"
      (cond
        ((= (clock-value office_rank) 0)
          "玻璃门、打卡机和永远亮着的走廊灯。这里给你稳定工资；第二天出勤未满 3 会直接降职。当前职级日薪 18 元，晋升需要 8 点绩效。")
        ((= (clock-value office_rank) 1)
          "玻璃门、打卡机和永远亮着的走廊灯。这里给你稳定工资；第二天出勤未满 3 会直接降职。当前职级日薪 26 元，晋升需要 12 点绩效。")
        (else
          "玻璃门、打卡机和永远亮着的走廊灯。这里给你稳定工资；第二天出勤未满 3 会直接降职。当前职级日薪 34 元，绩效奖金需要 16 点绩效。")))))

(define building-state
  (state-fragment
    (office_checked_day 1)
    (office_paid_day 0)
    (office_demoted_notice false)
    (office_attendance (clock :title "今日出勤" :desc "每天填满 3 格即全勤，工资会在满勤时立刻结算。" :initial 0 :max 3))
    (office_performance_rank0 (clock :title "绩效" :desc "职级 0 时，填满 8 格后升职。" :initial 0 :max 4))
    (office_performance_rank1 (clock :title "绩效" :desc "职级 1 时，填满 12 格后升职。" :initial 0 :max 6))
    (office_performance_rank2 (clock :title "绩效" :desc "职级 2 时，填满 16 格后发绩效奖金。" :initial 0 :max 8))
    (office_rank (clock :title "职级" :desc "职级越高，每日全勤工资越高。最多 2 级。" :initial 0 :max 2))))

(define building-reacts
  (reacts
    (react
      :when (and (= office_checked_day day) (clock-filled? office_attendance) (< office_paid_day day))
      :then (list
        (effect 'add money (office-salary))
        (effect 'set office_paid_day day)))
    (react
      :when (> day office_checked_day)
      :then (append
        (if (clock-filled? office_attendance)
          (if (< office_paid_day office_checked_day)
            (list
              (effect 'add money (office-salary))
              (effect 'set office_paid_day office_checked_day))
            (list))
          (list
            (when (> (clock-value office_rank) 0) (effect 'clock- office_rank 1))
            (when (> (clock-value office_rank) 0) (effect 'set office_demoted_notice true))))
        (list
          (effect-reset-clock office_attendance)
          (effect 'set office_checked_day day))))
    (react
      :when (and (= (clock-value office_rank) 0) (clock-filled? office_performance_rank0))
      :then (list
        (effect 'clock+ office_rank 1)
        (effect-reset-clock office_performance_rank0)
        (effect 'start-quick-dialogue "# 大厦升职\n\n# speaker: 主管\n“你最近表现不错。工资会涨一点，当然，期待也会涨。”")))
    (react
      :when (and (= (clock-value office_rank) 1) (clock-filled? office_performance_rank1))
      :then (list
        (effect 'clock+ office_rank 1)
        (effect-reset-clock office_performance_rank1)
        (effect 'start-quick-dialogue "# 大厦升职\n\n# speaker: 主管\n“你最近表现不错。工资会再涨一点，当然，活也不会少。”")))
    (react
      :when (and (clock-filled? office_rank) (clock-filled? office_performance_rank2))
      :then (list
        (effect 'add money 40)
        (effect-reset-clock office_performance_rank2)))))

(define (大厦)
  (node
    :title "大厦"
    :desc (office-desc)
    :position '(1270 280)
    :show-clocks (list office_attendance (office-performance-clock) office_rank)
    :actions (list
      (action
        :title "上班工作"
        :desc (office-action-desc)
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (if (clock-filled? office_attendance)
            (outcome (list (effect 'add money (office-overtime-pay)) (office-performance-effect 1)) "你留下来把别人推掉的活收尾。加班费当场塞进信封，数额不大，但不用等。")
            (outcome (list (effect 'set office_checked_day day) (effect 'set office_demoted_notice false) (effect 'clock+ office_attendance 1) (office-performance-effect 2))))
          :partial (if (clock-filled? office_attendance)
            (outcome (list (effect 'add money (office-overtime-pay)) (effect 'add energy -1)) "你多熬了一段，换来一小笔加班费，也把脑子熬得发硬。")
            (outcome (list (effect 'set office_checked_day day) (effect 'set office_demoted_notice false) (effect 'clock+ office_attendance 1) (office-performance-effect 1) (effect 'add energy -1))))
          :fail (if (clock-filled? office_attendance)
            (outcome (list (effect 'add money (office-overtime-fail-pay)) (effect 'add energy -1)) "你留下来耗到很晚，只拿到一点象征性的加班钱。")
            (outcome (list (effect 'set office_checked_day day) (effect 'set office_demoted_notice false) (effect 'clock+ office_attendance 1) (effect 'add energy -1)))))))))
