(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define relation-zone-label
  (lambda ()
    (cond
      ((<= (clock-value relation) 2) "惩罚区：情报收益 -1")
      ((>= (clock-value relation) 6) "奖励区：情报收益 +1")
      (else "正常区：情报收益正常"))))

(define relation-efficiency
  (lambda ()
    (cond
      ((<= (clock-value relation) 2) -1)
      ((>= (clock-value relation) 6) 1)
      (else 0))))

(define intel-gain
  (lambda (base)
    (+ base (relation-efficiency))))

(define-scene relation-efficiency-root
  (scene
    :title "关系平衡-效率"
    :desc "关系不是硬性约束，而是情报开采效率。1-2 惩罚，3-5 正常，6-7 奖励；0 冷掉，8 越界。"
    :show-clocks (list intel relation time)
    :actions (list
      (action
        :title "铺垫（投资关系）"
        :desc "提高关系，争取进入奖励区。好：关系 +3；中：关系 +2；坏：关系 +1。奖励区继续铺垫可能越界。"
        :check (check
          :suits (list 感知)
          :risk 'low
          :ok (outcome (list (effect 'clock+ relation 3)) "你把话题垫得很顺，对方愿意多留在这个氛围里。")
          :partial (outcome (list (effect 'clock+ relation 2)) "气氛暖了一些，但还没有完全松开。")
          :fail (outcome (list (effect 'clock+ relation 1)) "她礼貌地笑了笑，关系只是稍微回温。")))
      (action
        :title "试探（稳定情报）"
        :desc "基础情报 +2，受关系区间修正；关系 -1。惩罚区只适合保守推进，奖励区收益更高。"
        :check (check
          :suits (list 感知)
          :risk 'low
          :ok (outcome (list (effect 'clock+ intel (intel-gain 2)) (effect 'clock- relation 1)) "你问得轻，信息从闲谈里自然漏出来。")
          :partial (outcome (list (effect 'clock+ intel (intel-gain 1)) (effect 'clock- relation 1)) "你拿到一点边角，但她也察觉你在听重点。")
          :fail (outcome (list (effect 'clock- relation 2)) "问题太轻，反而显得绕。她的兴致往下掉了一截。")))
      (action
        :title "追问（高效开采）"
        :desc "基础情报 +3，受关系区间修正；关系 -2。奖励区很赚，但会快速消耗关系余量。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (outcome (list (effect 'clock+ intel (intel-gain 3)) (effect 'clock- relation 2)) "你抓住缝隙追下去，她说出了真正有用的细节。")
          :partial (outcome (list (effect 'clock+ intel (intel-gain 2)) (effect 'clock- relation 2)) "她回答了，但话尾已经明显收紧。")
          :fail (outcome (list (effect 'clock- relation 3)) "追问压得太实，她开始怀疑你到底想知道什么。")))
      (action
        :title "后撤（控制边界）"
        :desc "用于从奖励区退回正常区，避免越界。好：关系 -2；中：关系 -1；坏：关系不变。"
        :check (check
          :suits (list 意志)
          :risk 'low
          :ok (outcome (list (effect 'clock- relation 2)) "你收住攻势，把关系拉回一个舒服的位置。")
          :partial (outcome (list (effect 'clock- relation 1)) "你让话题稍微冷下来，没有伤到气氛。")
          :fail (outcome (list) "你想退开，但她已经在等你下一句话。")))
      (action
        :title "摊牌（最后赌博）"
        :desc "基础情报 +4，受关系区间修正；关系 -3。失败会直接越界，适合剩余时间少或情报缺口大时冒险。"
        :check (check
          :suits (list 意志)
          :risk 'high
          :ok (outcome (list (effect 'clock+ intel (intel-gain 4)) (effect 'clock- relation 3)) "你把真正的问题压到桌面上，她沉默片刻，说出了核心。")
          :partial (outcome (list (effect 'clock+ intel (intel-gain 3)) (effect 'clock- relation 3)) "你赌对了一半，情报到手，但关系几乎被抽空。")
          :fail (outcome (list (effect 'clock+ relation 8)) "她终于明白这不是聊天。那条线被你踩穿了。"))))))

(content
  :meta (meta :key '关系平衡-效率 :title "关系平衡-效率" :desc "关系区间决定情报收益，测试投资关系与直接开采之间的边际收益。")
  :on-success (list (effect 'set 'test_relation_efficiency_done true))
  :on-fail (list (effect 'set 'test_relation_efficiency_failed true))
  :on-cycle (list (effect 'clock+ time 1))
  :reacts (reacts
    (react :when (clock-filled? intel) :then (list
      (effect 'start-quick-dialogue "你拿到了关键情报。对方还以为这只是一次普通的闲谈。")
      (effect 'end-encounter 'success)))
    (react :when (clock-empty? relation) :then (list
      (effect 'start-quick-dialogue "关系彻底冷掉了。她把话题收回去，不再给你任何入口。")
      (effect 'end-encounter 'fail)))
    (react :when (clock-filled? relation) :then (list
      (effect 'start-quick-dialogue "你靠得太近。她突然警觉起来，意识到你一直在引导她。")
      (effect 'end-encounter 'fail)))
    (react :when (and (clock-filled? time) (not (clock-filled? intel))) :then (list
      (effect 'start-quick-dialogue "时间到了。你还差一点，但这个话题已经没有继续的机会。")
      (effect 'end-encounter 'fail))))
  :state (state
    (use-world-basics)
    (intel (clock :title "情报进度" :desc "填满即拿到关键情报。" :initial 0 :max 12))
    (relation (clock :title "关系" :desc "0 冷掉；1-2 情报 -1；3-5 正常；6-7 情报 +1；8 越界。" :initial 2 :max 8))
    (time (clock :title "时间" :desc "每次休整 +1，填满前没有完成即失败。" :initial 0 :max 4)))
  :root (relation-efficiency-root))
