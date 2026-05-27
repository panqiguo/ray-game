(include "../enum-symbols.scm")

(define (room_search)
  (scene
    :title "望月旅馆 · 302 房间"
    :desc "房间里有旧肥皂、潮湿地毯和长时间没人开窗的味道。薇拉已经离开，但这里没有被清空。有人付了钱，让老板把房间保留下来。"
    :actions (list
      (action
        :title "快速搜查房间"
        :desc "你没有时间把每一寸都翻开，只能先抓住最明显的东西：垃圾桶里的纸条、床底的小布袋，还有窗台背面的刻痕。"
        :effects (list
          (effect 'end-encounter 'success))))))

(content
  :meta (meta :key '望月旅馆搜寻 :title "望月旅馆搜寻" :desc "进入薇拉住过的 302 房间，带走她留下的痕迹。")
  ;; These quoted keys are world facts written back to the city after success.
  :on-success (list
    (effect 'set 'note_street_time true)
    (effect 'set 'pills_found true)
    (effect 'set 'red_room_clipping true)
    (effect 'set 'mb_knows true)
    (effect 'set 'corridor_man_seen true)
    (effect 'set 'hotel_search_done true))
  :state (list
    (var 'phase 'search))
  :root (room_search))
