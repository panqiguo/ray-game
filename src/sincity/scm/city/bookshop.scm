;; EXPORT bookshop-vars, bookshop-reacts, 书店
;; IMPORT helper.scm, common_clock_macros.scm (included by city_1.scm)

(define book-knowledge-text
  "# 读完：《县城账簿与谎言》\n\n# speaker: 科尔\n数字不会说真话，但它们也不擅长撒谎。读完这本书后，我更知道该从哪里看起。")

(define book-sense-text
  "# 读完：《街口观察法》\n\n# speaker: 科尔\n人们总以为自己藏得很好。其实鞋尖、肩膀和停顿，比嘴诚实多了。")

(define book-force-text
  "# 读完：《疼痛之后》\n\n# speaker: 科尔\n有些书不教你赢，只教你不要太快倒下。")

(define (make-book-action title desc clock suit)
  (action
    :title title
    :desc desc
    :check (check
      :suit suit
      :risk 'low
      :ok (outcome (list (effect 'clock+ clock 2)))
      :partial (outcome (list (effect 'clock+ clock 1) (effect 'add pressure 1)))
      :fail (outcome (list (effect 'add pressure 1))))))

(define bookshop-vars
  (list
    (var 'knowledge_book (clock :title "《县城账簿与谎言》" :desc "读完后知识 +1。" :initial 0 :max 3))
    (var 'sense_book (clock :title "《街口观察法》" :desc "读完后敏锐 +1。" :initial 0 :max 3))
    (var 'force_book (clock :title "《疼痛之后》" :desc "读完后暴力 +1。" :initial 0 :max 3))
    (var 'knowledge_book_done false)
    (var 'sense_book_done false)
    (var 'force_book_done false)
    (var 'bookshop_entered_today false)))

(define bookshop-reacts
  (list
    (react
      :when (and (clock-filled? knowledge_book) (not knowledge_book_done))
      :then (list
        (effect 'set knowledge_book_done true)
        (effect 'upgrade-spirit-value 'knowledge 1)
        (effect 'start-quick-dialogue book-knowledge-text)))
    (react
      :when (and (clock-filled? sense_book) (not sense_book_done))
      :then (list
        (effect 'set sense_book_done true)
        (effect 'upgrade-spirit-value 'sense 1)
        (effect 'start-quick-dialogue book-sense-text)))
    (react
      :when (and (clock-filled? force_book) (not force_book_done))
      :then (list
        (effect 'set force_book_done true)
        (effect 'upgrade-spirit-value 'force 1)
        (effect 'start-quick-dialogue book-force-text)))))

(define (书店)
  (location
    :title "书店"
    :desc "书店很小，座位更少。老板不喜欢闲逛的人，但喜欢付过钱后安静的人。"
    :position '(860 280)
    :show-clocks (list knowledge_book sense_book force_book)
    :actions (list
      (when (not bookshop_entered_today)
        (action
          :title "付今天的入场费"
          :desc "五块钱买一张当天的座位。今天之后，你可以在这里自由读书，直到回去睡觉。"
          :conditions (list (field-at-least 'money 5 "需要 5 元"))
          :inputs (list (item 'money 5 "入场费"))
          :effects (list (effect 'set bookshop_entered_today true))))
      (when (and bookshop_entered_today (not knowledge_book_done))
        (make-book-action "读《县城账簿与谎言》" "一本讲账本、公司壳和人情债的旧书。读完会提升知识。" knowledge_book 知识))
      (when (and bookshop_entered_today (not sense_book_done))
        (make-book-action "读《街口观察法》" "一本写给巡警的教材，后来流到旧书架上。读完会提升敏锐。" sense_book 敏锐))
      (when (and bookshop_entered_today (not force_book_done))
        (make-book-action "读《疼痛之后》" "关于戒断、疼痛和自我约束。读完会提升暴力。" force_book 暴力)))))
