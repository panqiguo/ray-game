;; Scene: 大厦.
;; Exports: building-vars, building-reacts, 大厦

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

(define office-desc
  (lambda ()
    (cond
      (office_demoted_notice
        "玻璃门、打卡机和永远亮着的走廊灯。职级已经被扣了，今天再不把三段出勤凑齐，下一个走人的就是你。")
      (office_missed_warning
        "玻璃门、打卡机和永远亮着的走廊灯。绩效已经被扣光了——昨天是最后一次警告，再缺勤一次直接降职。")
      ((= (clock-value office_rank) 0)
        "玻璃门、打卡机和永远亮着的走廊灯。这里给你一份稳定的日薪，也盯着你每天的三段出勤。缺勤一次扣光绩效，第二次降职。当前日薪 18 元。")
      ((= (clock-value office_rank) 1)
        "玻璃门、打卡机和永远亮着的走廊灯。升了一级，出勤规矩不变——缺勤扣绩效，再缺勤降职。当前日薪 26 元。")
      (else
        "玻璃门、打卡机和永远亮着的走廊灯。职级最高了，再往上没有晋升空间，但满绩效有奖金领。出勤规矩照旧。当前日薪 34 元。"))))

(define building-vars
  (list
    (var 'office_processed_day 1)
    (var 'office_salary_day 0)
    (var 'office_demoted_notice false)
    (var 'office_attendance (clock :title "今日出勤" :desc "三段出勤，填满就是全勤。工资当天到账，没满勤第二天扣绩效。" :initial 0 :max 3))
    (var 'office_performance_rank0 (clock :title "绩效" :desc "升职需要 8 点绩效。" :initial 0 :max 8))
    (var 'office_performance_rank1 (clock :title "绩效" :desc "升职需要 12 点绩效。" :initial 0 :max 12))
    (var 'office_performance_rank2 (clock :title "绩效" :desc "16 点绩效拿奖金。" :initial 0 :max 16))
    (var 'office_rank (clock :title "职级" :desc "职级越高，每日全勤工资越高。最多 2 级。" :initial 0 :max 2))
    (var 'office_missed_warning false)))

(define building-reacts
  (list
    (react
      :when (and (= office_processed_day day) (clock-filled? office_attendance) (< office_salary_day day))
      :then (list
        (effect 'add money (office-salary))
        (effect 'set office_salary_day day)))
    (react
      :when (> day office_processed_day)
      :then (append
        (if (clock-filled? office_attendance)
          ;; Full attendance: clear warning if any, pay if not yet paid
          (append
            (if office_missed_warning (list (effect 'set office_missed_warning false)) (list))
            (if (< office_salary_day office_processed_day)
              (list (effect 'add money (office-salary)) (effect 'set office_salary_day office_processed_day))
              (list)))
          ;; Not full attendance
          (if office_missed_warning
            ;; Second offense: demote
            (list
              (effect 'set office_missed_warning false)
              (when (> (clock-value office_rank) 0) (effect 'clock- office_rank 1))
              (when (> (clock-value office_rank) 0) (effect 'set office_demoted_notice true)))
            ;; First offense: lose current performance, warning
            (list
              (effect 'set office_missed_warning true)
              (effect-reset-clock (office-performance-clock)))))
        ;; Always: reset attendance, update processed_day
        (list
          (effect-reset-clock office_attendance)
          (effect 'set office_processed_day day))))
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
        :title (if (clock-filled? office_attendance) "留下加班" "上班打卡")
        :desc (if (clock-filled? office_attendance)
          "今日出勤已经满了。留下来多做一会儿算加班，拿点加班费和额外绩效。"
          (cond
            ((= (clock-value office_rank) 0)
              "日薪 18 元，三段出勤凑满就拿得到。攒满 8 点绩效能升职加薪——先填今天的出勤吧。")
            ((= (clock-value office_rank) 1)
              "日薪 26 元，一样三段出勤。攒满 12 点绩效升职到 34 元日薪，先把今天的出勤打好。")
            (else
              "日薪 34 元，三段出勤是底线。攒满 16 点绩效有奖金，别想太远，先把今天的打完。")))
        :check (check
          :suits (list 知识)
          :risk 'mid
          :ok (if (clock-filled? office_attendance)
            (outcome (list (effect 'add money (office-overtime-pay)) (office-performance-effect 1)) "你留下来把别人推掉的活收尾。加班费当场塞进信封，数额不大，但不用等。")
            (outcome (list (effect 'set office_processed_day day) (effect 'set office_demoted_notice false) (effect 'clock+ office_attendance 1) (office-performance-effect 2))))
          :partial (if (clock-filled? office_attendance)
            (outcome (list (effect 'add money (office-overtime-pay)) (effect 'add pressure 1)) "你多熬了一段，换来一小笔加班费，也把脑子熬得发硬。")
            (outcome (list (effect 'set office_processed_day day) (effect 'set office_demoted_notice false) (effect 'clock+ office_attendance 1) (office-performance-effect 1) (effect 'add pressure 1))))
          :fail (if (clock-filled? office_attendance)
            (outcome (list (effect 'add money (office-overtime-fail-pay)) (effect 'add pressure 1)) "你留下来耗到很晚，只拿到一点象征性的加班钱。")
            (outcome (list (effect 'set office_processed_day day) (effect 'set office_demoted_notice false) (effect 'clock+ office_attendance 1) (effect 'add pressure 1)))))))))