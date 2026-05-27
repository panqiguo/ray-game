;; Bookshop growth slice.
;; Exports: bookshop-state, bookshop-reacts, 书店
;; Depends on: helper.scm, common_clock_macros.scm

(define book-logic-text
  "# 读完：《县城账簿与谎言》\n\n# speaker: 科尔\n数字不会说真话，但它们也不擅长撒谎。读完这本书后，我更知道该从哪里看起。")

(define book-perception-text
  "# 读完：《街口观察法》\n\n# speaker: 科尔\n人们总以为自己藏得很好。其实鞋尖、肩膀和停顿，比嘴诚实多了。")

(define book-willpower-text
  "# 读完：《疼痛之后》\n\n# speaker: 科尔\n有些书不教你赢，只教你不要太快倒下。")

(define (make-book-action title desc clock suit)
  (action
    :title title
    :desc desc
    :check (check
      :suits (list suit)
      :risk 'low
      :ok (outcome (list (effect 'clock+ clock 2)))
      :partial (outcome (list (effect 'clock+ clock 1) (effect 'add energy -1)))
      :fail (outcome (list (effect 'add energy -1))))))

(define bookshop-state
  (state-fragment
    (logic_book (clock :title "《县城账簿与谎言》" :desc "读完后逻辑 +1。" :initial 0 :max 3))
    (perception_book (clock :title "《街口观察法》" :desc "读完后感知 +1。" :initial 0 :max 3))
    (willpower_book (clock :title "《疼痛之后》" :desc "读完后意志 +1。" :initial 0 :max 3))
    (logic_book_done false)
    (perception_book_done false)
    (willpower_book_done false)
    (bookshop_entered_today false)))

(define bookshop-reacts
  (reacts
    (react
      :when (and (clock-filled? logic_book) (not logic_book_done))
      :then (list
        (effect 'set logic_book_done true)
        (effect 'upgrade-spirit-value 'logic 1)
        (effect 'start-quick-dialogue book-logic-text)))
    (react
      :when (and (clock-filled? perception_book) (not perception_book_done))
      :then (list
        (effect 'set perception_book_done true)
        (effect 'upgrade-spirit-value 'perception 1)
        (effect 'start-quick-dialogue book-perception-text)))
    (react
      :when (and (clock-filled? willpower_book) (not willpower_book_done))
      :then (list
        (effect 'set willpower_book_done true)
        (effect 'upgrade-spirit-value 'willpower 1)
        (effect 'start-quick-dialogue book-willpower-text)))))

(define (书店)
  (node
    :title "书店"
    :desc "书店很小，座位更少。老板不喜欢闲逛的人，但喜欢付过钱后安静的人。"
    :position '(860 280)
    :show-clocks (list logic_book perception_book willpower_book)
    :actions (list
      (when (not bookshop_entered_today)
        (action
          :title "付今天的入场费"
          :desc "五块钱买一张当天的座位。今天之后，你可以在这里自由读书，直到回去睡觉。"
          :conditions (list (field-at-least 'money 5 "需要 5 元"))
          :inputs (list (item 'money 5 "入场费"))
          :effects (list (effect 'set bookshop_entered_today true))))
      (when (and bookshop_entered_today (not logic_book_done))
        (make-book-action "读《县城账簿与谎言》" "一本讲账本、公司壳和人情债的旧书。读完会提升逻辑。" logic_book 逻辑))
      (when (and bookshop_entered_today (not perception_book_done))
        (make-book-action "读《街口观察法》" "一本写给巡警的教材，后来流到旧书架上。读完会提升感知。" perception_book 感知))
      (when (and bookshop_entered_today (not willpower_book_done))
        (make-book-action "读《疼痛之后》" "关于戒断、疼痛和自我约束。读完会提升意志。" willpower_book 意志)))))
