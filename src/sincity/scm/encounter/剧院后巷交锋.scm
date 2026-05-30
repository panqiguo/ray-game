(include "../enum-symbols.scm")
(include "../common_world_bindings.scm")

(define-fragment catch-shadow
  (action
    :title "追上那个戴面具的人"
    :desc "他跑得很快，但他以为剧院后巷比你更熟。现在只差几步。"
    :effects (list
      (effect 'end-encounter 'success))))

(content
  :meta (meta :key '剧院后巷交锋 :title "剧院后巷交锋" :desc "追上送信后的可疑人影。")
  :on-success (list
    (effect 'set 'nightingale_first_confrontation_done true)
    (effect 'add 'health -1)
    (effect 'add 'energy -2))
  :on-fail (list
    (effect 'set 'nightingale_first_confrontation_done true)
    (effect 'add 'health -1)
    (effect 'add 'energy -2))
  :vars (append
    world-health-vars
    world-energy-vars)
  :root
  (scene
    :title "剧院后巷"
    :desc "（以后这里会播放一段追逐动画：雨水、灯箱、被撞开的侧门。你追上他，手指勾住面具边缘。下一秒，背后传来脚步。）"
    :actions (list
      (catch-shadow))))
