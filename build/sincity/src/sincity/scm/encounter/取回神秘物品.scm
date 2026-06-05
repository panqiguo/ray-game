(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define make-mid-search-action
  (lambda (title desc suit progress-clock fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suit suit
        :risk 'mid
        :ok (outcome (list (effect 'clock+ progress-clock 1)) "")
        :partial (outcome (list (effect 'clock+ progress-clock 1) (effect 'add energy -1)) "")
        :fail (outcome (list (effect 'clock+ alert 1)) fail-text)))))

(define make-low-search-action
  (lambda (title desc suit progress-clock fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suit suit
        :risk 'low
        :ok (outcome (list (effect 'clock+ progress-clock 1)) "")
        :partial (outcome (list (effect 'clock+ progress-clock 1) (effect 'add energy -1)) "")
        :fail (outcome (list (effect 'add energy -1)) fail-text)))))

(define make-high-search-action
  (lambda (title desc suit progress-clock fail-text)
    (action
      :title title
      :desc desc
      :check (check
        :suit suit
        :risk 'high
        :ok (outcome (list (effect 'clock+ progress-clock 2)) "")
        :partial (outcome (list (effect 'clock+ progress-clock 1) (effect 'add health -1)) "")
        :fail (outcome (list (effect 'clock+ alert 2)) fail-text)))))

(define awning-search-actions
  (lambda ()
    (list
      (make-mid-search-action
        "掀开防雨布"
        "帆布下面压着一排潮湿木箱。"
        敏锐
        awning_progress
        "帆布被你扯出一声脆响，巷子里有人抬头。")
      (make-high-search-action
        "硬搬开前排木箱"
        "直接把前面的障碍掀开，看后面有没有藏层。"
        暴力
        awning_progress
        "木箱砸地的声音让巷口更紧张了。"))))

(define office-search-actions
  (lambda ()
    (list
      (make-mid-search-action
        "翻账桌抽屉"
        "账桌里塞满了收据、烟盒和剪碎的纸片。"
        敏锐
        office_progress
        "抽屉卡了一下，发出的声音让你停住了手。")
      (make-low-search-action
        "比对出货账本"
        "不急着动铁柜，先把错页和出货记录一页页捋顺。"
        知识
        office_progress
        "你还是没理出头绪，只是白白耗掉了一口气。")
      (make-high-search-action
        "撬开铁皮柜"
        "不管账本，直接开最像临时藏物的铁柜。"
        暴力
        office_progress
        "铁柜纹丝不动，你反而先弄出了响声。"))))

(define truck-search-actions
  (lambda ()
    (list
      (make-mid-search-action
        "钻进车厢底部"
        "车厢里堆着麻袋和旧帆布，下面也许另有一层。"
        敏锐
        truck_progress
        "你刚探进去，车厢铁皮就回了一声闷响。")
      (make-high-search-action
        "掀翻麻袋搜底"
        "不管细节，先把能藏东西的地方全翻开。"
        暴力
        truck_progress
        "麻袋砸在铁板上的声音太响了。"))))

(define (awning-scene)
  (scene
    :title "雨棚堆箱"
    :desc (if awning_revealed
      "木箱后面只剩一截带血帆布和空木匣。这里已经可以排除。"
      "雨棚下堆着一排木箱和湿帆布。要藏一件东西，这里够快，但未必够稳。")
    :show-clocks (list alert awning_progress)
    :actions (if awning_revealed (list) (awning-search-actions))))

(define (office-scene)
  (scene
    :title "账房"
    :desc (if office_revealed
      "假背板已经被拆开，里面空了。你已经拿到了想要的东西。"
      "账房里有一张旧桌、两本错页账册和一个铁皮柜。要把样品藏稳，这里最像真正的藏点。")
    :show-clocks (list alert office_progress)
    :actions (if office_revealed (list) (office-search-actions))))

(define (truck-scene)
  (scene
    :title "巷尾车厢"
    :desc
      (if truck_eliminated
        "根据你之前摸到的死者线索，这辆车更像接应工具，不像真正的藏点。这里已经被排除了。"
        (if truck_revealed
          "车厢底下只有伪造单据和一把坏掉的封条钳。这里没有样品。"
          "巷尾那辆没熄火的车半开着后厢。要是有人准备立刻转手，样品也可能先塞在这里。"))
    :show-clocks (list alert truck_progress)
    :actions (if (or truck_eliminated truck_revealed) (list) (truck-search-actions))))

(define (recovery)
  (scene
    :title "仓库后巷 · 取回神秘物品"
    :desc
      (if police_knows_true_info
        (if (> wounded_man_lead 0)
          "样品被转到仓库后巷后，又被分散伪装在三处可能的藏点里。你之前交给警察的真消息已经让附近更紧张了；但你从死者身上摸到的线索，也替你先排除了一个错误地点。警觉填满之前，把样品找出来。"
          "样品被转到仓库后巷后，又被分散伪装在三处可能的藏点里。你之前交给警察的真消息已经让附近更紧张了。警觉填满之前，把样品找出来。")
        (if (> wounded_man_lead 0)
          "样品被转到仓库后巷后，又被分散伪装在三处可能的藏点里。死者留下的线索替你先排除了一个错误地点。警觉填满之前，把样品找出来。"
          "样品被转到仓库后巷后，又被分散伪装在三处可能的藏点里。警觉填满之前，把样品找出来。"))
    :show-clocks (list alert)
    :children (list
      (awning-scene)
      (office-scene)
      (truck-scene))))

(content
  :meta (meta :key '取回神秘物品 :title "取回神秘物品" :desc "在后巷的三处伪装藏点里先一步找到样品。")
  :on-success (list
    (effect 'set 'item_recovered true)
    (effect 'set 'item_recovery_started false)
    (effect 'add 'mysterious_item 1))
  :on-fail (list
    (effect 'set 'item_recovery_failed true)
    (effect 'set 'item_recovery_started false)
    (effect 'add 'police_relation -1)
    (effect 'add 'health -1))
  :on-cycle-start (list)
  :reacts (list
    (react
      :when (and police_knows_true_info (not police_alert_applied))
      :then (list
        (effect 'set police_alert_applied true)
        (effect 'clock+ alert 1)))
    (react
      :when (and (> wounded_man_lead 0) (not truck_eliminated))
      :then (list
        (effect 'set truck_eliminated true)
        (effect 'set truck_revealed true)
        (effect 'clock+ truck_progress 6)))
    (react
      :when (and (clock-filled? awning_progress) (not awning_revealed))
      :then (list
        (effect 'set awning_revealed true)
        (effect 'start-quick-dialogue "你掀开最后一层，只看到一截带血的帆布和一只空木匣。样品不在雨棚堆箱。")))
    (react
      :when (and (clock-filled? office_progress) (not office_revealed))
      :then (list
        (effect 'set office_revealed true)
        (effect 'start-quick-dialogue "你拆开账房的假背板，里面躺着密封好的小盒。样品在这里。")
        (effect 'end-encounter 'success)))
    (react
      :when (and (clock-filled? truck_progress) (not truck_revealed))
      :then (list
        (effect 'set truck_revealed true)
        (effect 'start-quick-dialogue "底板下面只有几张伪造单据和一把断掉的封条钳。这里不是样品的藏点。")))
    (react
      :when (>= (clock-value alert) 6)
      :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-health-vars
    world-energy-vars
    (list
    (var 'alert (clock :title "警觉" :initial 0 :max 6))
    (var 'awning_progress (clock :title "雨棚堆箱" :initial 0 :max 6))
    (var 'office_progress (clock :title "账房" :initial 0 :max 6))
    (var 'truck_progress (clock :title "巷尾车厢" :initial 0 :max 6))
    (var 'awning_revealed false)
    (var 'office_revealed false)
    (var 'truck_revealed false)
    (var 'truck_eliminated false)
    (import-world-item 'wounded_man_lead)
    (import-world-value 'police_knows_true_info false)
    (var 'police_alert_applied false))
    )
  :root (recovery))
