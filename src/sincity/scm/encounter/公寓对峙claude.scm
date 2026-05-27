(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

;; ══════════════════════════════════════════════════════════════
;;  公寓枪对峙 — 双轴状态机模型
;;
;;  两条轨道，各自独立推进，互相制约：
;;
;;    emotion  (0→9)   薇拉情绪
;;             0 = 极度恐慌    crisis 满 → 她开枪
;;             3 = 防御警惕    crisis 满 → 她逃跑
;;             6 = 愿意听
;;             9 = 放下枪      → 语言路径胜利
;;
;;    distance (0→9)   物理距离
;;             0 = 远
;;             3 = 中距
;;             6 = 近
;;             9 = 夺枪距离    → 解锁物理路径
;;
;;  全局压力：
;;    crisis   (0→18)  崩溃阈值
;;             错误行动推高，reaction-die 在高位自动推进
;;             满格时根据 emotion 触发不同失败分支
;;
;;  核心约束：
;;    1. emotion=0 时 distance 锁死（无法靠近）
;;    2. distance=9 才解锁夺枪行动
;;    3. 靠近成功后 crisis+1（移动有代价，不是免费的）
;;    4. 语言行动在不同 emotion 阶段风险不同
;;
;;  胜利路径：
;;    A. 语言路径：emotion 推至 9（她主动放下枪）
;;    B. 物理路径：emotion>=3 → 推 distance 至 9 → 夺枪
;; ══════════════════════════════════════════════════════════════

(define (standoff)
  (scene
   :title "无门牌公寓 · 枪口"
   :desc
   (cond
    ((= (clock-value emotion) 0)
     "屋里没有灯。她坐在阴影里，枪口稳稳对着你。手指压在扳机上。你说的每个字都在赌。")
    ((and (= (clock-value emotion) 3) (>= (clock-value crisis) 12))
     "她在听，但已经快到临界点了。枪口没有放下，脚步已经准备好。")
    ((= (clock-value emotion) 3)
     "她在听，但不信。枪口没有放下。")
    ((and (= (clock-value emotion) 6) (>= (clock-value distance) 6))
     "她愿意听了。但你已经很近，她能感觉到你的体温。")
    ((= (clock-value emotion) 6)
     "她愿意听你说话。枪口还在，但眼神变了。")
    (else
     ""))
   :show-clocks (list emotion distance crisis)
   :actions (list

             ;; ─── 语言行动 ─────────────────────────────────────────────
             ;;
             ;; 三个阶段对应三个版本，风险递减。
             ;; 同一个"开口"动作，在不同情绪阶段是完全不同的赌注。

             ;; 阶段 0：极度恐慌 — 高风险
             ;; 任何话都可能是最后一句

             (cond ((= (clock-value emotion) 0)
                    (action
                     :title "开口"
                     :desc "你必须说些什么。在这个状态下，任何话都可能是最后一句。"
                     :check (check
                             :suits (list 意志)
                             :risk 'high
                             :ok      (outcome (list (effect 'clock+ emotion 1)) "")
                             :partial (outcome (list (effect 'clock+ crisis 1)) "")
                             :fail    (outcome (list (effect 'clock+ crisis 2)) ""))))

                   ((< (clock-value emotion) 3)
                    (action
                     :title "继续说"
                     :desc "她在听，但还没有信。你有空间，但不多。"
                     :check (check
                             :suits (list 意志)
                             :risk 'mid
                             :ok      (outcome (list (effect 'clock+ emotion 1)) "")
                             :partial (outcome (list (effect 'clock+ crisis 1)) "")
                             :fail    (outcome (list (effect 'clock+ crisis 2)) ""))))

                   ((< (clock-value emotion) 6)
                    (action
                     :title "说下去"
                     :desc "她愿意听。这是目前最安全的推进方式。"
                     :check (check
                             :suits (list 意志)
                             :risk 'low
                             :ok      (outcome (list (effect 'clock+ emotion 1)) "")
                             :partial (outcome (list) "")
                             :fail    (outcome (list (effect 'clock+ crisis 2)) "")))))
             ;; 阶段 1：防御警惕 — 中风险
             ;; 语言开始有效，但随时可能失去她
             
             ;; 阶段 2：愿意听 — 低风险
             ;; 语言是这个阶段最好的工具，也是推向胜利的路
             
             ;; ─── 靠近 ─────────────────────────────────────────────────
             ;;
             ;; emotion=0 时此行动不出现——她太恐慌，任何移动都会触发开枪
             ;; 成功后 crisis+1：移动不是免费的，张力留在局面里
             ;; 这是两条轴互相咬合的核心：你必须先稳住情绪，才能移动身体

             (when (and (>= (clock-value emotion) 3) (< (clock-value distance) 9))
               (action
                :title "靠近"
                :desc "你用她注意力的间隙缩短距离。每一步都让枪口更近，也让选择更少。"
                :check (check
                        :suits (list 感知)
                        :risk 'mid
                        :ok      (outcome (list (effect 'clock+ distance 1) (effect 'clock+ crisis 1)) "")
                        :partial (outcome (list (effect 'clock+ crisis 1)) "")
                        :fail    (outcome (list (effect 'clock+ crisis 2)) ""))))

             ;; ─── 夺枪 ─────────────────────────────────────────────────
             ;;
             ;; 两个版本：情绪差时是强冲赌命，情绪好时是有把握的动作
             ;; 风险差距很大，这让玩家有理由在靠近后继续管理情绪

             ;; 情绪差（emotion < 2）：强冲，极高风险
             ;; 失败直接结束场景
             (when (and (= (clock-value distance) 9) (< (clock-value emotion) 6))
               (action
                :title "强冲"
                :desc "距离够了，但她还没有准备好。这是一个赌命的选择。"
                :check (check
                        :suits (list 意志)
                        :risk 'high
                        :ok      (outcome (list (effect 'end-encounter 'success)) "")
                        :partial (outcome (list (effect 'add health -1)
                                                (effect 'clock+ crisis 1)) "")
                        :fail    (outcome (list (effect 'add health -1)
                                                (effect 'clock+ crisis 2)) ""))))

             ;; 情绪好（emotion >= 2）：谨慎夺枪，中风险
             (when (and (= (clock-value distance) 9) (>= (clock-value emotion) 6))
               (action
                :title "夺枪"
                :desc "距离够了，她也没那么紧张了。现在是最好的时机。"
                :check (check
                        :suits (list 意志)
                        :risk 'mid
                        :ok      (outcome (list (effect 'end-encounter 'success)) "")
                        :partial (outcome (list (effect 'add health -1)
                                                (effect 'clock+ crisis 1)) "")
                        :fail    (outcome (list (effect 'clock+ crisis 2)) "")))))))

(content
 :meta (meta :key '公寓对峙 :title "公寓对峙" :desc "")

 :on-success (list (effect 'set 'standoff_resolved true))
 :on-fail    (list (effect 'set 'standoff_failed true))

 ;; reaction-die：薇拉的自主压力
 ;; 她不是在等你。crisis 高位时她会自己把局面推向临界点。
 :reaction-die
 (reaction-die
  (cond
   ((>= (clock-value crisis) 6)
    (reaction-table
     (face 1 "空")
     (face 2 "空")
     (face 3 "空")
     (face 4 "临界" (effect 'clock+ crisis 1))
     (face 5 "临界" (effect 'clock+ crisis 1))
     (face 6 "临界" (effect 'clock+ crisis 1))))
   ((>= (clock-value crisis) 3)
    (reaction-table
     (face 1 "空")
     (face 2 "空")
     (face 3 "空")
     (face 4 "空")
     (face 5 "加剧" (effect 'clock+ crisis 1))
     (face 6 "加剧" (effect 'clock+ crisis 1))))
   (else nil)))

 :reacts (list

          ;; 语言路径胜利：emotion 到达 3
          (react
           :when (clock-filled? emotion)
           :then (list (effect 'end-encounter 'success)))

          ;; crisis 满，emotion=0：她开枪
          (react
           :when (and (clock-filled? crisis) (= (clock-value emotion) 0))
           :then (list
                  (effect 'add health -2)
                  (effect 'end-encounter 'fail)))

          ;; crisis 满，emotion=3：她逃跑
          (react
           :when (and (clock-filled? crisis) (= (clock-value emotion) 3))
           :then (list
                  (effect 'end-encounter 'fail)))

          ;; crisis 满，emotion>=6：她没有崩溃，但代价已经付了
          ;; 场景继续，crisis 重置
          (react
           :when (and (clock-filled? crisis) (>= (clock-value emotion) 6))
           :then (list
                  (effect 'set crisis 0))))

 :state (list
         (use-world-basics)
         (var 'emotion
          (clock
           :title "情绪"
           :desc "0=极度恐慌, 3=防御警惕, 6=愿意听, 9=放下枪。填满触发语言路径胜利。"
           :initial 0
           :max 9))
         (var 'distance
          (clock
           :title "距离"
           :desc "0=远, 3=中距, 6=近, 9=夺枪距离。填满解锁夺枪行动。"
           :initial 0
           :max 9))
         (var 'crisis
          (clock
           :title "崩溃阈值"
           :desc "全局压力。满格时根据情绪阶段触发开枪（emotion=0）或逃跑（emotion=3）。"
           :initial 0
           :max 9)))

 :root (standoff))
