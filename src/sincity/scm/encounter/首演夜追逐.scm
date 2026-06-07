(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

;; Phase 1 — 舞台侧幕
(define-fragment side-stage-a
  (when (= chase_phase 'side_stage)
    (action
      :title "追上去"
      :desc "翻过舞台设备追出去。他消失在走廊尽头——那扇门不该通往任何地方。"
      :effects (list
        (effect 'set chase_phase 'backstage)
        (effect 'set clue_program true)
        (effect 'start-quick-dialogue "# 侧幕\n\n# speaker: 科尔\n幕布还在晃。那个人翻过音响箱，像提前排练过每一步。你追到走廊尽头，没有岔路，没有窗户——但已经空了。\n\n# speaker: 科尔\n地上有一张皱巴巴的节目单。莱恩的名字被人用笔圈了两遍。")))))

(define-fragment side-stage-b
  (when (= chase_phase 'side_stage)
    (action
      :title "先看他蹲过的地方"
      :desc "他在那里停了片刻，像在等什么。地上有痕迹。"
      :effects (list
        (effect 'set chase_phase 'backstage)
        (effect 'set clue_program true)
        (effect 'start-quick-dialogue "# 侧幕\n\n# speaker: 科尔\n他蹲过的地方有一个湿鞋印，鞋码不大，步距均匀——不像匆忙赶来的人留下的。\n\n# speaker: 科尔\n旁边落着一张节目单。莱恩的名字被人用笔圈了两遍，墨迹还没完全干。\n\n# speaker: 科尔\n有人在首演前就知道他会来。或者说，有人希望他出现在这里。")))))

;; Phase 2 — 后台走廊
(define-fragment backstage-a
  (when (= chase_phase 'backstage)
    (action
      :title "紧追不舍"
      :desc "你全力冲刺追上去。他在尽头停顿了一下——回头那一眼太稳了。"
      :effects (list
        (effect 'set chase_phase 'storage)
        (effect 'set clue_wallet true)
        (effect 'start-quick-dialogue "# 后台走廊\n\n# speaker: 科尔\n你追进走廊。应急灯把影子拉得很长。那个人在尽头停顿了一下，回头——那一眼不是恐惧，是确认。\n\n# speaker: 科尔\n他推进一扇门，门在身后弹开。里面是空的。后门在晃。地上有一只旧皮夹，边角磨得发白。\n\n# speaker: 科尔\n皮夹里夹着一张褪色的剧照——夜莺散场后的侧脸。边角磨损严重，像随身带了很久。码头酒馆的老板说过，莱恩有个从不离身的旧皮夹。")))))

(define-fragment backstage-b
  (when (= chase_phase 'backstage)
    (action
      :title "看他的动作——不对"
      :desc "这人跑动的方式不对。太轻，太熟练。莱恩不是这样的。"
      :effects (list
        (effect 'set chase_phase 'storage)
        (effect 'set clue_wallet true)
        (effect 'start-quick-dialogue "# 后台走廊\n\n# speaker: 科尔\n他的脚步太轻了。莱恩在码头干的是重活，跑起来不该这么安静。这人像踩过千百次这条走廊。\n\n# speaker: 科尔\n走廊尽头的地上躺着一只皮夹，像是什么人匆忙中掉落的。皮夹里有一张夜莺的剧照，纸边都摸软了。莱恩的东西。\n\n# speaker: 科尔\n但刚才那个人的步子，不像莱恩。")))))

;; Phase 3 — 道具仓库
(define-fragment storage-a
  (when (= chase_phase 'storage)
    (action
      :title "扑上去制伏"
      :desc "他终于停下来了。在货架之间翻找着什么。机会只有一次。"
      :check (check
        :suit 暴力
        :risk 'low
        :ok (outcome (list
          (effect 'set chase_phase 'roof)
          (effect 'set clue_jacket true))
          "你抓住了他的外套——他像条鱼一样滑了出去。外套是莱恩的旧工装，内袋里掉出一张拆迁补偿签收单。签名是莱恩，日期是首演前一天。金额高得不正常。")
        :partial (outcome (list
          (effect 'set chase_phase 'roof)
          (effect 'set clue_jacket true))
          "你只扯住衣角。外套被挣脱，人消失在货架后。补偿单从内袋飘出来——莱恩的名字，首演前一天的日期，一笔足够让他闭嘴的金额。")
        :fail (outcome (list
          (effect 'set chase_phase 'roof)
          (effect 'set clue_jacket true)
          (effect 'add 'pressure 1))
          "你扑了个空，撞进货架。他消失在后门方向。地上留着那件外套——莱恩的，内袋里有一张拆迁补偿签收单。")))))

(define-fragment storage-b
  (when (= chase_phase 'storage)
    (action
      :title "\"莱恩！停下！\""
      :desc "他不是莱恩，但这个名字是目前唯一能让他停下来的东西。"
      :check (check
        :suit 魅力
        :risk 'mid
        :ok (outcome (list
          (effect 'set chase_phase 'roof)
          (effect 'set clue_jacket true))
          "他僵住了。侧过头。光不够，你看不清脸，但你看见他嘴角有一丝笑——不是被认出的慌张，是表演被观众注意到的满足。然后他消失在货架后，留下一件莱恩的外套。")
        :partial (outcome (list
          (effect 'set chase_phase 'roof)
          (effect 'set clue_jacket true))
          "他停了一下，没有回头。脱掉外套扔向你——像在帮你确认这就是你要找的\"莱恩\"。然后他隐入暗处。")
        :fail (outcome (list
          (effect 'set chase_phase 'roof)
          (effect 'set clue_jacket true)
          (effect 'add 'pressure 2))
          "他笑了一声，很低，消失在货架深处。你没能让他停下，只在铁架缝隙里看见那件旧外套被顺手挂在钩子上——等你取走。")))))

;; Phase 4 — 屋顶
(define-fragment roof-a
  (when (= chase_phase 'roof)
    (action
      :title "上前一步"
      :desc "他就站在天台栏杆边。你已经不打算再追了——有些距离不是用速度能缩小的。"
      :effects (list
        (effect 'end-encounter 'success)
        (effect 'set clue_wire true)))))

(define-fragment roof-b
  (when (= chase_phase 'roof)
    (action
      :title "\"你不是莱恩。\""
      :desc "你不再追了。你只想听他怎么回答。"
      :effects (list
        (effect 'end-encounter 'success)
        (effect 'set clue_wire true)))))

(content
  :meta (meta :key '首演夜追逐 :title "剧院魅影" :desc "枪响后的追逐。你在黑暗的剧院里追一个神出鬼没的影子。")
  :on-success (list
    (effect 'set 'premiere_chase_completed true)
    (effect 'set 'premiere_night_completed true)
    (effect 'set 'premiere_clue_program true)
    (effect 'set 'premiere_clue_wallet true)
    (effect 'set 'premiere_clue_jacket true)
    (effect 'set 'premiere_clue_wire true)
    (effect 'add 'energy -2)
    (effect 'add 'pressure 1)
    (effect 'start-quick-dialogue "# 首演夜之后\n\n# speaker: 科尔\n剧院灯亮了。人群被疏散到街上。夜莺被人从后台扶出来，披着大衣，妆花了一半。她没受伤。\n\n# speaker: 夜莺\n“我看见你追出去了。”\n\n# speaker: 科尔\n我没办法告诉她我追到了什么——一件外套、一只旧皮夹、一张补偿单、一根窃听线。全都指向莱恩。全都太整齐。\n\n# speaker: 夜莺\n“首演完成了。”她轻声说。\n\n# speaker: 科尔\n是的。首演完成了。夜莺安全。莱恩被通缉。\n\n# speaker: 科尔\n没有更完美的结局了。\n\n# speaker: 科尔\n但我站在屋顶上，看着警车把剧院围成一个铁桶——这桶不是今晚才搭起来的。有人提前很久就搭好了。\n\n# speaker: 科尔\n我只是走进它的人。"))
  :on-fail (list
    (effect 'set 'premiere_chase_completed true)
    (effect 'set 'premiere_night_completed true)
    (effect 'set 'premiere_clue_program true)
    (effect 'set 'premiere_clue_wallet true)
    (effect 'set 'premiere_clue_jacket true)
    (effect 'set 'premiere_clue_wire true)
    (effect 'add 'pressure 2)
    (effect 'start-quick-dialogue "# 首演夜之后\n\n# speaker: 科尔\n剧院灯亮了。我没有追上他。至少在视野跟丢之前，他像烟一样散在了剧院的暗处。\n\n# speaker: 科尔\n但我找到了他留下的东西——一件外套、一只旧皮夹、一张补偿单、一根窃听线。和一句没有得到回答的质问。\n\n# speaker: 科尔\n我站在屋顶上，夜风把窃听线吹得嗡嗡响。今晚的一切都指向莱恩。\n\n# speaker: 科尔\n也许这正是他们想让我相信的。"))
  :vars (append
    world-energy-vars
    (list
      (var 'chase_phase 'side_stage)
      (var 'clue_program false)
      (var 'clue_wallet false)
      (var 'clue_jacket false)
      (var 'clue_wire false)))
  :root (cond
    ((= chase_phase 'side_stage)
      (location
        :title "舞台侧幕"
        :desc "枪响的余震还在耳膜里。舞台灯灭了，应急灯把幕布照成惨白。一个黑影蹲在舞台边缘——看见你就窜了出去。"
        :actions (list (side-stage-a) (side-stage-b))))
    ((= chase_phase 'backstage)
      (location
        :title "后台走廊"
        :desc "应急灯把走廊切成一段一段的。那个人的影子在尽头一闪。你追到拐角——他不见了，但下一扇门的把手还在晃。"
        :actions (list (backstage-a) (backstage-b))))
    ((= chase_phase 'storage)
      (location
        :title "道具仓库"
        :desc "货架之间堆着废弃布景和旧道具。他终于停下来了，在翻找什么。灯光从高窗漏进来，把他的影子切成很多块。"
        :actions (list (storage-a) (storage-b))))
    ((= chase_phase 'roof)
      (location
        :title "天台边缘"
        :desc "夜风很大。他就站在栏杆边，背对着你。楼下警车灯光旋转，把整条街照成白昼。他已经无路可走了。"
        :actions (list (roof-a) (roof-b))))))
