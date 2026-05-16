(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define trigger-watchman
  (lambda (amount)
    (list
      (effect 'clock+ alert amount)
      (effect 'set patrol_phase 'incoming)
      (effect-reset-clock patrol_incoming)
      (effect-reset-clock patrol_leaving))))

(define low-risk-search
  (lambda (title desc suit progress-clock ok-step ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'low
        :ok (outcome (list (effect 'clock+ progress-clock ok-step)) ok-text)
        :partial (outcome (list (effect 'clock+ progress-clock 1) (effect 'add energy -1)) partial-text)
        :fail (outcome (list (effect 'add energy -1)) fail-text)))))

(define mid-risk-search
  (lambda (title desc suit progress-clock ok-step ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'mid
        :ok (outcome (list (effect 'clock+ progress-clock ok-step)) ok-text)
        :partial (outcome (append (list (effect 'clock+ progress-clock 1)) (trigger-watchman 1)) partial-text)
        :fail (outcome (trigger-watchman 1) fail-text)))))

(define high-risk-search
  (lambda (title desc suit progress-clock ok-step ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list suit)
        :risk 'high
        :ok (outcome (list (effect 'clock+ progress-clock ok-step)) ok-text)
        :partial (outcome (append (list (effect 'clock+ progress-clock 1)) (trigger-watchman 1)) partial-text)
        :fail (outcome (trigger-watchman 1) fail-text)))))

(define hallway-actions
  (lambda ()
    (list
      (when (not target_room_known)
        (low-risk-search
          "观察走廊服务痕迹"
          "门外水壶、拖把印和烟灰，比房牌号码更诚实。"
          感知
          hallway_investigation
          1
          "你顺着送水车停留的位置，缩小了一圈范围。"
          "你还是摸到了一点门道，只是站得太久了。"
          "你什么也没看清，只好先换个角度。"))
      (when (not target_room_known)
        (mid-risk-search
          "偷听几间门缝"
          "有些房间装睡，有些房间真的有人。你得分清哪一扇门后面藏着你要找的东西。"
          逻辑
          hallway_investigation
          2
          "你听出了不该出现在普通住客房里的说话方式。"
          "你听到了半句有用的话，但也有人注意到走廊里多了个影子。"
          "你刚靠近门缝，楼梯口那边就有人动了一下。")))))

(define resource-entry-actions
  (lambda ()
    (list
      (action
        :title "等清洁工离开再进"
        :desc "这间房门没关严。你只需要等一个不会被撞见的空档。"
        :check (check
          :suits (list 感知)
          :risk 'low
          :ok (outcome (list (effect 'set resource_room_entered true)) "你从门缝里滑了进去。")
          :partial (outcome (list (effect 'set resource_room_entered true) (effect 'add energy -1)) "你进去了，只是多等了太久。")
          :fail (outcome (list (effect 'add energy -1)) "你刚要动，脚步声又回到了门口。"))))
      (action
        :title "撬开资源房门锁"
        :desc "旧锁比人可靠，但也比人更会出声。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (outcome (list (effect 'set resource_room_entered true)) "锁芯松开了。")
          :partial (outcome (append (list (effect 'set resource_room_entered true)) (trigger-watchman 1)) "门是开了，但动静也传出去了。")
          :fail (outcome (trigger-watchman 1) "锁舌弹回去的声音太清脆了。")))))

(define resource-loot-action
  (lambda (title desc effects ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suits (list 感知)
        :risk 'low
        :ok (outcome effects ok-text)
        :partial (outcome (append effects (list (effect 'add energy -1))) partial-text)
        :fail (outcome (list (effect 'add energy -1)) fail-text)))))

(define resource-search-actions
  (lambda ()
    (cond
      ((= (clock-value resource_loot) 0)
        (list
          (resource-loot-action
            "搜第一轮抽屉"
            "床头柜和水盆架通常最先藏零钱。"
            (list (effect 'clock+ resource_loot 1) (effect 'add money 12))
            "你摸出一卷零钱。"
            "你摸出零钱时碰掉了空药瓶。"
            "抽屉里只有灰和过期票据。")))
      ((= (clock-value resource_loot) 1)
        (list
          (resource-loot-action
            "翻旅行包"
            "旧皮包里总会剩点还能用的东西。"
            (list (effect 'clock+ resource_loot 1) (effect 'add food 1))
            "你翻到一份还没坏掉的食物。"
            "你翻到食物，但包扣卡住浪费了点力气。"
            "包里只剩换洗衬衣。")))
      ((= (clock-value resource_loot) 2)
        (list
          (resource-loot-action
            "检查床垫夹层"
            "穷人也会把急用钱塞在最难受的地方。"
            (list (effect 'clock+ resource_loot 1) (effect 'add money 8))
            "你从床垫边缘抽出几张钞票。"
            "你找到钞票时手臂也酸得发抖。"
            "这里已经被人搜过一遍了。")))
      ((= (clock-value resource_loot) 3)
        (list
          (resource-loot-action
            "把洗手台下也翻完"
            "最后那点零碎往往就丢在最潮湿的角落。"
            (list (effect 'clock+ resource_loot 1) (effect 'add food 1))
            "你又捞出一点能顶肚子的东西。"
            "你找到吃的，但蹲得太久腿都麻了。"
            "这里只剩湿毛巾和肥皂。")))
      (else (list)))))

(define target-entry-actions
  (lambda ()
    (list
      (action
        :title "等走廊空档再进"
        :desc "你盯着楼梯和转角，等所有能看见这扇门的人都移开视线。"
        :check (check
          :suits (list 感知)
          :risk 'low
          :ok (outcome (list (effect 'set target_room_entered true)) "你顺着空档溜进了门。")
          :partial (outcome (list (effect 'set target_room_entered true) (effect 'add energy -1)) "你是进去了，只是绷得太久。")
          :fail (outcome (list (effect 'add energy -1)) "你没等到真正干净的空档。"))))
      (action
        :title "撬开目标房门"
        :desc "门锁不复杂，难的是别让它替你打招呼。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (outcome (list (effect 'set target_room_entered true)) "门锁给了你面子。")
          :partial (outcome (append (list (effect 'set target_room_entered true)) (trigger-watchman 1)) "门开了，但这一层也更紧张了。")
          :fail (outcome (trigger-watchman 1) "锁芯哆嗦了一声，像在喊人。")))))

(define target-search-actions
  (lambda ()
    (list
      (mid-risk-search
        "检查行李与账本"
        "真正重要的东西不会只躺在床上，它会藏在需要你动脑子的地方。"
        逻辑
        target_search
        1
        "你理出了一层不属于普通住客的记录。"
        "你找到了一点门道，但也把紧张感往上推了一格。"
        "你翻得太慢，走廊那边已经有人开始留意。")
      (high-risk-search
        "拆床板和地毯夹层"
        "最值钱的东西，通常也藏在最粗暴的夹层里。"
        意志
        target_search
        2
        "你狠狠干开木板，摸到了藏在下面的小样品盒。"
        "你把夹层撬开了一半，样品已经很近了，但动静也大了。"
        "木板刚翘起来一点，你就知道这一层的人都听见了。"))))

(define patrol-status-text
  (lambda ()
    (cond
      ((= patrol_phase 'incoming) "守夜人正在朝这层走过来。休整会让警觉继续上升。")
      ((= patrol_phase 'leaving) "守夜人的脚步正在远去。休整会让警觉慢慢下降。")
      (else "二楼还没完全惊动，但每一声小动静都会留下回音。"))))

(define-scene hallway-scene
  (scene
    :title "二楼走廊"
    :desc
      (if target_room_known
        "你已经锁定了真正的目标房间。走廊上的每一次停顿，都在决定你能不能先一步进去。"
        (if resource_room_known
          "你先摸清了一间备用资源房，但真正的目标房间还藏在这排门后。"
          "你还不知道他们把东西放进了哪一间房。先在这层楼找出真正的门。"))
    :show-clocks (list hallway_investigation)
    :actions (hallway-actions)))

(define-scene resource-room-scene
  (scene
    :title "资源房"
    :desc
      (if (not resource_room_entered)
        "先被你确认的是一间备用资源房。门没上死锁，但也不是随便就能推开的。"
        (if (clock-filled? resource_loot)
          "这间房能拿的东西都被你翻完了。"
          "房里放着换洗布草、客人遗落的皮包和没来得及回收的零碎物资。"))
    :show-clocks (list resource_loot)
    :actions
      (if (not resource_room_known)
        (list)
        (if (not resource_room_entered)
          (resource-entry-actions)
          (resource-search-actions)))))

(define-scene target-room-scene
  (scene
    :title "目标房间"
    :desc
      (if (not target_room_entered)
        "你终于锁定了真正的门牌。现在问题只剩下怎么进去。"
        "房间里有人匆忙撤走过的痕迹。样品还在不在，得靠你自己翻出来。")
    :show-clocks (list target_search)
    :actions
      (if (not target_room_known)
        (list)
        (if (not target_room_entered)
          (target-entry-actions)
          (target-search-actions)))))

(define-scene infiltration
  (scene
    :title "望月旅馆 · 潜入"
    :desc (patrol-status-text)
    :show-clocks (list
      alert
      (when (= patrol_phase 'incoming) patrol_incoming)
      (when (= patrol_phase 'leaving) patrol_leaving))
    :children (list
      (hallway-scene)
      (when resource_room_known (resource-room-scene))
      (when target_room_known (target-room-scene)))))

(content
  :meta (meta :key '潜入旅馆 :title "潜入旅馆" :desc "在望月旅馆二楼锁定目标房间，找到样品。")
  :on-success (list
    (effect 'set 'hotel_infiltrated true))
  :on-fail (list
    (effect 'add energy -2))
  :on-cycle (list
    (effect 'clock+ cycle_pulse 1))
  :reacts (reacts
    (react
      :when (and (= patrol_phase 'incoming) (clock-filled? cycle_pulse) (not (clock-filled? patrol_incoming)))
      :then (list
        (effect-reset-clock cycle_pulse)
        (effect 'clock+ patrol_incoming 1)
        (effect 'clock+ alert 1)))
    (react
      :when (and (= patrol_phase 'incoming) (clock-filled? patrol_incoming))
      :then (list
        (effect 'set patrol_phase 'leaving)
        (effect-reset-clock patrol_leaving)))
    (react
      :when (and (= patrol_phase 'leaving) (clock-filled? cycle_pulse) (> (clock-value alert) 0) (not (clock-filled? patrol_leaving)))
      :then (list
        (effect-reset-clock cycle_pulse)
        (effect 'clock+ patrol_leaving 1)
        (effect 'clock- alert 1)))
    (react
      :when (and (= patrol_phase 'leaving) (or (clock-filled? patrol_leaving) (clock-empty? alert)))
      :then (list
        (effect 'set patrol_phase 'idle)))
    (react
      :when (and (>= (clock-value hallway_investigation) 2) (not resource_room_known))
      :then (list
        (effect 'set resource_room_known true)
        (effect 'start-quick-dialogue "你先摸到了一间备用资源房。里面不像目标，但能让你顺手捞点东西。")))
    (react
      :when (and (clock-filled? hallway_investigation) (not target_room_known))
      :then (list
        (effect 'set target_room_known true)
        (effect 'start-quick-dialogue "真正有人在意的是 212。门把手上有新擦掉的指纹，门缝里还有刚停住的味道。")))
    (react
      :when (clock-filled? target_search)
      :then (list
        (effect 'start-quick-dialogue "你在床板和旧账册之间摸到了那个小样品盒。旅馆这一趟没有白来。")
        (effect 'end-encounter 'success)))
    (react
      :when (>= (clock-value alert) 9)
      :then (list
        (effect 'end-encounter 'fail))))
  :state (state
    (use-world-basics)
    (alert (clock :title "警觉" :desc "填满则潜入失败。" :initial 0 :max 9))
    (patrol_incoming (clock :title "守夜人巡逻" :desc "正在朝这层走过来。每次休整，警觉 +1。" :initial 0 :max 2))
    (patrol_leaving (clock :title "守夜人离开" :desc "脚步声在远去。每次休整，警觉 -1。" :initial 0 :max 2))
    (hallway_investigation (clock :title "房间调查" :desc "找出真正的目标房间。" :initial 0 :max 4))
    (resource_loot (clock :title "资源搜寻" :desc "最多搜寻 4 次。" :initial 0 :max 4))
    (target_search (clock :title "寻找样品" :desc "把样品从目标房间里翻出来。" :initial 0 :max 3))
    (resource_room_known false)
    (resource_room_entered false)
    (target_room_known false)
    (target_room_entered false)
    (patrol_phase 'idle)
    (cycle_pulse (clock :title "巡逻节拍" :initial 0 :max 1)))
  :root (infiltration))
