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

(define lose-opening
  (lambda (effects)
    (append effects (list (effect-reset-clock opening)))))

(define disarm-fail
  (lambda ()
    (list
      (effect 'set hostility 12)
      (effect-reset-clock distance)
      (effect-reset-clock opening)
      (effect-reset-clock disarm))))

(define-scene standoff
  (scene
    :title "无门牌公寓 · 枪对峙"
    :desc
      (cond
        ((clock-filled? opening) "她的视线从你身上移开了一瞬。这个破绽不会等你。")
        ((>= (clock-value distance) 3) "你已经足够近。枪口仍然危险，但主动权第一次有可能从她手里滑出来。")
        ((<= (clock-value hostility) 3) "她的敌意降了下来。现在你可以开始处理距离，而不是只处理枪声。")
        ((>= (clock-value hostility) 9) "她的手指压得很深。你还不知道枪声会在哪句话后面响。")
        (else "门开着。屋里没有灯，只有窗外招牌的红光。薇拉坐在阴影里，枪口稳稳对着你。"))
    :show-clocks (list hostility distance opening disarm)
    :actions (list
      (make-standoff-action
        "举起双手"
        "你把自己变得没有攻击性。这样能压住敌意，但也等于放弃身体上的主动。"
        意志
        'low
        (lose-opening (list (effect 'clock- hostility 2) (effect 'clock- distance 1)))
        (lose-opening (list (effect 'clock- hostility 1) (effect 'clock- distance 1)))
        (lose-opening (list (effect 'clock+ hostility 1)))
        "你把手举到她能看清的位置。她没有放下枪，但呼吸慢了一点。"
        "她盯着你的手，枪口仍然稳着。"
        "你停得慢了半拍，她把那半拍理解成准备扑过去。")
      (make-standoff-action
        "用语言安抚她"
        "你不急着解释案子，只把语速放低，让她跟着你的节奏呼吸。"
        意志
        'low
        (lose-opening (list (effect 'clock- hostility 2) (when (>= (clock-value distance) 2) (effect 'clock- distance 1))))
        (lose-opening (list (effect 'clock- hostility 1) (when (>= (clock-value distance) 2) (effect 'clock- distance 1))))
        (lose-opening (list (effect 'clock+ hostility 2)))
        "她听进去了。枪口没有偏开，但她的视线短暂地离开了你的手。"
        "她听进去了半句，手指仍然扣着扳机。"
        "她把你的安抚听成了哄骗，枪口又稳了一点。")
      (when (<= (clock-value hostility) 3)
        (make-standoff-action
          "靠近"
          "你把移动藏在呼吸和桌角之间。走近一步，就少一分被枪口统治的距离。"
          感知
          'mid
          (lose-opening (list (effect 'clock+ distance 2)))
          (lose-opening (list (effect 'clock+ distance 1) (effect 'clock+ hostility 1)))
          (lose-opening (list (effect 'clock+ hostility 3) (effect-reset-clock distance)))
          "你挪近了一步，她还没有意识到这一步的价值。"
          "你的位置好了些，但她也重新紧张起来。"
          "她看穿了你的意图，枪口重新把你钉回原地。"))
      (when (>= (clock-value distance) 2)
        (make-standoff-action
          "压制手腕"
          "你不夺枪，只压住她持枪手的角度，逼出真正的破绽。"
          意志
          'high
          (list (effect 'clock+ opening 1) (effect 'clock+ distance 1))
          (lose-opening (list (effect 'clock+ hostility 2) (effect 'add health -1)))
          (disarm-fail)
          "你压住她的手腕，枪口偏开了一瞬。现在可以夺枪。"
          "你碰到了她的手腕，枪口擦着你偏开，疼痛让你差点松手。"
          "她猛地挣开，枪声贴着你的身体炸开。"))
      (when (clock-filled? opening)
        (make-standoff-action
          "夺枪"
          "她的视线移开了一瞬。现在动手，至少不是把命全压在蛮力上。"
          意志
          'mid
          (lose-opening (list (effect 'clock+ disarm 1)))
          (lose-opening (list (effect 'clock+ hostility 1) (effect 'clock- distance 1)))
          (lose-opening (list (effect 'add health -1) (effect-reset-clock distance)))
          "你压住她的手腕，枪口偏开。主动权终于不全在她手里。"
          "你碰到了枪，却没能完全夺下。她惊恐地把距离拉开。"
          "她猛地挣开，枪口擦着你的身体炸响。"))
      (when (>= (clock-value distance) 3)
        (make-standoff-action
          "强行夺枪"
          "没有破绽，只靠距离和速度硬抢。最快，也最容易让枪声响起来。"
          意志
          'high
          (lose-opening (list (effect 'clock+ disarm 1)))
          (lose-opening (list (effect 'add health -1) (effect 'clock+ hostility 2) (effect 'clock- distance 1)))
          (disarm-fail)
          "你压住她的手腕，枪口偏开。主动权终于不全在她手里。"
          "你碰到了枪，却没能完全夺下。疼痛和敌意一起顶了上来。"
          "她预判了你。枪声几乎贴着你的肋侧炸开。")))))

(content
  :meta (meta :key '公寓枪对峙2 :title "公寓枪对峙2" :desc "第二章尾声测试版：用反应骰模拟薇拉在休整时的变化。")
  :on-success (list
    (effect 'set 'chapter_2_done true)
    (effect 'set 'main_resolved true)
    (effect 'start-quick-dialogue "# 第二章尾声\n\n# speaker: 薇拉\n枪口终于偏开。她没有哭，只是像终于允许自己喘气。\n\n# speaker: 科尔\n弗雷德里克不是在找妻子。他是在找她带走的证据。"))
  :on-fail (list
    (effect 'set 'chapter_2_done true)
    (effect 'add 'health -2)
    (effect 'add 'police_relation -1)
    (effect 'start-quick-dialogue "# 走火\n\n# speaker: 科尔\n枪声在小房间里炸开。我没有死，但真相从门缝里逃了出去。"))
  :reaction-die
    (reaction-die
      (cond
        ((>= (clock-value hostility) 11)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "空")
            (face 5 "走火" (effect 'add health -1) (effect 'clock- hostility 2) (effect-reset-clock distance) (effect-reset-clock opening))
            (face 6 "走火" (effect 'add health -1) (effect 'clock- hostility 2) (effect-reset-clock distance) (effect-reset-clock opening))))
        ((>= (clock-value hostility) 9)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "空")
            (face 5 "空")
            (face 6 "走火" (effect 'add health -1) (effect 'clock- hostility 2) (effect-reset-clock distance) (effect-reset-clock opening))))
        (else
          nil)))
  :reacts (reacts
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
        (effect-reset-clock opening)
        (effect-reset-clock disarm)
        (effect 'start-quick-dialogue "# 枪声\n\n# speaker: 科尔\n枪声在小房间里炸开。子弹擦过肋侧，疼痛让我短暂失去声音。\n\n# speaker: 薇拉\n她也被那一枪吓住了。枪还在她手里，敌意却像被后坐力打回了原点。"))))
  :state (state
    (use-world-basics)
    (hostility (clock :title "敌意" :desc "降到 3 后可以稳定靠近；满格时薇拉会开枪。" :initial 5 :max 12))
    (distance (clock :title "距离" :desc "足够近时可以压制手腕或直接夺枪。" :initial 0 :max 4))
    (opening (clock :title "破绽" :desc "一次性的窗口。做出选择后就会消失。" :initial 0 :max 1))
    (disarm (clock :title "缴械" :desc "填满后科尔夺回主动权。" :initial 0 :max 1)))
  :root (standoff))
