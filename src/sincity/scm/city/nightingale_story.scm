;; EXPORT nightingale-vars, nightingale-reacts, nightingale-tasks, nightingale-* action helpers

(define nightingale-opening-text
  "# 保护夜莺\n\n# speaker: 科尔\n首演前一天，剧院的人把话递到我门口，说夜莺收到了威胁。\n\n# speaker: 科尔\n这座城里会写恐吓信的人不少，真正麻烦的是总有人愿意替他们把信送到地方。\n\n# speaker: 科尔\n先去剧院。别让整座城太早吵起来。")

(define nightingale-guard-text
  "# 剧院前门\n\n# speaker: 保安\n“科尔？里面等你。别到处乱走，今晚每个人都在假装自己没听说那封信。”\n\n# speaker: 科尔\n他说完往舞台方向让开半步。不是欢迎，是把麻烦递给下一个人。")

(define nightingale-stage-text
  "# 排练中的夜莺\n\n（以后这里会播放一段排练动画：舞台空着大半，灯光像一把冷刀落下来。夜莺唱了两句，声音在空剧场里悬住，又忽然停下。）\n\n# speaker: 夜莺\n“你就是科尔？”\n\n# speaker: 科尔\n“如果你收到的是第一封威胁信，我会说先别紧张。”\n\n# speaker: 夜莺\n她把信递过来，指尖很稳。\n\n# speaker: 夜莺\n“那就别这么说。这是第二封，刚刚才送到。”\n\n# speaker: 科尔\n第二封。送信的人还没走远，或者以为自己已经走远。")

(define nightingale-search-half-text
  "# 搜查剧院\n\n# speaker: 科尔\n后台门口有人踩过湿泥。不是演员的鞋，也不像负责搬道具的工人。\n\n# speaker: 科尔\n化妆室那边也许能看见信件经过哪里被交到手上。")

(define nightingale-shadow-text
  "# 可疑人影\n\n# speaker: 科尔\n后巷门缝晃了一下。有人站在雨里，像在确认信已经送到，又像在等另一个信号。\n\n# speaker: 科尔\n这次不能让他慢慢消失。")

(define nightingale-wakeup-text
  "# 醒来\n\n（以后这里会播放一段追逐后的短动画：你追上那个人，手已经碰到面具边缘。下一秒，后脑一阵钝响，剧院灯光像被水冲散。）\n\n# speaker: 夜莺\n“别动。你流了血。”\n\n# speaker: 科尔\n她坐在旁边，妆已经卸了一半，声音比舞台上低得多。\n\n# speaker: 夜莺\n“你追上了他。至少在被人从背后敲倒之前。”\n\n# speaker: 科尔\n这不算安慰，但比谎话好。等她离开，天已经亮了。城市终于重新把门打开。")

(define nightingale-letter-room-text
  "# 第一封威胁信\n\n# speaker: 科尔\n信纸沾着煤灰，折痕像从粗糙口袋里掏出来过不止一次。措辞故意学得像码头人的脾气，可里面有些细节太近后台了。\n\n# speaker: 科尔\n旧码头的味道是真的，剧院内部的眼睛也是真的。问题只是它们谁先动了手。")

(define nightingale-manager-text
  "# 剧院经理\n\n# speaker: 经理\n“首演不是普通演出。赞助、宣传、慈善名单，全都压在这一晚。旧码头那边的人要是闹起来，报纸会先写我们办事不周。”\n\n# speaker: 科尔\n他担心的是场面和票房，不是夜莺。但场面本身就是线索。")

(define nightingale-publicist-text
  "# 宣传口风\n\n# speaker: 宣传人员\n“这场首演是城市更新的招牌。旧码头、慈善晚宴、名人照片，报纸已经排好了版。”\n\n# speaker: 科尔\n把旧码头写进宣传词的人，通常不会去看那地方真正长什么样。")

(define nightingale-stagehand-text
  "# 后台工人\n\n# speaker: 后台工人\n“近两周总有人在后门打听首演流程，像怕错过什么时点。还有人提过莱恩，说他喝醉时什么脏话都敢往夜莺头上砸。”\n\n# speaker: 科尔\n名字终于落地了。莱恩。")

(define nightingale-stall-text
  "# 街头跑腿\n\n# speaker: 摊贩\n“有个湿透的小子拿着封信跑过这条街，像赶着把自己卖掉一样。往剧院那边去的，鞋底全是黑泥。”\n\n# speaker: 科尔\n不是剧院里的人自己送的。但信是被城市的手转过去的。")

(define nightingale-market-text
  "# 买来的线索\n\n# speaker: 黑市掌柜\n“钱给够，我就多想起来一点。那小子不是一个人跑的，背后有人按段付钱，信纸和煤灰也不是剧院自己的东西。”\n\n# speaker: 科尔\n消息被他切成几片卖。难看，但有用。")

(define nightingale-restaurant-done-text
  "# 饭摊老板终于说完\n\n# speaker: 摊贩\n“送信的小孩在我这儿吃过两回。他每次都坐边上，像怕有人从巷口出来认出他。最后一次，他提到剧院后巷，还提到旧码头那边有人给钱。”\n\n# speaker: 科尔\n老板把这句话拆成六顿饭。现在它终于能连起来。")

(define nightingale-bar-text
  "# 小报记者\n\n# speaker: 小报记者\n“首演、慈善、旧码头改造，这三个词绑在一起卖得最好。夜莺唱得越高，下面的人看起来就越像被踩在舞台灯底下。”\n\n# speaker: 科尔\n他还提到了莱恩。像提一个已经被写进草稿、只等警方盖章的名字。")

(define nightingale-waste-text
  "# 底层传递链\n\n# speaker: 跑腿少年\n“有人给钱，让我去认认路，别真去敲门。我只知道信最后会到剧院后巷，拿钱的人口音像码头那边。”\n\n# speaker: 科尔\n送信人不是主谋，只是这条链上最便宜的一节。")

(define nightingale-first-letter-done-text
  "# 第一封信的方向\n\n# speaker: 科尔\n纸、灰、递送方式都把线头往旧码头推，可那份对后台节奏的熟悉又不像外人能随手编出来的。\n\n# speaker: 科尔\n威胁不是凭空写出来的。它长了两张脸：一张朝着旧码头，一张看着剧院里面。")

