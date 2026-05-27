(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define hall-guard-factors
  (lambda ()
    (list
      (factor -1 :when (>= (clock-value hall_guards) 1) :label "1名守卫")
      (factor -1 :when (>= (clock-value hall_guards) 2) :label "2名守卫")
      (factor -1 :when (>= (clock-value hall_guards) 3) :label "3名守卫")
      (factor -1 :when (>= (clock-value hall_guards) 4) :label "4名守卫"))))

(define warehouse-guard-factors
  (lambda ()
    (list
      (factor -1 :when (>= (clock-value warehouse_guards) 1) :label "1名守卫")
      (factor -1 :when (>= (clock-value warehouse_guards) 2) :label "2名守卫")
      (factor -1 :when (>= (clock-value warehouse_guards) 3) :label "3名守卫")
      (factor -1 :when (>= (clock-value warehouse_guards) 4) :label "4名守卫"))))

(define yard-guard-factors
  (lambda ()
    (list
      (factor -1 :when (>= (clock-value yard_guards) 1) :label "1名守卫")
      (factor -1 :when (>= (clock-value yard_guards) 2) :label "2名守卫")
      (factor -1 :when (>= (clock-value yard_guards) 3) :label "3名守卫")
      (factor -1 :when (>= (clock-value yard_guards) 4) :label "4名守卫"))))

