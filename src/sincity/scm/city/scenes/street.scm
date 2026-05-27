;; Scene: 老街.
;; Exports: 老街
;;
;; Dependency note:
;; - Uses `exploitation-incident-action` from 富人飞地 scene when an incident
;;   lands in old street. This is a scene-level cross dependency until the DSL
;;   grows explicit provide/require.

(define-node 老街
  (node
    :desc "旧铺面、窄楼梯、晾衣绳和熟人的眼神。老街没有明确入口，但你总能从这里找到一点活路。"
    :position '(450 520)
    :show-clocks (list
      (when (and hotel_infiltrated (not vera_apartment_found)) vera_follow_progress)
      (when (and exploitation_incident_active (= exploitation_incident_location 'street)) exploitation_incident_timer)
      (when (and exploitation_incident_active (= exploitation_incident_location 'street)) exploitation_incident_resolution))
    :actions (list
      (exploitation-incident-action 'street)
      (when (and vera_thread_unlocked (not vera_street_checked))
        (action
          :title "去老街修鞋铺问薇拉的消息"
          :desc "三个地方里，只有这里的人真见过她最近的脸色。"
          :effects (list
            (effect 'set vera_street_checked true)
            (effect 'start-quick-dialogue vera-street-shoemaker-text))))
      (when (and hotel_infiltrated (not vera_apartment_found))
        (make-investigate-action
          "跟踪得到的线索"
          "不要靠太近，也不要跟丢。真正的地址藏在他以为自己安全的时候。"
          vera_follow_progress
          感知)))))
