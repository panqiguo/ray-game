(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")

(define-scene infiltration
  (scene
    :title "望月旅馆 · 潜入"
    :desc "老板不让你进 302。后门有锁，楼梯有响声，走廊尽头有人看报纸，但报纸半小时没翻过页。"
    :show-clocks (list access noise clue)
    :actions (list
      (action
        :title "绕到后门撬锁"
        :desc "后门比正门诚实，至少它不会问你有没有登记。"
        :check (check
          :suits (list 逻辑)
          :risk 'mid
          :ok (outcome "锁开得干净，后门没有呻吟。" (list (effect 'clock+ access 2)))
          :partial (outcome "门开了，合页却叫了一声。" (list (effect 'clock+ access 1) (effect 'clock+ noise 1)))
          :fail (outcome "锁芯卡住，楼上有人停下脚步。" (list (effect 'clock+ noise 1)))))
      (action
        :title "装成送货工"
        :desc "托盘、旧围裙和一张不看人的脸。有时候身份就是一套动作。"
        :check (check
          :suits (list 感知)
          :risk 'mid
          :ok (outcome "你从老板眼皮底下走了过去。" (list (effect 'clock+ access 2)))
          :partial (outcome "你混进去了，但有人记住了你的背影。" (list (effect 'clock+ access 1) (effect 'clock+ noise 1)))
          :fail (outcome "老板抬头看了你一眼，太久。" (list (effect 'clock+ noise 1)))))
      (when (clock-at-least-half? access)
        (action
          :title "搜查 302 房间"
          :desc "房间没有被清空。梳妆台、床缝和窗台背后都在等一只耐心的手。"
          :check (check
            :suits (list 感知)
            :risk 'mid
            :ok (outcome "你找到了旅馆后门的暗号和一张公寓收据。" (list (effect 'clock+ clue 2)))
            :partial (outcome "你找到一张收据，但走廊的脚步逼近。" (list (effect 'clock+ clue 1) (effect 'clock+ noise 1)))
            :fail (outcome "房间太干净，干净得像被人重新摆过。" (list (effect 'clock+ noise 1))))))
      (when (> (clock-value noise) 0)
        (action
          :title "压低动静"
          :desc "你停下来，等走廊的注意力从门缝边移开。"
          :check (check
            :suits (list 意志)
            :risk 'low
            :ok (outcome "走廊重新安静。" (list (effect 'clock- noise 1)))
            :partial (outcome "你等到了空档，但时间被耗掉。" (list (effect 'clock- noise 1) (effect 'add energy -1)))
            :fail (outcome "越安静，越像有人在听。" (list (effect 'clock+ noise 1)))))))))

(content
  :meta (meta :key '潜入旅馆 :title "潜入旅馆" :desc "进入望月旅馆 302，找到薇拉离开后的下一处线索。")
  :on-success (list
    (effect 'set 'hotel_infiltrated true))
  :on-fail (list
    (effect 'add 'police_relation -1)
    (effect 'add 'energy -2))
  :reacts (reacts
    (react :when (clock-filled? clue) :then (list (effect 'end-encounter 'success)))
    (react :when (>= (clock-value noise) 4) :then (list (effect 'end-encounter 'fail))))
  :state (state
    (access (clock :title "进入路线" :initial 0 :max 3))
    (noise (clock :title "动静" :initial 0 :max 4))
    (clue (clock :title "房间线索" :initial 0 :max 3)))
  :root (infiltration))
