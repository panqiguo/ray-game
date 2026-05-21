(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define-scene chaos-scene
  (scene
    :title "混乱"
    :desc (if (and window_active (not (clock-filled? window)))
      "外面有人在吵，秘书和律师都被声音拖走。现在偷看账本不会累积暴露。"
      "事务所安静得太整齐。想看账本，就得先弄出一点能遮住动作的声音。")
    :show-clocks (list window)
    :actions (list
      (action
        :title "制造混乱"
        :desc "撞翻文件车，借一场小事故打开短暂窗口。"
        :effects (list
          (effect 'set window_active true)
          (effect-reset-clock window)
          (effect 'start-quick-dialogue "文件车倒在走廊里，纸页像一群白色的鸟飞出去。两格时间，够不够看账本，就看你的手有多快。"))))))

(define-scene ledger-scene
  (scene
    :title "账本"
    :desc "账本就放在半开的柜子里。它不难拿，难的是拿的时候别被世界看见。"
    :show-clocks (list ledger exposure)
    :actions (list
      (action
        :title (if (and window_active (not (clock-filled? window))) "偷看账本（窗口期）" "偷看账本")
        :desc (if (and window_active (not (clock-filled? window))) "混乱遮住了你的动作。现在看账本没有暴露代价。" "速度更快，但每看一页都会让你更接近被发现。")
        :check (check
          :suits (list 感知 逻辑)
          :risk 'mid
          :ok (outcome (if (and window_active (not (clock-filled? window))) (list (effect 'clock+ ledger 1)) (list (effect 'clock+ ledger 1) (effect 'clock+ exposure 1))) "你记下一笔关键流向。")
          :partial (outcome (if (and window_active (not (clock-filled? window))) (list (effect 'clock+ ledger 1) (effect 'add energy -1)) (list (effect 'clock+ ledger 1) (effect 'clock+ exposure 1) (effect 'add energy -1))) "你看到了，但翻页慢了一点。")
          :fail (outcome (list (effect 'clock+ exposure 1)) "你刚翻开账本，就听见有人往回走。"))))))

(define-scene law-root
  (scene
    :title "律师事务所 · 混乱与暴露"
    :desc "最好的节奏不是一直偷看，也不是每次都制造混乱，而是自己找到窗口与账本之间的拍子。"
    :show-clocks (list exposure ledger)
    :children (list (chaos-scene) (ledger-scene))))

(content
  :meta (meta :key '测试律师事务所 :title "测试律师事务所" :desc "测试短窗口行动与暴露累计。")
  :on-success (list (effect 'set 'test_law_office_done true))
  :on-fail (list (effect 'set 'test_law_office_failed true) (effect 'add 'police_relation -1))
  :on-cycle (list
    (effect 'clock+ exposure 1)
    (when window_active (effect 'clock+ window 1)))
  :reacts (reacts
    (react :when (clock-filled? ledger) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? exposure) :then (list (effect 'end-encounter 'fail)))
    (react :when (and window_active (clock-filled? window)) :then (list (effect 'set window_active false))))
  :state (state
    (use-world-basics)
    (exposure (clock :title "被发现累计" :initial 0 :max 5))
    (ledger (clock :title "账本进度" :initial 0 :max 3))
    (window (clock :title "破绽窗口" :initial 0 :max 2))
    (window_active false))
  :root (law-root))
