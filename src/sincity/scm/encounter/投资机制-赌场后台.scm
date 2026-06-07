(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define (bartender-scene)
  (location
    :title "酒保"
    :desc "酒保知道后台谁在抽水，也知道什么话不能在牌桌边说。"
    :show-clocks (list bartender)
    :actions (if (clock-filled? bartender)
      (list)
      (list
        (action
          :title "套出后台名字"
          :desc "你装成替别人传话的人，慢慢摸清今晚管局的人。"
          :check (check
            :suit 魅力
            :risk 'low
            :ok (outcome (list (effect 'clock+ bartender 2)) "酒保把一个名字压在杯垫下面推给你。")
            :partial (outcome (list (effect 'clock+ bartender 1)) "他没明说，但眼神已经指向了后台门。")
            :fail (outcome (list (effect 'clock+ presence 1)) "你问得太直，目标人物抬头看了一眼。")))))))

(define (backstage-scene)
  (location
    :title "后台"
    :desc "有人把输掉的公道藏在账本背面，也有人把筹码藏在袖口里。"
    :show-clocks (list backstage)
    :actions (if (clock-filled? backstage)
      (list)
      (list
        (action
          :title "翻后台账袋"
          :desc "你不是偷赌场的钱，你是在把他们偷来的那一枚拿回来。至少你这样告诉自己。"
          :check (check
            :suit 知识
            :risk 'mid
            :ok (outcome (list (effect 'clock+ backstage 2)) "你摸到了被扣下的代币。")
            :partial (outcome (list (effect 'clock+ backstage 1) (effect 'clock+ presence 1)) "账袋被你翻开了一半，也留下了一点痕迹。")
            :fail (outcome (list (effect 'clock+ presence 2)) "后台有人咳了一声，你只能先把手收回来。")))))))

(define (rule-scene)
  (location
    :title "赌局规则"
    :desc "这张桌子不是公平的，但不公平也有规则。看懂规则，才能反过来用它。"
    :show-clocks (list rule)
    :actions (if (or (not (clock-filled? bartender)) (clock-filled? rule))
      (list)
      (list
        (action
          :title "读懂庄家的节奏"
          :desc "你盯的不是牌，是庄家什么时候不看牌。"
          :check (check
            :suit 敏锐
            :risk 'mid
            :ok (outcome (list (effect 'clock+ rule 2)) "你看懂了那套暗号。")
            :partial (outcome (list (effect 'clock+ rule 1) (effect 'clock+ presence 1)) "你看懂一半，也被人看见你在看。")
            :fail (outcome (list (effect 'clock+ presence 1)) "庄家的手势换了，你刚建立的判断又散掉。")))))))

(define (table-scene)
  (location
    :title "赌桌"
    :desc "目标人物还在场。你有多少准备，就能把多少运气从桌上抢回来。"
    :show-clocks (list tokens presence)
    :actions (list
      (action
        :title "普通赌博"
        :desc "纯靠骰运，庄家占优。赢也能赢，只是你要先把命交给桌子。"
        :check (check
          :suit 魅力
          :risk 'high
          :ok (outcome (list (effect 'clock+ tokens 2)) "你押中了，代币滚到你面前。")
          :partial (outcome (list (effect 'clock+ tokens 1) (effect 'clock+ presence 1)) "你小赢一把，但时间也被吃掉了。")
          :fail (outcome (list (effect 'clock- tokens 1) (effect 'clock+ presence 1)) "庄家把你的代币收走，笑得很标准。")))
      (when (clock-filled? rule)
        (action
          :title "利用规则赌博"
          :desc "你把行动骰当成下注前的预判工具，主动避开庄家的吃口。"
          :check (check
            :suit 知识
            :risk 'low
            :ok (outcome (list (effect 'clock+ tokens 2)) "你踩中了庄家换手前的一拍。")
            :partial (outcome (list (effect 'clock+ tokens 1)) "你稳稳吃下一点，不贪。")
            :fail (outcome (list (effect 'clock- tokens 1)) "你判断错了暗号，但至少知道错在哪里。")))))))

(define (casino-root)
  (location
    :title "赌场后台 · 替人讨回公道"
    :desc "有人在这张桌上被做掉了最后一笔救命钱。你要把代币赢回 8 枚，在目标人物离场前。"
    :show-clocks (list tokens presence)
    :children (list
      (bartender-scene)
      (backstage-scene)
      (when (clock-filled? bartender) (rule-scene))
      (table-scene))))

(content
  :meta (meta :key '投资机制-赌场后台 :title "投资机制-赌场后台" :desc "测试准备时间与赌博期望值的选择。")
  :on-success (list (effect 'set 'test_casino_done true) (effect 'add money 20))
  :on-fail (list (effect 'set 'test_casino_failed true) (effect 'add money -8))
  :on-cycle-start (list (effect 'clock+ presence 1))
  :reacts (list
    (react :when (and (clock-filled? backstage) (not backstage_claimed)) :then (list (effect 'clock+ tokens 1) (effect 'set backstage_claimed true)))
    (react :when (clock-filled? tokens) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-empty? tokens) :then (list (effect 'end-encounter 'fail)))
    (react :when (clock-filled? presence) :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-basics-vars
    (list
    (var 'tokens (clock :title "代币" :desc "初始 4，赢到 8 成功，归零失败。" :initial 4 :max 8))
    (var 'presence (clock :title "目标在场" :desc "目标人物离场前的时间。" :initial 0 :max 3))
    (var 'bartender (clock :title "酒保" :initial 0 :max 3))
    (var 'backstage (clock :title "后台" :initial 0 :max 3))
    (var 'rule (clock :title "赌局规则" :initial 0 :max 3))
    (var 'backstage_claimed false))
    )
  :root (casino-root))