(define (hall-scene)
  (scene
    :title "大厅"
    :desc "桌账、茶资和客人落下的钱都在这里。搜刮完成后会推进总完成进度。"
    :position '(260 250)
    :show-clocks (list hall_guards hall_target)
    :actions (list
      (action
        :title "制造干扰"
        :desc "把其他区域的守卫引过来。需要两次推进才能成功，每区限一次。"
        :conditions (list
          (field-equals 'hall_distracted false "大厅已制造过干扰"))
        :check (check
          :suits (list 意志)
          :risk 'low
          :ok (outcome (list (effect 'clock+ hall_distract 2)) "你弄出的响动足够大，其他区域的守卫闻声赶来。")
          :partial (outcome (list (effect 'clock+ hall_distract 1)) "动静不够，只有少数人回头。")
          :fail (outcome (list) "没人注意到你的动作。")))
      (action
        :title "搜刮大厅目标"
        :desc "推进大厅目标。每名在此区域的守卫 -1 难度；完成后总完成进度 +1。"
        :conditions (list
          (field-equals 'hall_done false "大厅目标已经完成"))
        :check (check
          :suits (list 感知)
          :risk 'mid
          :factors (hall-guard-factors)
          :ok (outcome (list (effect 'clock+ hall_target 2)) "你顺着桌边摸过去，几张钞票无声滑进袖口。")
          :partial (outcome (list (effect 'clock+ hall_target 1)) "你拿到一点钱，但不能多停。")
          :fail (outcome (list (effect 'clock+ alert 1)) "有人抬头看了你一眼，你只好把手收回来。"))))))

(define (warehouse-scene)
  (scene
    :title "仓库"
    :desc "破茶箱、旧铜管和能卖钱的废料堆在角落。搜刮完成后会推进总完成进度。"
    :position '(560 250)
    :show-clocks (list warehouse_guards warehouse_target)
    :actions (list
      (action
        :title "制造干扰"
        :desc "把其他区域的守卫引过来。需要两次推进才能成功，每区限一次。"
        :conditions (list
          (field-equals 'warehouse_distracted false "仓库已制造过干扰"))
        :check (check
          :suits (list 意志)
          :risk 'low
          :ok (outcome (list (effect 'clock+ warehouse_distract 2)) "你在仓库门口弄出响动，其他区域的守卫循声走来。")
          :partial (outcome (list (effect 'clock+ warehouse_distract 1)) "守卫朝仓库方向看了看，没完全过来。")
          :fail (outcome (list) "没人注意到你的动作。")))
      (action
        :title "搜刮仓库目标"
        :desc "推进仓库目标。每名在此区域的守卫 -1 难度；完成后总完成进度 +1。"
        :conditions (list
          (field-equals 'warehouse_done false "仓库目标已经完成"))
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :factors (warehouse-guard-factors)
          :ok (outcome (list (effect 'clock+ warehouse_target 2)) "你挑出几件值钱废料，顺手压住了会响的铁片。")
          :partial (outcome (list (effect 'clock+ warehouse_target 1)) "你拿到一小捆废料。")
          :fail (outcome (list (effect 'clock+ alert 1)) "铁片在箱底刮响，外面有人咳了一声。"))))))

(define (yard-scene)
  (scene
    :title "后院"
    :desc "目标物藏在后院杂物和晾衣绳之间。搜刮完成后会推进总完成进度。"
    :position '(860 250)
    :show-clocks (list yard_guards yard_target)
    :actions (list
      (action
        :title "制造干扰"
        :desc "把其他区域的守卫引过来。需要两次推进才能成功，每区限一次。"
        :conditions (list
          (field-equals 'yard_distracted false "后院已制造过干扰"))
        :check (check
          :suits (list 意志)
          :risk 'low
          :ok (outcome (list (effect 'clock+ yard_distract 2)) "后门传来一声响动，其他区域的守卫转身去查看。")
          :partial (outcome (list (effect 'clock+ yard_distract 1)) "守卫朝后院方向望了望，脚步没动。")
          :fail (outcome (list) "没人注意到你的动作。")))
      (action
        :title "搜刮后院目标"
        :desc "推进后院目标。每名在此区域的守卫 -1 难度；完成后总完成进度 +1。"
        :conditions (list
          (field-equals 'yard_done false "后院目标已经完成"))
        :check (check
          :suits (list 感知)
          :risk 'mid
          :factors (yard-guard-factors)
          :ok (outcome (list (effect 'clock+ yard_target 2)) "你在晾衣竹竿后面摸到一处松动，目标物近了。")
          :partial (outcome (list (effect 'clock+ yard_target 1)) "你排除了一片杂物，搜索范围缩小。")
          :fail (outcome (list (effect 'clock+ alert 1)) "后门轴响了一下，你不得不停住。"))))))

(define (teahouse-root)
  (scene
    :title "茶楼三处搜刮"
    :desc "每区 2 名守卫。制造干扰可吸引其他区域的守卫，降低目标区域搜刮难度。"
    :show-clocks (list alert completion)
    :children (list
      (hall-scene)
      (warehouse-scene)
      (yard-scene))))

(content
  :meta (meta :key '测试茶楼三处搜刮 :title "测试茶楼三处搜刮" :desc "测试守卫转移与多区域搜刮。")
  :on-success (list (effect 'set 'test_teahouse_scavenge_done true))
  :on-fail (list (effect 'set 'test_teahouse_scavenge_failed true))
  :on-cycle (list)
  :reacts (reacts
    (react :when (clock-filled? hall_distract) :then (list
      (effect 'set hall_distracted true)
      (effect 'clock+ hall_guards 2)
      (effect 'clock- warehouse_guards 1)
      (effect 'clock- yard_guards 1)
      (effect 'clock+ alert 2)
      (effect-reset-clock hall_distract)
      (effect-expr (action-log! "大厅干扰成功：大厅守卫+2，仓库和院各-1。"))))
    (react :when (clock-filled? warehouse_distract) :then (list
      (effect 'set warehouse_distracted true)
      (effect 'clock+ warehouse_guards 2)
      (effect 'clock- hall_guards 1)
      (effect 'clock- yard_guards 1)
      (effect 'clock+ alert 2)
      (effect-reset-clock warehouse_distract)
      (effect-expr (action-log! "仓库干扰成功：仓库守卫+2，大厅和院各-1。"))))
    (react :when (clock-filled? yard_distract) :then (list
      (effect 'set yard_distracted true)
      (effect 'clock+ yard_guards 2)
      (effect 'clock- hall_guards 1)
      (effect 'clock- warehouse_guards 1)
      (effect 'clock+ alert 2)
      (effect-reset-clock yard_distract)
      (effect-expr (action-log! "后院干扰成功：后院守卫+2，大厅和仓库各-1。"))))
    (react :when (and (clock-filled? hall_target) (not hall_done)) :then (list
      (effect 'set hall_done true)
      (effect 'clock+ completion 1)
      (effect-expr (action-log! "大厅目标完成：总完成进度 +1。"))))
    (react :when (and (clock-filled? warehouse_target) (not warehouse_done)) :then (list
      (effect 'set warehouse_done true)
      (effect 'clock+ completion 1)
      (effect-expr (action-log! "仓库目标完成：总完成进度 +1。"))))
    (react :when (and (clock-filled? yard_target) (not yard_done)) :then (list
      (effect 'set yard_done true)
      (effect 'clock+ completion 1)
      (effect-expr (action-log! "后院目标完成：总完成进度 +1。"))))
    (react :when (clock-filled? alert) :then (list
      (effect 'start-quick-dialogue "你的动静太大了。茶楼的人开始注意你，再待下去只会惹祸上身。")
      (effect 'end-encounter 'fail)))
    (react :when (clock-filled? completion) :then (list
      (effect 'start-quick-dialogue "三个目标都搜刮完了。茶楼重新安静下来之前，你已经把该拿的东西都拿走。")
      (effect 'end-encounter 'success))))
  :state (state
    (use-world-basics)
    (hall_guards (clock :title "大厅守卫" :initial 2 :max 6))
    (warehouse_guards (clock :title "仓库守卫" :initial 2 :max 6))
    (yard_guards (clock :title "后院守卫" :initial 2 :max 6))
    (hall_distract (clock :title "大厅干扰" :initial 0 :max 2))
    (warehouse_distract (clock :title "仓库干扰" :initial 0 :max 2))
    (yard_distract (clock :title "后院干扰" :initial 0 :max 2))
    (hall_distracted false)
    (warehouse_distracted false)
    (yard_distracted false)
    (alert (clock :title "警觉" :desc "全局察觉程度。满 6 即失败。" :initial 0 :max 6))
    (completion (clock :title "完成进度" :desc "三个目标各完成一次，总计 3 格。" :initial 0 :max 3))
    (hall_target (clock :title "大厅目标" :initial 0 :max 4))
    (warehouse_target (clock :title "仓库目标" :initial 0 :max 4))
    (yard_target (clock :title "后院目标" :initial 0 :max 5))
    (hall_done false)
    (warehouse_done false)
    (yard_done false))
  :root (teahouse-root))
