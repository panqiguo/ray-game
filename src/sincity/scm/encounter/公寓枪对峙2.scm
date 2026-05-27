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
      (effect 'set hostility 12))))

(define (standoff)
  (scene
    :title "无门牌公寓 · 枪对峙"
    :desc
      (cond
        ((>= (clock-value approach) 6) "你已经逼到足够近的位置。现在问题不是能不能碰到枪，而是枪声会不会先响。")
        ((>= (clock-value approach) 3) "你正在一点点缩短距离。每一步都让她更紧张，也让枪更近。")
        ((>= (clock-value hostility) 9) "她的手指压得很深。你还不知道枪声会在哪句话后面响。")
        (else "门开着。屋里没有灯，只有窗外招牌的红光。薇拉坐在阴影里，枪口稳稳对着你。"))
    :show-clocks (list hostility approach disarm)
    :actions (list
      (make-standoff-action
        "举起双手"
        "你把自己变得没有攻击性。它不会让压力下降，但能让你少付一点代价。"
        意志
        'low
        (list)
        (list (effect 'clock+ hostility 1))
        (list (effect 'clock+ hostility 2))
        "你把手举到她能看清的位置。枪口没有放下，但局势没有继续恶化。"
        "她盯着你的手，枪口仍然稳着，压力又往上顶了一点。"
        "你停得慢了半拍，她把那半拍理解成准备扑过去。")
      (make-standoff-action
        "用语言安抚她"
        "你不急着解释案子，只把语速放低，让她跟着你的节奏呼吸。"
        意志
        'low
        (list)
        (list (effect 'clock+ hostility 1))
        (list (effect 'clock+ hostility 2))
        "她听进去了。枪口没有偏开，但压力没有继续升高。"
        "她听进去了半句，手指仍然扣着扳机，压力慢慢积起来。"
        "她把你的安抚听成了哄骗，枪口又稳了一点。")
      (make-standoff-action
        "靠近"
        "你把移动藏在呼吸和桌角之间。每一步都更接近枪，也更接近枪声。"
        感知
        'mid
        (list (effect 'clock+ approach 2) (effect 'clock+ hostility 1))
        (list (effect 'clock+ approach 1) (effect 'clock+ hostility 2))
        (list (effect 'clock+ hostility 3))
        "你挪近了一步，她还没有意识到这一步的价值。"
        "你的位置好了些，但她也重新紧张起来。"
        "她看穿了你的意图，枪口重新把你钉在原地。")
      (when (>= (clock-value approach) 4)
        (make-standoff-action
          "压制手腕"
          "你不夺枪，只压住她持枪手的角度，把最后一点距离抢出来。"
          意志
          'high
          (list (effect 'clock+ approach 2) (effect 'clock+ hostility 2))
          (list (effect 'clock+ approach 1) (effect 'clock+ hostility 3) (effect 'add health -1))
          (disarm-fail)
          "你压住她的手腕，枪口偏开了一瞬。距离被你硬抢出来。"
          "你碰到了她的手腕，枪口擦着你偏开，疼痛让你差点松手。"
          "她猛地挣开，枪声贴着你的身体炸开。"))
      (when (>= (clock-value approach) 6)
        (make-standoff-action
          "强行夺枪"
          "你已经足够近，只能靠速度硬抢。越拖，枪声越可能先到。"
          意志
          'high
          (list (effect 'clock+ disarm 1))
          (list (effect 'add health -1) (effect 'clock+ hostility 3))
          (list (effect 'clock+ hostility 4))
          "你压住她的手腕，枪口偏开。主动权终于不全在她手里。"
          "你碰到了枪，却没能完全夺下。疼痛和敌意一起顶了上来。"
          "她预判了你，猛地把枪收回去。压力立刻顶到喉咙口。")))))

(content
  :meta (meta :key '公寓枪对峙2 :title "公寓枪对峙2" :desc "第二章尾声测试版：用反应骰模拟薇拉在休整时的变化。")
  :on-success (list
    (effect 'set 'chapter_2_done true)
    (effect 'set 'main_resolved true)
    (effect 'start-quick-dialogue "# 第二章尾声\n\n# speaker: 薇拉\n枪口终于偏开。她没有哭，只是像终于允许自己喘气。\n\n# speaker: 科尔\n弗雷德里克不是在找妻子。他是在找她带走的证据。"))
  :on-fail (list
    (effect 'set 'chapter_2_done true)
    (effect 'start-quick-dialogue "# 走火\n\n# speaker: 科尔\n枪声在小房间里炸开。我没有死，但真相从门缝里逃了出去。"))
  :reaction-die
    (reaction-die
      (cond
        ((>= (clock-value hostility) 11)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "走火" (effect 'add health -1) (effect 'set hostility 8))
            (face 5 "走火" (effect 'add health -1) (effect 'set hostility 8))
            (face 6 "走火" (effect 'add health -1) (effect 'set hostility 8))))
        ((>= (clock-value hostility) 9)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "空")
            (face 5 "走火" (effect 'add health -1) (effect 'set hostility 8))
            (face 6 "走火" (effect 'add health -1) (effect 'set hostility 8))))
        ((>= (clock-value hostility) 7)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "空")
            (face 5 "空")
            (face 6 "走火" (effect 'add health -1) (effect 'set hostility 8))))
        (else
          nil)))
  :reacts (list
    (react
      :when (clock-filled? disarm)
      :then (list
        (effect 'end-encounter 'success)))
    (react
      :when (clock-filled? hostility)
      :then (list
        (effect 'add health -2)
        (effect 'set hostility 8)
        (effect 'start-quick-dialogue "# 枪声\n\n# speaker: 科尔\n枪声在小房间里炸开。子弹擦过肋侧，疼痛让我短暂失去声音。\n\n# speaker: 薇拉\n她也被那一枪吓住了。枪还在她手里，敌意却像被后坐力打回了原点。"))))
  :vars (append
    world-basics-vars
    (list
    (var 'hostility (clock :title "敌意" :desc "只会上升的压力。高位时休整可能走火，满格时薇拉会开枪。" :initial 0 :max 12))
    (var 'approach (clock :title "靠近" :desc "填满代表你已经进入夺枪距离。" :initial 0 :max 8))
    (var 'disarm (clock :title "缴械" :desc "填满后科尔夺回主动权。" :initial 0 :max 1)))
    )
  :root (standoff))
