;; global 全局有一个警戒时钟, 填满所有人都醒了, 就会失败
;; scene1 房间, 手被捆住, 用不同的方式脱困, 填满挣脱进度钟完成脱困
;; scene2 二楼, 房屋往一楼走,有几条路, 不知道哪条才能到达, 每条路都有进度钟, 填满后揭晓, 有两条是死路, 有一条是通路, 到达大门
;; scene3 大门, 你有两个选择,第一个(地点)是进办公室,然后跟头目交谈,会有一段对话, 交谈过之后,就是和头目交谈这个选项会被替换为,这个头目被你打晕了的文本. 第二个选择(行动)是离开这里.

(include "common_clock_macros.scm")

;; ==========================================
;; 元数据与状态定义
;; ==========================================

;; 当调用 (effect 'finish 'success) 时执行
(on-success 
 (list 
  (effect 'start-quick-dialogue 
          "# 自由的滋味\n\n你推开了沉重的诊所大门，清冷的夜风瞬间灌满了你的肺部。你没有回头看那座阴森的建筑，径直消失在街道尽头的阴影中。\n\n虽然你还不知道他们为什么要抓你，但至少今晚，你活了下来。")))

;; 当调用 (effect 'finish 'fail) 时执行
(on-fail 
 (list 
  (effect 'start-quick-dialogue 
          "# 逃跑失败\n\n沉重的脚步声在走廊回荡。在你触碰到出口之前，冰冷的枪口已经抵住了你的后脑勺。\n\n“你哪儿也去不了，”头目的声音在你耳边响起，“现在的实验才刚刚开始。”\n\n黑暗再次吞噬了你的意识。")))

