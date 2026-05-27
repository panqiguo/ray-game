(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define (chaos-scene)
  (scene
    :title "混乱"
    :desc
      (if (= guard_state "checking")
        "文件车倒在走廊里。秘书和律师都被声音拖走——现在偷看账本不会累积暴露。"
        "事务所安静得太整齐。想看账本，得先弄出一点能遮住动作的声音。")
    :show-clocks (list disturbance (when (= guard_state "checking") guard_check))
    :actions (list
      (action
        :title "制造混乱"
        :desc "撞翻文件车，借一场小事故打开短暂窗口。"
        :conditions (list (field-equals 'guard_state "watching" "守门人正在坐着的时候可用"))
        :check (check
          :suits (list 感知 逻辑)
          :risk 'low
          :ok (outcome (list (effect 'clock+ disturbance 2)) "文件车倒了，纸页飞散。混乱够了。")
          :partial (outcome (list (effect 'clock+ disturbance 1)) "动静太小，律师只是抬头看了一眼。")
          :fail (outcome (list) "你没找到机会。再等等。"))))))

(define (ledger-scene)
  (scene
    :title "账本"
    :desc
      (cond
        ((= guard_state "checking") "账本摊开在柜子里。窗外的声音足够盖住翻页。")
        ((= guard_state "watching") "账本就放在半开的柜子里。守门人的目光时不时扫过来。")
        (else "账本就放在半开的柜子里。没人注意这个角落。"))
    :show-clocks (list ledger exposure (when (= guard_state "checking") guard_check))
    :actions (list
      (action
        :title "偷看账本"
        :desc "混乱盖住了你的动作。现在看账本很安全。"
        :conditions (list (field-equals 'guard_state "checking" "守门人不在这儿的时候可用"))
        :check (check
          :suits (list 感知 逻辑)
          :risk 'mid
          :ok (outcome (list (effect 'clock+ ledger 1)) "你记下一笔关键流向。")
          :partial (outcome (list (effect 'clock+ ledger 1) (effect 'add energy -1)) "你看到了，但翻页慢了一点。")
          :fail (outcome (list) "你刚翻开账本，就听见有人往回走。")))
      (action
        :title "翻看账本"
        :desc "守门人在看着这边。每翻一页都可能被发现。"
        :conditions (list (field-equals 'guard_state "watching" ""))
        :check (check
          :suits (list 感知 逻辑)
          :risk 'high
          :ok (outcome (list (effect 'clock+ ledger 1) (effect 'clock+ exposure 1)) "你记下一笔关键流向，但翻页声引起了注意。")
          :partial (outcome (list (effect 'clock+ ledger 1) (effect 'clock+ exposure 1) (effect 'add energy -1)) "你看到了，但翻页慢了一点。")
          :fail (outcome (list (effect 'clock+ exposure 1)) "你刚翻开账本，就听见有人往回走。"))))))

(define (law-root)
  (scene
    :title "律师事务所 · 混乱与暴露"
    :desc "守门人的注意力就是你的资源。制造混乱引开他，趁窗口期翻账本。"
    :show-clocks (list exposure ledger (when (= guard_state "checking") guard_check))
    :children (list (chaos-scene) (ledger-scene))))

(content
  :meta (meta :key '投资降低风险-翻看账本 :title "投资降低风险-翻看账本" :desc "测试守门人状态与混乱窗口。")
  :on-success (list (effect 'set 'test_law_office_done true))
  :on-fail (list (effect 'set 'test_law_office_failed true) (effect 'add 'police_relation -1))
  :on-cycle (list
    (effect 'clock+ exposure 1)
    (when (= guard_state "checking")
      (effect 'clock+ guard_check 1)))
  :reacts (list
    (react :when (clock-filled? ledger) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? exposure) :then (list (effect 'end-encounter 'fail)))
    (react :when (and (clock-filled? disturbance) (= guard_state "watching")) :then (list
      (effect 'set guard_state "checking")
      (effect-reset-clock disturbance)
      (effect-reset-clock guard_check)
      (effect 'start-quick-dialogue "文件车倒在走廊里，纸页像一群白色的鸟飞出去。守门人被声音引开了。接下来一回合看账本很安全。")))
    (react :when (and (= guard_state "checking") (clock-filled? guard_check)) :then (list
      (effect 'set guard_state "watching")
      (effect-reset-clock guard_check)
      (effect 'start-quick-dialogue "守门人检查完回来了。目光重新落在房间方向。"))))
  :vars (append
    world-basics-vars
    (list
    (var 'guard_state "watching")
    (var 'guard_check (clock :title "守门人查看混乱" :desc "填满后守门人回到门口。" :initial 0 :max 2))
    (var 'exposure (clock :title "被发现" :initial 0 :max 5))
    (var 'ledger (clock :title "账本进度" :initial 0 :max 3))
    (var 'disturbance (clock :title "制造混乱" :desc "填满后引开守门人。" :initial 0 :max 3)))
    )
  :root (law-root))
