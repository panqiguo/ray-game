(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define stealth-factors
  (lambda ()
    (list
      (factor -1 :when security_online :label "监控"))))

(define safe-factors
  (lambda ()
    (append
      (stealth-factors)
      (list
        (factor -1 :when (and guard_at_safe (not power_cut)) :label "守卫")))))

(define-scene power-room
  (scene
    :title "配电房"
    :desc
      (cond
        (power_cut "主电源已经被切断。警戒时钟冻结，但备用电源正在接管。")
        (backup_power_active "备用电源已经接管，配电柜被锁死，没法再次断电。")
        (else "配电柜在黑暗里低声震动。断电需要真正切开主线路，不是按一个开关。"))
    :show-clocks (list power_progress (when power_cut backup_power) alert)
    :actions (list
      (action
        :title "断电"
        :desc "切断主电源。成功后监控和守卫关注暂时失效，两回合后备用电源启动，警戒 +4。"
        :conditions (list
          (field-equals 'power_cut false "当前已经断电")
          (field-equals 'backup_power_active false "备用电源已经接管"))
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :factors (stealth-factors)
          :ok (outcome (list (effect 'clock+ power_progress 2)) "你切开一组主线，配电柜的嗡鸣低了一截。")
          :partial (outcome (list (effect 'clock+ power_progress 1) (effect 'clock+ alert 1)) "线路松了，但电火花照亮了半面墙。")
          :fail (outcome (list (effect 'clock+ alert 1)) "你没能找到正确的线路，继电器响了一声。")))
      (action
        :title "工具辅助断电"
        :desc "用储藏间工具稳定切开一段主电源线路。"
        :conditions (list
          (field-equals 'power_cut false "当前已经断电")
          (field-equals 'backup_power_active false "备用电源已经接管"))
        :inputs (list (item 'tools 1 "工具"))
        :effects (list
          (effect 'clock+ power_progress 1))))))

(define-scene camera-room
  (scene
    :title "监控室"
    :desc
      (cond
        (monitor_cut "监控主线被切断，屏幕墙正在一格格闪噪点。这个窗口不会持续太久。")
        (else "屏幕墙映着走廊、楼梯和大厅。只要监控还在，所有潜入行动都会被压低。"))
    :show-clocks (list camera_progress (when monitor_cut monitor_window) alert)
    :actions (list
      (action
        :title "切断监控"
        :desc "切断监控主线。完成后警戒 +2，监控失效两回合。"
        :conditions (list (field-equals 'monitor_cut false "监控已经断开"))
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :factors (stealth-factors)
          :ok (outcome (list (effect 'clock+ camera_progress 2)) "你拔掉一组线路，屏幕墙抖了一下。")
          :partial (outcome (list (effect 'clock+ camera_progress 1) (effect 'clock+ alert 1)) "你找到了线路，但短路声传进走廊。")
          :fail (outcome (list (effect 'clock+ alert 1)) "警报灯闪了一下，你不得不缩回手。")))
      (action
        :title "工具辅助监控"
        :desc "用储藏间工具稳定切开一段监控线路。"
        :conditions (list
          (field-equals 'monitor_cut false "监控已经断开"))
        :inputs (list (item 'tools 1 "工具"))
        :effects (list
          (effect 'clock+ camera_progress 1))))))

(define-scene storage-room
  (scene
    :title "道具储藏间"
    :desc "一排工具箱和几个零钱抽屉。这里没有守卫，但每次行动仍会消耗你的夜晚。"
    :show-clocks (list tool_progress money_search)
    :actions (list
      (action
        :title "寻找道具"
        :desc "翻找能用于破坏或盗取行动的工具。"
        :conditions (list (field-equals 'tool_taken false "已经取得道具"))
        :check (check
          :suits (list 感知)
          :risk 'low
          :factors (stealth-factors)
          :ok (outcome (list (effect 'clock+ tool_progress 2)) "你找到一套薄撬片和短柄螺丝刀。")
          :partial (outcome (list (effect 'clock+ tool_progress 1)) "你摸到几件能用的小工具，但还差关键那件。")
          :fail (outcome (list (effect 'clock+ alert 1)) "箱子翻得太响，走廊里有人停了一下。")))
      (action
        :title "翻找零钱"
        :desc "从抽屉和外套口袋里找一点现金。最多翻四次。"
        :conditions (list (field-below 'money_search 4 "零钱已经翻空"))
        :check (check
          :suits (list 感知)
          :risk 'low
          :factors (stealth-factors)
          :ok (outcome (list (effect 'clock+ money_search 1) (effect 'add money 4)) "你摸出几张皱巴巴的钞票。")
          :partial (outcome (list (effect 'clock+ money_search 1) (effect 'add money 2)) "你翻出一点零钱。")
          :fail (outcome (list (effect 'clock+ money_search 1) (effect 'clock+ alert 1)) "抽屉卡住，响声有点刺耳。"))))))

(define-scene hall
  (scene
    :title "大厅"
    :desc
      "保险箱嵌在大厅墙后，一个人就站在旁边看着。你不能处理他，只能把这种关注当成环境压力。"
    :show-clocks (list safe alert)
    :actions (list
      (action
        :title "打开保险箱"
        :desc "主目标。监控和看守都会压低这次盗取行动。"
        :check (check
          :suits (list 逻辑)
          :risk 'high
          :factors (safe-factors)
          :ok (outcome (list (effect 'clock+ safe 2)) "锁舌松开了一大截。")
          :partial (outcome (list (effect 'clock+ safe 1) (effect 'clock+ alert 1)) "你推进了锁芯，但金属声太清楚。")
          :fail (outcome (list (effect 'clock+ alert 1)) "锁芯卡住，看守似乎听见了什么。")))
      (action
        :title "工具辅助保险箱"
        :desc "用工具稳定推进保险箱 1 格，不需要行动卡。"
        :inputs (list (item 'tools 1 "工具"))
        :effects (list
          (effect 'clock+ safe 1))))))

(define-scene infiltration-root
  (scene
    :title "切断与潜入"
    :desc "你不是在打一场仗，而是在和一栋精密运转的建筑博弈。"
    :show-clocks (list alert safe)
    :children (list (power-room) (camera-room) (storage-room) (hall))))

(content
  :meta (meta :key '测试切断潜入 :title "不错:切断与潜入" :desc "测试监控关注、断电窗口、监控断开窗口、工具和看守状态。")
  :on-success (list (effect 'set 'test_infiltration_done true))
  :on-fail (list (effect 'set 'test_infiltration_failed true) (effect 'add health -1))
  :on-cycle (list
             ;; (when (not power_cut)
             ;;   (effect 'clock+ alert 1))
             (when power_cut
               (effect 'clock+ backup_power 1))
             (when monitor_cut
               (effect 'clock+ monitor_window 1))
             )
  :reacts (reacts
    (react :when (clock-filled? power_progress) :then (list
      (effect 'set power_cut true)
      (effect 'set security_online false)
      (effect-reset-clock power_progress)
      (effect-reset-clock backup_power)
      (effect 'start-quick-dialogue "主电源断开，警戒系统的推进暂时冻结。备用电源正在倒计时。")))
    (react :when (clock-filled? backup_power) :then (list
      (effect 'set power_cut false)
      (effect 'set backup_power_active true)
      (effect-expr (set! security_online (not monitor_cut)))
      (effect-reset-clock backup_power)
      (effect 'clock+ alert 4)
      (effect 'start-quick-dialogue "备用电源启动，整栋楼的灯一层层亮起。警戒立刻增加 4 格。")))
    (react :when (clock-filled? camera_progress) :then (list
      (effect 'set monitor_cut true)
      (effect 'set security_online false)
      (effect-reset-clock camera_progress)
      (effect-reset-clock monitor_window)
      (effect 'clock+ alert 2)
      (effect 'start-quick-dialogue "监控主线被切断。系统会发现异常，但接下来两回合监控关注消失。")))
    (react :when (clock-filled? monitor_window) :then (list
      (effect 'set monitor_cut false)
      (effect-expr (set! security_online (not power_cut)))
      (effect-reset-clock monitor_window)
      (effect 'start-quick-dialogue "监控系统重新接上，红点再次沿着走廊亮起。")))
    (react :when (clock-filled? tool_progress) :then (list
      (effect 'set tool_taken true)
      (effect 'add tools 2)
      (effect-reset-clock tool_progress)
      (effect 'start-quick-dialogue "你把两件真正有用的工具塞进口袋。它们可以稳定推进破坏或盗取行动。")))
    (react :when (clock-filled? safe) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? alert) :then (list (effect 'end-encounter 'fail))))
  :state (state
    (use-world-basics)
    (security_online true)
    (power_cut false)
    (backup_power_active false)
    (monitor_cut false)
    (guard_at_safe true)
    (tool_taken false)
    (tools (world-item 'tools 0))
    (alert (clock :title "警戒" :initial 0 :max 6))
    (power_progress (clock :title "断电" :initial 0 :max 4))
    (backup_power (clock :title "备用电源" :desc "填满后恢复供电，警戒 +4。" :initial 0 :max 2))
    (camera_progress (clock :title "切断监控" :initial 0 :max 3))
    (monitor_window (clock :title "监控断开" :desc "填满后监控恢复。" :initial 0 :max 2))
    (tool_progress (clock :title "取得道具" :initial 0 :max 2))
    (money_search (clock :title "翻找零钱" :desc "每填 1 格代表已经翻找过一次，最多 4 次。" :initial 0 :max 4))
    (safe (clock :title "保险箱" :initial 0 :max 8)))
  :root (infiltration-root))
