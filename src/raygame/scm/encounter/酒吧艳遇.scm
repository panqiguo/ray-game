(include "../enum-symbols.scm")

(define cold_direct_talk
  (action
    :title "直白搭话"
    :desc "你没有铺垫，直接把话扔到他面前。"
    :check (check
    :suits (list empathy reason)
    :risk low
    :ok (outcome "他抬眼看了你一眼，开始愿意接话。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他回了你一句，话匣子松了一点。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "他礼貌地点了点头，话头又被关上了。" (list (effect 'clock+ tension 1)))
  )
  ))

(define breathe
  (action
    :title "喘息一下"
    :desc "你拉开半口气，重新整理手里的节奏，但也会挨上一下。"
    :before (list (effect 'reset-hand) (effect 'health -1))
  ))

(define cold_ask_help
  (action
    :title "寻求帮助"
    :desc "你借一个无害的小问题，把自己的目的藏进请教里。"
    :check (check
    :suits (list reason empathy)
    :risk low
    :ok (outcome "他很自然地开始解释，戒心松了一层。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他给了个简短答案，但没有彻底关门。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "他看出这不是单纯请教，气氛冷了下来。" (list (effect 'clock+ tension 1)))
  )
  ))

(define cold_use_room
  (action
    :title "借环境起头"
    :desc "你拿酒吧里的动静做引子，把他拉到同一条观察线上。"
    :check (check
    :suits (list empathy instinct)
    :risk mid
    :ok (outcome "他顺着你的目光看过去，开始把你当成同类。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他跟着扫了一眼，嗯了一声。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "时机不对，他没接住你抛过去的视角。" (list (effect 'clock+ tension 1)))
  )
  ))

(define cold_leave_hook
  (action
    :title "留个钩子"
    :desc "你故意停在半句上，让他忍不住追问。"
    :check (check
    :suits (list reason instinct)
    :risk mid
    :ok (outcome "他果然追了上来，主动权开始往你手里滑。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他没追问，但眼神明显被你钩住了。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "他没上钩，空气里只剩下一点尴尬。" (list (effect 'clock+ tension 1)))
  )
  ))

(define warm_interest
  (action
    :title "引起兴趣"
    :desc "你抛出一个他没想到的观点，让这段聊天开始有重量。"
    :check (check
    :suits (list reason empathy)
    :risk mid
    :ok (outcome "他往前倾了一点，开始认真听你说话。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他表示认同，话题顺势延续。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你说的东西没落到他心上，热度掉下去一点。" (list (effect 'clock+ tension 1)))
  )
  ))

(define warm_flirt
  (action
    :title "制造暧昧"
    :desc "你把语气往模糊的地方轻轻一推。"
    :check (check
    :suits (list empathy instinct)
    :risk mid
    :ok (outcome "他接住了那点模糊，氛围一下子变软了。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他有些犹豫，但还是没有退开。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你推得太过，他把距离又收了回去。" (list (effect 'clock- rapport 1)))
  )
  ))

(define warm_read_him
  (action
    :title "展示判断力"
    :desc "你说出他没说出口的那半句，让他知道你听懂了。"
    :check (check
    :suits (list reason empathy)
    :risk mid
    :ok (outcome "他愣了一下，防备明显松了。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他嘴上没承认，但表情已经出卖了他。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你猜错了，他的态度一下子硬了起来。" (list (effect 'clock- rapport 1)))
  )
  ))

(define warm_keep_distance
  (action
    :title "留一点距离"
    :desc "你在他靠近的时候轻轻退半步，让他意识到你不是唾手可得。"
    :check (check
    :suits (list empathy instinct)
    :risk low
    :ok (outcome "他反而更想往前一步，兴趣被你勾起来了。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他有点不确定，但没有失去耐心。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "距离留得太硬，他误读成了拒绝。" (list ))
  )
  ))

(define soft_follow_lead
  (action
    :title "接住主动"
    :desc "他主动抛出一句话，你只负责顺着接住，不打断也不评判。"
    :check (check
    :suits (list empathy instinct)
    :risk low
    :ok (outcome "他越说越顺，口风开始往外松。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他说了一些，但还留着最后半句。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你接歪了方向，他觉得自己被牵着走。" (list (effect 'clock+ tension 1)))
  )
  ))

(define soft_make_promise
  (action
    :title "许诺"
    :desc "你给他一个理由，相信继续说是值得的。"
    :check (check
    :suits (list reason empathy)
    :risk mid
    :ok (outcome "他决定相信你，话明显多了起来。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他半信半疑，但已经开始松口。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你的许诺太空，他听得出你没落地。" (list (effect 'clock+ tension 1)))
  )
  ))

(define soft_tempt
  (action
    :title "诱惑"
    :desc "你让他看到，说出来会得到某种隐秘的好处。"
    :check (check
    :suits (list empathy instinct)
    :risk mid
    :ok (outcome "他被你说动了，继续聊下去的欲望压过了防备。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他靠近了一点，但还没真正开口。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你踩到了他的线，他把话题往回缩了。" (list (effect 'clock- rapport 1)))
  )
  ))

(define soft_pull_thread
  (action
    :title "顺势套话"
    :desc "你抓住他刚刚那句无心的话，从口子里继续往里切。"
    :check (check
    :suits (list reason instinct)
    :risk mid
    :ok (outcome "情报浮了出来，他已经挡不住这条线了。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "他只吐出了一半，还差一步。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你切得太准，他马上警觉起来了。" (list (effect 'clock- rapport 1)))
  )
  ))

(define soft_answer_probe
  (action
    :title "回应试探"
    :desc "他在测试你，你的回答决定他会不会把最后那层门打开。"
    :check (check
    :suits (list reason empathy)
    :risk high
    :ok (outcome "你通过了他的测试，他最后的防线松开了。" (list (effect 'clock+ rapport 2)))
    :partial (outcome "你稳稳接住了试探，局面没有散。" (list (effect 'clock+ rapport 1)))
    :fail (outcome "你暴露了意图，他把信任收了回去。" (list (effect 'clock- rapport 2)))
  )
  ))

(define leave_polite
  (action
    :title "找借口离开"
    :desc "你编一个合理的理由，把今晚收得体面一点。"
    :before (list (effect 'set ending 'clean) (effect 'end-encounter 'success))
  ))

(define walk_away
  (action
    :title "头也不回地离开"
    :desc "你什么也不解释，起身就走。"
    :check (check
    :suits (list instinct)
    :risk high
    :ok (outcome "你留下一点谜面，然后消失在门口。" (list (effect 'set ending 'mystery) (effect 'end-encounter 'success)))
    :partial (outcome "你走得太干脆，留下的味道有点复杂。" (list (effect 'set ending 'mystery) (effect 'clock+ tension 1) (effect 'end-encounter 'success)))
    :fail (outcome "你转身太快，连尾声都显得有点可疑。" (list (effect 'set ending 'mystery) (effect 'clock+ tension 1) (effect 'end-encounter 'fail)))
  )
  ))

(define invite_along
  (action
    :title "邀请共度一晚"
    :desc "你把话题往更近的地方推了一步。"
    :check (check
    :suits (list empathy instinct)
    :risk high
    :ok (outcome "他接受了这份延伸，故事还会继续。" (list (effect 'set ending 'continue) (effect 'end-encounter 'success)))
    :partial (outcome "他没有立刻拒绝，关系被你往前推了一点。" (list (effect 'set ending 'continue) (effect 'clock+ tension 1) (effect 'end-encounter 'success)))
    :fail (outcome "你推得太急，他一下子警觉起来。" (list (effect 'set ending 'continue) (effect 'clock+ tension 1) (effect 'end-encounter 'fail)))
  )
  ))

(define stage_cold
  (scene
    :title "冷淡"
    :desc "目标把自己裹在沉默里。你得先让他愿意继续说话。"
    :show-clocks (list rapport tension)
    :actions (list breathe (when (and (< (clock-value rapport) 3) (= cold_direct_talk_used false)) cold_direct_talk) (when (and (< (clock-value rapport) 3) (= cold_ask_help_used false)) cold_ask_help) (when (and (< (clock-value rapport) 3) (= cold_use_room_used false)) cold_use_room) (when (and (< (clock-value rapport) 3) (= cold_leave_hook_used false)) cold_leave_hook))
  ))

(define stage_warm
  (scene
    :title "熟络"
    :desc "话题已经打开了。你要让他意识到，这次偶遇有点不一样。"
    :show-clocks (list rapport tension)
    :actions (list breathe (when (and (>= (clock-value rapport) 3) (< (clock-value rapport) 6) (= warm_interest_used false)) warm_interest) (when (and (>= (clock-value rapport) 3) (< (clock-value rapport) 6) (= warm_flirt_used false)) warm_flirt) (when (and (>= (clock-value rapport) 3) (< (clock-value rapport) 6) (= warm_read_him_used false)) warm_read_him) (when (and (>= (clock-value rapport) 3) (< (clock-value rapport) 6) (= warm_keep_distance_used false)) warm_keep_distance))
  ))

(define stage_soft
  (scene
    :title "松动"
    :desc "他的防备已经松了。现在只差最后一层，情报就在那后面。"
    :show-clocks (list rapport tension)
    :actions (list breathe (when (and (>= (clock-value rapport) 6) (< (clock-value rapport) 9) (= soft_follow_lead_used false)) soft_follow_lead) (when (and (>= (clock-value rapport) 6) (< (clock-value rapport) 9) (= soft_make_promise_used false)) soft_make_promise) (when (and (>= (clock-value rapport) 6) (< (clock-value rapport) 9) (= soft_tempt_used false)) soft_tempt) (when (and (>= (clock-value rapport) 6) (< (clock-value rapport) 9) (= soft_pull_thread_used false)) soft_pull_thread) (when (and (>= (clock-value rapport) 6) (< (clock-value rapport) 9) (= soft_answer_probe_used false)) soft_answer_probe))
  ))

(define stage_exit
  (scene
    :title "离场"
    :desc "情报已经到手。你只剩下决定今晚怎么收尾。"
    :show-clocks (list rapport tension)
    :actions (list breathe leave_polite walk_away invite_along)
  ))

(content
  :meta (meta :key '酒吧艳遇 :title "酒吧艳遇" :desc "深夜的酒吧里，玩家要在目标关上心门之前钻进去，把情报带出来。")
  :on-success (list)
  :state (state
    (rapport (clock :title "好感" :initial 0 :max 9))
    (tension (clock :title "警觉度" :initial 0 :max 3))
    (attitude 'cold)
    (ending none)
    (cold_direct_talk_used false)
    (cold_ask_help_used false)
    (cold_use_room_used false)
    (cold_leave_hook_used false)
    (warm_interest_used false)
    (warm_flirt_used false)
    (warm_read_him_used false)
    (warm_keep_distance_used false)
    (soft_follow_lead_used false)
    (soft_make_promise_used false)
    (soft_tempt_used false)
    (soft_pull_thread_used false)
    (soft_answer_probe_used false))
  :reacts (reacts
    (react :when (>= (clock-value tension) (clock-max tension)) :then (list (effect 'end-encounter 'fail)))
    (react :when (>= (clock-value rapport) 3) :then (list (effect 'set attitude 'chatty)))
    (react :when (>= (clock-value rapport) 6) :then (list (effect 'set attitude 'engaged)))
    (react :when (>= (clock-value rapport) 9) :then (list (effect 'set attitude 'loose))))
  :root
  (cond 
    ((< (clock-value rapport) 3) stage_cold)
    ((< (clock-value rapport) 6) stage_warm)
    ((< (clock-value rapport) 9) stage_soft)
    (else stage_exit)))
