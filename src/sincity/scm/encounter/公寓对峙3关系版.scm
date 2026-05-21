(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define explain-action
  (lambda ()
    (cond
      ((>= (clock-value calm) 6)
        (action
          :title "解释"
          :desc "你把弗雷德里克、旅馆和她正在逃的东西连成一条线。她已经能听完整句话。"
          :check (check
            :suits (list 逻辑)
            :risk 'low
            :ok (outcome (list (effect 'clock+ calm 2)) "她的眼神终于从枪口后面抬起来。")
            :partial (outcome (list (effect 'clock+ calm 1)) "她没有完全相信，但至少没有打断你。")
            :fail (outcome (list (effect 'clock+ pressure 1)) "你说错了一个细节，她立刻重新绷紧。"))))
      ((>= (clock-value calm) 3)
        (action
          :title "解释"
          :desc "你开始讲证据，而不是讲道理。她仍然警惕，但已经给了你几句话的空间。"
          :check (check
            :suits (list 逻辑)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ calm 2)) "一个名字让她动摇了一下。")
            :partial (outcome (list (effect 'clock+ calm 1) (effect 'clock+ pressure 1)) "她听进去半句，枪口却没有松。")
            :fail (outcome (list (effect 'clock+ pressure 2)) "她把你的推理听成了审问。"))))
      (else
        (action
          :title "解释"
          :desc "你试着先把事情讲清楚。问题是她现在只相信枪。"
          :check (check
            :suits (list 逻辑)
            :risk 'high
            :ok (outcome (list (effect 'clock+ calm 1)) "她抓住了你话里那个不该外人知道的细节。")
            :partial (outcome (list (effect 'clock+ pressure 1)) "她听见了，但没有相信。")
            :fail (outcome (list (effect 'clock+ pressure 2)) "你的解释太像逼供，她的手指压得更深。")))))))

(define soothe-action
  (lambda ()
    (cond
      ((>= (clock-value calm) 6)
        (action
          :title "安抚"
          :desc "你不再追问，只让她知道现在还可以不扣扳机。"
          :check (check
            :suits (list 意志)
            :risk 'low
            :ok (outcome (list (effect 'clock+ calm 1)) "她的呼吸慢下来，枪口低了一点。")
            :partial (outcome (list (effect 'clock+ calm 1)) "她还握着枪，但眼神不再那么硬。")
            :fail (outcome (list (effect 'clock+ pressure 1)) "她听出了你声音里的急。"))))
      ((>= (clock-value calm) 3)
        (action
          :title "安抚"
          :desc "你放低声音，先处理她的恐惧，而不是你自己的答案。"
          :check (check
            :suits (list 意志)
            :risk 'low
            :ok (outcome (list (effect 'clock+ calm 1)) "她的手仍然抖，但已经不是完全冲着你。")
            :partial (outcome (list) "她沉默着，至少这份沉默没有变得更坏。")
            :fail (outcome (list (effect 'clock+ pressure 1)) "她把你的温和理解成靠近前的伪装。"))))
      (else
        (action
          :title "安抚"
          :desc "你先让她听见一个不带命令的声音。"
          :check (check
            :suits (list 意志)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ calm 1)) "她没有回应，但枪口慢了半拍。")
            :partial (outcome (list) "她盯着你，像在确认你下一秒会不会扑上来。")
            :fail (outcome (list (effect 'clock+ pressure 1)) "她不吃这套，房间里的压力更满了。")))))))

(define approach-action
  (lambda ()
    (cond
      ((>= (clock-value calm) 6)
        (action
          :title "靠近一点"
          :desc "你把一步藏进谈话停顿里。她看见了，但没有立刻把它当成攻击。"
          :check (check
            :suits (list 感知)
            :risk 'low
            :ok (outcome (list (effect 'clock+ approach 2) (effect 'clock+ pressure 1)) "你离枪近了很多，代价只是她重新看了你一眼。")
            :partial (outcome (list (effect 'clock+ approach 1) (effect 'clock+ pressure 1)) "你挪近了半步，她也重新握紧了枪。")
            :fail (outcome (list (effect 'clock+ pressure 2)) "她察觉到你的重心，枪口立刻抬回胸口。"))))
      ((>= (clock-value calm) 3)
        (action
          :title "靠近一点"
          :desc "她愿意听，但还不愿意让你靠近。每一步都会让压力上升。"
          :check (check
            :suits (list 感知)
            :risk 'mid
            :ok (outcome (list (effect 'clock+ approach 2) (effect 'clock+ pressure 1)) "你绕过桌角，枪口跟着你，但慢了。")
            :partial (outcome (list (effect 'clock+ approach 1) (effect 'clock+ pressure 2)) "距离缩短了，危险也缩短了。")
            :fail (outcome (list (effect 'clock+ pressure 2)) "她看穿你的脚步，声音一下变冷。"))))
      (else
        (action
          :title "靠近一点"
          :desc "她还没有把你当成能谈的人。现在移动，几乎就是拿身体压枪口。"
          :check (check
            :suits (list 感知)
            :risk 'high
            :ok (outcome (list (effect 'clock+ approach 1) (effect 'clock+ pressure 2)) "你抢到了一点距离，但她已经被逼到边缘。")
            :partial (outcome (list (effect 'clock+ pressure 2)) "你刚动，她就把枪口顶回来了。")
            :fail (outcome (list (effect 'clock+ pressure 3)) "她差点扣下扳机。你知道下一次可能不会只是差点。")))))))

(define-scene gun-scene
  (scene
    :title "枪"
    :desc
      (cond
        ((not armed) "枪已经离开她的手。这个房间里终于有了人声。")
        (disarm_failed "她死死握住枪，手背上青筋绷起。刚才那一下之后，她不会再让你碰到第二次。")
        ((clock-filled? approach) "你已经足够近。现在不是继续等机会，而是决定要不要把局面抢过来。")
        (else "枪口稳定地指着你。它不是一个谜题，是所有谈话都绕不过去的事实。"))
    :actions (list
      (when (and armed (not disarm_failed) (clock-filled? approach))
        (cond
          ((>= (clock-value calm) 6)
            (action
              :title "夺下枪支"
              :desc "她已经有一瞬间不想开枪。你要把这一瞬变成结果。"
              :check (check
                :suits (list 意志)
                :risk 'mid
                :ok (outcome (list (effect 'set armed false) (effect 'end-encounter 'success)) "你扣住她的手腕，把枪压向地面。她终于松开了。")
                :partial (outcome (list (effect 'set disarm_failed true) (effect 'add health -1) (effect 'clock+ pressure 2)) "你碰到了枪，但没能夺下。枪口擦过你，疼痛逼你退开。")
                :fail (outcome (list (effect 'set disarm_failed true) (effect 'clock+ pressure 3)) "她猛地把枪收回去，像把最后一点信任也一起收走。"))))
          (else
            (action
              :title "夺下枪支"
              :desc "距离够了，但她还没有冷静。你可以赌速度，也可能把这条路彻底赌没。"
              :check (check
                :suits (list 意志)
                :risk 'high
                :ok (outcome (list (effect 'set armed false) (effect 'end-encounter 'success)) "你压住枪身，膝盖撞开她的重心，枪从她手里掉下去。")
                :partial (outcome (list (effect 'set disarm_failed true) (effect 'add health -1) (effect 'clock+ pressure 3)) "你抓到枪，又被她抢回去。子弹没有打中要害，但这条路关上了。")
                :fail (outcome (list (effect 'set disarm_failed true) (effect 'clock+ pressure 4)) "她预判了你的动作，枪口重新抵住你。你没有第二次机会。")))))))))

(define-scene emotion-scene
  (scene
    :title "情绪"
    :desc
      (cond
        ((>= (clock-value calm) 6) "她还没有相信你，但已经开始相信自己可以不开枪。")
        ((>= (clock-value calm) 3) "她在听。她仍然把枪握得很紧，但每句话都不再只是在撞墙。")
        (else "她被恐惧、羞耻和愤怒推着。你要先让她从枪后面露出一点人。"))
    :show-clocks (list calm)
    :actions (list
      (explain-action)
      (soothe-action))))

(define-scene distance-scene
  (scene
    :title "距离"
    :desc
      (if (clock-filled? approach)
        "你已经在可以触到枪的范围里。继续靠近只会让她看清你的意图。"
        "桌角、椅背、地上的玻璃碎片，把几步距离拆成了好几个决定。")
    :show-clocks (list approach)
    :actions (list
      (when (not (clock-filled? approach))
        (approach-action)))))

(define-scene standoff
  (scene
    :title "无门牌公寓 · 关系版"
    :desc
      (cond
        ((not armed) "枪落在地上，声音很轻，但足够让整个房间变成另一种地方。")
        ((>= (clock-value pressure) 6) "她已经被逼得太紧。休整时，枪有可能先替她作出反应。")
        ((>= (clock-value pressure) 3) "压力开始积起来。它还不是枪声，但已经让枪声变得可能。")
        (else "薇拉站在暗处。你面对的不是一个房间，而是一段随时会断掉的关系。"))
    :show-clocks (list pressure calm approach)
    :children (list
      (gun-scene)
      (emotion-scene)
      (distance-scene))))

(content
  :meta (meta :key '公寓对峙3关系版 :title "公寓对峙3关系版" :desc "第二章尾声测试版：把枪口对峙建模为枪、情绪、距离三条关系轴。")
  :on-success (list
    (effect 'set 'chapter_2_done true)
    (effect 'set 'main_resolved true)
    (effect 'set 'standoff_resolved true)
    (effect 'start-quick-dialogue "# 第二章尾声\n\n# speaker: 薇拉\n枪终于离开了她的手。她看着地面，像第一次意识到自己还活着。\n\n# speaker: 科尔\n现在我们可以谈谈弗雷德里克真正想要的东西了。"))
  :on-fail (list
    (effect 'set 'chapter_2_done true)
    (effect 'set 'standoff_failed true)
    (effect 'add 'health -1)
    (effect 'start-quick-dialogue "# 枪声\n\n# speaker: 科尔\n枪声把房间切成两半。我还活着，但薇拉已经不在这里了。\n\n# speaker: 科尔\n有些真相不是找不到，是你来得太晚。"))
  :reaction-die
    (reaction-die
      (cond
        ((not armed) nil)
        ((>= (clock-value pressure) 6)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "空")
            (face 5 "走火" (effect 'add health -1) (effect 'clock+ pressure 1))
            (face 6 "走火" (effect 'add health -1) (effect 'clock+ pressure 1))))
        ((>= (clock-value pressure) 3)
          (reaction-table
            (face 1 "空")
            (face 2 "空")
            (face 3 "空")
            (face 4 "空")
            (face 5 "空")
            (face 6 "走火" (effect 'add health -1) (effect 'clock+ pressure 1))))
        (else nil)))
  :reacts (reacts
    (react
      :when (clock-filled? calm)
      :then (list
        (effect 'set armed false)
        (effect 'end-encounter 'success)))
    (react
      :when (clock-filled? pressure)
      :then (list
        (effect 'add health -2)
        (effect 'end-encounter 'fail))))
  :state (state
    (use-world-basics)
    (armed true)
    (disarm_failed false)
    (pressure (clock :title "压力" :desc "只会上升的危险条。3/6 后休整可能走火，填满则场景失败。" :initial 0 :max 9))
    (calm (clock :title "冷静" :desc "她重新获得判断力的程度。3/6 后行动风险降低，填满则语言路径胜利。" :initial 0 :max 9))
    (approach (clock :title "距离" :desc "你接近枪口的程度。填满后可以尝试夺下枪支。" :initial 0 :max 6)))
  :root (standoff))
