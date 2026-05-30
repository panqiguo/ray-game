(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

; 三时钟模型
;
;   calm     (0→8)    缓和进度
;            填满 = 薇拉主动放下枪（语言路径胜利）
;
;   danger   (0→12)   危险程度
;            高位时 gate 靠近行动（她太激动 = 你无法移动）
;            满格时走火，扣血后重置为 6，场景继续
;
;   distance (0→6)    物理距离
;            达到 3 解锁「压制手腕」
;            达到 5 解锁「夺枪」（物理路径胜利入口）
;
; 两条胜利路径：
;   A. 语言路径：calm 填满，她主动放下枪
;   B. 物理路径：先把 danger 压到 7 以下，推进 distance，最后夺枪
;
; 核心张力：
;   danger 同时是「危险压力」和「靠近行动的门」
;   玩家不能只推一条轴——必须交替管理情绪和距离

(define (standoff)
  (scene
    :title "无门牌公寓 · 枪口"
    :desc
      (cond
        ((>= (clock-value danger) 9)
          "她的手指压得很深。你说的每个字都在赌。")
        ((>= (clock-value distance) 4)
          "枪口和你的距离以厘米计。她能感觉到你的体温。")
        ((>= (clock-value calm) 5)
          "她还拿着枪，但她在听。这是目前唯一的进展。")
        (else
          "屋里没有灯。她坐在阴影里，枪口稳稳对着你。"))
    :show-clocks (list calm danger distance)
    :actions (list

      ; ─── 语言行动 ───────────────────────────────────────────
      ; 始终可用
      ; 成功推进 calm，失败推高 danger

      (action
        :title "放低姿态"
        :desc "你把自己变得没有威胁。不急着解释，先让她的呼吸跟上你的节奏。"
        :check (check
          :suits (list 魅力)
          :risk 'low
          :ok      (outcome (list (effect 'clock+ calm 1)) "")
          :partial (outcome (list) "")
          :fail    (outcome (list (effect 'clock+ danger 2)) "")))

      (action
        :title "解释立场"
        :desc "你说出你为什么在这里，以及你知道什么。信息量更大，风险也更大。"
        :check (check
          :suits (list 魅力)
          :risk 'mid
          :ok      (outcome (list (effect 'clock+ calm 2)) "")
          :partial (outcome (list (effect 'clock+ calm 1) (effect 'clock+ danger 1)) "")
          :fail    (outcome (list (effect 'clock+ danger 3)) "")))

      (action
        :title "反问她"
        :desc "你不解释，而是问一个她没想到你会问的问题。"
        :check (check
          :suits (list 敏锐)
          :risk 'mid
          :ok      (outcome (list (effect 'clock+ calm 2) (effect 'clock- danger 1)) "")
          :partial (outcome (list (effect 'clock+ calm 1)) "")
          :fail    (outcome (list (effect 'clock+ danger 2)) "")))

      ; ─── 靠近 ────────────────────────────────────────────────
      ; 被 danger gate：她太激动时这个行动不出现
      ; 这是两条轴互相咬合的核心机制

      (when (< (clock-value danger) 7)
        (action
          :title "缓慢靠近"
          :desc "你用她注意力的间隙缩短距离。只有她足够冷静时才有机会移动。"
          :check (check
          :suits (list 敏锐)
          :risk 'mid
          :ok      (outcome (list (effect 'clock+ distance 2)) "")
            :partial (outcome (list (effect 'clock+ distance 1) (effect 'clock+ danger 2)) "")
            :fail    (outcome (list (effect 'clock+ danger 3)) ""))))

      ; ─── 夺枪行动 ─────────────────────────────────────────────
      ; 被 distance gate：必须先靠近才能解锁

      (when (>= (clock-value distance) 3)
        (action
          :title "压制手腕"
          :desc "你不夺枪，只压住她持枪手的角度，把枪口从你身上挪开。"
          :check (check
          :suits (list 暴力)
          :risk 'high
          :ok      (outcome (list (effect 'clock+ distance 2) (effect 'clock+ danger 1)) "")
            :partial (outcome (list (effect 'clock+ distance 1) (effect 'clock+ danger 3) (effect 'add health -1)) "")
            :fail    (outcome (list (effect 'clock+ danger 4)) ""))))

      (when (>= (clock-value distance) 5)
        (action
          :title "夺枪"
          :desc "距离够了。剩下的只有速度。"
          :check (check
          :suits (list 暴力)
          :risk 'high
          :ok      (outcome (list (effect 'clock+ calm 8)) "")   ; 直接填满 calm = 物理路径胜利
            :partial (outcome (list (effect 'clock+ danger 3) (effect 'add health -1)) "")
            :fail    (outcome (list (effect 'clock+ danger 5)) "")))))))

(content
  :meta (meta :key '公寓对峙 :title "公寓对峙" :desc "")

  :on-success (list
    (effect 'set 'standoff_resolved true)
    (effect 'set 'chapter_2_done true)
    (effect 'set 'main_resolved true)
    (effect 'start-quick-dialogue "# 第二章尾声\n\n# speaker: 薇拉\n枪口终于偏开。她没有哭，只是像终于允许自己喘气。\n\n# speaker: 科尔\n弗雷德里克不是在找妻子。他是在找她带走的证据。"))
  :on-fail (list
    (effect 'set 'standoff_failed true)
    (effect 'set 'chapter_2_done true)
    (effect 'add 'police_relation -1)
    (effect 'start-quick-dialogue "# 走火\n\n# speaker: 科尔\n枪声在小房间里炸开。我没有死，但真相从门缝里逃了出去。"))

  ; reaction-die：薇拉的自主压力
  ; danger 越高，每回合走火概率越大
  ; 走火不直接结束场景，而是扣血 + 重置 danger = 6，场景继续
  :reaction-die
    (reaction-die
      (cond
        ((>= (clock-value danger) 10)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "走火" (effect 'add health -1) (effect 'set danger 6))
            (face 5 "走火" (effect 'add health -1) (effect 'set danger 6))
            (face 6 "走火" (effect 'add health -1) (effect 'set danger 6))))
        ((>= (clock-value danger) 7)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "空")
            (face 5 "走火" (effect 'add health -1) (effect 'set danger 6))
            (face 6 "走火" (effect 'add health -1) (effect 'set danger 6))))
        (else nil)))

  :reacts (list
    ; 语言路径胜利：calm 填满
    (react
      :when (clock-filled? calm)
      :then (list (effect 'end-encounter 'success)))
    ; danger 满格：走火，扣血，重置后场景继续
    (react
      :when (clock-filled? danger)
      :then (list
        (effect 'add health -2)
        (effect 'set danger 6))))

  :vars (append
    world-basics-vars
    (list
    (var 'calm
      (clock
        :title "缓和"
        :desc "填满后薇拉主动放下枪。"
        :initial 0
        :max 8))
    (var 'danger
      (clock
        :title "危险"
        :desc "她的恐慌程度。超过 7 时无法靠近；满格时走火。"
        :initial 3
        :max 12))
    (var 'distance
      (clock
        :title "距离"
        :desc "物理距离。达到 3 解锁压制，达到 5 解锁夺枪。"
        :initial 0
        :max 6)))

)
  :root (standoff))
