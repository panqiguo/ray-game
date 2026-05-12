(include "../enum-symbols.scm")

(define breathe
  (action
    :title "喘息一下"
    :desc "你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。"
    :always (list (effect 'reset-hand) (effect 'add health -1))
  ))

(define counter
  (action
    :title "防守反击"
    :desc "你先稳住头脸和脚步，再找机会把他顶开。"
    :check (check
    :suits (list 逻辑)
    :risk low
    :ok (outcome "你稳稳顶住了节奏。" (list (effect 'clock+ initiative 1)))
    :partial (outcome "你至少没有继续吃亏。" (list (effect 'clock+ initiative 1)))
    :fail (outcome "你还是没完全顶住。" (list (effect 'add health -1)))
  )
  ))

(define heavy_punch
  (action
    :title "重拳追击"
    :desc "你不给他喘气空间，直接压上去狠狠干。"
    :check (check
    :suits (list 意志)
    :risk mid
    :ok (outcome "你狠狠干中了一拳。" (list (effect 'clock- enemy_hp 1)))
    :partial (outcome "你打实了一下，但他还撑着。" (list (effect 'clock- enemy_hp 1)))
    :fail (outcome "你被他架住了。" (list (effect 'add health -1)))
  )
  ))

(define feint
  (action
    :title "假动作试探"
    :desc "你做一个假动作，先试着把他的防守骗开一层。"
    :check (check
    :suits (list 感知)
    :risk mid
    :ok (outcome "他的防守被你骗得动了一下。" (list (effect 'clock+ opening 1)))
    :partial (outcome "他开始有点被你带着走。" (list (effect 'clock+ opening 1)))
    :fail (outcome "他没上当。" (list ))
  )
  ))

(define knee_kick
  (action
    :title "踹膝脱身"
    :desc "你不追求漂亮，而是直接踹他的支撑腿。"
    :check (check
    :suits (list 逻辑)
    :risk mid
    :ok (outcome "你一下踹垮了他。" (list (effect 'clock- enemy_hp 1)))
    :partial (outcome "你们各有胜负" (list (effect 'clock- enemy_hp 1) (effect 'add health -1)))
    :fail (outcome "你动作慢了。" (list (effect 'add health -1)))
  )
  ))

(define rush_knife
  (action
    :title "扑向折刀"
    :desc "你冒险扑向地上的折刀，想先把局势翻过来。"
    :always (list (effect 'add health -1))
    :check (check
    :suits (list 感知)
    :risk high
    :ok (outcome "你手已经摸到刀柄了。" (list (effect 'clock+ knife 1)))
    :partial (outcome "你拖着伤抢到了第一步位置。" (list (effect 'clock+ knife 1)))
    :fail (outcome "你被拦住了" (list ))
  )
  ))

(define blunt_punch
  (action
    :title "直接挥拳"
    :desc "你不跟他磨，直接狠狠干出一步空间。"
    :check (check
    :suits (list 意志)
    :risk high
    :ok (outcome "你狠狠干出了一步空间。" (list (effect 'clock+ initiative 1)))
    :partial (outcome "你砸中了他，但也只是暂时逼开。" (list (effect 'clock+ initiative 1) (effect 'add health -1)))
    :fail (outcome "你被他顶了回来。" (list (effect 'add health -1)))
  )
  ))

(define knife_press
  (action
    :title "持刀逼退"
    :desc "刀一到手，你立刻逼他后撤，把主动权压回来。"
    :check (check
    :suits (list 意志)
    :risk mid
    :ok (outcome "你借着刀势一口气压住了他。" (list (effect 'clock+ initiative 2)))
    :partial (outcome "你逼得他后退了一步。" (list (effect 'clock+ initiative 1)))
    :fail (outcome "他还是硬顶了上来。" (list (effect 'add health -1)))
  )
  ))

(define finisher
  (action
    :title "终结一击"
    :desc "你抓住空门，一击把他放倒。"
    :check (check
    :suits (list 意志)
    :risk low
    :ok (outcome "你干净利落地结束了这场架。" (list (effect 'clock- enemy_hp 2)))
    :partial (outcome "你一击放倒了他。" (list (effect 'clock- enemy_hp 2)))
    :fail (outcome "没打实，但已经足够。" (list (effect 'clock- enemy_hp 1)))
  )
  ))

(content
  :meta (meta :key '教训小混混 :title "教训小混混" :desc "拿人钱财，帮人把这件事办干干净净。")
  :on-success (list (effect 'add money 80))
  :state (state
    (initiative (clock :title "主动权" :initial 0 :max 4))
    (knife (clock :title "夺刀" :initial 0 :max 2))
    (enemy_hp (clock :title "敌人血量" :initial 4 :max 4))
    (opening (clock :title "破绽" :initial 0 :max 2)))
  :reacts (reacts
    (react :when (<= (clock-value enemy_hp) 0) :then (list (effect 'end-encounter 'success))))
  :root
  (cond ((< (clock-value initiative) (clock-max initiative)) (if (< (clock-value knife) (clock-max knife)) (scene
    :title "徒手受压"
    :desc "打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。"
    :show-clocks (list initiative (when (> (clock-value knife) 0) knife))
    :actions (list counter blunt_punch rush_knife breathe)
  ) (scene
    :title "持刀逼退"
    :desc "刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。"
    :show-clocks (list initiative knife)
    :actions (list counter knife_press breathe)
  ))) ((< (clock-value opening) (clock-max opening)) (scene
    :title "对峙"
    :desc "对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。"
    :show-clocks (list enemy_hp opening)
    :actions (list heavy_punch feint knee_kick breathe)
  )) (else (scene
    :title "空门大开"
    :desc "他的防守空档已经完全露出来了。狠狠干净地结束这场架。"
    :show-clocks (list enemy_hp opening)
    :actions (list finisher knee_kick breathe)
  ))))
