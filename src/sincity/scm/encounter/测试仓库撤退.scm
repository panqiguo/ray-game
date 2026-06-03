;; 这个情景感觉是对的, 不断涌来的危机, 目标之间的切换

;; 在这个dsl上我们花费了太多力气了, 他总是中断我们测试游戏的循环.

(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define make-enemy
  (lambda (kind)
    (object
      (kind kind)
      (life (clock :title "血量" :desc "填满即击倒。" :initial 0 :max 3))
      (attack (clock :title "攻击" :desc "填满后敌人行动。" :initial 0 :max (if (= kind 'gun) 3 2))))))

(define enemy-kind
  (lambda (enemy)
    (get enemy 'kind)))

(define enemy-life
  (lambda (enemy)
    (get enemy 'life)))

(define enemy-attack
  (lambda (enemy)
    (get enemy 'attack)))

(define enemy-title
  (lambda (enemy)
    (if (= (enemy-kind enemy) 'knife) "持刀者" "枪手")))

(define enemy-desc
  (lambda (enemy)
    (if (= (enemy-kind enemy) 'knife)
      "他贴得很近，刀尖总在视野边缘闪。攻击很快，但不算耐打。"
      "他躲在货架后面换位置。攻击慢一些，但枪声会压住你的撤退动作。")))

(define enemy-tick
  (lambda (enemy)
    (update enemy
      (attack (clock-shift (enemy-attack enemy) 1)))))

(define enemy-hit
  (lambda (enemy amount)
    (update enemy
      (life (clock-shift (enemy-life enemy) amount))
      (attack (clock-reset (enemy-attack enemy))))))

(define enemy-alive?
  (lambda (enemy)
    (not (clock-filled? (enemy-life enemy)))))

(define enemy-dead?
  (lambda (enemy)
    (clock-filled? (enemy-life enemy))))

(define knife-ready?
  (lambda (enemy)
    (and (= (enemy-kind enemy) 'knife) (clock-filled? (enemy-attack enemy)))))

(define gun-ready?
  (lambda (enemy)
    (and (= (enemy-kind enemy) 'gun) (clock-filled? (enemy-attack enemy)))))

(define reset-ready-knife
  (lambda (enemy)
    (if (knife-ready? enemy)
      (update enemy (attack (clock-reset (enemy-attack enemy))))
      enemy)))

(define reset-ready-gun
  (lambda (enemy)
    (if (gun-ready? enemy)
      (update enemy (attack (clock-reset (enemy-attack enemy))))
      enemy)))

(define add-enemy
  (lambda (items kind)
    (if (< (length items) 4)
      (append items (list (make-enemy kind)))
      items)))

(define hit-this-enemy
  (lambda (target amount)
    (effect-expr
      (set! enemies
        (map enemies
          (lambda (enemy)
            (if (= enemy target)
              (enemy-hit enemy amount)
              enemy)))))))

(define enemy-scene
  (lambda (enemy)
    (scene
      :title (enemy-title enemy)
      :desc (enemy-desc enemy)
      :show-clocks (list (enemy-life enemy) (enemy-attack enemy))
      :actions (list
        (action
          :title "压制敌人"
          :desc "先打断他的攻击节奏，不急着把人彻底打倒。"
          :check (check
            :suit 暴力
            :risk 'mid
            :ok (outcome (list (hit-this-enemy enemy 1)) "你把他逼回货架后，攻击节奏被打断。")
            :partial (outcome (list (hit-this-enemy enemy 1) (effect 'add energy -1)) "你挡住这一波，自己也被拖住。")
            :fail (outcome (list) "你没压住他，反而吃了一下。")))
        (action
          :title "冒险击倒"
          :desc "不管撤退节奏，直接把这个威胁从场上清掉。"
          :check (check
            :suit 敏锐
            :risk 'high
            :ok (outcome (list (hit-this-enemy enemy 2)) "你狠狠干中要害，他快撑不住了。")
            :partial (outcome (list (hit-this-enemy enemy 1) (effect 'add energy -1)) "你打中了，也被他拖住。")
            :fail (outcome (list (effect 'add energy -1)) "你扑空了，他的反击立刻追上来。")))))))

(define (exit-scene)
  (scene
    :title "被堵塞的出口"
    :desc (if (some enemies (lambda (enemy) (= (enemy-kind enemy) 'gun)))
      "枪手压住了出口。你可以硬推，但风险会变得难看。"
      "出口就在前面，只要把最后几层障碍推开。")
    :show-clocks (list exit)
    :actions (list
      (action
        :title "冲开出口"
        :desc "越过碎玻璃和铁门，把逃生路线硬推出去。"
        :check (check
          :suit 敏锐
          :risk (if (some enemies (lambda (enemy) (= (enemy-kind enemy) 'gun))) 'high 'mid)
          :ok (outcome (list (effect 'clock+ exit 2)) "出口被你撞开一截。")
          :partial (outcome (list (effect 'clock+ exit 1) (effect 'add energy -1)) "你推进了，但枪声和碎片一起追上来。")
          :fail (outcome (list (effect 'add energy -1)) "你被压回仓库深处。"))))))

(define (warehouse-root)
  (scene
    :title "仓库撤退"
    :desc "敌人会一波波涌进来。你不可能把所有人都处理干净，关键是判断什么时候该忍伤推进。"
    :show-clocks (list spawn exit)
    :children (append
      (list (exit-scene))
      (map enemies (lambda (enemy) (enemy-scene enemy))))))

(content
  :meta (meta :key '测试仓库撤退 :title "测试仓库撤退" :desc "测试持续涌现敌人与撤退进度的分诊。")
  :on-success (list (effect 'set 'test_warehouse_escape_done true))
  :on-fail (list (effect 'set 'test_warehouse_escape_failed true) (effect 'add health -1))
  :on-cycle-start (list
    (effect 'clock+ spawn 1)
    (effect-expr
      (set! enemies (map enemies enemy-tick))))
  :reacts (list
    (react
      :when (clock-filled? exit)
      :then (list (effect 'end-encounter 'success)))
    (react
      :when (clock-filled? spawn)
      :then (list
        (effect-reset-clock spawn)
        (effect-expr
          (if (< (length enemies) 4)
            (begin
              (action-log! "敌人浪潮：又有人冲进仓库。")
              (set! enemies (add-enemy enemies 'knife)))
            (begin
              (action-log! "敌人浪潮：仓库里已经挤满了人，没有再增加人。")
              )))))
    (react
      :when (some enemies enemy-dead?)
      :then (list
        (effect-expr
          (begin
            (action-log! "敌人被击倒。")
            (set! enemies (filter enemies enemy-alive?))))))
    (react
      :when (some enemies knife-ready?)
      :then (list
        (effect 'add health -1)
        (effect-expr
          (begin
            (action-log! "敌人行动：持刀者扑上来，健康 -1。")
            (set! enemies (map enemies reset-ready-knife))))))
    (react
      :when (some enemies gun-ready?)
      :then (list
        (effect 'add health -2)
        (effect-expr
          (begin
            (action-log! "敌人行动：枪手开火，健康 -2。")
            (set! enemies (map enemies reset-ready-gun)))))))
  :vars (append
    world-basics-vars
    (list
    (var 'spawn (clock :title "敌人涌入" :desc "每 3 cycle 随机生成一名敌人，最多四名。" :initial 0 :max 3))
    (var 'exit (clock :title "出口" :initial 0 :max 12))
    (var 'enemies (list (make-enemy 'knife) (make-enemy 'gun))))
    )
  :root (warehouse-root))
