(include "../encounters/helper.scm")
(include "../encounters/common_clock_macros.scm")

(define make-scout-action
  (lambda (title desc clock suits risk ok-text partial-text fail-text fail-effects)
    (action
      :title title
      :desc desc
      :before (list (effect 'clock+ clock 1))
      :check (check
        :suits suits
        :risk risk
        :ok (outcome ok-text (list (effect 'clock+ clock 1)))
        :partial (outcome partial-text (list))
        :fail (outcome fail-text fail-effects)))))

(define bridge
  (node
    :title (if (> day 1) "圣莫尼卡码头下方" "0")
    :desc "夜雨、咸腥的海水和生锈的铁柱。这里是个免费的落脚处，但躺在潮湿的沙子上熬过一晚，感觉就像躺在停尸房的冰柜里等死。"
    :position '(88 62)
    :show-clocks (list pursuit)
    :actions (list
      (action
        :title "睡一晚"
        :desc "把领子立起来，靠着桥墩等天亮。睡眠对穷人来说不值钱，但仇家离你又近了一步。\n压力+2"
        :effects (list
          (effect 'reset-hand)
          (effect 'clock+ pursuit 1)
          (effect 'advance-day)
          (effect 'add stress 2)

          )))))

(define east_district
  (node
    :title "贝城暗巷"
    :desc "这里的警察比黑帮还要下作，巷子里的规矩全靠拳头和美钞来定。你得先摸清门路，不然怎么死在臭水沟里的都不知道。"
    :position '(710 58)
    :show-clocks (list east_info)
    :actions (list
      (make-scout-action
        "在贝城的阴影里打探"
        "弄清谁在卖禁酒，谁在替黑帮盯梢，还有谁会在你转身买烟的时候给你后腰来一刀。"
        east_info
        (list 直觉)
        'mid
        "你避开了几个麻烦的暗警，并从一个老线人嘴里撬出了点真东西。"
        "你摸到了一点边缘消息，但今晚还不够深入。"
        "你瞎撞进了一条死胡同，差点被几个拿弹簧刀的瘾君子堵住。"
        (list (effect 'add stress 1))))))

(define west_district
  (node
    :title "好莱坞边缘"
    :desc "这里的霓虹灯亮得刺眼，但照不透底子里的腐烂。得先弄清在这片花哨的地方，谁能洗钱，谁能救命。"
    :position '(390 44)
    :show-clocks (list west_info)
    :actions (list
      (make-scout-action
        "在灯红酒绿中摸底"
        "顺着夜总会、破旅馆和黑诊所的门牌，一点点把这里的落脚点理出来。"
        west_info
        (list 感知)
        'low
        "你给门童塞了点小费，从酒鬼的胡话里拼出了几条可靠线索。"
        "你听到了一些风声，但全都是些还需要验证的废话。"
        "你兜了一大圈，除了染上一身劣质香水味和恶心感，什么也没得到。"
        (list (effect 'add stress 1))))))

(define bar
  (node
   :title "街角酒馆"
   :desc "廉价波旁酒、走调的爵士乐和女人的谎话在这里一样便宜。只要你肯掏钱请客，吧台前的失意者总能多吐两句真言。"
   :position '(632 176)
   :show-clocks (list bar_rumor)
   :children (list
              (when (clock-filled? bar_rumor)
                (node
                 :title "地下牌局"
                 :desc "门口没有招牌，只有两个西装下鼓鼓囊囊的看门狗。里面的骰子声和筹码碰撞声，比教堂的祈祷更诚实。"
                 ;; :position '(704 278)
                 :actions (list
                           (action
                            :title "上桌赌一把"
                            :desc "把二十块拍在绿呢桌面上，看看今晚命运这个婊子站不站在你这边。"
                            :inputs (list (item 'money 20))
                            :check (check
                                    :suits (list 'instinct 'reason)
                                    :risk 'mid
                                    :ok (outcome "今晚骰子爱你。筹码像听话的狗一样朝你这边滑了过来。" (list (effect 'add money 60)))
                                    :partial (outcome "你没赢走大头，但至少没让桌上那些老千把你当成肥羊。" (list (effect 'add money 25)))
                                    :fail (outcome "庄家把你的二十块扫走时，动作快得像殡仪馆在收尸。" (list)))))))
              )
   :actions (list
             (action
              :title "点一杯双份波旁s"
              :desc "花点钱，让辛辣的酒精烧掉你脑子里那些发作的刺痛。"
              :inputs (list (item 'money 10))
              :effects (list (effect 'add stress -3)))
             (action
              :title "临时当服务生"
              :desc "帮忙端盘子、收桌子、擦杯子。客人聊得再大声，你也顺手能听到一点赌场风声。"
              :before (list (when (not (clock-filled? bar_rumor)) (effect 'clock+ bar_rumor 1)))
              :check (check
                      :suits (list 感知)
                      :risk 'low
                      :ok (outcome "你手脚利落地忙完一轮，老板照规矩结了工钱，几个喝高的客人还额外塞了你一点小费。"
                                   (list (effect 'add money 35)))
                      :partial (outcome "你把该干的活都干完了，钱不算多，但总归没有白忙。"
                                        (list (effect 'add money 20)))
                      :fail (outcome "你打碎了两个杯子，老板骂了两句，最后还是把最基本的工钱丢给了你。"
                                     (list (effect 'add money 10))))))))

(define river_landmark
  (node
   :title "太平洋海岸线"
   :desc "太平洋的水面黑得像一张破旧的黑胶唱片。只有猛烈的海风吹过来时，你才能短暂忘掉这座城市的狐臭味。"
   :position '(862 170)
   :actions (list
             (action
              :title "沿海岸慢慢走一圈"
              :desc "点根烟，丢一张牌进去，让自己像个正常人那样喘口气。"
              ;; :inputs (list (card 'any))
              :check (check
                      :suits (list 'instinct)
                      :risk 'low
                      :ok (outcome "单调的潮水声让你的太阳穴终于不再像打鼓一样乱跳了。" (list (effect 'add stress -2)))
                      :partial (outcome "你吹了一阵冷风，但心里那股火还是没压下去。" (list))
                      :fail (outcome "海风只是把烟灰吹进了你的眼睛，你还是那个倒霉蛋。" (list)))))))


(define hotel
  (node
    :title "廉价汽车旅馆"
    :desc "房间里一股劣质肥皂、发霉地毯和陈年绝望混合的味道。但门上有防盗链，而且床不会漏雨。"
    :position '(266 184)
    :actions (list
      (action
        :title "预定房间"
        :desc "买下今晚的房间门卡，证明你暂时还不是个流落街头的流浪汉。"
        ;; :conditions (list (field-at-least 'money 15 "需要 25 美钞"))
        :inputs (list (item 'money 10))
        :effects (list (effect 'add hotel_pass 1)))
      (action
        :title "睡上一觉"
        :desc "把配枪压在枕头底下闭上眼睛。这床硬得像铁板，但总归是个庇护所。"
        :conditions (list (has-item 'hotel_pass 1 "需要房卡"))
        :inputs (list (item 'hotel_pass 1))
        :effects (list
          (effect 'reset-hand)
          (effect 'clock+ pursuit 1)
          (effect 'advance-day)
          (effect 'add stress -1))))))

(define clinic
  (node
   :title "黑市诊所"
   :desc "隐蔽在干洗店后门的诊所. 他们对你是怎么中的枪毫无兴趣，他们只认富兰克林的头像。"
   :position '(474 188)
   :show-clocks (list (when clinic_treatment_started clinic_treatment_progress))
   :actions (list
             (when (not clinic_treatment_started) (action
                                                   :title "付钱开疗程"
                                                   :desc "让医生给你排一个完整疗程。治疗2点健康。"
                                                   ;; :conditions (list (field-truthy clinic_treatment_started))
                                                   :inputs (list (item 'money 20))
                                                   :effects (list
                                                             (effect 'set clinic_treatment_started true))))
             (when (and clinic_treatment_started (not (clock-filled? clinic_treatment_progress)))
               (action
                :title "做一次疗程"
                :desc "按医生的安排处理伤口、换药、缝合。这次能不能特别顺利另说，但总得把这一步熬过去。"
                :before (when (clock-filled? clinic_treatment_progress)
                          (list
                           (effect 'set clinic_treatment_started false)
                           (log "clinic treated started? " clinic_treatment_started)
                           (log "clocl value" (clock-value clinic_treatment_progress))
                           (effect-reset-clock clinic_treatment_progress)
                           ))
                :check (check
                        :suits (list 理性)
                        :risk 'low
                        :ok (outcome "你咬牙熬过了这一轮，医生居然还算像样地把伤口收拾整齐了。"
                                     (list (effect 'clock+ clinic_treatment_progress 2)))
                        :partial (outcome "这一轮处理又疼又慢，但总归还是完成了。"
                                          (list (effect 'clock+ clinic_treatment_progress 1)))
                        :fail (outcome "医生手忙脚乱，你也被折腾得满头冷汗，只能勉强稳住伤口。"
                                       (list (effect 'add stress 1))))))
             )))

(define residential_area
  (node
    :title "帕萨迪纳富人区"
    :desc "草坪修剪得像台球桌一样平整，精致的窗帘后藏着无数见不得光的丑闻。你得找出哪扇高档木门可以被撬开。"
    :position '(626 306)
    :show-clocks (list residential_info)
    :actions (list
      (make-scout-action
        "在富人区外围兜圈子"
        "观察送奶工、邮差和园丁的路线，看阔太太们的私会情人都在走哪扇后门。"
        residential_info
        (list 理性)
        'low
        "你看穿了体面表象下的漏洞，找到了几个关键的入口。"
        "你摸清了一部分安保规律，但还没法直接潜入。"
        "你那副寒酸样引起了巡逻警察的注意，被盘问了半天。"
        (list (effect 'add stress 1))))))

(define shop
  (node
    :title "黑市当铺"
    :desc "当铺老板用看死人的眼神看着你。想要变回那个体面且危险的硬汉侦探，你得在这里花点血本。"
    :position '(482 430)
    :actions (list
      (action
        :title "买一件像样的粗花呢风衣"
        :desc "一套干净的行头，能让你在骗过门卫时省掉成吨的废话。"
        :conditions (list (field-at-least 'money 80 "需要 80 美钞"))
        :inputs (list (item 'money 80 ))
        :effects (list (effect 'add clothes 1)))
      (action
        :title "弄一套万能开锁工具"
        :desc "不管多漂亮的门，只要它上了锁，就是在邀请你打开它。"
        :conditions (list (field-at-least 'money 45 "需要 45 美钞"))
        :inputs (list (item 'money 45 ))
        :effects (list (effect 'add lockpick 1)))
      (action
        :title "买一把柯尔特.38左轮"
        :desc "跟这座腐烂的城市讲道理时，枪口往往是最好的标点符号。"
        :conditions (list (field-at-least 'money 120 "需要 120 美钞"))
        :inputs (list (item 'money 120 ))
        :effects (list (effect 'add gun 1))))))

(define bulletin_board
  (node
    :title "旧线人的联络点"
    :desc "你现在的名声烂透了，只能去公用电话亭接点同行不屑于干的脏活来糊口。钱不多，但比饿死强。"
    :position '(652 428)
    :actions (list
      (action
        :title "接下替人收债的脏活"
        :desc "某位放高利贷的朋友出了笔小钱，想让一个不知天高地厚的赌棍断两根肋骨。"
        :effects (list (effect 'start-encounter 'teach_thug)))
      (action
        :title "接下监视狐狸精的委托"
        :desc "一位多疑的阔太太想让你去酒吧，跟一个迷人的危险女人套套近乎。"
        :effects (list (effect 'start-encounter '酒吧艳遇)))
      (action
        :title "接下午夜闯空门的差事"
        :desc "有人出钱让你溜进一栋静得过分的宅子里，找一份‘不小心遗失’的文件。"
        :effects (list (effect 'start-encounter 'black_night))))))

(define repair_shop
  (node
    :title "郊外黑车厂"
    :desc "满地机油污渍，空气里混着汽油和黑钱的臭味。老板嘴上不饶人，但他手里有你离开洛杉矶的车票。"
    :position '(820 420)
    :actions (list
      (action
        :title "帮着拆卸黑市赃车"
        :desc "忍着废气和机油干点体力活，换点干净的钞票。"
        :check (check
          :suits (list 强硬)
          :risk 'mid
          :ok (outcome "你熟练地把一辆偷来的福特拆成了零件，老板嘟囔着把钱拍在了引擎盖上。" (list (effect 'add money 45)))
          :partial (outcome "活儿干完了，但刺耳的电钻声和满手洗不掉的油污让你烦躁得想打人。" (list (effect 'add money 30) (effect 'add stress 1)))
          :fail (outcome "你搞砸了水箱，老板骂骂咧咧地只扔给你一点可怜的零票子。" (list (effect 'add money 15)))))
      (action
        :title "掏出 300 美钞买辆没挂牌的福特"
        :desc "这价格跟当街抢劫没区别，但要想彻底甩掉追兵，你需要这台能把油门踩到底的V8引擎。"
        :conditions (list (field-at-least 'money 300 "需要 300 美钞"))
        :inputs (list (item 'money 300 ))
        :effects (list
          (effect 'start-quick-dialogue "# 发动引擎\n\n钥匙拧下去的那一刻，发动机发出一声沙哑却结实的低吼。你把那三百块脏兮兮的钞票留在了修车厂，踩下油门，让这辆没挂牌的福特冲进洛杉矶还没亮透的清晨。\n\n后视镜里的街区一点点缩小。你不知道前方是不是更好的地方，但至少，你已经离开了这里。")
          (effect 'end-game)))
      (when
        (not villa_job_taken)
        (action
          :title "问老板有没有别的交易"
          :desc "老板吐出一口雪茄烟圈，说如果你嫌贵，可以用一件去山顶别墅的潜入活儿来抵车钱。"
          :effects (list
            (effect 'set villa_job_taken true)
            (effect 'start-quick-dialogue "# 别墅窃案\n\n黑车厂老板把雪茄屁股碾灭在满是油污的地板上。他说好莱坞山上有一栋豪宅，主人去了东海岸，但保险柜里有一份他急需的账本。\n\n“你要么把三百块现金放桌上，”他咧着发黄的牙齿笑了笑，“要么替我把那玩意儿偷回来。钥匙就在车上。”\n\n这听起来是一桩极其经典的硬汉侦探烂摊子，只是我们暂时还没把这个关卡做出来。")))))))

;; 场景数据

(define world-state
  (state
   (被追杀已触发 false)
   (pursuit (clock :title "被追捕" :desc "每天+1. 他们在找你, 一个擅自离开戒毒所的人, 每一天他们都离你更近。" :initial 0 :max 6))
   (east_info (clock :title "贝城探索进度" :desc "东边的酒馆、海岸和地下买卖都埋在深不见底的黑幕中。" :initial 0 :max 4))
   (west_info (clock :title "了解好莱坞" :desc "西边的破旅馆和黑诊所必须先用时间去探明。" :initial 0 :max 4))
   (clinic_treatment_started false)
   (clinic_treatment_progress (clock :title "诊所疗程" :desc "付钱开启后，需要完成四轮治疗，才能真正把伤势稳定下来。" :initial 0 :max 3))
   (bar_rumor (clock :title "酒馆线报" :desc "关于地下高额牌局的风声。" :initial 0 :max 4))
   (residential_info (clock :title "打探富人区门路" :desc "那些看似优雅的别野区里，同样藏着下水道般的暗门。" :initial 0 :max 2))
   (residential_intro_played false)
   (villa_job_taken false)))

(define world-reacts
  (reacts
   ;; (react-once-until 被追杀已触发 (effect 'start-encounter 'first_scene))
   (react-once-until 被追杀已触发 (effect 'add 'money 40))
   (react
    :when (and clinic_treatment_started (clock-filled? clinic_treatment_progress))
    :then (list
           
           (effect 'set clinic_treatment_started false)
           (effect-reset-clock clinic_treatment_progress)
           (effect 'add 'health 2)
           ;; (effect 'start-quick-dialogue "# 疗程结束\n\n第四次回到那间黑诊所时，医生总算像个真正干过几年活的人，把你身上的口子一一收拾妥当。酒精、碘酒和陈旧止痛药的味道让人反胃，但至少，你终于不再像一只勉强缝起来的破麻袋了。")
           ))
   
   (react
    :when (and (>= day 3) (not residential_intro_played))
    :then (list
           (effect 'set residential_intro_played true)
           (effect 'start-quick-dialogue "# 第三天\n\n你刚从充满宿醉和冷汗的浅眠中醒来，就敏锐地察觉到街上的风向变了。昨晚还只是隐秘的传闻，今天街头已经响起了黑警粗暴的查问声。\n\n桑德堡的人正在拿着你的照片到处打听——包括你昨晚是在哪个破桥洞底下缩着身子。你不能再只混迹于贫民窟了，得赶紧弄身体面的衣服，去富人区找找别的出路。")))))

(content
 :meta (meta :key 'escape :title "" :desc "")
 :state world-state
 :reacts world-reacts
 :root (node
        :title "洛杉矶街头"
        :desc "在这个充满霓虹灯与死巷的城市里，你必须在仇家找上门之前，给自己弄到一条离开的活路。"
        :show-clocks (list pursuit)
        :children (list
                   bridge
                   (when (< (clock-value east_info) 4) east_district)
                   (when (>= (clock-value east_info) 2) bar)
                   (when (>= (clock-value east_info) 4) river_landmark)
                   
                   (when (< (clock-value west_info) 4) west_district)
                   (when (>= (clock-value west_info) 2) hotel)
                   (when (>= (clock-value west_info) 4) clinic)
                   (when (>= (clock-value west_info) 4) repair_shop)
                   
                   (when (and (>= day 3) (not (clock-filled? residential_info))) residential_area)
                   (when (clock-at-least-half? residential_info) shop)
                   (when (clock-filled? residential_info) bulletin_board)
                   )))
