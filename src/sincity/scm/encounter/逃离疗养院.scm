;; global 全局有一个警戒时钟, 填满所有人都醒了, 就会失败
;; scene1 拘禁室, 手被皮带捆住, 用不同的方式脱困, 填满挣脱进度钟完成脱困
;; scene2 二楼, 房屋往一楼走,有几条路, 不知道哪条才能到达, 每条路都有进度钟, 填满后揭晓, 有两条是死路, 有一条是通路, 到达大门
;; scene3 大门, 你有两个选择,第一个(地点)是进桑德堡医生的办公室,然后跟头目交谈,交谈过之后,这个选项会被替换为桑德堡被打晕的文本. 第二个选择(行动)是离开这里.
(include "../helper.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")


(define react-once-until
  (lambda (var effect-ir)
    (react
     :when (not var)
     :then (list
            (effect 'set var true)
            effect-ir))))


;; ==========================================
;; 通用动作
;; ==========================================
(define-fragment rest
  (action
   :title "原地喘口气"
   :desc "靠在墙上深呼吸，试图把肺里的药味和眩晕感排出去。"
   :always (list
            (effect 'advance-cycle)
            (effect 'clock+ alert_clock 1))))

(define make_knowledge_path_action
  (lambda (title desc progress-clock ok-text partial-text fail-text)
    (action
     :title title
     :desc desc
     :check (check
              :suit 知识
              :risk 'mid
              :ok (outcome ok-text (list (effect 'clock+ progress-clock 1)))
              :partial (outcome partial-text (list (effect 'clock+ progress-clock 1) (effect 'clock+ alert_clock 1)))
              :fail (outcome fail-text (list (effect 'clock+ alert_clock 1)))))))


(define make_sense_path_action
  (lambda (title desc progress-clock ok-text partial-text fail-text)
    (action
     :title title
     :desc desc
     :check (check
              :suit 敏锐
              :risk 'mid
              :ok (outcome ok-text (list (effect 'clock+ progress-clock 1)))
              :partial (outcome partial-text (list (effect 'clock+ progress-clock 1) (effect 'clock+ alert_clock 1)))
              :fail (outcome fail-text (list (effect 'clock+ alert_clock 1)))))))


(define make_force_path_action
  (lambda (title desc progress-clock ok-text partial-text fail-text)
    (action
     :title title
     :desc desc
     :check (check
              :suit 暴力
              :risk 'high
              :ok (outcome ok-text (list (effect 'clock+ progress-clock 2)))
              :partial (outcome partial-text (list (effect 'clock+ progress-clock 1) (effect 'clock+ alert_clock 2)))
              :fail (outcome fail-text (list (effect 'clock+ alert_clock 3)))))))


;; ==========================================
;; Scene 1: 房间脱困
;; ==========================================
(define (location1)
  (location
   :title "拘禁室"
   :desc "我的脑袋像塞满了浸水的棉花，双手被皮带死死捆在椅子上。门外偶尔传来胶底鞋走过的声音。我得尽快弄断这些束缚。"
   :show-clocks (list alert_clock 挣脱束缚钟)
   :actions (list
             (rest)
             ;; 方式一：用蛮力
             (action
              :title "暴力挣脱"
              :desc "咬紧牙关，不顾手腕被勒出血痕，拼命对抗那些劣质皮带。"
              :check (check
                       :suit 暴力
                       :risk 'high
                       :ok (outcome "粗糙的皮带被你硬生生崩开了一个扣子" (list (effect 'clock+ 挣脱束缚钟 2)))
                      :partial (outcome "你的手腕磨破了皮，铁椅摩擦地板弄出了点声响" (list (effect 'clock+ 挣脱束缚钟 1) (effect 'clock+ alert_clock 1)))
                      :fail (outcome "该死，皮带没断，床腿摩擦地板的声音反而引起了外面的注意" (list (effect 'add health -1) (effect 'clock+ alert_clock 2)))))
             ;; 方式二：靠感知寻找可用边角
             (action
              :title "寻找尖锐物割裂"
              :desc "试着转动酸痛的脖子，寻找铁皮边缘或碎玻璃去磨蹭皮带。"
              :check (check
                       :suit 敏锐
                       :risk 'mid
                       :ok (outcome "你利用椅子底部的锋利铁片，成功割裂了部分皮带" (list (effect 'clock+ 挣脱束缚钟 2)))
                      :partial (outcome "进展缓慢，你的手指被铁片划破了" (list (effect 'clock+ 挣脱束缚钟 1) (effect 'clock+ alert_clock 1)))
                      :fail (outcome "你不仅没割开皮带，反而打翻了旁边的点滴架" (list (effect 'add health -1) (effect 'clock+ alert_clock 1)))))
             ;; 方式三：靠逻辑拆解搭扣
             (action
              :title "分析搭扣结构"
              :desc "你盯住皮带扣和受力点，尝试用最小动作把它们一段段松开。"
              :check (check
                       :suit 知识
                       :risk 'mid
                       :ok (outcome "你抓到搭扣的薄弱点，连续松开了两段固定带" (list (effect 'clock+ 挣脱束缚钟 2)))
                      :partial (outcome "你拆开了一处受力点，但金属碰撞声让你心里一紧" (list (effect 'clock+ 挣脱束缚钟 1) (effect 'clock+ alert_clock 1)))
                      :fail (outcome "你判断错了方向，搭扣卡死，还发出清脆的金属声" (list (effect 'clock+ alert_clock 1))))))))

;; ==========================================
;; Scene 2: 二楼探索
;; ==========================================
(define (location2)
  (location
   :title "疗养院走廊"
   :desc "你跌跌撞撞地溜出病房。走廊里的灯光昏暗得像劣质威士忌。前方有三条岔路，桑德堡医生的狗腿子随时会巡逻过来。"
   :show-clocks (list alert_clock)
   :actions (list (rest))
   :children (list
              ;; 探索路径A
              (location
               :title "左侧阴影"
               :desc (if path_a_revealed
                         "这是一条死路，只有监护室。"
                         "左侧的阴影里似乎有一条狭长的通道。")
               :show-clocks (list 左侧探索进度 alert_clock)
               :actions (list
                         (if path_a_revealed
                             (action :title "左侧道路 (死路) " :desc "这条路已经被证实不通。" :always (list))
                            (make_knowledge_path_action
                             "观察巡逻节奏"
                              "先听清巡逻脚步和停顿，再按节奏推进。"
                              左侧探索进度
                              "你抓到巡逻空档，稳稳推进到了更深处。"
                              "你判断得还算准，但转身时还是碰到了走廊角落的扫帚。"
                              "你算错了一个转角节奏，黑暗里立刻回荡起一声闷响。"))
                         (when (not path_a_revealed)
                            (make_sense_path_action
                             "像猫一样潜行"
                            "贴着墙根挪步，确保自己的皮鞋没踩进什么会响的东西里。"
                            左侧探索进度
                            "你借着夜色安静地摸到了更深处。"
                            "你虽然放轻了动作，但还是碰翻了走廊角落的扫帚。"
                            "你在黑暗里踩偏了一步，走廊里立刻回荡起一声空洞的闷响。"))
                         (when (not path_a_revealed)
                            (make_force_path_action
                             "大胆硬闯"
                            "趁还没人露面，咬牙一口气把左侧这段路抢过去。"
                            左侧探索进度
                            "你几乎是贴着黑影一口气冲到了尽头。"
                            "你冲得太急，沉重的脚步声在墙面间弹了两下。"
                            "你撞翻了堆在一旁的金属医疗车，瓶瓶罐罐碎了一地。"))))
              ;; 探索路径B
              (location
               :title "右侧深处"
               :desc (if path_b_revealed
                         "这条路已经被证实被死死锁住了。"
                         "右侧的通道尽头似乎隐匿着一扇门。")
               :show-clocks (list 右侧探索进度 alert_clock)
               :actions (list
                         (if path_b_revealed
                             (action :title "右侧道路 (死路) " :desc "这边的门被挂锁锁死了。" :always (list))
                              (make_knowledge_path_action
                               "先判路线再推进"
                              "你停下脚步，先判断锁门位置与遮挡，再择机前压。"
                              右侧探索进度
                              "你借着墙面分区稳稳推进了一段距离。"
                              "你路线选得不错，但风衣下摆还是带倒了墙边的铁盘。"
                              "你对地形判断失误，鞋底在光滑瓷砖上擦出刺耳响声。"))
                         (when (not path_b_revealed)
                            (make_sense_path_action
                             "谨慎摸索"
                            "先停下脚步听听动静，再顺着右边的黑影慢慢蹭过去。"
                            右侧探索进度
                            "你像个幽灵般推进了一段距离。"
                            "你靠得太近，风衣的下摆带倒了墙边的一个铁盘。"
                            "你还没摸清地形，皮鞋在光滑的瓷砖上打滑，发出了刺耳的摩擦声。"))
                         (when (not path_b_revealed)
                            (make_force_path_action
                             "迅速逼近"
                            "不再磨蹭，靠侦探的敏捷把这段路先占下来。"
                            右侧探索进度
                            "你踩着节奏一口气冲到了门边。"
                            "你是冲到了尽头，但粗重的喘息声可能已经暴露了你。"
                            "你扑得太快，整个人重重地撞在了走廊的木墙板上。"))))
              ;; 探索路径C
              (location
               :title "正前方通道"
               :desc (if path_c_revealed
                         "这道楼梯通向一楼的大门。"
                         "正前方有一条看似通向楼梯的宽阔通道。")
               :show-clocks (list 前方探索进度 alert_clock)
               :actions (list
                         (if path_c_revealed
                             (action :title "正前道路 (通路) " :desc "这条路能通向自由。" :always (list))
                              (make_knowledge_path_action
                               "推演视线盲区"
                              "你先判断拐角监视死角，再沿着盲区推进。"
                              前方探索进度
                              "你抓住盲区窗口，稳稳向前推进了一截。"
                              "你路线是对的，但鞋底还是在地板上拖出了沙沙声。"
                              "你推演慢了一拍，差点和拐角抽烟的打手迎面撞上。"))
                         (when (not path_c_revealed)
                            (make_sense_path_action
                             "借视野死角潜伏"
                            "压低身体，借着走廊立柱的死角一点点逼近前方。"
                            前方探索进度
                            "你稳稳地向前推进了一截，连只老鼠都没惊动。"
                            "你虽然没暴露，但鞋底还是在地板上拖出了沙沙声。"
                            "你差点和拐角处抽烟的打手撞个正着，只能猛地退回阴影里。"))
                         (when (not path_c_revealed)
                            (make_force_path_action
                             "快步穿插"
                            "趁走廊现在还空着，直接从正前方大步走过去。"
                            前方探索进度
                            "你几步就抢到了通道深处的楼梯口。"
                            "你冲过去了，但外套刮到了墙壁，弄出了不小的响动。"
                            "你冲得太猛，拐角那头的打手立刻警觉地转过身来拔枪。")))))))

;; ==========================================
;; Scene 3: 一楼大门
;; ==========================================
(define (location3)
  (location
   :title "疗养院一楼大厅"
   :desc "你顺着楼梯摸到了一楼。大门就在不远处，外面的洛杉矶夜景正向你招手。但在门旁边，桑德堡医生的办公室亮着灯，那个老狐狸肯定坐在里面。"
   :show-clocks (list alert_clock)
   :actions (list
             ;; 选择1：处理头目 (地点/对话互动)
             (if boss_defeated
                 (action
                  :title "昏迷的桑德堡医生"
                  :desc "桑德堡医生现在正四仰八叉地躺在波斯地毯上做着美梦，脸上还多了一块漂亮的淤青。他暂时没法再给人开毒品处方了。")
                 (action
                  :title "进入桑德堡的办公室"
                  :desc "就这么夹着尾巴逃跑可不是菲利普·马洛的作风。你决定进去跟桑德堡好好‘谈谈’，顺便找回你的柯尔特左轮手枪。"
                  :always (list
                           (effect 'start-dialogue 'first_scene_doctor_office)
                           (effect 'set boss_defeated true))))
             ;; 选择2：直接离开 (行动)
             (action
              :title "离开这个鬼地方"
              :desc "推开那扇沉重的大门，回到属于你的冷酷街头。"
              :always (list (effect 'end-encounter 'success))))))

;; ==========================================
;; 元数据与状态定义
;; ==========================================


(define all-state
  (append
   world-health-vars
   world-money-vars
   (list
   ;; 流程控制标志
   (var 'intro-has-played false)
   (var 'escaped false) ;; 是否已挣脱
   (var 'path_a_revealed false) ;; 走廊A是否揭晓
   (var 'path_b_revealed false) ;; 走廊B是否揭晓
   (var 'path_c_revealed false) ;; 楼梯间是否揭晓
   (var 'boss_defeated false) ;; 桑德堡医生是否被打晕
   
   ;; 全局时钟
  (var 'alert_clock (clock 
                :title "守卫警觉" 
                :initial 0 
                :max 9))
   ;; 场景时钟
   (var '挣脱束缚钟 (clock :title "挣脱皮带" :initial 0 :max 4))
   (var '左侧探索进度 (clock :title "探查左侧" :initial 0 :max 3))
   (var '右侧探索进度 (clock :title "探查右侧" :initial 0 :max 3))
   (var '前方探索进度 (clock :title "探查正前方" :initial 0 :max 3)))))

;; ==========================================
;; 全局响应 (Reacts)
;; ==========================================
(define all-reacts
  (list
   (react-once-until intro-has-played (effect 'start-quick-dialogue "# 宿醉与麻醉剂\n\n黑暗一点点褪去，但我宁愿它别走。我嘴里的味道像是一个修车工的旧手套。脑袋里有个小人在用大锤猛砸我的视神经。\n\n我花了好几分钟才意识到自己身处何地。这是一间病房，墙壁白得令人作呕。空气里弥漫着廉价消毒水和海洛因的混合气味。我低头，发现自己被几条粗壮的皮带死死绑在一张沉重的铁椅上，手腕已经勒出了血痕。\n\n桑德堡医生——那个专门给道上的人提供黑心庇护的家伙，正把我关在他的秘密疗养院里。门外隐约传来打手粗重的脚步声。如果我不赶紧弄断这些皮带，下一针足以让我变成白痴的毒品很快就会打进我的静脉。"))
   ;; 警戒拉满，直接失败
   (react
    :when (clock-filled? alert_clock)
    :then (list (effect 'start-quick-dialogue "狗腿子们被惊动了！\n门被粗暴地踹开，你还没来得及站稳，就被几个壮汉重新按倒在地……")
                (effect 'end-encounter 'fail)))
   ;; 挣脱进度拉满，推进到下一个阶段
   (react
    :when (and (clock-filled? 挣脱束缚钟) (not escaped))
    :then (list (effect 'set escaped true)
                (effect 'start-quick-dialogue "最后一条皮带的搭扣终于‘咔嗒’一声松开了。我像一条刚被捞上岸的鱼一样喘着粗气，双手麻木得像两截烂木头，但我还是挣扎着站了起来。\n\n门外的走廊死气沉沉。桑德堡的打手们显然认为我已经彻底变成了一个没脑子的瘾君子。现在我必须赶在他们发现之前，找到溜出这个毒窟的路。")))
   ;; 二楼走廊探索揭晓
   (react
    :when (and (clock-filled? 左侧探索进度) (not path_a_revealed))
    :then (list (effect 'set path_a_revealed true)
                (effect 'start-quick-dialogue "左边那条路的尽头是一排封死的重症监护室。厚重的铁门上只开着观察窗，里面偶尔传来某个可怜虫因为毒瘾发作而撞击墙壁的闷响。\n\n这是一条死路，除了绝望，什么都没有。")))
   (react
    :when (and (clock-filled? 右侧探索进度) (not path_b_revealed))
    :then (list (effect 'set path_b_revealed true)
                (effect 'start-quick-dialogue "右边尽头的门把手上落着灰，我用力推了推，发现门被从外面用粗大的挂锁锁死了。这可能是间废弃的药房，想要破门而入发出的动静，足以吵醒半个洛杉矶的警察。\n\n此路不通，我只能原路退回。")))
   (react
    :when (and (clock-filled? 前方探索进度) (not path_c_revealed))
    :then (list (effect 'set path_c_revealed true)
                (effect 'start-quick-dialogue "正前方的阴影并没有欺骗我。我贴着墙根摸索到了尽头，那里有一段铺着陈旧地毯的楼梯。楼下透上来一丝穿堂风，还夹杂着一楼大厅的雪茄味。\n\n这是通往一楼大门的唯一出路。离重获自由，或者吃枪子儿，只剩最后一段距离了。")))))

;; ==========================================
;; 场景调度逻辑
;; ==========================================

(content
 :meta (meta :key '逃离疗养院 :title "逃离疗养院" :desc "菲利普·马洛从桑德堡疗养院脱身的那一夜。")
 :on-success (list
              (effect 'start-quick-dialogue
                      "# 洛杉矶的夜风\n\n你推开沉重的大门，洛杉矶夜晚的冷空气像一盆冰水，把你脑子里残存的麻醉药味冲得一干二净。\n身后的桑德堡疗养院亮着几盏惨白的灯，像个专门吞噬死人的怪物。你没有回头。你只是把手插进皱巴巴的风衣口袋，摸到了那把失而复得的左轮手枪，顺着街边的黑影快步走向马路。\n你终于又回到了这座冷酷的城市。至于桑德堡和那些黑帮的烂摊子，你发誓等弄到一杯威士忌后，会跟他们一笔一笔地算清楚。")
              (effect 'add money 40))
 :on-fail (list
           (effect 'start-quick-dialogue
                   "# 重回深渊\n\n你离出口只差最后几步，几乎能闻到外面潮湿的沥青味。\n但走廊拐角处的阴影里突然伸出一把枪管，接着是某个壮汉粗暴的闷棍。你的后脑勺一阵剧痛，地板迎面砸向你的鼻子。\n你听见有人冷笑：“马洛先生，你的疗程还没结束呢。”\n接着，黑暗像一块巨大的湿毛巾，再次死死捂住了你的脸。")
           (effect 'end-game))
 :vars all-state
 :reacts all-reacts
 :root (cond
        ((not escaped) (location1))
        ((not path_c_revealed) (location2))
        (else (location3))))
