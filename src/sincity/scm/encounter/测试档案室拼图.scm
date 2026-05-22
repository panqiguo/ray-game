(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define clue-action
  (lambda (title desc clock-field flag suits)
    (when (not flag)
      (action
        :title title
        :desc desc
        :check (check
          :suits suits
          :risk 'mid
          :ok (outcome (list (effect 'clock+ clock-field 2)) "线索快完整了。")
          :partial (outcome (list (effect 'clock+ clock-field 1)) "你抓到一点边。")
          :fail (outcome (list (effect 'clock+ alert 1)) "抽屉和纸页的声音太响了。"))))))

(define-scene clue-a-scene
  (scene
    :title "病历柜"
    :desc "旧病历上的签名，被人用墨水涂过。"
    :show-clocks (list clue_a)
    :actions (list (clue-action "搜病历柜" "翻找同一晚的就诊记录。" clue_a clue_a_done (list 感知)))))

(define-scene clue-b-scene
  (scene
    :title "财务夹"
    :desc "真正的名字通常不会写在封面，而会写在报销人那一栏。"
    :show-clocks (list clue_b)
    :actions (list (clue-action "搜财务夹" "从付款记录里找出谁在替谁遮账。" clue_b clue_b_done (list 逻辑)))))

(define-scene clue-c-scene
  (scene
    :title "人事盒"
    :desc "离职档案堆在最下面，像故意等人忘掉。"
    :show-clocks (list clue_c)
    :actions (list (clue-action "搜人事盒" "查一份被撤掉的夜班名单。" clue_c clue_c_done (list 意志)))))

(define analysis-factors
  (lambda ()
    (list
      (factor -1 :when (not clue_a_done) :label "缺失病历线索")
      (factor -1 :when (not clue_b_done) :label "缺失财务线索")
      (factor -1 :when (not clue_c_done) :label "缺失人事线索"))))

(define analysis-desc
  (lambda ()
    (let ((count (+ (if clue_a_done 1 0) (if clue_b_done 1 0) (if clue_c_done 1 0))))
      (cond
        ((>= count 3) "三条线索全部咬合。推理有了牢固的起点。")
        ((= count 2) "两条线索交叉，指向同一个方向。还差几笔推理。")
        ((= count 1) "一条线索太单薄，推理需要跳很多步。")
        (else "没有线索就去下结论，无异于赌博。")))))

(define-scene analysis-scene
  (scene
    :title "判断行动"
    :desc (analysis-desc)
    :show-clocks (list analysis)
    :actions (list
      (action
        :title "开始拼图"
        :desc "停下搜索，把已有线索放到同一张纸上。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :factors (analysis-factors)
          :ok (outcome (list (effect 'clock+ analysis 2)) "你把两个看似无关的名字连到了一起。")
          :partial (outcome (list (effect 'clock+ analysis 1)) "推理卡在一处，还没能咬合。")
          :fail (outcome (list (effect 'clock+ alert 1)) "你推错了一步，不得不重新来过。"))))))

(define-scene archive-root
  (scene
    :title "档案室 · 时间不够用的拼图"
    :desc "你不可能既找全所有线索，又有时间从容分析。缺少的线索越多，推理就越不可靠。"
    :show-clocks (list alert)
    :children (list (clue-a-scene) (clue-b-scene) (clue-c-scene) (analysis-scene))))

(content
  :meta (meta :key '测试档案室拼图 :title "测试档案室拼图" :desc "每条缺失线索让分析行动 -1，找到后对应 factor 消失。")
  :on-success (list (effect 'set 'test_archive_done true))
  :on-fail (list (effect 'set 'test_archive_failed true) (effect 'add energy -1))
  ;; :on-cycle (list (effect 'clock+ alert 1))
  :reacts (reacts
    (react :when (and (clock-filled? clue_a) (not clue_a_done)) :then (list (effect 'set clue_a_done true) (effect 'start-quick-dialogue "病历柜里有一张被换过的登记页。")))
    (react :when (and (clock-filled? clue_b) (not clue_b_done)) :then (list (effect 'set clue_b_done true) (effect 'start-quick-dialogue "财务夹里有一笔不该由诊所支付的车费。")))
    (react :when (and (clock-filled? clue_c) (not clue_c_done)) :then (list (effect 'set clue_c_done true) (effect 'start-quick-dialogue "人事盒里的夜班名单少了一个人。")))
    (react
      :when (clock-filled? analysis)
      :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? alert) :then (list (effect 'end-encounter 'fail))))
  :state (state
    (use-world-basics)
    (alert (clock :title "被发现" :initial 0 :max 5))
    (analysis (clock :title "分析" :initial 0 :max 16))
    (clue_a (clock :title "病历线索" :initial 0 :max 3))
    (clue_b (clock :title "财务线索" :initial 0 :max 3))
    (clue_c (clock :title "人事线索" :initial 0 :max 3))
    (clue_a_done false)
    (clue_b_done false)
    (clue_c_done false))
  :root (archive-root))
