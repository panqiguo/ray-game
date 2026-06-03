(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define trigger-watchman
  (lambda (amount)
    (list
      (effect 'clock+ alert amount))))

(define low-risk-search
  (lambda (title desc suit progress-clock ok-step ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suit suit
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
        :suit suit
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
        :suit suit
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
          敏锐
           hallway_investigation
           1
           "你顺着送水车停留的位置，缩小了一圈范围。"
           "你还是摸到了一点门道，只是站得太久了。"
           "你什么也没看清，只好先换个角度。"))
      (when (not target_room_known)
        (mid-risk-search
          "偷听几间门缝"
          "有些房间装睡，有些房间真的有人。你得分清哪一扇门后面藏着你要找的东西。"
          知识
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
          :suit 敏锐
          :risk 'low
          :ok (outcome (list (effect 'set resource_room_entered true)) "你从门缝里滑了进去。")
          :partial (outcome (list (effect 'set resource_room_entered true) (effect 'add energy -1)) "你进去了，只是多等了太久。")
          :fail (outcome (list (effect 'add energy -1)) "你刚要动，脚步声又回到了门口。"))))
      (action
        :title "撬开资源房门锁"
        :desc "旧锁比人可靠，但也比人更会出声。"
        :check (check
          :suit 知识
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
        :suit 敏锐
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
          :suit 敏锐
          :risk 'low
          :ok (outcome (list (effect 'set target_room_entered true)) "你顺着空档溜进了门。")
          :partial (outcome (list (effect 'set target_room_entered true) (effect 'add energy -1)) "你是进去了，只是绷得太久。")
          :fail (outcome (list (effect 'add energy -1)) "你没等到真正干净的空档。"))))
      (action
        :title "撬开目标房门"
        :desc "门锁不复杂，难的是别让它替你打招呼。"
        :check (check
          :suit 知识
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
        知识
        target_search
        1
        "你理出了一层不属于普通住客的记录。"
        "你找到了一点门道，但也把紧张感往上推了一格。"
        "你翻得太慢，走廊那边已经有人开始留意。")
      (high-risk-search
        "拆床板和地毯夹层"
        "最值钱的东西，通常也藏在最粗暴的夹层里。"
        暴力
        target_search
        2
        "你狠狠干开木板，摸到了藏在下面的小样品盒。"
        "你把夹层撬开了一半，样品已经很近了，但动静也大了。"
        "木板刚翘起来一点，你就知道这一层的人都听见了。"))))

(define soften-wife-patrol
  (lambda (title desc suit ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suit suit
        :risk 'mid
        :ok (outcome (list (effect 'clock+ wife_patrol 2)) ok-text)
        :partial (outcome (list (effect 'clock+ wife_patrol 1) (effect 'add energy -1)) partial-text)
        :fail (outcome (list (effect 'clock+ alert 1)) fail-text)))))

(define soften-husband-patrol
  (lambda (title desc suit ok-text partial-text fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suit suit
        :risk 'mid
        :ok (outcome (list (effect 'clock+ husband_patrol 2)) ok-text)
        :partial (outcome (list (effect 'clock+ husband_patrol 1) (effect 'add energy -1)) partial-text)
        :fail (outcome (list (effect 'clock+ alert 1)) fail-text)))))

(define (wife-patrol-scene)
  (scene
    :title "旅馆老板娘巡查"
    :desc "楼下传来拖鞋踩过木阶的声音。老板娘没喊人，只是把每扇门外的影子都看了一遍。她在场时，每次休整都会让警觉继续上升。"
    :show-clocks (list wife_patrol)
    :actions (list
      (soften-wife-patrol
        "把动静引到窗外的猫"
        "窗台下面确实有野猫。你只需要让它看起来像罪魁祸首。"
        魅力
        "她听见猫叫，脚步停了一会儿。"
        "她半信半疑，但暂时没往你这边来。"
        "猫没配合，楼梯声反而更近了。")
      (soften-wife-patrol
        "伪装成隔壁住客咳嗽"
        "这种旅馆里，夜里有人咳两声不算稀奇。"
        魅力
        "她在门外停了一下，最后把这动静归到隔壁房。"
        "你的咳声有点刻意，但也算拖住了她。"
        "你咳得太干净，像一个正在撒谎的人。"))))

(define (husband-patrol-scene)
  (scene
    :title "旅馆老板巡查"
    :desc "老板的脚步比老板娘重。他不是来确认有没有声音，他是来确认有没有人敢不付代价。老板在场时，每次休整都会让警觉继续上升。"
    :show-clocks (list husband_patrol)
    :actions (list
      (soften-husband-patrol
        "把门缝下的光压灭"
        "先让他相信这层没人醒着，至少没人敢醒着。"
        敏锐
        "门缝暗下去，他的脚步慢了一拍。"
        "你压住了光，也压住了自己的呼吸。"
        "光影晃了一下，他看见了不该有的轮廓。")
      (soften-husband-patrol
        "丢一枚硬币到走廊另一头"
        "不是让他相信没人，而是让他先去看别处。"
        魅力
        "硬币滚到远处，他骂了一声，转身过去看。"
        "他被引开一点，但没有完全离开。"
        "硬币撞得太响，像有人故意为之。"))))

(define patrol-status-text
  (lambda ()
    (cond
      (husband_patrol_active "老板正在巡查这层。先把他糊弄过去，再继续翻。")
      (wife_patrol_active "老板娘已经上楼巡查。她不一定看见了你，但她听见了这层的不对劲。")
      (else "二楼还没完全惊动，但每一声小动静都会留下回音。"))))

(define (hallway-scene)
  (scene
    :title "二楼走廊"
    :desc
      (if target_room_known
        "你已经锁定了真正的目标房间。走廊上的每一次停顿，都在决定你能不能先一步进去。"
        (if resource_room_known
          "你先摸清了一间备用资源房，但真正的目标房间还藏在这排门后。"
          "你还不知道他们把东西放进了哪一间房。先在这层楼找出真正的门。"))
    :show-clocks (list (when (not target_room_known) hallway_investigation))
    :actions (hallway-actions)))

(define (resource-room-scene)
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

(define (target-room-scene)
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

(define (infiltration)
  (scene
    :title "望月旅馆 · 潜入"
    :desc (patrol-status-text)
    :show-clocks (list alert)
    :children (list
      (when wife_patrol_active (wife-patrol-scene))
      (when husband_patrol_active (husband-patrol-scene))
      (when (not target_room_known) (hallway-scene))
      (when resource_room_known (resource-room-scene))
      (when target_room_known (target-room-scene)))))

(content
  :meta (meta :key '潜入旅馆 :title "潜入旅馆" :desc "在望月旅馆二楼锁定目标房间，找到样品。")
  :on-success (list
    (effect 'set 'hotel_infiltrated true))
  :on-fail (list
    (effect 'add energy -2))
  :on-cycle-start (list
    (effect 'clock+ wife_patrol_tick 1)
    (effect 'clock+ husband_patrol_tick 1))
  :reacts (list
    (react
      :when (and (>= (clock-value alert) 3) (not wife_patrol_triggered))
      :then (list
        (effect 'set wife_patrol_triggered true)
        (effect 'set wife_patrol_active true)
        (effect-reset-clock wife_patrol_tick)
        (effect 'start-quick-dialogue "楼下传来拖鞋踩上木阶的声音。旅馆老板娘醒了。")))
    (react
      :when (and (>= (clock-value alert) 6) (not husband_patrol_triggered))
      :then (list
        (effect 'set husband_patrol_triggered true)
        (effect 'set husband_patrol_active true)
        (effect-reset-clock husband_patrol_tick)
        (effect 'start-quick-dialogue "更重的脚步从楼下压上来。旅馆老板也被惊动了。")))
    (react
      :when (and wife_patrol_active (clock-filled? wife_patrol_tick))
      :then (list
        (effect-reset-clock wife_patrol_tick)
        (effect 'clock+ alert 1)))
    (react
      :when (and husband_patrol_active (clock-filled? husband_patrol_tick))
      :then (list
        (effect-reset-clock husband_patrol_tick)
        (effect 'clock+ alert 1)))
    (react
      :when (and (clock-filled? wife_patrol) wife_patrol_active)
      :then (list
        (effect 'set wife_patrol_active false)
        (effect 'start-quick-dialogue "老板娘终于把这层的动静归到那些夜里乱窜的小东西身上，拖鞋声慢慢下楼去了。")))
    (react
      :when (and (clock-filled? husband_patrol) husband_patrol_active)
      :then (list
        (effect 'set husband_patrol_active false)
        (effect 'start-quick-dialogue "老板骂了一句，像是决定明天再找人算账。他的脚步离开了这一层。")))
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
  :vars (append
    world-basics-vars
    (list
    (var 'alert (clock :title "警觉" :desc "填满则潜入失败。" :initial 0 :max 9))
    (var 'wife_patrol (clock :title "老板娘巡查" :desc "填满后老板娘离开。" :initial 0 :max 4))
    (var 'husband_patrol (clock :title "老板巡查" :desc "填满后老板离开。" :initial 0 :max 4))
    (var 'wife_patrol_tick (clock :title "老板娘巡查节拍" :initial 0 :max 1))
    (var 'husband_patrol_tick (clock :title "老板巡查节拍" :initial 0 :max 1))
    (var 'hallway_investigation (clock :title "房间调查" :desc "找出真正的目标房间。" :initial 0 :max 4))
    (var 'resource_loot (clock :title "资源搜寻" :desc "最多搜寻 4 次。" :initial 0 :max 4))
    (var 'target_search (clock :title "寻找样品" :desc "把样品从目标房间里翻出来。" :initial 0 :max 3))
    (var 'resource_room_known false)
    (var 'resource_room_entered false)
    (var 'target_room_known false)
    (var 'target_room_entered false)
    (var 'wife_patrol_triggered false)
    (var 'wife_patrol_active false)
    (var 'husband_patrol_triggered false)
    (var 'husband_patrol_active false))
    )
  :root (infiltration))
