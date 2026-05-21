(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define-scene stance-scene
  (scene
    :title (cond
      ((= stance 'guard) "防守")
      ((= stance 'press) "压制")
      (else "进攻"))
    :desc
      (cond
        ((= stance 'guard) "他把身体收得很窄。普通攻击会被挡掉一半，除非你用佯攻骗他换姿态。")
        ((= stance 'press) "他开始压你的行动空间。这里适合强攻，但拖久了资源会被削。")
        (else "他终于露出进攻欲望。危险最大，但格挡反击能把伤害化成推进。"))
    :show-clocks (list stance_timer duel_progress)
    :actions (list
      (action
        :title "观察"
        :desc "花一个行动读他的节奏，确认姿态还能维持多久。"
        :effects (list
          (effect 'start-quick-dialogue "你盯住他的肩和脚踝。姿态时钟每三格切换一次；现在剩下的格数，已经写在他的呼吸里。")))
      (when (= stance 'guard)
        (action
          :title "佯攻诱骗"
          :desc "不追求伤害，只骗他提前离开防守姿态。"
          :check (check
            :suits (list 感知)
            :risk 'mid
            :ok (outcome (list (effect 'set stance 'press) (effect-reset-clock stance_timer)) "他被你骗出防守，重心压了出来。")
            :partial (outcome (list (effect 'clock+ duel_progress 1)) "他挡住了大半，但防守边缘裂开一点。")
            :fail (outcome (list (effect 'add energy -1)) "他没有上当，只让你白白交出一次节奏。"))))
      (when (= stance 'press)
        (action
          :title "强攻"
          :desc "他压得越凶，身后越空。这个姿态下强攻进度翻倍。"
          :check (check
            :suits (list 意志)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ duel_progress 2)) "你迎着压制撞进去，直接打穿他的节奏。")
            :partial (outcome (list (effect 'clock+ duel_progress 1) (effect 'add health -1)) "你推进了，也被他顶了一下。")
            :fail (outcome (list (effect 'add health -1)) "你被他压回原地。"))))
      (when (= stance 'attack)
        (action
          :title "格挡反击"
          :desc "在进攻姿态里防住第一下，再把反击塞进他的空门。"
          :check (check
            :suits (list 意志 感知)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ duel_progress 1) (effect 'set counter_guard true)) "你架住他的拳，反击打在肋侧。")
            :partial (outcome (list (effect 'clock+ duel_progress 1) (effect 'set counter_guard true)) "你挡得不漂亮，但足够让伤害落空。")
            :fail (outcome (list (effect 'add health -1)) "你慢了半拍，先进了他的攻击线。"))))
      (action
        :title "普通推进"
        :desc "不针对姿态，只稳稳抢进度。防守姿态下效果会显得很钝。"
        :check (check
          :suits (list 意志)
          :risk 'low
          :ok (outcome (list (effect 'clock+ duel_progress (if (= stance 'guard) 1 2))) "你抢到一点主动。")
          :partial (outcome (list (effect 'clock+ duel_progress 1)) "你至少没有被节奏甩开。")
          :fail (outcome (list (effect 'add energy -1)) "这一拍被他吃掉了。"))))))

(content
  :meta (meta :key '测试姿态对抗 :title "测试姿态对抗" :desc "测试固定姿态循环、反应骰与针对性破绽行动。")
  :on-success (list (effect 'set 'test_stance_done true))
  :on-fail (list (effect 'set 'test_stance_failed true))
  :on-cycle (list (effect 'clock+ stance_timer 1) (effect 'set counter_guard false))
  :reaction-die
    (reaction-die
      (cond
        ((= stance 'guard)
          (reaction-table
            (face 1 "格挡" (effect 'clock- duel_progress 1))
            (face 2 "格挡" (effect 'clock- duel_progress 1))
            (face 3 "格挡" (effect 'clock- duel_progress 1))
            (face 4 "格挡" (effect 'clock- duel_progress 1))
            (face 5 "空")
            (face 6 "空")))
        ((= stance 'press)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "削弱" (effect 'add energy -1))
            (face 5 "削弱" (effect 'add energy -1))
            (face 6 "削弱" (effect 'add energy -1))))
        (else
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "伤害" (when (not counter_guard) (effect 'add health -1)))
            (face 4 "伤害" (when (not counter_guard) (effect 'add health -1)))
            (face 5 "伤害" (when (not counter_guard) (effect 'add health -1)))
            (face 6 "伤害" (when (not counter_guard) (effect 'add health -1)))))))
  :reacts (reacts
    (react :when (clock-filled? duel_progress) :then (list (effect 'end-encounter 'success)))
    (react
      :when (clock-filled? stance_timer)
      :then (list
        (cond
          ((= stance 'guard) (effect 'set stance 'press))
          ((= stance 'press) (effect 'set stance 'attack))
          (else (effect 'set stance 'guard)))
        (effect-reset-clock stance_timer))))
  :state (state
    (use-world-basics)
    (stance 'guard)
    (stance_timer (clock :title "姿态持续" :initial 0 :max 3))
    (duel_progress (clock :title "压制进度" :initial 0 :max 8))
    (counter_guard false))
  :root (stance-scene))
