(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define-fragment put-the-note-on-the-desk
  (action
    :title "把便条拍在记者桌上"
    :desc "先别让他把这当成一次采访。你手里有东西，他必须先解释为什么这东西会在他这里。"
    :check (check
      :suit 魅力
      :risk 'mid
      :ok (outcome (list (effect 'clock+ concession 2)) "他看见便条，笑容短了一瞬。")
      :partial (outcome (list (effect 'clock+ concession 1) (effect 'clock+ backlash 1)) "他承认见过类似的稿源，也开始把你的名字写进脑子里。")
      :fail (outcome (list (effect 'clock+ backlash 1)) "他把便条推回来，说匿名投稿不归侦探管。"))))

(define-fragment pick-apart-his-story
  (action
    :title "拆穿他的时间线"
    :desc "事故、通报、排版、标题，每个时间点都能压住他一句漂亮话。"
    :check (check
      :suit 知识
      :risk 'mid
      :ok (outcome (list (effect 'clock+ concession 2)) "他的解释被时间线卡住，只能承认稿子来得太准。")
      :partial (outcome (list (effect 'clock+ concession 1) (effect 'clock+ backlash 1)) "他让步了一点，也警告你别把报社当成证人席。")
      :fail (outcome (list (effect 'clock+ backlash 1) (effect 'add 'pressure 1)) "他把你的问题改写成骚扰，语气越来越像明天的小标题。"))))

(define-fragment offer-a-better-story
  (action
    :title "给他一个更大的故事"
    :desc "记者不怕麻烦，他怕的是麻烦不够值钱。让他相信继续瞒着你会错过真正的头版。"
    :check (check
      :suit 魅力
      :risk 'high
      :ok (outcome (list (effect 'clock+ concession 3)) "他终于放低声音：便条像莱恩送来的，但送得太像有人安排。")
      :partial (outcome (list (effect 'clock+ concession 1) (effect 'clock+ backlash 1)) "他被吊住了胃口，却还想从你这里多榨一句。")
      :fail (outcome (list (effect 'clock+ backlash 2)) "他笑着说，你才是那个正在把自己送上头版的人。"))))

(content
  :meta (meta :key '报社谈判交锋 :title "报社谈判交锋" :desc "在编辑室外的小桌旁，逼小报记者承认事故便条的来路不正常。")
  :on-success (list
    (effect 'set 'reporter_negotiation_done true)
    (effect 'set 'press_feed_confirmed true)
    (effect 'start-quick-dialogue "# 报社的让步\n\n# speaker: 小报记者\n“便条看起来像莱恩。字也像，脾气也像。”\n\n# speaker: 科尔\n“但你不信？”\n\n# speaker: 小报记者\n他把烟按灭，声音低了下去。\n\n# speaker: 小报记者\n“我信他想让人听见。可我不信一个码头疯子知道该在什么时候、把什么词、递到哪张桌上。”\n\n# speaker: 科尔\n莱恩和报社之间有一条路。下一步不是问报纸，而是追那张便条是怎么走到这里的。"))
  :on-fail (list
    (effect 'add 'pressure 2)
    (effect 'start-quick-dialogue "# 谈判失手\n\n# speaker: 小报记者\n“侦探，你拿一张匿名便条就想审报社？”\n\n# speaker: 科尔\n他没有让步。更糟的是，他已经知道我在查什么。也许明天再来，报社的声音会小一点。"))
  :reacts (list
    (react :when (clock-filled? concession) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? backlash) :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-basics-vars
    (list
      (var 'concession (clock :title "记者让步" :desc "让他承认便条和事故稿的时间线不正常。" :initial 0 :max 4))
      (var 'backlash (clock :title "舆论反咬" :desc "他越能把你写成麻烦，你越难从报社拿到东西。" :initial 0 :max 3))))
  :root
  (scene
    :title "报社谈判桌"
    :desc "记者靠在桌边，笔尖还停在纸上。这里没有拳头，只有谁先把谁写进故事里。"
    :show-clocks (list concession backlash)
    :actions (list
      (put-the-note-on-the-desk)
      (pick-apart-his-story)
      (offer-a-better-story))))
