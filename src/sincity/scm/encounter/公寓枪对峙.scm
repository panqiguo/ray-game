(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")

(define-scene standoff
  (scene
    :title "无门牌公寓 · 枪对峙"
    :desc "门开着。屋里没有灯，只有窗外招牌的红光。女人坐在阴影里，枪口稳稳对着你。"
    :show-clocks (list trust danger truth)
    :actions (list
      (action
        :title "先把手举起来"
        :desc "活着的人才有资格问第二个问题。"
        :effects (list (effect 'clock+ trust 1)))
      (action
        :title "说出弗雷德里克的矛盾"
        :desc "他太想让自己像个受害者。你把这点轻轻放到桌上。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (outcome (list (effect 'clock+ truth 2) (effect 'clock+ trust 1)) "枪口没有放下，但她开始听你说话。")
          :partial (outcome (list (effect 'clock+ truth 1) (effect 'clock+ danger 1)) "她听见了，也更紧张了。")
          :fail (outcome (list (effect 'clock+ danger 1)) "她以为你在替弗雷德里克拖时间。")))
      (action
        :title "拿出鉴定结果"
        :desc "底片上的名字证明这件事不是婚姻纠纷那么简单。"
        :conditions (list (field-truthy 'auth_done "需要先取得鉴定结果"))
        :check (check
          :suits (list 逻辑)
          :risk 'low
          :ok (outcome (list (effect 'clock+ truth 2) (effect 'clock+ trust 1)) "她认出了底片，也认出了自己没法继续躲。")
          :partial (outcome (list (effect 'clock+ truth 1)) "她承认底片是真的，但仍然不肯完全相信你。")
          :fail (outcome (list (effect 'clock+ danger 1)) "你递得太快，她的手指也收得更紧。")))
      (action
        :title "观察她的持枪手"
        :desc "不是为了夺枪，是为了知道她到底想不想开枪。"
        :check (check
          :suits (list 感知)
          :risk 'mid
          :ok (outcome (list (effect 'clock+ trust 1) (effect 'clock- danger 1)) "她的手在抖。不是杀人的抖，是撑太久的抖。")
          :partial (outcome (list (effect 'clock+ trust 1) (effect 'clock+ danger 1)) "你看见一点破绽，也看见她快到极限。")
          :fail (outcome (list (effect 'clock+ danger 1)) "你的视线让她误会成动作。")))
      (when (clock-at-least-half? trust)
        (action
          :title "让她讲完"
          :desc "你不急着追问，只给她一个不会立刻被打断的空间。"
          :check (check
            :suits (list 意志 感知)
            :risk 'low
            :ok (outcome (list (effect 'clock+ truth 2)) "她终于说出了弗雷德里克真正藏起来的东西。")
            :partial (outcome (list (effect 'clock+ truth 1)) "她讲了一半，另一半还卡在喉咙里。")
            :fail (outcome (list (effect 'clock+ danger 1)) "沉默拉得太久，门外传来脚步声。")))))))

(content
  :meta (meta :key '公寓枪对峙 :title "公寓枪对峙" :desc "第二章尾声：在无门牌公寓里，让薇拉放下枪或让真相失控。")
  :on-success (list
    (effect 'set 'chapter_2_done true)
    (effect 'set 'main_resolved true)
    (effect 'start-quick-dialogue "# 第二章尾声\n\n# speaker: 薇拉\n枪口终于垂下去。她没有哭，只是像终于允许自己喘气。\n\n# speaker: 科尔\n弗雷德里克不是在找妻子。他是在找她带走的证据。"))
  :on-fail (list
    (effect 'set 'chapter_2_done true)
    (effect 'add 'health -2)
    (effect 'add 'police_relation -1)
    (effect 'start-quick-dialogue "# 走火\n\n# speaker: 科尔\n枪声在小房间里炸开。我没有死，但真相从门缝里逃了出去。"))
  :reacts (reacts
    (react :when (clock-filled? truth) :then (list (effect 'end-encounter 'success)))
    (react :when (>= (clock-value danger) 4) :then (list (effect 'end-encounter 'fail))))
  :state (state
    (trust (clock :title "信任" :initial 0 :max 3))
    (danger (clock :title "危险" :initial 1 :max 4))
    (truth (clock :title "真相" :initial 0 :max 4)))
  :root (standoff))
