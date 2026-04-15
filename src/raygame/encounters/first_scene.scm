(include "common_clock_macros.scm")

(meta :key 'first_scene :title "逃出这里" :desc "")

(state
  (leave false))

(scene
  :key '牢笼
  :title "牢笼"
  :desc ""
  :actions (list (action
      :title "走出去"
      :desc "就这样走了出去"
      :check (check
        :suits (list 'force)
        :risk 'low
        :ok (outcome "win" (list (effect 'finish 'success)))
        :partial (outcome "partial" (list (effect 'finish 'fail)))
        :fail (outcome "fail" (list (effect 'finish 'fail)))))))
