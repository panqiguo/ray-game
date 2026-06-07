(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define-fragment check-the-tin-box
  (action
    :title "翻看墙角的铁皮箱"
    :desc "铁皮箱上压着几件旧衣服。锁已经坏了，麻烦在于它响起来会像一只被踩住的罐头。"
    :check (check
      :suit 敏锐
      :risk 'mid
      :ok (outcome (list (effect 'clock+ search_progress 2)) "箱底有一叠潮软的旧照片。")
      :partial (outcome (list (effect 'clock+ search_progress 1) (effect 'clock+ helen_stirring 1)) "你摸到了照片，也让箱盖发出一声轻响。")
      :fail (outcome (list (effect 'clock+ helen_stirring 1)) "箱子一歪，里面的铁扣撞在地板上。"))))

(define-fragment steady-the-bottle
  (action
    :title "稳住快倒的酒瓶"
    :desc "桌边的酒瓶慢慢滑向地面。让它安静下来，比继续翻找更要紧。"
    :check (check
      :suit 敏锐
      :risk 'low
      :ok (outcome (list (effect 'clock- helen_stirring 1)) "瓶底停住了，老海伦的呼吸没有变。")
      :partial (outcome (list) "你接住了瓶子，但也浪费了一点时间。")
      :fail (outcome (list (effect 'clock+ helen_stirring 1)) "玻璃擦过桌沿，老海伦含糊地骂了一句。"))))

(define-fragment inspect-the-frame
  (action
    :title "查看床头旧相框"
    :desc "相框背面夹着纸片。照片里的莱恩还年轻，五金店的招牌也还没有歪。"
    :check (check
      :suit 知识
      :risk 'mid
      :ok (outcome (list (effect 'clock+ search_progress 2)) "相框背后写着一个日期：改造说明会前夜。")
      :partial (outcome (list (effect 'clock+ search_progress 1)) "你看清了莱恩和那间店，没看清照片边缘那个女人。")
      :fail (outcome (list (effect 'clock+ helen_stirring 1)) "相框背板卡得太紧，木片发出一声裂响。"))))

(define-fragment listen-to-her-breathing
  (action
    :title "停下来听她的呼吸"
    :desc "有时候最好的动作是先别动。她要是醒了，整个房间都会变成证词。"
    :effects (list (effect 'clock- helen_stirring 1))))

(define-fragment lift-the-hidden-layer
  (action
    :title "直接掀开箱底暗层"
    :desc "你看到了箱底不自然的缝。这里可能藏着东西，也可能藏着一声足够吵醒她的动静。"
    :check (check
      :suit 敏锐
      :risk 'high
      :ok (outcome (list (effect 'clock+ search_progress 3)) "暗层下面就是那张照片，边角被酒渍染黄。")
      :partial (outcome (list (effect 'clock+ search_progress 2) (effect 'clock+ helen_stirring 1)) "照片到手了，木板也响了。")
      :fail (outcome (list (effect 'clock+ helen_stirring 2)) "暗层被你掀得太猛，老海伦在椅子里猛地动了一下。"))))

(content
  :meta (meta :key '老海伦房间搜查 :title "老海伦房间搜查" :desc "趁老海伦醉睡过去，在她堆满旧物的房间里找到莱恩过去的照片。")
  :on-success (list
    (effect 'set 'helen_room_searched true)
    (effect 'set 'helen_photo_found true)
    (effect 'set 'ryan_old_life_known true)
    (effect 'set 'ryan_followed_after_helen true)
    (effect 'set 'docks_threat_escalated true)
    (effect 'set 'ryan_old_shop_unlocked true)
    (effect 'set 'theater_accident_unlocked true)
    (effect 'start-quick-dialogue "# 旧照片\n\n# speaker: 科尔\n照片里是莱恩年轻时的五金店。门口站着老海伦、几个码头工人，还有一个穿演出服的年轻女人。\n\n背面写着：改造说明会前夜。\n\n# speaker: 科尔\n下楼时，我没有回头。到街口，我在橱窗倒影里看见一个人影停了下来。不是偶遇。\n\n# 剧院来电\n\n# speaker: 剧院经理\n“后台出事了。夜莺在里面。你最好现在过来。”\n\n# speaker: 科尔\n旧照片还没在口袋里放稳，事故已经追到了剧院。"))
  :on-fail (list
    (effect 'set 'helen_room_searched true)
    (effect 'set 'helen_photo_damaged true)
    (effect 'set 'ryan_old_life_known true)
    (effect 'set 'ryan_followed_after_helen true)
    (effect 'set 'docks_threat_escalated true)
    (effect 'set 'ryan_old_shop_unlocked true)
    (effect 'set 'theater_accident_unlocked true)
    (effect 'add 'pressure 1)
    (effect 'start-quick-dialogue "# 照片残片\n\n# speaker: 老海伦\n她醒来时第一件事就是抢那张照片。纸在你们手里裂开，只剩一角留在你掌心。\n\n# speaker: 科尔\n走到街口时，一个年轻码头人靠在电线杆旁，假装点烟。火柴亮起时，他正看着我的口袋。\n\n# 剧院来电\n\n# speaker: 剧院经理\n“后台出事了。夜莺在里面。你最好现在过来。”\n\n# speaker: 科尔\n残片还攥在手里，剧院的事故已经把下一步推到我面前。"))
  :reacts (list
    (react :when (clock-filled? search_progress) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? helen_stirring) :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-basics-vars
    (list
      (var 'search_progress (clock :title "搜查进度" :desc "找到旧照片前，你还需要在房间里多翻一点。" :initial 0 :max 4))
      (var 'helen_stirring (clock :title "惊醒" :desc "老海伦越接近醒来，这件事就越不像调查。" :initial 0 :max 3))))
  :root
  (location
    :title "老海伦的房间"
    :desc "老海伦歪在椅子里，杯子还在手边。房间堆满旧物，像旧码头被拆下来的碎片全被塞进了这里。"
    :show-clocks (list search_progress helen_stirring)
    :actions (list
      (check-the-tin-box)
      (steady-the-bottle)
      (inspect-the-frame)
      (listen-to-her-breathing)
      (lift-the-hidden-layer))))
