(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")

(define step-between
  (action
    :title "插进去替他解围"
    :desc "你像个刚好路过、又刚好不爱看热闹的人一样插进他们中间。"
    :check (check
      :suits (list 敏锐)
      :risk 'low
      :ok (outcome (list (effect 'clock+ advantage 2)) "")
      :partial (outcome (list (effect 'clock+ advantage 1) (effect 'add 'energy -1)) "")
      :fail (outcome (list (effect 'add 'energy -1)) "他们先把你也算进了麻烦里。"))))

(define crack-one-open
  (action
    :title "狠狠干翻一个追债人"
    :desc "最快的说服方式通常都很粗糙。"
    :check (check
      :suits (list 暴力)
      :risk 'mid
      :ok (outcome (list (effect 'clock+ advantage 2)) "")
      :partial (outcome (list (effect 'clock+ advantage 1) (effect 'add 'health -1)) "")
      :fail (outcome (list (effect 'add 'health -1)) "你没狠狠干净，场面一下子乱了。"))))

(content
  :meta (meta :key '巷口赌徒 :title "巷口赌徒" :desc "赌徒被人按在巷口，你可以路过，也可以插手。")
  :on-success (list
    (effect 'set 'gambler_met true))
  :on-fail (list
    (effect 'add 'energy -1))
  :reacts (list
    (react :when (clock-filled? advantage) :then (list (effect 'end-encounter 'success))))
  :vars (list
    (var 'advantage (clock :title "局势" :initial 0 :max 3)))
  :root
  (scene
    :title "巷口碰撞"
    :desc "追债的人把赌徒按在墙上搜身。他脸上那点求生欲，比西装里的零钱更先掉出来。"
    :show-clocks (list advantage)
    :actions (list step-between crack-one-open)))
