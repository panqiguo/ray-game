(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define make-standoff-action
  (lambda (title desc suit risk ok-effects partial-effects fail-effects ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk risk
        :ok (outcome ok-effects ok-text)
        :partial (outcome partial-effects partial-text)
        :fail (outcome fail-effects fail-text)))))

(define disarm-fail
  (lambda ()
    (list
      (effect 'set hostility 12)
      (effect 'clock- distance 3)
      (effect-reset-clock disarm))))

(define (standoff)
  (scene
    :title "无门牌公寓 · 枪对峙"
    :desc
      (cond
        ((>= (clock-value distance) 3) "你已经足够近。枪口仍然危险，但主动权第一次有可能从她手里滑出来。")
        ((<= (clock-value hostility) 3) "她的敌意降了下来。现在你可以开始处理距离，而不是只处理枪声。")
        (else "门开着。屋里没有灯，只有窗外招牌的红光。薇拉坐在阴影里，枪口稳稳对着你。"))
    :show-clocks (list hostility distance disarm)
    :actions (list
      (make-standoff-action
         "举起双手，先停住"
         "先让她知道你现在不会扑过去。活着的人才有资格问第二个问题。"
         魅力
         'low
        (list (effect 'clock- hostility 2))
        (list (effect 'clock- hostility 1))
        (list )
        "你把手举到她能看清的位置。她没有放下枪，但没有立刻开枪。"
        "她盯着你的手，枪口仍然稳着。"
        "你停得慢了半拍，她把那半拍理解成准备扑过去。")
      (make-standoff-action
         "安抚她的呼吸"
         "不急着解释案子，只让她跟着你的语速慢下来。"
         魅力
         'low
        (list (effect 'clock- hostility 2))
        (list (effect 'clock- hostility 1))
        (list )
        "她没有放下枪，但呼吸慢了一点。"
        "她听进去了半句，手指仍然扣着扳机。"
        "她把你的安抚听成了哄骗。")
      (make-standoff-action
         "承认自己受雇于德雷福雷"
         "这句话很危险，但半真半假的辩解只会让枪口更稳。"
         知识
         'mid
        (list (effect 'clock- hostility 2))
        (list (effect 'clock- hostility 1))
        (list (effect 'clock+ hostility 1))
        "她听见了那个名字，也听见你没有替他辩解。"
        "她仍然怀疑你，但这份诚实给你换来一点空间。"
        "她以为你终于承认自己是来抓她的人。")
      (when (<= (clock-value hostility) 3)
        (make-standoff-action
           "靠近桌边"
           "你把移动伪装成寻找支撑点。桌角、椅背、她的手腕，距离开始有意义。"
           敏锐
           'mid
          (list (effect 'clock+ distance 2))
          (list (effect 'clock+ distance 1) (effect 'clock+ hostility 1))
          (list (effect 'clock+ hostility 2) (effect 'clock- distance 3))
          "你挪近了一步，她还没有意识到这一步的价值。"
          "你的位置好了些，但她也重新紧张起来。"
          "她看穿了你的意图，枪口重新把你钉回原地。"))
      (when (<= (clock-value hostility) 3)
        (make-standoff-action
           "借椅背挡住半身"
           "你没有冲过去，只是让一件家具变成她和你之间的犹豫。"
           知识
           'mid
          (list (effect 'clock+ distance 2) (effect 'clock- hostility 1))
          (list (effect 'clock+ distance 1))
          (list (effect 'clock+ hostility 2) (effect 'clock- distance 3))
          "椅背遮住了你的重心，她不得不重新判断你的距离。"
          "你站到了更好的角度，但她看见了你的计算。"
          "椅脚擦过地面，她的枪口立刻追了上来。"))
      (when (>= (clock-value distance) 3)
        (make-standoff-action
           "关键时刻夺枪"
           "只能在她分神的一瞬间动手。失败的话，距离会被重新拉开。"
           暴力
           'high
          (list (effect 'clock+ disarm 1))
          (append (list (effect 'clock+ hostility 2)) (disarm-fail))
          (disarm-fail)
          "你压住她的手腕，枪口偏开。主动权终于不全在她手里。"
          "你碰到了枪，却没能完全夺下。她惊恐地把距离重新拉开。"
          "她预判了你。枪声几乎贴着你的肋侧炸开。")))))

(content
  :meta (meta :key '公寓枪对峙 :title "公寓枪对峙" :desc "第二章尾声：在无门牌公寓里，从薇拉的枪口下夺回主动权。")
  :on-success (list
    (effect 'set 'chapter_2_done true)
    (effect 'set 'main_resolved true)
    (effect 'start-quick-dialogue "# 第二章尾声\n\n# speaker: 薇拉\n枪口终于偏开。她没有哭，只是像终于允许自己喘气。\n\n# speaker: 科尔\n弗雷德里克不是在找妻子。他是在找她带走的证据。"))
  :on-fail (list
    (effect 'set 'chapter_2_done true)
    (effect 'add 'health -2)
    (effect 'add 'police_relation -1)
    (effect 'start-quick-dialogue "# 走火\n\n# speaker: 科尔\n枪声在小房间里炸开。我没有死，但真相从门缝里逃了出去。"))
  :reacts (list
    (react
      :when (clock-filled? disarm)
      :then (list
        (effect 'end-encounter 'success)))
    (react
      :when (clock-empty? hostility)
      :then (list
        (effect 'end-encounter 'success)))
    (react
      :when (clock-filled? hostility)
      :then (list
        (effect 'add health -2)
        (effect 'set hostility 5)
        (effect-reset-clock distance)
        (effect-reset-clock disarm)
        (effect 'start-quick-dialogue "# 枪声\n\n# speaker: 科尔\n枪声在小房间里炸开。子弹擦过肋侧，疼痛让我短暂失去声音。\n\n# speaker: 薇拉\n她也被那一枪吓住了。枪还在她手里，敌意却像被后坐力打回了原点。"))))
  :vars (append
    world-basics-vars
    (list
    (var 'hostility (clock :title "敌意" :desc "降到 3 后可以尝试拉近距离；满格时薇拉会开枪。" :initial 5 :max 12))
    (var 'distance (clock :title "距离" :desc "足够近时才能夺枪。" :initial 0 :max 4))
    (var 'disarm (clock :title "缴械" :desc "填满后科尔夺回主动权。" :initial 0 :max 1)))
    )
  :root (standoff))
