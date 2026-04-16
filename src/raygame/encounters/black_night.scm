(include "enum-symbols.scm")

(include "common_clock_macros.scm")

(define bedroom_circle_probe
  (action
    :title "试探迂回"
    :desc "你从边角绕进去，把话一点点逼近核心。"
    :check (check
    :suits (list reason instinct)
    :risk low
    :ok (outcome "他被你绕开了防备。" (list (effect 'clock+ truth 1)))
    :partial (outcome "你逼近了真相，但还差一口气。" (list (effect 'clock+ truth 1)))
    :fail (outcome "他看穿了你的路子。" (list (effect 'clock+ alert 1)))
  )
  ))

(define bedroom_leave
  (action
    :title "收手离开"
    :desc "你已经听到足够多的半句真话。"
    :before (list (effect 'finish abort))
  ))

(define front_pick_lock
  (action
    :title "撬锁进入"
    :desc "你从正门进去，尽量别留下动静。"
    :check (check
    :suits (list reason instinct)
    :risk mid
    :ok (outcome "门锁被你撬开了。" (list (effect 'set entry_method 'front)))
    :partial (outcome "门开得不够干净，但你还是挤了进去。" (list (effect 'set entry_method 'front) (effect 'clock+ alert 1)))
    :fail (outcome "锁发出一声轻响。" (list (effect 'clock+ alert 1)))
  )
  ))

(define front_wait_gap
  (action
    :title "等巡查空档"
    :desc "你盯着屋里的人影，等他们错开。"
    :check (check
    :suits (list reason empathy)
    :risk low
    :ok (outcome "你抓住了空档，悄悄从正门进去了。" (list (effect 'set entry_method 'front)))
    :partial (outcome "你等得有点久，还是进去了。" (list (effect 'set entry_method 'front) (effect 'clock+ alert 1)))
    :fail (outcome "你等得太久，外头的动静多了起来。" (list (effect 'clock+ alert 1)))
  )
  ))

(define climb_window
  (action
    :title "翻上二楼窗户"
    :desc "你沿着排水管往上爬，从窗缝里翻进去。"
    :check (check
    :suits (list instinct force)
    :risk high
    :ok (outcome "你无声翻进了二楼。" (list (effect 'set entry_method 'window)))
    :partial (outcome "你擦伤了手，但还是进去了。" (list (effect 'set entry_method 'window) (effect 'health -1)))
    :fail (outcome "你没抓稳，差点摔下去。" (list (effect 'health -1) (effect 'clock+ alert 1)))
  )
  ))

(define left_start_patrol
  (action
    :title "扔石子"
    :desc "你把石头弹到视线外，引他转身去看。巡逻就从这一刻开始朝你压过来。"
    :before (list (effect 'set route 'left) (effect 'set patrol 1) (effect 'set traverse 0) (effect 'set dog_state 'calm) (effect 'set entry_method none))
  ))

(define left_hold_position
  (action
    :title "压低呼吸"
    :desc "你先不冒进，只贴着阴影停住，等他这一轮手电扫过去。"
    :before (list (effect 'clock+ patrol 1))
  ))

(define left_advance
  (action
    :title "趁隙穿越"
    :desc "你贴着墙往前压，赌他还没回头。"
    :check (check
    :suits (list reason instinct)
    :risk mid
    :ok (outcome "你稳稳跨过一段。" (list (effect 'clock+ traverse 1) (effect 'clock+ patrol 1)))
    :partial (outcome "你碰到了点动静，但还是往前挪了一步。" (list (effect 'clock+ traverse 1) (effect 'clock+ patrol 1) (effect 'clock+ alert 1)))
    :fail (outcome "手电光差点扫到你。你只能先把呼吸压住。" (list (effect 'clock+ patrol 1) (effect 'clock+ alert 1)))
  )
  ))

(define left_fight_guard
  (action
    :title "搏斗"
    :desc "你只能抢先动手，把人压回去。"
    :check (check
    :suits (list force)
    :risk high
    :ok (outcome "保安倒下了，通路也开了。" (list (effect 'set route none) (effect 'set phase 'entry) (effect 'set traverse 0) (effect 'clock+ alert 1)))
    :partial (outcome "你把他压住了，自己也挨了一下。" (list (effect 'set route none) (effect 'set phase 'entry) (effect 'set traverse 0) (effect 'health -1) (effect 'clock+ alert 1)))
    :fail (outcome "你没压住他。" (list (effect 'health -2) (effect 'clock+ alert 2)))
  )
  ))

(define left_berserk_rush
  (action
    :title "狠狠干硬闯"
    :desc "你不跟他绕，狠狠干着肩膀和步子直接撞穿这条走廊。"
    :check (check
    :suits (list force instinct)
    :risk high
    :ok (outcome "你狠狠干翻了保安，直接冲到了屋外。" (list (effect 'set route none) (effect 'set phase 'entry) (effect 'set patrol 0) (effect 'set traverse 0) (effect 'clock+ alert 2)))
    :partial (outcome "你是硬闯过去了，但自己也挨了一下。" (list (effect 'set route none) (effect 'set phase 'entry) (effect 'set patrol 0) (effect 'set traverse 0) (effect 'health -1) (effect 'clock+ alert 2)))
    :fail (outcome "你刚冲出去就被堵了回来。" (list (effect 'set route 'left) (effect 'set patrol 2) (effect 'health -1) (effect 'clock+ alert 2)))
  )
  ))

(define right_edge_forward
  (action
    :title "贴墙慢行"
    :desc "你贴着外墙慢慢挪，尽量不碰响任何东西。"
    :check (check
    :suits (list reason instinct)
    :risk mid
    :ok (outcome "你无声挪过了一段。" (list (effect 'set route 'right) (effect 'set patrol 0) (effect 'clock+ traverse 1)))
    :partial (outcome "你还是让它抬了头。你往前挪了一步。" (list (effect 'set route 'right) (effect 'set patrol 0) (effect 'clock+ traverse 1) (effect 'clock+ alert 1) (effect 'set dog_state 'agitated)))
    :fail (outcome "狗开始低吠。" (list (effect 'set route 'right) (effect 'set patrol 0) (effect 'set traverse 0) (effect 'set dog_state 'agitated) (effect 'clock+ alert 1)))
  )
  ))

(define drug_the_dog
  (action
    :title "投喂毒食"
    :desc "你把预备好的毒食丢进它够得着的地方。"
    :check (check
    :suits (list reason instinct)
    :risk high
    :ok (outcome "狗安静了下来。" (list (effect 'set dog_state 'asleep) (effect 'clock+ traverse 1)))
    :partial (outcome "它吃下去了，但还是挣扎了一下。" (list (effect 'set dog_state 'asleep) (effect 'clock+ traverse 1) (effect 'clock+ alert 1)))
    :fail (outcome "它警觉地躲开了。" (list (effect 'clock+ alert 1)))
  )
  ))

(define soothe_the_dog
  (action
    :title "低声安抚"
    :desc "你压低声音和动作，试着先让它把你当成没有威胁的东西。"
    :check (check
    :suits (list empathy instinct)
    :risk mid
    :ok (outcome "它慢慢安静下来，你也顺势往前挪了一段。" (list (effect 'set route 'right) (effect 'set dog_state 'asleep) (effect 'clock+ traverse 1)))
    :partial (outcome "它没有彻底放松，但也没立刻扑上来。" (list (effect 'set route 'right) (effect 'set dog_state 'agitated) (effect 'clock+ alert 1)))
    :fail (outcome "它被你这一下彻底惊起来了。" (list (effect 'set route 'right) (effect 'set dog_state 'agitated) (effect 'clock+ alert 1)))
  )
  ))

(define slip_past_dog
  (action
    :title "穿过小径"
    :desc "你放轻脚步，从它旁边穿过去。"
    :before (list (effect 'clock+ traverse 1))
  ))

(define front_direct_inquiry
  (action
    :title "直接询问"
    :desc "你开门见山，问他到底在藏什么。"
    :check (check
    :suits (list reason empathy)
    :risk low
    :ok (outcome "他沉默了一下，吐出了一点实话。" (list (effect 'clock+ truth 1)))
    :partial (outcome "他没回答全部，但你听到了关键半句。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :fail (outcome "他把话题挡了回去。" (list (effect 'clock+ alert 1)))
  )
  ))

(define front_present_evidence
  (action
    :title "摆出线索"
    :desc "你把一路摸来的痕迹摊给他看。"
    :check (check
    :suits (list reason empathy)
    :risk mid
    :ok (outcome "他终于不再硬扛。" (list (effect 'clock+ truth 2)))
    :partial (outcome "他承认了一半。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :fail (outcome "他知道你手里的东西还不够。" (list (effect 'clock+ alert 1)))
  )
  ))

(define front_silent_pressure
  (action
    :title "沉默施压"
    :desc "你什么也不说，只是看着他。"
    :check (check
    :suits (list empathy instinct)
    :risk mid
    :ok (outcome "他先败下阵来。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :partial (outcome "他开始坐不住了。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :fail (outcome "沉默压不住他。" (list (effect 'clock+ alert 1)))
  )
  ))

(define window_direct_inquiry
  (action
    :title "直接询问"
    :desc "你开门见山，问他到底在藏什么。"
    :check (check
    :suits (list reason empathy)
    :risk mid
    :ok (outcome "他沉默了一下，吐出了一点实话。" (list (effect 'clock+ truth 1)))
    :partial (outcome "他没回答全部，但你听到了关键半句。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :fail (outcome "他把话题挡了回去。" (list (effect 'clock+ alert 1)))
  )
  ))

(define window_present_evidence
  (action
    :title "摆出线索"
    :desc "你把一路摸来的痕迹摊给他看。"
    :check (check
    :suits (list reason empathy)
    :risk high
    :ok (outcome "他终于不再硬扛。" (list (effect 'clock+ truth 2)))
    :partial (outcome "他承认了一半。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :fail (outcome "他知道你手里的东西还不够。" (list (effect 'clock+ alert 1)))
  )
  ))

(define window_silent_pressure
  (action
    :title "沉默施压"
    :desc "你什么也不说，只是看着他。"
    :check (check
    :suits (list empathy instinct)
    :risk high
    :ok (outcome "他先败下阵来。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :partial (outcome "他开始坐不住了。" (list (effect 'clock+ truth 1) (effect 'clock+ alert 1)))
    :fail (outcome "沉默压不住他。" (list (effect 'clock+ alert 1)))
  )
  ))

(define exposed_scene
  (scene
    :title "暴露撤退"
    :desc "宅子里已经乱起来了。你没能把话听完，只能先退开。"
    :show-clocks (list alert truth)
    :actions (list )
  ))

(define yard_act
  (scene
    :title "院墙缺口"
    :desc "深夜。你站在宅邸外墙的阴影里。第一幕的目标很简单：穿过外部警戒，摸到屋外。左边是保安巡逻的走廊，右边是看门犬守着的小径。"
    :show-clocks (list alert)
    :actions (list )
    :children (list (scene
    :title "左侧走廊"
    :desc "这是一条没有遮挡的硬路。你可以先控场，把巡逻引偏后再穿；也可以狠狠干硬闯，拿伤势和警觉度去换速度。"
    :show-clocks (list alert patrol traverse)
    :actions (list (when (clock-empty? patrol) left_start_patrol) (when (not (clock-filled? traverse)) left_berserk_rush) (when (and (= route 'left) (clock-partial? patrol) (not (clock-filled? traverse))) left_hold_position) (when (and (= route 'left) (not (clock-empty? patrol)) (not (clock-filled? traverse))) left_advance) (when (and (= route 'left) (clock-filled? patrol) (not (clock-filled? traverse))) left_fight_guard))
  ) (scene
    :title "右侧小径"
    :desc "这条路更偏潜行。你可以贴墙慢行，也可以先处理那条看门犬，再从树影里悄悄摸过去。"
    :show-clocks (list alert traverse)
    :actions (list (when (and (= dog_state 'calm) (not (clock-filled? traverse))) right_edge_forward) (when (and (or (= dog_state 'calm) (= dog_state 'agitated)) (not (clock-filled? traverse))) soothe_the_dog) (when (and (= route 'right) (= dog_state 'agitated)) drug_the_dog) (when (and (= route 'right) (= dog_state 'asleep) (not (clock-filled? traverse))) slip_past_dog))
  ))
  ))

(define entry_act
  (scene
    :title "房屋外墙"
    :desc "第二幕里，你已经摸到屋外。现在的问题不是还能不能潜过去，而是你要以什么姿态进屋。正门稳一点，窗户快一点，也险一点。"
    :show-clocks (list alert)
    :actions (list )
    :children (list (scene
    :title "大门"
    :desc "门锁不算新，里头的人影偶尔会从门缝后晃过去。"
    :show-clocks (list alert)
    :actions (list front_pick_lock front_wait_gap)
  ) (scene
    :title "窗户"
    :desc "排水管能借力，但二楼那扇窗只留了一道窄缝。"
    :show-clocks (list alert)
    :actions (list climb_window)
  ))
  ))

(define bedroom_front_scene
  (scene
    :title "卧室"
    :desc "第三幕开始了。你从正门进来，老大抬头时明显愣了一下。现在你的目标不是再潜，而是逼他说出真相。"
    :show-clocks (list alert truth)
    :actions (list front_direct_inquiry bedroom_circle_probe front_present_evidence front_silent_pressure bedroom_leave)
  ))

(define bedroom_window_scene
  (scene
    :title "卧室"
    :desc "第三幕开始了。你从窗户翻进来，他看你的眼神更冷，也更警觉。你得在更高压的气氛里把真相逼出来。"
    :show-clocks (list alert truth)
    :actions (list window_direct_inquiry bedroom_circle_probe window_present_evidence window_silent_pressure bedroom_leave)
  ))

(define bedroom_act
  (if (= entry_method 'front) bedroom_front_scene bedroom_window_scene))

(content
  :meta (meta :key 'black_night :title "黑夜入宅" :desc "深夜潜入戒备森严的宅邸，只为听到一个真相。")
  :on-fail (list (effect 'stress 2))
  :state (state
    (alert (clock :title "全局警觉度" :initial 0 :max 6))
    (patrol (clock :title "保安巡逻" :initial 0 :max 3))
    (traverse (clock :title "穿越进度" :initial 0 :max 2))
    (truth (clock :title "真相" :initial 0 :max 3))
    (phase 'yard)
    (route none)
    (dog_state 'calm)
    (entry_method none))
  :reacts (reacts
    (react :when (clock-filled? alert) :then (list (effect 'finish fail)))
    (react :when (clock-filled? truth) :then (list (effect 'finish success)))
    (react :when (and (= phase 'yard) (= route 'left) (clock-filled? traverse)) :then (list (effect 'set phase 'entry) (effect 'set route none) (effect 'set patrol 0) (effect 'set traverse 0)))
    (react :when (and (= phase 'yard) (= route 'right) (clock-filled? traverse)) :then (list (effect 'set phase 'entry) (effect 'set route none) (effect 'set traverse 0)))
    (react :when (and (= phase 'entry) (not (= entry_method none))) :then (list (effect 'set phase 'bedroom))))
  :root
  (cond ((clock-filled? alert) exposed_scene) ((= phase 'yard) yard_act) ((= phase 'entry) entry_act) (else bedroom_act)))
