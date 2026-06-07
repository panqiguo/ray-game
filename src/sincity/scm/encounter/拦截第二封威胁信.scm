(include "../enum-symbols.scm")
(include "../common_world_bindings.scm")

(define-fragment cut-through-crowd
  (action
    :title "穿过雨里的人群"
    :desc "盯住那件沾雨的外套，别让街口的人潮把他整个吞下去。"
    :check (check
      :suit 敏锐
      :risk 'mid
      :ok (outcome (list (effect 'clock+ distance 2)) "")
      :partial (outcome (list (effect 'clock+ distance 1) (effect 'clock+ panic 1)) "")
      :fail (outcome (list (effect 'clock+ panic 1)) "你被人群绊慢了一步。"))))

(define-fragment cut-into-alley
  (action
    :title "抄近巷堵前面"
    :desc "别跟着他的路线走，抢在他以为安全的出口等他。"
    :check (check
      :suit 知识
      :risk 'mid
      :ok (outcome (list (effect 'clock+ distance 2)) "")
      :partial (outcome (list (effect 'clock+ distance 1) (effect 'add energy -1)) "")
      :fail (outcome (list (effect 'clock+ panic 1) (effect 'add energy -1)) "你猜错了巷口，只听见脚步声离你更远。"))))

(define-fragment pin-him-with-voice
  (action
    :title "亮身份逼他停下"
    :desc "有时候一句够冷的话，比冲刺更快。"
    :check (check
      :suit 魅力
      :risk 'high
      :ok (outcome (list (effect 'clock+ distance 2)) "")
      :partial (outcome (list (effect 'clock+ distance 1) (effect 'clock+ panic 1)) "")
      :fail (outcome (list (effect 'clock+ panic 2)) "他被你吓得更快，也更想把信先丢进门里。"))))

(content
  :meta (meta :key '拦截第二封威胁信 :title "拦截第二封威胁信" :desc "在剧院后巷和雨夜街口之间追上递信人。")
  :on-success (list
    (effect 'set 'nightingale_second_letter_intercepted true)
    (effect 'set 'nightingale_docks_direction_known true))
  :on-fail (list
    (effect 'set 'nightingale_second_letter_failed true)
    (effect 'set 'nightingale_second_letter_delivered true)
    (effect 'add 'police_relation -1))
  :reacts (list
    (react
      :when (clock-filled? distance)
      :then (list (effect 'end-encounter 'success)))
    (react
      :when (clock-filled? panic)
      :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-health-vars
    world-energy-vars
    (list
      (import-world-value 'nightingale_second_letter_harder false)
      (var 'distance (clock :title "追上递信人" :initial 0 :max 4))
      (var 'panic (clock :title "信件脱手风险" :initial 0 :max 4))))
  :root
  (location
    :title "雨里追信"
    :desc (if nightingale_second_letter_harder
      "你来得稍晚了半步。递信人已经离剧院更近，雨水和人群都在替他遮掩。"
      "线人替你指准了方向。一个跑腿的背影正朝剧院那头钻，信还没来得及交出去。")
    :show-clocks (list distance panic)
    :actions (list
      (cut-through-crowd)
      (cut-into-alley)
      (pin-him-with-voice))))