(state
  ;; 流程控制标志
  (escaped false)           ;; 是否已挣脱
  (path_a_revealed false)   ;; 走廊A是否揭晓
  (path_b_revealed false)   ;; 走廊B是否揭晓
  (path_c_revealed false)   ;; 楼梯间是否揭晓
  (boss_defeated false)     ;; 头目是否被打晕

  ;; 全局时钟
  (alert_clock (clock 
                :title "警戒程度" 
                :initial 0 
                :max 6 
                :persist 'encounter))
  
  ;; 场景时钟
  (挣脱束缚钟 (clock :title "挣扎进度" :initial 0 :max 4))
  (path_a_clock (clock :title "探索左侧" :initial 0 :max 2))
  (path_b_clock (clock :title "探索右侧" :initial 0 :max 2))
  (path_c_clock (clock :title "探索正前方" :initial 0 :max 2)))

;; ==========================================
;; 全局响应 (Reacts)
;; ==========================================
(reacts 
  ;; 警戒拉满，直接失败
  (react 
    :key 'react_alert_full
    :when (clock-filled? alert_clock)
    :then (list (effect 'start-quick-dialogue "警报大作！\n守卫发现了你，你被重新按倒在地……")
                (effect 'finish 'fail)))
                
  ;; 挣脱进度拉满，推进到下一个阶段
  (react 
    :key 'react_escaped
    :when (and (clock-filled? 挣脱束缚钟) (not escaped))
    :then (list (effect 'set escaped true)
                (effect 'start-quick-dialogue "你终于挣脱了束缚！\n现在必须离开这里，小心不要惊动守卫。")))
                
  ;; 二楼走廊探索揭晓
  (react 
    :key 'react_path_a
    :when (and (clock-filled? path_a_clock) (not path_a_revealed))
    :then (list (effect 'set path_a_revealed true)
                (effect 'start-quick-dialogue "你摸索到了尽头，却发现这是一条死路。")))
                
  (react 
    :key 'react_path_b
    :when (and (clock-filled? path_b_clock) (not path_b_revealed))
    :then (list (effect 'set path_b_revealed true)
                (effect 'start-quick-dialogue "尽头是一扇铁门，但被死死锁住了，根本打不开。")))
  
  (react 
    :key 'react_path_c
    :when (and (clock-filled? path_c_clock) (not path_c_revealed))
    :then (list (effect 'set path_c_revealed true)
                (effect 'start-quick-dialogue "你发现了一段隐蔽的楼梯，一直通向一楼的大门！"))))

;; ==========================================
;; 通用动作
;; ==========================================
(define rest
  (action
   :title "原地休息"
   :desc "平复呼吸，整理手牌。"
   :before (list (effect 'reset-hand))))

;; ==========================================
;; Scene 1: 房间脱困
;; ==========================================
(define scene1
  (scene
   :key 'scene_cell
   :title "牢房"
   :desc "你孤身一人被捆在椅子上。外面偶尔传来脚步声，你必须想办法脱困。"
   :show-clocks (list alert_clock 挣脱束缚钟)
   :actions (list 
             rest
             ;; 方式一：用蛮力
             (action
              :title "强行挣断"
              :desc "用纯粹的蛮力尝试撑开束缚。"
              :check (check
                      :suits (list 'force)
                      :risk 'high
                      :ok (outcome "绳子被你猛地崩开了一大段" (list (effect 'clock+ 挣脱束缚钟 2)))
                      :partial (outcome "有所松动，但弄出了声响" (list (effect 'clock+ 挣脱束缚钟 1) (effect 'clock+ alert_clock 1)))
                      :fail (outcome "不仅没挣开，还惊动了守卫" (list (effect 'health -1) (effect 'clock+ alert_clock 2)))))
             ;; 方式二：利用理智/直觉寻找利器
             (action
              :title "寻找利器割绳"
              :desc "仔细观察周围，尝试在地上摸索尖锐的碎片。"
              :check (check
                      :suits (list 'reason 'instinct)
                      :risk 'mid
                      :ok (outcome "你摸到了一块玻璃，割断了部分绳索" (list (effect 'clock+ 挣脱束缚钟 2)))
                      :partial (outcome "进展缓慢，过程有些冒险" (list (effect 'clock+ 挣脱束缚钟 1) (effect 'clock+ alert_clock 1)))
                      :fail (outcome "一无所获，还划伤了自己" (list (effect 'health -1) (effect 'clock+ alert_clock 1))))))))

;; ==========================================
;; Scene 2: 二楼探索
;; ==========================================
(define scene2
  (scene
   :key 'scene_corridor
   :title "二楼走廊"
   :desc "你溜出了房间。走廊前方有三条岔路，你不知道哪条才能通向一楼的大门。"
   :show-clocks (list alert_clock path_a_clock path_b_clock path_c_clock)
   :actions (list 
             rest
             ;; 探索路径A
             (if path_a_revealed
                 (action :title "左侧道路 (死路)" :desc "这条路已经被证实不通。" :before (list))
                 (action
                  :title "探索左侧道路"
                  :desc "借着微弱的光线往左边摸索。"
                  :check (check
                          :suits (list 'reason 'instinct)
                          :risk 'mid
                          :ok (outcome "推进顺利" (list (effect 'clock+ path_a_clock 2)))
                          :partial (outcome "缓慢前行" (list (effect 'clock+ path_a_clock 1) (effect 'clock+ alert_clock 1)))
                          :fail (outcome "不小心踢到了杂物" (list (effect 'clock+ alert_clock 2))))))
             ;; 探索路径B
             (if path_b_revealed
                 (action :title "右侧道路 (死路)" :desc "这边的门被锁死了。" :before (list))
                 (action
                  :title "探索右侧道路"
                  :desc "小心翼翼地走向右侧的阴影处。"
                  :check (check
                          :suits (list 'reason 'instinct)
                          :risk 'mid
                          :ok (outcome "推进顺利" (list (effect 'clock+ path_b_clock 2)))
                          :partial (outcome "缓慢前行" (list (effect 'clock+ path_b_clock 1) (effect 'clock+ alert_clock 1)))
                          :fail (outcome "引起了守卫的怀疑" (list (effect 'clock+ alert_clock 2))))))
             ;; 探索路径C
             (if path_c_revealed
                 (action :title "正前道路 (通路)" :desc "这里通向一楼。" :before (list))
                 (action
                  :title "探索正前道路"
                  :desc "硬着头皮径直往前走。"
                  :check (check
                          :suits (list 'reason 'instinct)
                          :risk 'mid
                          :ok (outcome "推进顺利" (list (effect 'clock+ path_c_clock 2)))
                          :partial (outcome "缓慢前行" (list (effect 'clock+ path_c_clock 1) (effect 'clock+ alert_clock 1)))
                          :fail (outcome "差点撞上巡逻人员" (list (effect 'clock+ alert_clock 2)))))))))

;; ==========================================
;; Scene 3: 一楼大门
;; ==========================================
(define scene3
  (scene
   :key 'scene_exit
   :title "一楼大门"
   :desc "你顺着楼梯来到了一楼。自由近在咫尺，但大门旁边就是头目的办公室。"
   :show-clocks (list alert_clock)
   :actions (list 
             rest
             ;; 选择1：处理头目 (地点/对话互动)
             (if boss_defeated
                 (action
                  :title "昏迷的头目"
                  :desc "头目倒在办公室的地板上，不省人事，不会再造成威胁了。"
                  :before (list)) ; 只有描述，不执行效果
                 (action
                  :title "进入办公室"
                  :desc "你决定在离开前跟头目做个了断。"
                  :before (list 
                           (effect 'start-quick-dialogue "# 办公室\n头目：你怎么跑出来的？！\n\n（你没有和他废话，三拳两脚将其击倒在地，打晕了过去。）")
                           (effect 'set boss_defeated true))))
             ;; 选择2：直接离开 (行动)
             (action
              :title "离开这里"
              :desc "直接推开大门，重获自由！"
              :before (list (effect 'finish 'success))))))

;; ==========================================
;; 场景调度逻辑
;; ==========================================
(cond
  ((not escaped) scene1)           ;; 还没挣脱时，渲染牢房
  ((not path_c_revealed) scene2)   ;; 还没找到通路时，渲染二楼走廊
  (else scene3))                   ;; 找到通路后，前往大门
