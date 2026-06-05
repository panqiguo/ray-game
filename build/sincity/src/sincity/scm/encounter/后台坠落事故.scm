(include "../enum-symbols.scm")
(include "../common_clock_macros.scm")
(include "../common_world_bindings.scm")

(define-fragment rush-the-falling-rig
  (action
    :title "冲向坠落的灯架"
    :desc "灯架从黑暗里晃下来，金属摩擦声刺得人牙根发酸。你只能先冲过去，把最近的人推出去。"
    :check (check
      :suit 敏锐
      :risk 'high
      :ok (outcome (list (effect 'clock+ control 2)) "你撞开一个舞台工，灯架砸在他刚才站的位置。")
      :partial (outcome (list (effect 'clock+ control 1) (effect 'clock+ nightingale_danger 1)) "你救下一个人，另一侧的吊绳却继续往下滑。")
      :fail (outcome (list (effect 'clock+ nightingale_danger 1) (effect 'add 'health -1)) "你被灯架边缘擦中，后台的尖叫声更近了。"))))

(define-fragment pull-nightingale-away
  (action
    :title "把夜莺拖离舞台侧门"
    :desc "有人在喊她的名字，也有人在把人往错误的出口推。你看见夜莺站在灯影下面，半秒之后就会太晚。"
    :check (check
      :suit 暴力
      :risk 'mid
      :ok (outcome (list (effect 'clock+ control 2)) "你抓住她的手腕，把她从坠落的阴影里拖出来。")
      :partial (outcome (list (effect 'clock+ control 1) (effect 'add 'health -1)) "你把她带出来，自己肩膀撞上道具箱。")
      :fail (outcome (list (effect 'clock+ nightingale_danger 2)) "人群把你们隔开，夜莺被推向更窄的通道。"))))

(define-fragment stop-the-backstage-crowd
  (action
    :title "喊停后台人群"
    :desc "混乱会自己找出口。你必须让这些人先听见一个比尖叫更硬的声音。"
    :check (check
      :suit 魅力
      :risk 'mid
      :ok (outcome (list (effect 'clock+ control 2)) "几个工人停住脚步，终于有人开始按你的方向搬人。")
      :partial (outcome (list (effect 'clock+ control 1) (effect 'clock+ nightingale_danger 1)) "有人听见了，也有人继续往错的方向挤。")
      :fail (outcome (list (effect 'clock+ nightingale_danger 1) (effect 'add 'pressure 1)) "你的声音被尖叫和木板断裂声吞掉了。"))))

(define-fragment grab-the-stagehand
  (action
    :title "抓住乱跑的舞台工"
    :desc "他不是在逃命。他在喊错出口，像是早知道哪条路会变成死路。"
    :check (check
      :suit 敏锐
      :risk 'mid
      :ok (outcome (list (effect 'clock+ control 2)) "你把他按在布景板上。他眼神里的恐惧不像意外，更像露馅。")
      :partial (outcome (list (effect 'clock+ control 1) (effect 'clock+ nightingale_danger 1)) "你扯住了他的袖子，他挣脱前丢下一句：“不是我喊的！”")
      :fail (outcome (list (effect 'clock+ nightingale_danger 1)) "他钻进人群里，只留下一个仓皇的背影。"))))

(define-fragment cut-the-second-rope
  (action
    :title "割断另一根摇晃的绳"
    :desc "还有一组布景吊在半空。按正常流程不该这样晃，按现在的声音，它马上就会落下来。"
    :check (check
      :suit 知识
      :risk 'high
      :ok (outcome (list (effect 'clock+ control 3)) "你找准受力点割断绳头，布景斜落在空地上。")
      :partial (outcome (list (effect 'clock+ control 1) (effect 'clock+ nightingale_danger 1)) "布景没有砸中人，但落点比你预想得近。")
      :fail (outcome (list (effect 'clock+ nightingale_danger 2)) "你判断错了受力方向，另一侧开始下坠。"))))

(define-fragment protect-the-old-photo
  (action
    :title "护住口袋里的旧照片"
    :desc "你撞过一排道具箱时，口袋里的照片差点滑出来。它不是现在最重的东西，却可能是之后唯一能说话的东西。"
    :check (check
      :suit 敏锐
      :risk 'low
      :ok (outcome (list (effect 'clock- nightingale_danger 1) (effect 'clock+ control 1)) "照片还在。你也趁低身避开了一块飞来的木片。")
      :partial (outcome (list (effect 'clock+ control 1)) "照片被你按回内袋，纸角已经潮了。")
      :fail (outcome (list (effect 'clock+ nightingale_danger 1)) "你慢了一拍，差点被后退的人群撞倒。"))))

(content
  :meta (meta :key '后台坠落事故 :title "后台坠落事故" :desc "剧院后台的灯架和布景开始坠落。事故还在发生，你必须先让人活下来。")
  :on-success (list
    (effect 'set 'theater_accident_survived true)
    (effect 'set 'nightingale_saved true)
    (effect 'set 'accident_sabotage_seen true)
    (effect 'start-quick-dialogue "# 后台事故\n\n# speaker: 科尔\n夜莺的手还在发抖。她看着坠落的灯架，没有哭。\n\n# speaker: 科尔\n事故被压下去了，但后台没有安静。每个人都在说话，每个人也都像漏掉了最重要的一句。"))
  :on-fail (list
    (effect 'set 'theater_accident_survived true)
    (effect 'set 'nightingale_hurt true)
    (effect 'set 'accident_sabotage_seen true)
    (effect 'add 'health -1)
    (effect 'start-quick-dialogue "# 后台事故\n\n# speaker: 科尔\n灯架落下来的声音不像事故，像一记早就排练好的鼓点。\n\n夜莺被人扶走时，脸色白得像舞台上的粉。\n\n# speaker: 科尔\n事故结束了，麻烦没有。后台的人开始整理碎木头，也开始整理他们准备说出口的版本。"))
  :reacts (list
    (react :when (clock-filled? control) :then (list (effect 'end-encounter 'success)))
    (react :when (clock-filled? nightingale_danger) :then (list (effect 'end-encounter 'fail))))
  :vars (append
    world-basics-vars
    (list
      (var 'control (clock :title "控制局面" :desc "稳住人群、布景和夜莺的位置。填满后事故被压住。" :initial 0 :max 5))
      (var 'nightingale_danger (clock :title "夜莺的危险" :desc "坠落、踩踏和错误指令正在把夜莺推向事故中心。填满则她会受伤。" :initial 0 :max 4))))
  :root
  (scene
    :title "剧院后台"
    :desc "尖叫从幕布后面炸开。灯架、绳索、布景板和乱跑的人挤成一团，夜莺的名字被一遍遍喊出来。"
    :show-clocks (list control nightingale_danger)
    :actions (list
      (rush-the-falling-rig)
      (pull-nightingale-away)
      (stop-the-backstage-crowd)
      (grab-the-stagehand)
      (cut-the-second-rope)
      (protect-the-old-photo))))