(define nightingale-trust-loss-text
  "# 夜莺的信任\n\n# speaker: 科尔\n时间拖得太久，剧院那边开始怀疑我是不是还能控制局面。夜莺没有催促，但沉默本身已经是一种回答。")

(define nightingale-trust-fail-text
  "# 委托失败\n\n# speaker: 科尔\n夜莺不再等我。剧院把材料交给警方，把门也一并关上。\n\n# speaker: 科尔\n这座城市里，失去信任有时候比失去线索更快。")

(define nightingale-lore-text
  "# 莱恩这个名字\n\n# speaker: 科尔\n经理怕丑闻，宣传怕掉版面，后台工人怕出人命。三种怕拼在一起，只留下同一个名字：莱恩。\n\n# speaker: 科尔\n到目前为止，他更像个被推到台前的嫌疑人，而不是全部答案。")

(define nightingale-second-letter-alert-text
  "# 第二封信的踪迹\n\n# speaker: 剧院代理人\n“刚有人来报，第二封信已经在路上。你之前安插的线人盯到了送信的影子，就在剧院后巷附近。”\n\n# speaker: 科尔\n信终于从纸上站起来了。")

(define nightingale-second-letter-fail-text
  "# 剧院绕过你\n\n# speaker: 剧院经理\n“信已经进来了，我们只能先交给警方。”\n\n# speaker: 科尔\n我慢了一步。现在剧院和警局之间，又多了一份不经过我的材料。")

(define nightingale-accident-call-text
  "# 剧院来电\n\n# speaker: 科尔\n旧照片还没在抽屉里躺稳，剧院那边的电话就打了进来。\n\n# speaker: 剧院经理\n“后台出事了。夜莺在里面。你最好现在过来。”\n\n# speaker: 科尔\n电话里没人说调查。那种语气只说明一件事：事故还没有结束。")

