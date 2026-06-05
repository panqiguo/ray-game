(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define-fragment keep-your-distance
  (action
    :title "挡住莱恩的第一下"
    :desc "他不是来解释的。他拎着半截木柄从废墙后冲出来，像整个旧码头都压在这一击里。"
    :check (check
      :suit 暴力
      :risk 'mid
      :ok (outcome (list (effect 'clock+ ryan_break 2)) "你架住木柄，把他逼回碎砖旁。")
      :partial (outcome (list (effect 'clock+ ryan_break 1) (effect 'clock+ police_arrival 1)) "你挡住了他，也让围挡外的脚步声注意到这里。")
      :fail (outcome (list (effect 'clock+ police_arrival 1) (effect 'add 'health -1)) "木柄擦过你的肩，疼痛让废墟晃了一下。"))))

(define-fragment show-the-blueprint
  (action
    :title "把改造蓝图摊给他看"
    :desc "别只问他恨不恨夜莺。让他看见你已经知道这场首演和拆迁被画在同一张纸上。"
    :check (check
      :suit 知识
      :risk 'mid
      :ok (outcome (list (effect 'clock+ ryan_break 2)) "他盯着蓝图上的剪彩路线，怒气第一次变成了话。")
      :partial (outcome (list (effect 'clock+ ryan_break 1) (effect 'clock+ police_arrival 1)) "他认出了图，也听见围挡外有人在喊你的名字。")
      :fail (outcome (list (effect 'clock+ police_arrival 1)) "他把蓝图拍开，说你们这些人只会拿纸来埋人。"))))

(define-fragment press-the-newspaper-note
  (action
    :title "追问报社便条"
    :desc "便条像他的字，也像有人希望它像他的字。问错一句，他就会把你和报纸一起算账。"
    :check (check
      :suit 敏锐
      :risk 'high
      :ok (outcome (list (effect 'clock+ ryan_break 3)) "他承认给报社递过话，却不是为了替谁写好故事。")
      :partial (outcome (list (effect 'clock+ ryan_break 1) (effect 'clock+ police_arrival 1)) "他说报社至少会看见旧码头，但拒绝说是谁教他该怎么送。")
      :fail (outcome (list (effect 'clock+ police_arrival 2) (effect 'add 'pressure 1)) "“你也觉得我是他们写好的疯子。”他向后退，警哨声更近了。"))))

(define-fragment let-him-speak
  (action
    :title "让他说完旧码头的事"
    :desc "现在逼得太紧，只会把他重新推回拳头里。沉默有时候也是一种追问。"
    :check (check
      :suit 魅力
      :risk 'mid
      :ok (outcome (list (effect 'clock+ ryan_break 2) (effect 'clock- police_arrival 1)) "他终于说出工会今晚会游行，剧院门口会比舞台上更危险。")
      :partial (outcome (list (effect 'clock+ ryan_break 1)) "他吐出几句关于首演、剪彩和游行的碎话。")
      :fail (outcome (list (effect 'clock+ police_arrival 1)) "你给了他沉默，他只把沉默攥成更硬的拳头。"))))

(content
  :meta (meta :key '拆迁废墟里的莱恩 :title "拆迁废墟里的莱恩" :desc "在旧店后的拆迁废墟里第一次正面对峙莱恩，抢在警察干涉前听清首演夜背后的真正场面。")
  :on-success (list
    (effect 'set 'ryan_confronted true)
    (effect 'set 'ryan_ruins_confronted true)
    (effect 'set 'ryan_ruins_truth_heard true)
    (effect 'set 'ryan_police_interfered true)
    (effect 'add 'police_relation -1)
    (effect 'start-quick-dialogue "# 废墟里的莱恩\n\n# speaker: 莱恩\n“夜莺今晚唱的不是歌，是他们给旧码头盖棺材板前的祝词。”\n\n# speaker: 科尔\n他把拆迁通知拍在蓝图上。剧院、贵宾席、剪彩路线，全都连着旧街区。\n\n# speaker: 莱恩\n“工会今晚也会去。游行、堵门、喊口号。你们只需要一个疯子冲出来，就能让所有人闭嘴。”\n\n# speaker: 科尔\n“所以你不是他们找的人。”\n\n# speaker: 莱恩\n他笑得很难看。\n\n# speaker: 莱恩\n“我是他们需要的人。”\n\n# speaker: 科尔\n警哨声在围挡外响起。莱恩从塌墙后翻出去，两个便衣警察把枪口和手铐一起对准了我。"))
  :on-fail (list
    (effect 'set 'ryan_confronted true)
    (effect 'set 'ryan_ruins_confronted true)
    (effect 'set 'ryan_police_interfered true)
    (effect 'add 'pressure 2)
    (effect 'add 'police_relation -1)
    (effect 'start-quick-dialogue "# 废墟里的混战\n\n# speaker: 科尔\n莱恩没有说完。拳头、碎砖和警哨声把话全砸散了。\n\n# speaker: 莱恩\n“他不是你们找的人！”\n\n# speaker: 科尔\n我不知道他说的是谁。下一秒，他钻进废墙后面，两个便衣警察把我按在围挡上。今晚的首演夜，忽然变得更近，也更糟。"))
  :reacts (list
    (react :when (clock-filled? ryan_break) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? police_arrival) :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-basics-vars
    (list
      (var 'ryan_break (clock :title "莱恩开口" :desc "让莱恩从动手转向说出首演、拆迁和旧码头游行之间的关系。" :initial 0 :max 5))
      (var 'police_arrival (clock :title "警察逼近" :desc "便衣和封锁线保安正在靠近。填满后莱恩逃走，你被带去警局。" :initial 0 :max 4))))
  :root
  (scene
    :title "拆迁废墟"
    :desc "旧五金店后墙塌了一半。莱恩站在碎砖、雨水和拆迁木桩之间，眼睛红得像整晚都没睡。"
    :show-clocks (list ryan_break police_arrival)
    :actions (list
      (keep-your-distance)
      (show-the-blueprint)
      (press-the-newspaper-note)
      (let-him-speak))))
