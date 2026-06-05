(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")

(define-fragment cold-warning
  (action
    :title "把话说得够冷"
    :desc "先给他一个体面的台阶，看他要不要自己滚下去。"
    :check (check
      :suit 魅力
      :risk 'low
      :ok (outcome (list (effect 'clock+ pressure 2)) "")
      :partial (outcome (list (effect 'clock+ pressure 1) (effect 'add 'energy -1)) "")
      :fail (outcome (list (effect 'add 'energy -1)) "他把你的客气听成了软弱。"))))

(define-fragment push-him-back
  (action
    :title "直接把人从吧台前挤开"
    :desc "别讲道理，直接把空间抢回来。"
    :check (check
      :suit 暴力
      :risk 'mid
      :ok (outcome (list (effect 'clock+ pressure 2)) "")
      :partial (outcome (list (effect 'clock+ pressure 1) (effect 'add 'health -1)) "")
      :fail (outcome (list (effect 'add 'health -1)) "他不肯让，你们把酒杯和椅子都撞响了。"))))

(content
  :meta (meta :key '酒吧赶客人 :title "酒吧赶客人" :desc "替金发女郎把占便宜的客人请远一点。")
  :on-success (list
    (effect 'set 'blonde_customer_chased true))
  :on-fail (list
    (effect 'add 'energy -1))
  :reacts (list
    (react :when (clock-filled? pressure) :then (list (effect 'end-encounter 'success))))
  :vars (list
    (var 'pressure (clock :title "施压" :initial 0 :max 3)))
  :root
  (scene
    :title "吧台边的麻烦"
    :desc "一个喝高了的客人把手搭得太自然，像这里所有女人都该免费替他解闷。你只需要让他明白今晚不行。"
    :show-clocks (list pressure)
    :actions (list (cold-warning) (push-him-back))))
