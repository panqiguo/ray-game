Encounter / World SCM 速查

顶层：

```scheme
(include "common.scm")
(define name expr)
(define-node name node-expr)
(define-scene name scene-expr)

(content
  :meta meta-expr
  :state state-expr
  :reacts reacts-expr
  :on-success (list effect...)
  :on-fail (list effect...)
  :root node-expr)
```

- 顶层 `define` 会在模块加载时立即求值，和标准 Scheme 更接近。
- `define-node` / `define-scene` 是零参数过程糖，适合动态 node/scene。
- 使用 `define-node` / `define-scene` 后，引用时要显式调用：`(office)`、`(room_search)`。
- `define-node` / `define-scene` 的直接 `(node ...)` / `(scene ...)` 没写 `:title` 时，会自动使用定义名作为标题。
- 如果只是静态常量、文本、helper lambda，用普通 `define`。

`meta`：

```scheme
(meta :key 'city_1 :title "标题" :desc "描述")
```

- 必填：`:key` `:title`
- 选填：`:desc`

`state`：

```scheme
(state
  (field initial)
  (clock-field (clock ...)))
```

`clock`：

```scheme
(clock :title "名称" :initial 0 :max 4)
```

- 必填：`:title` `:initial` `:max`

字段作用域：

- encounter 局部字段：encounter `:state` 绑定
- encounter 需要读写世界状态时，先在 `:state` 显式导入：
  - 角色属性：`(energy (world-attr 'energy))`、`(health (world-attr 'health))`
  - 世界物品：`(money (world-item 'money 0))`
  - 世界值：`(case_done (world-value 'case_done false))`
- 可 include `common_world_bindings.scm` 使用 helper 展开常用绑定：`(use-world-health)`、`(use-world-energy)`、`(use-world-money)`、`(use-world-food)`、`(use-world-basics)`。
- 修改字段统一写已绑定的字段名：`money`、`health`、`energy`、`villa_job_taken`
- `stress` 是旧字段名兼容层；新内容优先写 `energy`。`(effect 'add energy -1)` 表示精力减少 1。
- completion bucket（`:on-success` / `:on-fail`）可以使用已导入的世界绑定；未在 `:state` 导入的世界字段继续使用 quoted key，例如 `(effect 'add 'money 20)`。
- `day` 是特例：修改只用 `(effect 'advance-day)`

`node` / `scene`：

```scheme
(node
  :title "标题"
  :desc "描述"
  :position '(120 80)
  :show-clocks (list clock-a clock-b)
  :conditions (list condition...)
  :actions (list action-a action-b)
  :children (list node-a node-b))
```

- 必填：`:title`
- 选填：`:desc` `:position` `:show-clocks` `:conditions` `:actions` `:children`

`action`：

```scheme
(action
  :title "标题"
  :desc "描述"
  :position '(120 80)
  :conditions (list condition...)
  :inputs (list input...)
  :always (list effect...)
  :effects (list effect...)
  :check check-expr)
```

- 必填：`:title`
- 选填：`:desc` `:position` `:conditions` `:inputs` `:always` `:effects` `:check`
- `:always` 会在行动执行时先触发，可与 `:effects` 或 `:check` 共存
- `:check` 与 `:effects` 互斥

`check`：

```scheme
(check
  :suits (list 'logic 'perception)
  :risk 'mid
  :factors (list
    (factor -1 :when security_online :label "监控")
    (factor 1 :when power_cut :label "断电"))
  :ok outcome
  :partial outcome
  :fail outcome)
```

- `:risk`：`'low` `'mid` `'high`
- `:suits`：`'logic` `'perception` `'willpower`
- 不写 `:suits` 或写空列表时，表示不使用人物属性加成
- 写了 `:suits` 时，行动卡本身仍然无属性；最终值 = 行动卡点数 + 使用者对应属性 + 启用的 `:factors`
- `factor` 用于环境/场景状态修正，`:when` 为真时启用；会显示在行动卡上，例如 `监控 -1`

`outcome`：

```scheme
(outcome "结果文本" (list effect...))
```

`react` / `reacts`：

