(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define (stance-scene)
  (scene
    :title (if (= stance 'guard) "防守" "进攻")
    :desc
      (if (= stance 'guard)
        "他把身体收得很窄，不轻易出手。普通攻击会被挡掉大半。"
        "他开始向前压。破绽更多，但失误的代价也更大。")
    :show-clocks (list stance_timer duel_progress)
    :actions (list
      (action
        :title "佯攻"
        :desc "不追求伤害，只试探他的重心。防守姿态下成功可以逼他提前切换。"
        :check (check
          :suit 敏锐
          :risk 'mid
          :ok (outcome
                (if (= stance 'guard)
                  (list (effect 'set stance 'attack) (effect-reset-clock stance_timer) (effect 'clock+ duel_progress 1))
                  (list (effect 'clock+ duel_progress 2)))
                "你读出了他的重心变化。")
          :partial (outcome (list (effect 'clock+ duel_progress 1)) "他挡开了，但节奏被你牵动。")
          :fail (outcome (list (effect 'add energy -1)) "他没有上当。")))
      (action
        :title "普通攻击"
        :desc "稳扎稳打。防守姿态下推进减半，进攻姿态下效果更好。"
        :check (check
          :suit 暴力
          :risk 'low
          :ok (outcome
                (if (= stance 'guard)
                  (list (effect 'clock+ duel_progress 1))
                  (list (effect 'clock+ duel_progress 2)))
                "你抢到一点主动。")
          :partial (outcome (list (effect 'clock+ duel_progress 1)) "你没有被节奏甩开。")
          :fail (outcome (list (effect 'add energy -1)) "这一拍被他吃掉了。")))
      (action
        :title "防守反击"
        :desc "架住他的攻势再回敬。进攻姿态下效果好但风险更高。"
        :check (check
          :suit 知识
          :risk (if (= stance 'attack) 'high 'mid)
          :ok (outcome
                (if (= stance 'attack)
                  (list (effect 'clock+ duel_progress 2))
                  (list (effect 'clock+ duel_progress 1)))
                "你架住他的攻势，回敬了一击。")
          :partial (outcome (list (effect 'clock+ duel_progress 1)) "你挡得不漂亮，但足够稳住。")
          :fail (outcome
                (if (= stance 'attack)
                  (list (effect 'add health -1))
                  (list (effect 'add energy -1)))
                "你慢了半拍。"))))))

(content
  :meta (meta :key '测试姿态对抗 :title "测试姿态对抗" :desc "固定三行动对两姿态的对抗系统。")
  :on-success (list (effect 'set 'test_stance_done true))
  :on-fail (list (effect 'set 'test_stance_failed true))
  :on-cycle (list (effect 'clock+ stance_timer 1))
  :reaction-die
    (reaction-die
      (if (= stance 'guard)
        (reaction-table
          (face 1 "格挡" (effect 'clock- duel_progress 1))
          (face 2 "格挡" (effect 'clock- duel_progress 1))
          (face 3 "格挡" (effect 'clock- duel_progress 1))
          (face 4 "空")
          (face 5 "空")
          (face 6 "空"))
        (reaction-table
          (face 1 "空")
          (face 2 "空")
          (face 3 "空")
          (face 4 "伤害" (effect 'add health -1))
          (face 5 "伤害" (effect 'add health -1))
          (face 6 "伤害" (effect 'add health -1)))))
  :reacts (list
    (react :when (clock-filled? duel_progress) :then (list (effect 'end-encounter 'success)))
    (react
      :when (clock-filled? stance_timer)
      :then (list
        (if (= stance 'guard)
          (effect 'set stance 'attack)
          (effect 'set stance 'guard))
        (effect-reset-clock stance_timer))))
  :vars (append
    world-basics-vars
    (list
    (var 'stance 'guard)
    (var 'stance_timer (clock :title "姿态持续" :initial 0 :max 3))
    (var 'duel_progress (clock :title "压制进度" :initial 0 :max 8)))
    )
  :root (stance-scene))