(define nightingale-vars
  (list
    (var 'nightingale_theater_unlocked true)
    (var 'nightingale_front_done false)
    (var 'nightingale_commission_taken false)
    (var 'nightingale_theater_search (clock :title "剧院搜查" :desc "在剧院里追查第二封威胁信刚刚经过的路线。" :initial 0 :max 4))
    (var 'nightingale_search_half_seen false)
    (var 'nightingale_shadow_seen false)
    (var 'nightingale_first_confrontation_done false)
    (var 'nightingale_city_day_started false)
    (var 'nightingale_clinic_unlocked false)
    (var 'nightingale_stall_unlocked false)
    (var 'nightingale_market_unlocked false)
    (var 'nightingale_bar_unlocked false)
    (var 'nightingale_waste_unlocked false)
    (var 'nightingale_letter_checked false)
    (var 'nightingale_stall_checked false)
    (var 'nightingale_market_checked false)
    (var 'nightingale_restaurant_talk (clock :title "饭摊老板的半句话" :desc "老板每次只肯多说一点。多吃几顿饭，他才会把送信人的路线讲完整。" :initial 0 :max 6))
    (var 'nightingale_restaurant_done false)
    (var 'nightingale_bar_checked false)
    (var 'nightingale_waste_checked false)
    (var 'nightingale_manager_talked false)
    (var 'nightingale_publicist_talked false)
    (var 'nightingale_stagehand_talked false)
    (var 'nightingale_first_letter_progress (clock :title "威胁信调查" :desc "顺着纸张、递送链和口风，查清第一封信背后的方向。" :initial 0 :max 4))
    (var 'nightingale_first_letter_deadline (clock :title "送信路线调查期限" :desc "必须在期限内查清送信路线。" :initial 3 :max 3))
    (var 'nightingale_deadline_checked_day 0)
    (var 'nightingale_first_letter_done false)
    (var 'nightingale_first_letter_due_day 0)
    (var 'nightingale_second_letter_ready false)
    (var 'nightingale_second_letter_harder false)
    (var 'nightingale_second_letter_intercepted false)
    (var 'nightingale_second_letter_failed false)
    (var 'nightingale_second_letter_delivered false)
    (var 'nightingale_trust (clock :title "夜莺的信任" :desc "拖得越久，夜莺和剧院越会怀疑你是否还能保护她。降到 0 时委托失败。" :initial 8 :max 8))
    (var 'nightingale_trust_initialized false)
    (var 'nightingale_trust_checked_day 0)
    (var 'nightingale_trust_failed false)
    (var 'nightingale_lore_progress (clock :title "夜莺的传说" :desc "经理、宣传、工人——每个人都记得一部分关于夜莺的传闻。拼起来就是一个完整的故事。" :initial 0 :max 3))
    (var 'nightingale_lore_known false)
    (var 'nightingale_docks_direction_known false)
    (var 'nightingale_side_job_clock (clock :title "旧码头卸货" :desc "临时招工，搬几趟箱子换工钱。" :initial 0 :max 4))
    (var 'nightingale_side_job_available false)
    (var 'nightingale_side_job_done false)
    (var 'theater_accident_unlocked false)
    (var 'theater_accident_survived false)
    (var 'theater_accident_started false)
    (var 'nightingale_saved false)
    (var 'nightingale_hurt false)
    (var 'accident_sabotage_seen false)
    (var 'theater_photo_discussed false)
    (var 'theater_accident_clue (clock :title "事故现场线索" :desc "在坠落灯架和断绳里找到足以说明事故不是意外的东西。" :initial 0 :max 3))
    (var 'theater_accident_clue_found false)
    (var 'theater_accident_supplies (clock :title "后台可用物资" :desc "事故后散落的工具、药品和备用材料。可以冒险搜出一点有用东西。" :initial 0 :max 3))
    (var 'theater_accident_supplies_found false)
    (var 'theater_accident_cleanup (clock :title "现场清理" :desc "剧院的人正在把事故残骸清走。填满后，后台道具废墟不再能被搜刮。" :initial 0 :max 2))
    (var 'theater_accident_cleanup_started false)
    (var 'theater_accident_cleanup_checked_day 0)
    (var 'press_angle_seen false)
    (var 'newspaper_office_unlocked false)
    (var 'newspaper_first_visit_done false)
    (var 'press_source (clock :title "稿源线索" :desc "查清后台事故稿件的来源，以及报社为什么能提前拿到这套说法。" :initial 0 :max 9))
    (var 'press_alert (clock :title "今日报社警觉" :desc "你越打扰编辑、排字工和记者，报社越会防着你。每天会重置。" :initial 0 :max 3))
    (var 'press_source_found false)
    (var 'press_note_found false)
    (var 'reporter_negotiation_unlocked false)
    (var 'reporter_negotiation_done false)
    (var 'press_feed_confirmed false)
    (var 'premiere_perimeter_checked false)
    (var 'premiere_vip_lounge_visited false)
    (var 'premiere_backstage_visited false)
    (var 'premiere_ready false)
    (var 'premiere_chase_completed false)
    (var 'premiere_night_completed false)
    (var 'premiere_clue_program false)
    (var 'premiere_clue_wallet false)
    (var 'premiere_clue_jacket false)
    (var 'premiere_clue_wire false)
    (var 'reporter_storyline_unlocked false)
    (var 'reporter_second_meeting_done false)
    (var 'reporter_evidence_committed false)
    (var 'reporter_headline_wait (clock :title "头版准备" :desc "记者正在排版、核查、顶住压力。每天推进一格，期间城市会开始反应。" :initial 0 :max 3))
    (var 'reporter_headline_wait_started false)
    (var 'reporter_headline_wait_checked_day 0)
    (var 'reporter_city_impact_1_seen false)
    (var 'reporter_city_impact_2_seen false)
    (var 'reporter_city_impact_3_seen false)
    (var 'reporter_more_proof_needed false)
    (var 'reporter_story_strength (clock :title "报道支撑" :desc "头版需要不只是一份证据，还需要活证词、街面反应或上层失言来压住版面。" :initial 0 :max 2))
    (var 'reporter_helen_statement_done false)
    (var 'reporter_docks_reaction_done false)
    (var 'reporter_editor_pressure_done false)
    (var 'reporter_frontpage_ready false)
    (var 'reporter_frontpage_published false)
    (var 'reporter_aftershock (clock :title "刊登后的余波" :desc "报道已经印出，人们的命运开始被这篇头版改写。" :initial 0 :max 3))
    (var 'reporter_aftershock_started false)
    (var 'reporter_aftershock_checked_day 0)
    (var 'reporter_aftershock_1_seen false)
    (var 'reporter_aftershock_2_seen false)
    (var 'reporter_aftershock_3_seen false)
    (var 'reporter_rumor_event_active false)
    (var 'reporter_rumor_event_location 'none)
    (var 'reporter_rumor_event_expires_day 0)
    (var 'reporter_rumor_event_seen false)))

(define nightingale-reacts
  (list
    (react
      :when (and (>= (clock-value nightingale_theater_search) 2) (not nightingale_search_half_seen))
      :then (list
        (effect 'set nightingale_search_half_seen true)
        (effect 'start-quick-dialogue nightingale-search-half-text)))
    (react
      :when (and (clock-filled? nightingale_theater_search) (not nightingale_shadow_seen))
      :then (list
        (effect 'set nightingale_shadow_seen true)
        (effect 'start-quick-dialogue nightingale-shadow-text)))
    (react
      :when (and nightingale_first_confrontation_done (not nightingale_city_day_started))
      :then (list
        (effect 'set nightingale_city_day_started true)
        (effect 'set nightingale_clinic_unlocked true)
        (effect 'set nightingale_stall_unlocked true)
        (effect 'set nightingale_waste_unlocked true)
        (effect 'start-quick-dialogue nightingale-wakeup-text)))
    (react
      :when (and nightingale_stall_checked (not nightingale_market_unlocked))
      :then (list
        (effect 'set nightingale_market_unlocked true)))
    (react
      :when (and (clock-filled? nightingale_restaurant_talk) (not nightingale_restaurant_done))
      :then (list
        (effect 'set nightingale_restaurant_done true)
        (effect 'clock+ nightingale_first_letter_progress 1)
        (effect 'start-quick-dialogue nightingale-restaurant-done-text)))
    (react
      :when (and nightingale_market_checked (not nightingale_bar_unlocked))
      :then (list
        (effect 'set nightingale_bar_unlocked true)))
    (react
      :when (and nightingale_commission_taken (= nightingale_first_letter_due_day 0))
      :then (list
        (effect 'set nightingale_first_letter_due_day (+ day 3))
        (effect 'set nightingale_deadline_checked_day day)
        (effect 'set nightingale_trust_checked_day day)))
    (react
      :when (and nightingale_commission_taken
                 (not nightingale_first_letter_done)
                 (> day nightingale_deadline_checked_day))
      :then (list
        (effect 'clock- nightingale_first_letter_deadline 1)
        (effect 'set nightingale_deadline_checked_day day)))
    (react
      :when (and nightingale_city_day_started (not nightingale_trust_initialized))
      :then (list
        (effect 'set nightingale_trust_initialized true)
        (effect 'clock+ nightingale_trust 8)))
    (react
      :when (and nightingale_city_day_started
                 (not nightingale_first_letter_done)
                 (> nightingale_first_letter_due_day 0)
                 (> day nightingale_first_letter_due_day)
                 (> day nightingale_trust_checked_day)
                 (> (clock-value nightingale_trust) 0))
      :then (list
        (effect 'clock- nightingale_trust 1)
        (effect 'set nightingale_trust_checked_day day)
        (when (or (= (clock-value nightingale_trust) 7)
                  (= (clock-value nightingale_trust) 2))
          (effect 'start-quick-dialogue nightingale-trust-loss-text))))
    (react
      :when (and nightingale_city_day_started
                 (not nightingale_first_letter_done)
                 (clock-empty? nightingale_trust)
                 (not nightingale_trust_failed))
      :then (list
        (effect 'set nightingale_trust_failed true)
        (effect 'end-game "委托失败" "夜莺不再信任你，剧院把威胁信交给警方。保护夜莺的委托到此结束。")))
    (react
      :when (and nightingale_stall_checked nightingale_market_checked nightingale_restaurant_done (not nightingale_first_letter_done))
      :then (list
        (effect 'set nightingale_first_letter_done true)
        (effect 'set nightingale_second_letter_ready true)
        (effect 'set nightingale_docks_direction_known true)
        (effect 'clock+ nightingale_trust 3)
        (effect 'start-quick-dialogue nightingale-first-letter-done-text)))
    (react
      :when (and (clock-filled? nightingale_lore_progress) (not nightingale_lore_known))
      :then (list
        (effect 'set nightingale_lore_known true)
        (effect 'start-quick-dialogue nightingale-lore-text)))
    (react
      :when (and nightingale_commission_taken
                 (not nightingale_side_job_done)
                 (not nightingale_side_job_available)
                 (> nightingale_first_letter_due_day 0)
                 (>= day nightingale_first_letter_due_day))
      :then (list
        (effect 'set nightingale_side_job_available true)))
    (react
      :when (and nightingale_side_job_available
                 (not nightingale_side_job_done)
                 (> day (+ nightingale_first_letter_due_day 1)))
      :then (list
        (effect 'set nightingale_side_job_available false)))
    (react
      :when (and (clock-filled? nightingale_side_job_clock) (not nightingale_side_job_done))
      :then (list
        (effect 'set nightingale_side_job_done true)
        (effect 'set nightingale_side_job_available false)
        (effect 'add money 30)
        (effect 'start-quick-dialogue "# 卸货工钱\n\n# speaker: 工头\n“干完了。这是你的工钱。”")))
    (react
      :when (and helen_room_searched
                 (not theater_accident_unlocked)
                 (not theater_accident_survived))
      :then (list
        (effect 'set theater_accident_unlocked true)))
    (react
      :when (and (clock-filled? theater_accident_clue)
                 (not theater_accident_clue_found))
      :then (list
        (effect 'set theater_accident_clue_found true)
        (effect 'set theater_accident_cleanup_started true)
        (effect 'set theater_accident_cleanup_checked_day day)
        (effect 'start-quick-dialogue "# 断绳和楔片\n\n# speaker: 科尔\n断口太干净了，像有人提前咬过一口。灯架下还卡着一枚金属楔片，不属于剧院常用的固定件。\n\n# speaker: 科尔\n这不是单纯的意外。有人知道后台怎样运转，也知道该让事故看起来像莱恩那种粗暴破坏。")))
    (react
      :when (and theater_accident_clue_found
                 (not theater_accident_supplies_found)
                 (not theater_accident_cleanup_started))
      :then (list
        (effect 'set theater_accident_cleanup_started true)
        (effect 'set theater_accident_cleanup_checked_day day)))
    (react
      :when (and theater_accident_cleanup_started
                 (not theater_accident_supplies_found)
                 (not (clock-filled? theater_accident_cleanup))
                 (> day theater_accident_cleanup_checked_day))
      :then (list
        (effect 'clock+ theater_accident_cleanup (- day theater_accident_cleanup_checked_day))
        (effect 'set theater_accident_cleanup_checked_day day)))
    (react
      :when (and (clock-filled? theater_accident_supplies)
                 (not theater_accident_supplies_found))
      :then (list
        (effect 'set theater_accident_supplies_found true)
        (effect 'add health 1)
        (effect 'add energy 1)
        (effect 'start-quick-dialogue "# 后台物资\n\n# speaker: 科尔\n急救箱里还剩一点绷带和醒神药。剧院的人忙着清场，没人顾得上这些小东西。\n\n# speaker: 科尔\n拿走它们不体面，但今晚已经没有多少体面的余地。")))
    (react
      :when (and (clock-filled? press_source)
                 (not press_source_found))
      :then (list
        (effect 'set press_source_found true)
        (effect 'set press_note_found true)
        (effect 'set reporter_negotiation_unlocked true)
        (effect 'start-quick-dialogue "# 提前送来的便条\n\n# speaker: 科尔\n记者工位的夹层里塞着一张便条。上面写着：莱恩、夜莺、旧码头、后台事故。顺序像一份标题提纲。\n\n# speaker: 科尔\n纸上的字迹粗暴，像莱恩会写出来的东西。可问题不在这里。\n\n# speaker: 科尔\n如果他真想威胁夜莺，为什么要把威胁送给报社？他是想吓她，还是想让整座城替他看见什么？")))
    (react
      :when (and premiere_night_unlocked
                 (not premiere_ready)
                 (>= (+ (if premiere_perimeter_checked 1 0)
                        (if premiere_vip_lounge_visited 1 0)
                        (if premiere_backstage_visited 1 0)) 2))
      :then (list
        (effect 'set premiere_ready true)))
    (react
      :when (and premiere_night_completed
                 (not reporter_storyline_unlocked))
      :then (list
        (effect 'set reporter_storyline_unlocked true)
        (effect 'start-quick-dialogue "# 结案之后\n\n# speaker: 科尔\n首演夜过去得太快，报纸来得更快。警方的版本已经写好：莱恩、旧码头、嫉恨、袭击。\n\n# speaker: 小报记者\n他在楼下等我，帽檐压得很低。\n\n# speaker: 小报记者\n“你手里有东西。我有版面。但这次不是一张便条就够。”")))
    (react
      :when (and (clock-filled? reporter_headline_wait)
                 (not reporter_more_proof_needed))
      :then (list
        (effect 'set reporter_more_proof_needed true)
        (effect 'start-quick-dialogue "# 头版还不够硬\n\n# speaker: 小报记者\n“编辑同意留版面，但律师和警局的人已经在楼下喝咖啡。”\n\n# speaker: 科尔\n“你要反悔？”\n\n# speaker: 小报记者\n“我要更多东西。一个活人愿意说话，或者一条街已经开始变样的证据。否则他们会把这篇稿子按死在排字间。”")))
    (react
      :when (and (clock-filled? reporter_story_strength)
                 reporter_more_proof_needed
                 (not reporter_frontpage_ready))
      :then (list
        (effect 'set reporter_frontpage_ready true)
        (effect 'start-quick-dialogue "# 可以刊登\n\n# speaker: 小报记者\n“够了。老人的证词、码头人的反应、还有编辑室里那些被改掉的字，终于能互相撑住。”\n\n# speaker: 科尔\n“你会怎么写？”\n\n# speaker: 小报记者\n“写成他们明天早上不能假装没看见的样子。”")))
    (react
      :when (and (>= (clock-value reporter_headline_wait) 1)
                 reporter_headline_wait_started
                 (not reporter_city_impact_1_seen))
      :then (list
        (effect 'set reporter_city_impact_1_seen true)
        (effect 'start-quick-dialogue "# 城市开始听见\n\n# speaker: 科尔\n饭摊边有人压低声音讨论“莱恩也许不是唯一的问题”。这句话还很轻，但已经让旁边的人不再继续吃汤。")))
    (react
      :when (and (>= (clock-value reporter_headline_wait) 2)
                 reporter_headline_wait_started
                 (not reporter_city_impact_2_seen))
      :then (list
        (effect 'set reporter_city_impact_2_seen true)
        (effect 'start-quick-dialogue "# 压力往下落\n\n# speaker: 科尔\n剧院经理派人问我有没有把材料交给报社。码头酒馆里，有人第一次不是骂莱恩，而是骂“他们早就写好了故事”。")))
    (react
      :when (and (>= (clock-value reporter_headline_wait) 3)
                 reporter_headline_wait_started
                 (not reporter_city_impact_3_seen))
      :then (list
        (effect 'set reporter_city_impact_3_seen true)
        (effect 'start-quick-dialogue "# 版面前夜\n\n# speaker: 科尔\n警局门口多了两个穿便装的人。贝城晚报的排字间灯亮到后半夜。\n\n# speaker: 科尔\n这篇稿子还没印出来，已经开始改变人们站的位置。")))
    (react
      :when (and (>= (clock-value reporter_aftershock) 1)
                 reporter_aftershock_started
                 (not reporter_aftershock_1_seen))
      :then (list
        (effect 'set reporter_aftershock_1_seen true)
        (effect 'start-quick-dialogue "# 头版之后：旧码头\n\n# speaker: 科尔\n报纸被贴在码头酒馆门口。有人把莱恩的名字划掉，又在旁边写上“拆迁”。\n\n# speaker: 科尔\n这不是平反。只是旧码头第一次看见官方故事裂开了一条缝。")))
    (react
      :when (and (>= (clock-value reporter_aftershock) 2)
                 reporter_aftershock_started
                 (not reporter_aftershock_2_seen))
      :then (list
        (effect 'set reporter_aftershock_2_seen true)
        (effect 'start-quick-dialogue "# 头版之后：剧院\n\n# speaker: 科尔\n夜莺取消了一次公开露面。剧院门口的花篮还在，但记者比观众更多。\n\n# speaker: 科尔\n她终于不再只是幸存者。这个位置让她更危险，也更自由。")))
    (react
      :when (and (>= (clock-value reporter_aftershock) 3)
                 reporter_aftershock_started
                 (not reporter_aftershock_3_seen))
      :then (list
        (effect 'set reporter_aftershock_3_seen true)
        (effect 'start-quick-dialogue "# 头版之后：新的敌人\n\n# speaker: 科尔\n一个陌生人把信封放在我办公室门缝下。里面没有威胁，只有一张私人俱乐部的请柬。\n\n# speaker: 科尔\n真相刚刚开始产生后果。下一步，他们不会只想让我闭嘴。")))
    ))

(define (nightingale-cycle-start-effects)
  (list
    (when newspaper_first_visit_done
      (effect 'clock- press_alert (clock-value press_alert)))
    (when (and reporter_frontpage_published
               (not reporter_rumor_event_active)
               (not reporter_rumor_event_seen))
      (effect 'set reporter_rumor_event_active true))
    (when (and reporter_frontpage_published
               reporter_rumor_event_active
               (= reporter_rumor_event_location 'none))
      (effect 'set reporter_rumor_event_location (reporter-rumor-location-for-day)))
    (when (and reporter_frontpage_published
               reporter_rumor_event_active
               (= reporter_rumor_event_expires_day 0))
      (effect 'set reporter_rumor_event_expires_day (+ day 2)))
    (when (and reporter_rumor_event_active
               (> reporter_rumor_event_expires_day 0)
               (>= day reporter_rumor_event_expires_day))
      (effect 'set reporter_rumor_event_active false))
    (when (and (not reporter_rumor_event_active)
               (> reporter_rumor_event_expires_day 0)
               (not reporter_rumor_event_seen))
      (effect 'set reporter_rumor_event_seen true))
    (when (and (not reporter_rumor_event_active)
               (> reporter_rumor_event_expires_day 0))
      (effect 'set reporter_rumor_event_location 'none))
    (when (and reporter_headline_wait_started
               (not reporter_more_proof_needed)
               (> day reporter_headline_wait_checked_day))
      (effect 'clock+ reporter_headline_wait (- day reporter_headline_wait_checked_day)))
    (when (and reporter_headline_wait_started
               (not reporter_more_proof_needed)
               (> day reporter_headline_wait_checked_day))
      (effect 'set reporter_headline_wait_checked_day day))
    (when (and reporter_aftershock_started
               (not (clock-filled? reporter_aftershock))
               (> day reporter_aftershock_checked_day))
      (effect 'clock+ reporter_aftershock (- day reporter_aftershock_checked_day)))
    (when (and reporter_aftershock_started
               (not (clock-filled? reporter_aftershock))
               (> day reporter_aftershock_checked_day))
      (effect 'set reporter_aftershock_checked_day day))))

(define (reporter-rumor-location-for-day)
  (cond
    ((= (mod day 3) 0) 'stall)
    ((= (mod day 3) 1) 'docks)
    (else 'newspaper)))

(define (reporter-rumor-text)
  (cond
    ((= reporter_rumor_event_location 'stall)
      "# 街边摊贩的低声话\n\n# speaker: 摊贩\n“今天少了两艘船靠岸。不是没货，是没人想在报纸上被拍到和旧码头站太近。”\n\n# speaker: 科尔\n汤锅还在冒热气，排队的人却比平时少。头版不是命令，但它已经让一些人开始重新算账。")
    ((= reporter_rumor_event_location 'docks)
      "# 旧码头的墙边\n\n# speaker: 码头工人\n“他们说莱恩是疯子。报纸现在说，疯子后面还有人拿尺子画线。”\n\n# speaker: 科尔\n没人因此原谅莱恩。可他们终于开始问：如果故事早就写好了，谁拿着笔？")
    (else
      "# 报社门口\n\n# speaker: 报童\n“加印！旧码头那篇加印！”\n\n# speaker: 科尔\n报童喊得越响，报社门口的西装就越多。城市不是相信了另一种真相，只是发现真相可以不止一种。")))

(define (reporter-rumor-event-action location-id)
  (when (and reporter_rumor_event_active
             (= reporter_rumor_event_location location-id))
    (action
      :title "听见关于头版的街头议论"
      :desc "头版已经印出去，城市开始用自己的方式复述它。停下来听一会儿。"
      :effects (list
        (effect 'set reporter_rumor_event_active false)
        (effect 'set reporter_rumor_event_seen true)
        (effect 'set reporter_rumor_event_location 'none)
        (effect 'start-quick-dialogue (reporter-rumor-text))))))

(define nightingale-tasks
  (list
    (task
      :kind '主线
      :title "保护夜莺：剧院里的第二封信"
      :desc "去剧院见夜莺。第二封威胁信刚刚送到，送信的人可能还在附近。"
      :active nightingale_theater_unlocked
      :completed nightingale_city_day_started
      :failed false
      :steps (list
        (step :title "和前门保安交谈" :completed nightingale_front_done)
        (step :title "在舞台见到夜莺" :completed nightingale_commission_taken)
        (step :title "搜查剧院里的送信路线" :completed nightingale_shadow_seen)
        (step :title "追上可疑人影" :completed nightingale_first_confrontation_done)))
    (task
      :kind '主线
      :title "三天内追查送信路线"
      :desc "你被打昏后醒来，身体状态很差。先找医生和食物撑住，再顺着城市里的线索追查下一次送信。"
      :active nightingale_city_day_started
      :completed nightingale_first_letter_done
      :failed nightingale_trust_failed
      :steps (list
        (step :title "去诊所处理伤势" :completed nightingale_clinic_unlocked)
        (step :title "从摊贩处打听街头跑腿" :completed nightingale_stall_checked)
        (step :title "凑钱从黑市买到送信线索" :completed nightingale_market_checked)
        (step :title "在饭摊吃几顿饭，让老板说完" :completed nightingale_restaurant_done)
        (step :title "拼出下一次送信路线" :completed nightingale_first_letter_done)))
    (task
      :kind '主线
      :title "保护夜莺：旧码头的莱恩"
      :desc "第二封威胁信没有解释所有问题，但它把线索推向旧码头。莱恩的名字开始反复出现——醉话、闹事、旧怨，以及一间已经撑不住的新店。"
      :active (and ryan_docks_unlocked (not ryan_old_shop_checked))
      :completed ryan_old_shop_checked
      :failed false
      :steps (list
        (step :title "在旧码头打听莱恩" :completed ryan_tavern_challenge_unlocked)
        (step :title "在码头酒馆问出莱恩的地址" :completed ryan_address_found)
        (step :title "找到老海伦的寄宿公寓" :completed helen_boarding_unlocked)
        (step :title "让老海伦开口" :completed helen_asleep)
        (step :title "偷偷搜索房间，拿到旧照片" :completed helen_room_searched)
        (step :title "脱身，发现有人在跟踪你" :completed ryan_followed_after_helen)
        (step :title "调查莱恩的老店铺" :completed ryan_old_shop_checked)))
    (task
      :kind '主线
      :title "保护夜莺：后台坠落事故"
      :desc "老海伦房间里的旧照片还没给出答案，剧院后台就传来事故。你必须在混乱还没结束前赶回去。"
      :active (and helen_room_searched (not press_angle_seen))
      :completed press_angle_seen
      :failed false
      :steps (list
        (step :title "回到剧院，处理后台事故" :completed theater_accident_survived)
        (step :title "调查事故现场，找到关键线索" :completed theater_accident_clue_found)
        (step :title "把旧照片和现场线索拿给夜莺看" :completed theater_photo_discussed)
        (step :title "意识到报社提前知道事故叙事" :completed press_angle_seen)))
    (task
      :kind '主线
      :title "保护夜莺：报纸的速度"
      :desc "后台事故还没冷下来，报社已经像提前拿到了故事。去贝城晚报，查清谁在给记者喂料。"
      :active (and newspaper_office_unlocked (not press_feed_confirmed))
      :completed press_feed_confirmed
      :failed false
      :steps (list
        (step :title "前往贝城晚报" :completed newspaper_first_visit_done)
        (step :title "调查事故稿件的来源" :completed press_source_found)
        (step :title "找到提前送来的事故口径便条" :completed press_note_found)
        (step :title "在报社逼小报记者让步" :completed reporter_negotiation_done)
        (step :title "确认莱恩与报社线索有关" :completed press_feed_confirmed)))
    (task
      :kind '主线
      :title "保护夜莺：拆迁废墟里的莱恩"
      :desc "报社便条把莱恩重新推回旧码头。拆迁封锁线内藏着首演夜真正的背景：庆功、剪彩、游行和一个被需要的疯子。"
      :active (and ryan_ruins_unlocked (not premiere_night_unlocked))
      :completed premiere_night_unlocked
      :failed false
      :steps (list
        (step :title "进入旧码头拆迁封锁线" :completed ryan_ruins_unlocked)
        (step :title "收集两条拆迁和首演相关线索" :completed ryan_found_in_ruins)
        (step :title "在废墟里发现莱恩" :completed ryan_found_in_ruins)
        (step :title "与莱恩在拆迁废墟中对峙" :completed ryan_ruins_confronted)
        (step :title "被干涉调查的警察带走" :completed ryan_police_interfered)
        (step :title "熬过警局审问，赶往首演夜" :completed premiere_night_unlocked)))
    (task
      :kind '主线
      :title "保护夜莺：首演夜"
      :desc "你从警局脱身赶到剧院。夜莺马上就要登台。剧院外围的警力密得不正常，暗处有人已经等了一晚。做好你该做的事，等枪响。"
      :active (and premiere_night_unlocked (not premiere_night_completed))
      :completed premiere_night_completed
      :failed false
      :steps (list
        (step :title "检查剧院外围的警力布防" :completed premiere_perimeter_checked)
        (step :title "在贵宾休息室探听口风" :completed premiere_vip_lounge_visited)
        (step :title "去后台见夜莺" :completed premiere_backstage_visited)
        (step :title "在首演现场追击黑影" :completed premiere_chase_completed)))
    (task
      :kind '主线
      :title "结案之后：头版之前"
      :desc "小报记者愿意刊登另一种说法，但这不是交换资源的按钮。你把证据交出去后，城市会先开始反应；而报社会要求你继续把这篇报道撑起来。"
      :active (and reporter_storyline_unlocked (not reporter_frontpage_published))
      :completed reporter_frontpage_published
      :failed false
      :steps (list
        (step :title "和小报记者再次见面" :completed reporter_second_meeting_done)
        (step :title "把首演夜和旧码头的材料交给他" :completed reporter_evidence_committed)
        (step :title "等待三天，让报道开始影响城市" :completed reporter_more_proof_needed)
        (step :title "补强报道，让它压得住压力" :completed reporter_frontpage_ready)
        (step :title "决定刊登头版" :completed reporter_frontpage_published)))
    (task
      :kind '主线
      :title "头版之后：城市回声"
      :desc "报道已经刊出。它不会立刻带来真相大白，只会让旧码头、剧院、警局和上层社会都开始重新摆放自己的位置。"
      :active reporter_frontpage_published
      :completed (clock-filled? reporter_aftershock)
      :failed false
      :steps (list
        (step :title "旧码头开始重新谈论莱恩" :completed reporter_aftershock_1_seen)
        (step :title "剧院和夜莺的受害者位置开始动摇" :completed reporter_aftershock_2_seen)
        (step :title "上层社会开始向你递出新的邀请" :completed reporter_aftershock_3_seen)))))

(define (press-alert-factors)
  (list
    (factor -1 :when (>= (clock-value press_alert) 1) :label "报社起疑")
    (factor -1 :when (>= (clock-value press_alert) 2) :label "有人盯着你")
    (factor -1 :when (>= (clock-value press_alert) 3) :label "快被赶出去")))

(define (press-source-action title desc suit ok-text partial-text fail-text)
  (when (not press_source_found)
    (action
      :title title
      :desc desc
      :check (check
        :suit suit
        :risk 'mid
        :factors (press-alert-factors)
        :ok (outcome (list (effect 'clock+ press_source 2)) ok-text)
        :partial (outcome (list (effect 'clock+ press_source 1) (effect 'clock+ press_alert 1)) partial-text)
        :fail (outcome (list (effect 'clock+ press_alert 1) (effect 'add pressure 1)) fail-text)))))

(define (报社编辑室)
  (node
    :title "编辑室"
    :desc "编辑们把烟灰弹在校样边上。这里的每一行字都像刚从事故现场跑回来，但有些标题跑得太早。"
    :show-clocks (list
      press_source
      press_alert)
    :actions (list
      (press-source-action
        "翻看事故稿的修改痕迹"
        "标题从“后台意外”改成“旧情人威胁”，改得太熟练，像有人早就知道该往哪个方向写。"
        敏锐
        "你在校样边缘找到旧标题，改稿时间早得不合常理。"
        "你看见一处改稿时间，但编辑开始问你是哪家报社的人。"
        "编辑把校样从你手下抽走，声音冷得像铅字。")
      (press-source-action
        "套问值班编辑的口风"
        "他不会承认稿源，但会记得谁把这篇稿子催得最急。"
        魅力
        "他漏出一句：事故发生前，记者已经在等“旧码头那条线”。"
        "他多说了半句，也立刻意识到自己说多了。"
        "他让你离稿桌远点，整个编辑室都听见了。"))))

(define (报社排版间)
  (node
    :title "排版间"
    :desc "铅字、油墨和机器声把话压得很低。排版时间不会撒谎，除非有人提前把谎话排好了。"
    :show-clocks (list
      press_source
      press_alert)
    :actions (list
      (press-source-action
        "核对铅字排版时间"
        "版面上有事故稿的位置。真正的问题是，这块位置是什么时候被空出来的。"
        知识
        "排字工的记录显示，事故稿的版位在电话打来前就预留好了。"
        "你找到一条时间记录，但排字工已经开始收本子。"
        "机器声盖过你的问题，排字工只当你在找麻烦。")
      (press-source-action
        "翻找废弃校样"
        "废纸篓里的早版校样可能比记者嘴里的解释更诚实。"
        敏锐
        "一张废样上已经写着莱恩的名字，旁边还圈了旧码头。"
        "你捡到半张废样，手指上沾满油墨，也被人看见了。"
        "废纸篓被人一脚踢远，你只抓到一手油墨。"))))

(define (记者工位)
  (node
    :title "记者工位"
    :desc "桌上摊着笔记本、电话记录和没喝完的咖啡。记者本人不在，但他的稿子已经替他占好了位置。"
    :show-clocks (list
      press_source
      press_alert)
    :actions (list
      (press-source-action
        "检查记者的电话记录"
        "如果事故消息来得太快，电话铃一定比事故先响过。"
        知识
        "电话记录里有一个没有署名的号码，时间早于剧院正式通报。"
        "你抄下一段号码，报社职员也记住了你的脸。"
        "电话簿被人合上，你只看见几个断开的数字。")
      (press-source-action
        "搜记者笔记本夹层"
        "记者写得很快，但真正危险的东西通常不会写在明面上。"
        敏锐
        "夹层里有一角便条，关键词和事故稿完全对得上。"
        "你摸到夹层，却不得不先把本子放回原位。"
        "抽屉响得太大，隔壁桌的打字声停了一拍。"))))

(define (贝城晚报)
  (node
    :title "贝城晚报"
    :desc "印刷机在楼后震动，编辑室里全是烟味和铅字味。这里不生产真相，只生产能赶上明早的版本。"
    :position '(1080 500)
    :show-clocks (list
      (when (and newspaper_first_visit_done (not press_source_found)) press_source)
      (when (and newspaper_first_visit_done (not press_source_found)) press_alert)
      (when (and reporter_evidence_committed (not reporter_more_proof_needed)) reporter_headline_wait)
      (when (and reporter_more_proof_needed (not reporter_frontpage_ready)) reporter_story_strength)
      (when reporter_aftershock_started reporter_aftershock))
    :actions (list
      (when (not newspaper_first_visit_done)
        (action
          :title "走进贝城晚报"
          :desc "后台事故还没冷下来，报社已经把铅字烧热。你得先看清这台机器在印什么。"
          :effects (list
            (effect 'set newspaper_first_visit_done true)
            (effect 'start-quick-dialogue "# 贝城晚报\n\n# speaker: 科尔\n印刷机在楼后震动。后台事故的稿子已经排进版面，标题里有莱恩，有夜莺，也有旧码头。\n\n# speaker: 科尔\n报社不是跑得快。它像是提前知道该往哪里跑。"))))
      (when (and reporter_negotiation_unlocked (not reporter_negotiation_done))
        (action
          :title "逼小报记者说出便条来路"
          :desc "便条给了你谈判的筹码。现在问题不是问他知不知道，而是让他承认自己知道多少。"
          :effects (list
            (effect 'start-encounter "报社谈判交锋")))))
      (when (and reporter_storyline_unlocked (not reporter_second_meeting_done))
        (action
          :title "和小报记者再次见面"
          :desc "他这次没有装作偶遇。首演夜之后，所有人都想尽快把故事定型，而他想在定型前撕开一道口子。"
          :effects (list
            (effect 'set reporter_second_meeting_done true)
            (effect 'start-quick-dialogue "# 小报记者再次找你\n\n# speaker: 小报记者\n“官方版本太顺了。顺到像昨晚之前就已经排好版。”\n\n# speaker: 科尔\n“你想刊出来？”\n\n# speaker: 小报记者\n“我想活着刊出来。所以你得给我能撑住三天的东西。”"))))
      (when (and reporter_second_meeting_done
                 (not reporter_evidence_committed))
        (action
          :title "把首演夜材料交给记者"
          :desc "这一步不是换奖励。材料交出去以后，故事就会开始离开你的手，进入报社、警局、剧院和街头。"
          :conditions (list (field-eq 'premiere_night_completed true "需要完成首演夜"))
          :effects (list
            (effect 'set reporter_evidence_committed true)
            (effect 'set reporter_headline_wait_started true)
            (effect 'set reporter_headline_wait_checked_day day)
            (effect 'start-quick-dialogue "# 材料交出去\n\n# speaker: 科尔\n我把首演夜的材料放到他桌上：莱恩出现前就准备好的警力、包厢里的电话、后台那条不该出现的路线。\n\n# speaker: 小报记者\n他没有立刻翻，先看了我一眼。\n\n# speaker: 小报记者\n“从现在开始，这东西会让很多人睡不着。你也是。”"))))
      (when (and reporter_more_proof_needed
                 (not reporter_editor_pressure_done)
                 (not reporter_frontpage_ready))
        (action
          :title "在编辑室顶住压稿压力"
          :desc "编辑想要能自保的说法，律师想要能吓退你的说法。你必须让这篇稿子还有站上版面的勇气。"
          :check (check
            :suit 魅力
            :risk 'high
            :ok (outcome (list
              (effect 'set reporter_editor_pressure_done true)
              (effect 'clock+ reporter_story_strength 1))
              "你让编辑承认：不刊登也是一种站队。")
            :partial (outcome (list
              (effect 'set reporter_editor_pressure_done true)
              (effect 'clock+ reporter_story_strength 1)
              (effect 'add pressure 1))
              "编辑答应继续留版面，但你的名字被写进了报社门房的记录。")
            :fail (outcome (list (effect 'add pressure 1)) "编辑把稿纸压回抽屉，说他不能拿整间报社替你赌。"))))
      (when (and reporter_frontpage_ready (not reporter_frontpage_published))
        (action
          :title "决定刊登头版"
          :desc "这不是结局，只是让另一种版本进入城市。刊登之后，旧码头、夜莺、剧院和上层都会开始被它改变。"
          :effects (list
            (effect 'set reporter_frontpage_published true)
            (effect 'set reporter_aftershock_started true)
            (effect 'set reporter_aftershock_checked_day day)
            (effect 'start-quick-dialogue "# 头版刊出\n\n# speaker: 小报记者\n铅字压上纸面时，机器声像一场低沉的雨。\n\n# speaker: 小报记者\n“明早，这座城会多一个版本。”\n\n# speaker: 科尔\n“真相？”\n\n# speaker: 小报记者\n“别太贪心，侦探。先让他们不能只相信那一个版本。”"))))
      (reporter-rumor-event-action 'newspaper))
    :children (list
      (when (and newspaper_first_visit_done (not press_source_found)) (报社编辑室))
      (when (and newspaper_first_visit_done (not press_source_found)) (报社排版间))
      (when (and newspaper_first_visit_done (not press_source_found)) (记者工位))))

(define (nightingale-stall-investigation-action)
  (when (and nightingale_commission_taken
             (not nightingale_second_letter_ready)
             (not nightingale_stall_checked))
    (action
      :title "打听谁替剧院跑过信"
      :desc "摊贩看街的时间比警察还久。送信的人如果匆忙经过，这里最容易留下口风。"
      :check (check
        :suit 敏锐
        :risk 'low
        :ok (outcome (list
          (effect 'set nightingale_stall_checked true)
          (effect 'clock+ nightingale_first_letter_progress 1)
          (effect 'start-quick-dialogue nightingale-stall-text)))
        :partial (outcome (list
          (effect 'set nightingale_stall_checked true)
          (effect 'clock+ nightingale_first_letter_progress 1)
          (effect 'add pressure 1)
          (effect 'start-quick-dialogue nightingale-stall-text)))
        :fail (outcome (list (effect 'add pressure 1)) "摊贩先顾着手里的热汤，不想把你的问题也一起端起来。")))))

(define (nightingale-blackmarket-investigation-action)
  (when (and nightingale_commission_taken
             (not nightingale_second_letter_ready)
             (not nightingale_market_checked))
    (action
      :title "花钱买送信人的来路"
      :desc "黑市掌柜把消息切成几段卖。十块钱，他就把送信人的关键名字吐出来。"
      :conditions (list (field-at-least 'money 100 "需要 100 元"))
      :inputs (list (item 'money 100 "消息费"))
      :effects (list
        (effect 'set nightingale_market_checked true)
        (effect 'clock+ nightingale_first_letter_progress 1)
        (effect 'start-quick-dialogue nightingale-market-text)))))

(define (nightingale-bar-context-action)
  (when (and nightingale_commission_taken
             (not nightingale_lore_known)
             (not nightingale_bar_checked))
    (action
      :title "和小报记者聊夜莺的首演"
      :desc "酒吧里总有人比报纸更早拿到草稿。问题只是你愿意让谁记住你在问。"
      :effects (list
        (effect 'set nightingale_bar_checked true)
        (effect 'clock+ nightingale_lore_progress 1)
        (effect 'start-quick-dialogue nightingale-bar-text)))))

(define (旧码头卸货)
  (node
    :title "旧码头卸货"
    :desc "码头临时招人手卸货，干一天结一天钱。机会不等人。"
    :position '(700 520)
    :show-clocks (list nightingale_side_job_clock)
    :actions (list
      (action
        :title "帮忙卸货"
        :desc "搬几趟箱子，出点力气换工钱。"
        :check (check
          :suit 暴力
          :risk 'low
          :ok (outcome (list (effect 'clock+ nightingale_side_job_clock 1)) "你干得利索，工头点头记了一工。")
          :partial (outcome (list (effect 'clock+ nightingale_side_job_clock 1)) "活不算重，你勉强跟上了节奏。")
          :fail (outcome (list) "今天不缺人手，你白等了一趟。"))))))