```scheme
(react
  :when expr
  :then (list effect...))

(reacts
  (react ...)
  some-react
  (when cond (react ...)))
```

`conditions`：

```scheme
:conditions (list
  (has-item 'clothes 1 "需要体面的衣服")
  (field-at-least 'money 20 "需要 20 美钞")
  (field-below 'cash_search_count 4 "零钱已经翻空")
  (field-truthy 'hotel_pass "需要先取得使用权")
  (condition 'clock_at_least "alert:2" "警觉至少 2"))
```

- `conditions` 只表示“满足时才可用”
- 是否出现优先用 `if` / `when` / `cond`

`inputs`：

```scheme
(item 'money 20 "美钞")
(item 'lockpick 1 "开锁器")
(card 'any)
(card 'negative "负面牌")
```

- `card` 输入现在表示“要求放入一项本回合可用的精力”

`effects`：

```scheme
(effect 'clock+ clock-field amount)
(effect 'clock- clock-field amount)
(effect 'set field value)
(effect 'add field amount)
(effect 'copy target-field source-field)
(effect 'start-dialogue 'dialogue_id)
(effect 'start-quick-dialogue "对白内容")
(effect 'start-encounter 'encounter_id)
(effect 'end-encounter 'success)
(effect 'end-encounter 'fail)
(effect 'end-encounter 'abort)
(effect 'advance-day)
(effect 'end-game)
(effect 'end-game "结局标题" "结局正文")
(effect 'reset-hand)
```

- `(effect 'reset-hand)` 现在的语义是“按健康状态抽取新的行动卡”
- `(effect 'advance-day)` 会推进一天，并使精力 -1
- `(effect 'set field value)` 只设置字面值；复制当前字段值使用 `(effect 'copy target source)`。
- 已废弃短名效果：不要写 `(effect 'health -1)` / `(effect 'stress 1)`
- 推荐写法：先在 `:state` 导入，再写 `(effect 'add health -1)`、`(effect 'add energy -1)`、`(effect 'add money 20)`

时钟查询：

```scheme
(clock-value clock-field)
(clock-max clock-field)
```

`common_clock_macros.scm`：

```scheme
(clock-half clock-field)
(clock-empty? clock-field)
(clock-filled? clock-field)
(clock-partial? clock-field)
(clock-at-least-half? clock-field)
(effect-reset-clock clock-field)
```

基础 Scheme：

```scheme
(if cond a b)
(when cond expr)
(cond (cond expr) (else expr))
(and ...)
(or ...)
(not expr)
(let ((name expr)) body)
(let* ((name expr)) body)
(lambda (args...) body)
(begin ...)
(quote x)
'x
(console-log ...)
```

- `let` 是标准并行绑定：绑定表达式在外层环境求值。
- `let*` 是顺序绑定：后一个绑定可以使用前一个绑定。
- truthiness：只有 `false` 和 `nil` 为假；`0` 和空列表都是真。
- `(- x)` 是一元取负。
- `(console-log ...)` 会打印到 Python 终端，返回最后一个参数；常用于调试脚本

列表：

```scheme
(list ...)
(car xs)
(cdr xs)
(cons x xs)
(append xs ys)
(length xs)
(list? x)
(pair? x)
(map f xs)
(filter f xs)
(member x xs)
(reverse xs)
(apply f xs)
```

alist：

```scheme
(assoc 'key table)
(assoc-ref table 'key)
(assoc-set table 'key value)
(assoc-remove table 'key)
```

精神与成长：

- 初始精神：`logic = 2`，`perception = 1`，`willpower = 1`
- 每种精力默认 1 项；重大升级可以增加额外精力项
- 每个槽位每回合只能使用 1 次
- 受伤会按固定顺序给槽位叠加创伤；每层创伤让该槽位当前值 `-2`

数值/比较：

```scheme
(+ ...)
(- ...)
(min ...)
(max ...)
(= a b)
(< a b)
(<= a b)
(> a b)
(>= a b)
```

判定：

```scheme
(null? value)
(number? value)
(string? value)
(boolean? value)
(symbol? value)
```
