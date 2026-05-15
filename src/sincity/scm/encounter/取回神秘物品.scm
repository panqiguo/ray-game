(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")

(define-scene recovery
  (scene
    :title "仓库后巷 · 取回神秘物品"
    :desc (if (> wounded_man_lead 0) (if police_knows_true_info "东西被人从办公室转到了仓库后巷。雨棚下有两个人守着门，巷尾还有一辆没有熄火的车。你要把油纸包拿回来。（对死者有所了解，难度下降）（警察也会去拿，难度轻微上升）" "东西被人从办公室转到了仓库后巷。雨棚下有两个人守着门，巷尾还有一辆没有熄火的车。你要把油纸包拿回来。（对死者有所了解，难度下降）") (if police_knows_true_info "东西被人从办公室转到了仓库后巷。雨棚下有两个人守着门，巷尾还有一辆没有熄火的车。你要把油纸包拿回来。（警察也会去拿，难度轻微上升）" "东西被人从办公室转到了仓库后巷。雨棚下有两个人守着门，巷尾还有一辆没有熄火的车。你要把油纸包拿回来。"))
    :show-clocks (list alert package)
    :actions (list
      (when (and (not lead_used) (field-truthy 'wounded_man_lead "拥有死者线索"))
        (action
          :title "利用死者线索绕开正门"
          :desc "你知道他们临时换手的路线，可以从装卸口切进去。"
          :inputs (list (item 'wounded_man_lead 1 "死者线索"))
          :effects (list
            (effect 'set lead_used true)
            (effect 'clock+ package 1)
            (effect 'clock- alert 1))))
      (when (and (not police_pressure_seen) (field-truthy 'police_knows_true_info "警方知道实情"))
        (action
          :title "避开警方封锁"
          :desc "你说了真话，警察也知道这里可能有东西。现在他们挡在最不方便的位置。"
          :check (check
            :suits (list 感知)
            :risk 'mid
            :ok (outcome (list (effect 'set police_pressure_seen true)) "你绕过巡警，没让他们看见你的脸。")
            :partial (outcome (list (effect 'set police_pressure_seen true) (effect 'clock+ alert 1)) "你绕过去了，但封锁线因为一点动静收紧。")
            :fail (outcome (list (effect 'set police_pressure_seen true) (effect 'clock+ alert 2)) "手电光扫过来，你只能先退进阴影。"))))
      (action
        :title "撬开仓库侧门"
        :desc "门锁旧，但旧锁也有旧脾气。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (outcome (list (effect 'clock+ package 1)) "锁舌轻轻让开，你摸进了仓库。")
          :partial (outcome (list (effect 'clock+ package 1) (effect 'clock+ alert 1)) "门开了，声音也传了出去。")
          :fail (outcome (list (effect 'clock+ alert 1)) "铁门响得太大，里面有人开始走动。")))
      (action
        :title "压住看门人"
        :desc "不让他喊出来，比打倒他更重要。"
        :check (check
          :suits (list 意志)
          :risk 'high
          :ok (outcome (list (effect 'clock+ package 2) (effect 'clock+ alert 1)) "他被你按回墙上，钥匙落进你手心。")
          :partial (outcome (list (effect 'clock+ package 1) (effect 'add health -1) (effect 'clock+ alert 1)) "你抢到了钥匙，也挨了一下。")
          :fail (outcome (list (effect 'add health -1) (effect 'clock+ alert 2)) "他喊出半声，巷尾的车灯亮了。")))
      (action
        :title "翻找油纸包"
        :desc "柜子、木箱、旧账本。东西就在这里，但你的时间不多。"
        :check (check
          :suits (list 感知)
          :risk 'mid
          :ok (outcome (list (effect 'clock+ package 2)) "你在夹层里摸到了油纸边。")
          :partial (outcome (list (effect 'clock+ package 1) (effect 'clock+ alert 1)) "你找到了包裹，但动作慢了一拍。")
          :fail (outcome (list (effect 'clock+ alert 1)) "你翻错了箱子，外头脚步声变密。"))))))

(content
  :meta (meta :key '取回神秘物品 :title "取回神秘物品" :desc "在别人拆开油纸包之前，把它从仓库后巷拿回来。")
  :on-success (list
    (effect 'set 'item_recovered true)
    (effect 'set 'item_recovery_started false)
    (effect 'add 'mysterious_item 1))
  :on-fail (list
    (effect 'set 'item_recovery_failed true)
    (effect 'set 'item_recovery_started false)
    (effect 'add 'police_relation -1)
    (effect 'add 'health -1))
  :on-cycle (list
    (effect 'clock+ alert 1))
  :reacts (reacts
    (react :when (clock-filled? package) :then (list (effect 'end-encounter 'success)))
    (react :when (>= (clock-value alert) 4) :then (list (effect 'end-encounter 'fail))))
  :state (state
    (package (clock :title "包裹" :initial 0 :max 4))
    (alert (clock :title "警觉" :initial 0 :max 4))
    (lead_used false)
    (police_pressure_seen false)
    (wounded_man_lead (world-item 'wounded_man_lead 0))
    (police_knows_true_info (world-value 'police_knows_true_info false)))
  :root (recovery))
