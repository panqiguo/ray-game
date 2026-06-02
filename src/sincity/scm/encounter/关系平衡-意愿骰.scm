;; 这只是一个会切换话题的关系筹码版本而已, 我们增加关系, 然后利用它来获取情报
;; 事实上你几乎没有选择, 你的目的出奇地一致


(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define relation-desc
  (lambda ()
    (cond
      ((<= (clock-value relation) 1) "关系快耗尽了。再强行引导，很可能让她关上门。")
      ((>= (clock-value relation) 5) "关系余量很足。你可以考虑把话题往情报上带。")
      (else "关系还稳。顺势聊能补余量，转向情报会消耗余量。"))))

(define topic-current?
  (lambda (topic-key)
    (= topic topic-key)))

(define topic-status
  (lambda (topic-key)
    (if (topic-current? topic-key)
      "她现在想聊这个。顺着谈会推进关系。"
      "她现在不想聊这个。强行转来这里会消耗关系。")))

(define social-topic-action
  (lambda (topic-key action-title ok-text partial-text fail-text)
    (action
      :title action-title
      :desc "如果这是她当前想聊的话题：好关系 +2，中关系 +1，坏无收益。否则：好关系 +1，中无收益，坏关系 -1。"
      :check (check
        :suit 魅力
        :risk 'low
        :ok (outcome ok-text
          (if (topic-current? topic-key)
            (list (effect 'clock+ relation 2))
            (list (effect 'clock+ relation 1))))
        :partial (outcome partial-text
          (if (topic-current? topic-key)
            (list (effect 'clock+ relation 1))
            (list)))
        :fail (outcome fail-text
          (if (topic-current? topic-key)
            (list)
            (list (effect 'clock- relation 1))))))))

(define clue-action
  (lambda ()
    (action
      :title "谈情报（获取情报）"
      :desc "如果她当前想聊 C：好情报 +3、关系 +1；中情报 +2；坏情报 +1、关系 -1。否则：好情报 +2、关系 -2；中情报 +1、关系 -2；坏关系 -3。"
      :check (check
        :suit 知识
        :risk 'high
        :ok (outcome "你把问题放在她愿意靠近的地方，关键线索自然浮了出来。"
          (if (topic-current? 'clue)
            (list (effect 'clock+ intel 3) (effect 'clock+ relation 1))
            (list (effect 'clock+ intel 2) (effect 'clock- relation 2))))
        :partial (outcome "答案出来了一半，但她也察觉到你的方向。"
          (if (topic-current? 'clue)
            (list (effect 'clock+ intel 2))
            (list (effect 'clock+ intel 1) (effect 'clock- relation 2))))
        :fail (outcome "你问得太直，她把话题截断了。"
          (if (topic-current? 'clue)
            (list (effect 'clock+ intel 1) (effect 'clock- relation 1))
            (list (effect 'clock- relation 3))))))))

(define ease-action
  (lambda ()
    (action
      :title "缓一缓（修复关系）"
      :desc "暂时放弃推进情报，回到她舒服的话题。好：关系 +2；中：关系 +1；坏：时间 +1。"
      :check (check
        :suit 魅力
        :risk 'low
        :ok (outcome "你主动退了一步，她重新愿意把话接下去。"
          (list (effect 'clock+ relation 2)))
        :partial (outcome "你把气氛从紧绷处拉了回来。"
          (list (effect 'clock+ relation 1)))
        :fail (outcome "你退得太刻意，时间被白白耗掉。"
          (list (effect 'clock+ time 1)))))))

(define (topic-a-scene)
  (scene
    :title "话题A：她的过去"
    :desc (topic-status 'past)
    :position '(260 260)
    :actions (list
      (social-topic-action
        'past
        "谈过去（推进关系）"
        "你没有急着问正事，只是让她把自己的过去说完。"
        "她说了一点，又把某些名字轻轻放过去。"
        "你碰到了不该碰的地方，她的声音淡了。")
      (ease-action))))

(define (topic-b-scene)
  (scene
    :title "话题B：她的看法"
    :desc (topic-status 'view)
    :position '(540 260)
    :actions (list
      (social-topic-action
        'view
        "谈看法（推进关系）"
        "你顺着她对那个人的判断往下聊，她开始把你当成同谋。"
        "她给出了一句评价，但还没完全放松。"
        "你的附和显得太快，她没有接这句话。")
      (ease-action))))

(define (topic-c-scene)
  (scene
    :title "话题C：关键情报"
    :desc (if (topic-current? 'clue)
      "她现在愿意靠近情报话题。这是最好的推进窗口。"
      "她现在不想谈这里。你可以强行转向，但会消耗关系。")
    :position '(820 260)
    :actions (list
      (clue-action)
      (ease-action))))

(define (will-root)
  (scene
    :title "关系平衡-意愿骰"
    :desc (relation-desc)
    :show-clocks (list intel relation time)
    :children (list
      (topic-a-scene)
      (topic-b-scene)
      (topic-c-scene))))

(content
  :meta (meta :key '关系平衡-意愿骰 :title "关系平衡-意愿骰" :desc "用反应骰表达对方当前意愿，测试顺势、转向与关系消耗。")
  :on-success (list (effect 'set 'test_relation_will_done true))
  :on-fail (list (effect 'set 'test_relation_will_failed true))
  :on-cycle (list (effect 'clock+ time 1))
  :reaction-die
    (reaction-die
      (reaction-table
        (face 1 "A：过去" (effect 'set topic 'past))
        (face 2 "A：过去" (effect 'set topic 'past))
        (face 3 "B：看法" (effect 'set topic 'view))
        (face 4 "B：看法" (effect 'set topic 'view))
        (face 5 "C：情报" (effect 'set topic 'clue))
        (face 6 "C：情报" (effect 'set topic 'clue))))
  :reacts (list
    (react :when (clock-filled? intel) :then (list
      (effect 'start-quick-dialogue "你没有硬撬她的嘴，而是在她愿意靠近的时候拿到了关键情报。")
      (effect 'end-encounter 'success)))
    (react :when (clock-empty? relation) :then (list
      (effect 'start-quick-dialogue "关系被消耗干净了。她还坐在你面前，但已经不再跟你说真话。")
      (effect 'end-encounter 'fail)))
    (react :when (and (clock-filled? time) (not (clock-filled? intel))) :then (list
      (effect 'start-quick-dialogue "时间到了。她把最后一点话咽回去，今晚的门关上了。")
      (effect 'end-encounter 'fail))))
  :vars (append
    world-basics-vars
    (list
    (var 'topic 'past)
    (var 'intel (clock :title "情报" :desc "填满即拿到关键情报。" :initial 0 :max 8))
    (var 'relation (clock :title "关系" :desc "把话题引向情报会消耗关系；归零失败。" :initial 3 :max 6))
    (var 'time (clock :title "时间" :desc "每次休整 +1，填满前没完成即失败。" :initial 0 :max 5)))
    )
  :root (will-root))
