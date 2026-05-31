(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define-fragment drink-them-down
  (action
    :title "跟他们一杯接一杯喝下去"
    :desc "这桌人不怕问题，只怕你先倒下。把酒喝完，话才会从牙缝里漏出来。"
    :check (check
      :suits (list 暴力)
      :risk 'mid
      :ok (outcome (list (effect 'clock+ table_pressure 2)) "最吵的那个先把杯子扣在桌上。")
      :partial (outcome (list (effect 'clock+ table_pressure 1) (effect 'add 'health -1)) "你撑住了，但胃里像压着一块铁。")
      :fail (outcome (list (effect 'clock+ drunkenness 1) (effect 'add 'health -1)) "他们笑起来，下一杯倒得更满。"))))

(define-fragment press-the-bartender
  (action
    :title "趁乱逼酒保开口"
    :desc "酒保一直在听。现在桌上的人声够乱，足够让他假装自己什么也没说。"
    :check (check
      :suits (list 魅力)
      :risk 'mid
      :ok (outcome (list (effect 'clock+ table_pressure 2)) "他把旧地址压在杯垫下面。")
      :partial (outcome (list (effect 'clock+ table_pressure 1) (effect 'clock+ drunkenness 1)) "他只说了一半，你得从醉话里把另一半拼出来。")
      :fail (outcome (list (effect 'clock+ drunkenness 1)) "他把杯子擦得更响，像是什么都没听见。"))))

(content
  :meta (meta :key '码头酒馆喝酒交锋 :title "码头酒馆喝酒交锋" :desc "在不欢迎陌生人的酒桌上，喝倒他们，问出莱恩的旧地址。")
  :on-success (list
    (effect 'set 'ryan_address_found true)
    (effect 'set 'ryan_old_shop_unlocked true)
    (effect 'start-quick-dialogue "# 莱恩的旧地址\n\n# speaker: 酒保\n“东货栈后面的巷子。以前有间五金店，招牌早烂了。”\n\n# speaker: 科尔\n他说的是旧地址，不是现在的落脚点。但旧地址往往比新地址更诚实。"))
  :on-fail (list
    (effect 'add 'health -1)
    (effect 'start-quick-dialogue "# 酒桌败退\n\n# speaker: 科尔\n你被灌得太狠，醒来时只记得几张笑脸和桌上的酒渍。\n\n莱恩的地址还没问出来。"))
  :reacts (list
    (react :when (clock-filled? table_pressure) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? drunkenness) :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-health-vars
    (list
      (var 'table_pressure (clock :title "酒桌压力" :initial 0 :max 3))
      (var 'drunkenness (clock :title "醉意" :initial 0 :max 3))))
  :root
  (scene
    :title "码头酒馆"
    :desc "酒桌上的人故意把杯子摆得很满。你问莱恩，他们就让你先喝。"
    :show-clocks (list table_pressure drunkenness)
    :actions (list
      (drink-them-down)
      (press-the-bartender))))
