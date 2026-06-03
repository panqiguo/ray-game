(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define charm-factors
  (lambda ()
    (list
      (factor -1 :when (>= (clock-value tension) 6) :label "关系过热")
      (factor -1 :when (<= (clock-value tension) 1) :label "关系冷淡"))))

(define knowledge-factors
  (lambda ()
    (list
      (factor -1 :when (>= (clock-value tension) 6) :label "关系过热")
      (factor -1 :when (<= (clock-value tension) 1) :label "关系冷淡"))))

(define (tension-root)
  (scene
    :title "关系"
    :desc "你要在关系没有冷掉、也没有越界之前，把关键情报套出来。关系 3-5 是安全区。"
    :show-clocks (list intel tension time)
    :actions (list
      (action
        :title "铺垫（推进关系）"
        :desc "把冷淡开局推向安全区。好：情报 +1、关系 +2；中：关系 +1；坏：关系 -1。"
        :check (check
          :suit 魅力
          :risk 'low
          :factors (charm-factors)
          :ok (outcome (list (effect 'clock+ intel 1) (effect 'clock+ tension 2)) "对方接住了你的话，顺口漏出一点信息。")
          :partial (outcome (list (effect 'clock+ tension 1)) "气氛热了一点，但还没到能问关键问题的时候。")
          :fail (outcome (list (effect 'clock- tension 1)) "你铺得太刻意，对方反而冷了一点。")))
      (action
        :title "试探（套话）"
        :desc "主要获取情报。好：情报 +2；中：情报 +1、关系 -1；坏：关系 -2。"
        :check (check
          :suit 魅力
          :risk 'mid
          :factors (charm-factors)
          :ok (outcome (list (effect 'clock+ intel 2)) "你问得刚好，对方没有防备。")
          :partial (outcome (list (effect 'clock+ intel 1) (effect 'clock- tension 1)) "你拿到一点东西，但问题让她起了疑心。")
          :fail (outcome (list (effect 'clock- tension 2)) "她绕开了问题，眼神也冷了下来。")))
      (action
        :title "追问（快速情报）"
        :desc "快速推进情报。好：情报 +3、关系 +1；中：情报 +2、关系 +2；坏：关系 -3。"
        :check (check
          :suit 知识
          :risk 'high
          :factors (knowledge-factors)
          :ok (outcome (list (effect 'clock+ intel 3) (effect 'clock+ tension 1)) "你抓住了矛盾，她被迫多说了几句。")
          :partial (outcome (list (effect 'clock+ intel 2) (effect 'clock+ tension 2)) "你逼出一点真东西，也把关系推得太近。")
          :fail (outcome (list (effect 'clock- tension 3)) "追问太明显了，她开始防备。")))
      (action
        :title "后撤（拉开关系）"
        :desc "用于防止越界。好：关系 -2；中：关系 -1；坏：关系 +1。"
        :check (check
          :suit 魅力
          :risk 'low
          :ok (outcome (list (effect 'clock- tension 2)) "你及时收住，气氛重新松下来。")
          :partial (outcome (list (effect 'clock- tension 1)) "你让对方缓了一口气。")
          :fail (outcome (list (effect 'clock+ tension 1)) "你退得太生硬，她反而察觉你在控制节奏。")))
      )))

(content
  :meta (meta :key '测试关系平衡 :title "测试关系平衡" :desc "测试4个 cycle 内的关系区间管理与情报获取。")
  :on-success (list (effect 'set 'test_relation_tension_done true))
  :on-fail (list (effect 'set 'test_relation_tension_failed true))
  :on-cycle-start (list (effect 'clock+ time 1))
  :reacts (list
    (react :when (clock-filled? intel) :then (list
      (effect 'end-encounter 'success)))
    (react :when (clock-empty? tension) :then (list
      (effect 'start-quick-dialogue "对方的兴致彻底冷掉了。再问下去也只会得到敷衍。")
      (effect 'end-encounter 'fail)))
    (react :when (clock-filled? tension) :then (list
      (effect 'start-quick-dialogue "你越过了那条线。对方忽然意识到你真正想要的是什么。")
      (effect 'end-encounter 'fail)))
    (react :when (and (clock-filled? time) (not (clock-filled? intel))) :then (list
      (effect 'start-quick-dialogue "机会结束了。对方看了看时间，把剩下的话咽了回去。")
      (effect 'end-encounter 'fail))))
  :vars (append
    world-basics-vars
    (list
    (var 'intel (clock :title "情报进度" :initial 0 :max 12))
    (var 'tension (clock :title "关系" :desc "3-5 安全区；0 冷掉，8 越界。" :initial 2 :max 8))
    (var 'time (clock :title "时间" :desc "每休整一次 +1，填满前没完成即失败。" :initial 0 :max 4)))
    )
  :root (tension-root))
