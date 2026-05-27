(include "../enum-symbols.scm")
(include "../common_world_bindings.scm")

(define (favor)
  (scene
    :title "黑市 · 证件人情"
    :desc "假证件不是从柜台上买来的。接头人把你带到一条潮湿后巷，要你替他拿回一本账册。账册在一个胆子很小、手里却有刀的人那里。"
    :actions (list
      (action
        :title "压住对方，把账册拿回来"
        :desc "你不用把事情闹大，只要让他明白这本账册不该继续留在他手里。"
        :check (check
          :suits (list 意志)
          :risk 'mid
          :ok (outcome "他退得很快，账册也交得很快。" (list (effect 'end-encounter 'success)))
          :partial (outcome "你拿到了账册，但手背被划开一道口子。" (list (effect 'add health -1) (effect 'end-encounter 'success)))
          :fail (outcome "他从后门跑了。接头人不会为失败的人做证件。" (list (effect 'add energy -2) (effect 'end-encounter 'fail)))))
      (action
        :title "绕到后门堵他"
        :desc "你试着不靠拳头解决这件事。后门窄，脚步声会先出卖人。"
        :check (check
          :suits (list 感知)
          :risk 'mid
          :ok (outcome "你堵住了他，也堵住了他的侥幸。" (list (effect 'end-encounter 'success)))
          :partial (outcome "你追上了他，但这一跑耗掉不少力气。" (list (effect 'add energy -1) (effect 'end-encounter 'success)))
          :fail (outcome "你慢了一步，只听见铁门在巷尾合上。" (list (effect 'add energy -2) (effect 'end-encounter 'fail))))))))

(content
  :meta (meta :key '黑市证件人情 :title "黑市证件人情" :desc "替黑市接头人处理一件棘手事，换一套假证件。")
  ;; These quoted keys are world facts written back to the city after success.
  :on-success (list
    (effect 'set 'fake_id_job_done true)
    (effect 'add 'fake_id 1))
  :on-fail (list
    (effect 'set 'fake_id_job_failed true))
  :vars (append
    world-health-vars
    world-energy-vars
    (list
    (var 'phase 'favor))
    )
  :root (favor))
