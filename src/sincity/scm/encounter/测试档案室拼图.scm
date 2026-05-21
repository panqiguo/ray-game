(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define clue-action
  (lambda (title desc clock-field flag)
    (when (not flag)
      (action
        :title title
        :desc desc
        :check (check
          :suits (list 感知 逻辑)
          :risk 'mid
          :ok (outcome (list (effect 'clock+ clock-field 2)) "线索快完整了。")
          :partial (outcome (list (effect 'clock+ clock-field 1)) "你抓到一点边。")
          :fail (outcome (list (effect 'clock+ alert 1)) "抽屉和纸页的声音太响了。"))))))

(define-scene clue-a-scene
  (scene
    :title "病历柜"
    :desc "旧病历上的签名，被人用墨水涂过。"
    :show-clocks (list clue_a)
    :actions (list (clue-action "搜病历柜" "翻找同一晚的就诊记录。" clue_a clue_a_done))))

(define-scene clue-b-scene
  (scene
    :title "财务夹"
    :desc "真正的名字通常不会写在封面，而会写在报销人那一栏。"
    :show-clocks (list clue_b)
    :actions (list (clue-action "搜财务夹" "从付款记录里找出谁在替谁遮账。" clue_b clue_b_done))))

(define-scene clue-c-scene
  (scene
    :title "人事盒"
    :desc "离职档案堆在最下面，像故意等人忘掉。"
    :show-clocks (list clue_c)
    :actions (list (clue-action "搜人事盒" "查一份被撤掉的夜班名单。" clue_c clue_c_done))))

(define define-analysis-risk
  (lambda ()
    (cond
      ((>= clues 2) 'low)
      ((= clues 1) 'mid)
      (else 'high))))

(define-scene analysis-scene
  (scene
    :title "判断行动"
      :desc
        (cond
          ((>= clues 3) "三条线索全部咬合。你还剩一点就能关上这个案子。")
          ((= clues 2) "两条线索交叉，指向同一个方向。还差几笔推理。")
          ((= clues 1) "一条线索太单薄，推理需要跳很多步。")
          (else "没有线索就去下结论，无异于赌博。"))
    :show-clocks (list analysis)
    :actions (list
      (action
        :title "开始拼图"
        :desc "停下搜索，把已有线索放到同一张纸上。"
        :check (check
          :suits (list 逻辑)
          :risk (define-analysis-risk)
          :ok (outcome (list (effect 'clock+ analysis 1)) "你把两个看似无关的名字连到了一起。")
          :partial (outcome (list) "推理卡在一处，还没能咬合。")
          :fail (outcome (list (effect 'clock+ alert 1)) "你推错了一步，不得不重新来过。"))))))

(define-scene archive-root
  (scene
    :title "档案室 · 时间不够用的拼图"
    :desc "你不可能搜完全部再从容分析。线索能让推理变快，但搜线索本身也要时间。"
    :show-clocks (list alert)
    :children (list (clue-a-scene) (clue-b-scene) (clue-c-scene) (analysis-scene))))

(content
  :meta (meta :key '测试档案室拼图 :title "测试档案室拼图" :desc "测试线索数量动态改变分析难度。")
  :on-success (list (effect 'set 'test_archive_done true))
  :on-fail (list (effect 'set 'test_archive_failed true) (effect 'add energy -1))
  :on-cycle (list (effect 'clock+ alert 1))
  :reacts (reacts
    (react :when (and (clock-filled? clue_a) (not clue_a_done)) :then (list (effect 'set clue_a_done true) (effect 'add clues 1) (effect 'clock+ analysis 2) (effect 'start-quick-dialogue "病历柜里有一张被换过的登记页。")))
    (react :when (and (clock-filled? clue_b) (not clue_b_done)) :then (list (effect 'set clue_b_done true) (effect 'add clues 1) (effect 'clock+ analysis 2) (effect 'start-quick-dialogue "财务夹里有一笔不该由诊所支付的车费。")))
    (react :when (and (clock-filled? clue_c) (not clue_c_done)) :then (list (effect 'set clue_c_done true) (effect 'add clues 1) (effect 'clock+ analysis 2) (effect 'start-quick-dialogue "人事盒里的夜班名单少了一个人。")))
    (react
      :when (clock-filled? analysis)
      :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? alert) :then (list (effect 'end-encounter 'fail))))
  :state (state
    (use-world-basics)
    (alert (clock :title "被发现" :initial 0 :max 3))
    (analysis (clock :title "分析" :desc "每条已完成线索直接推进分析进度。" :initial 0 :max 10))
    (clues 0)
    (clue_a (clock :title "病历线索" :initial 0 :max 3))
    (clue_b (clock :title "财务线索" :initial 0 :max 3))
    (clue_c (clock :title "人事线索" :initial 0 :max 3))
    (clue_a_done false)
    (clue_b_done false)
    (clue_c_done false))
  :root (archive-root))
