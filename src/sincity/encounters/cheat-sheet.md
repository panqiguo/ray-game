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
- ⚠️ **动态绑定**：lambda 内的自由变量不在定义时捕获，而在**每次调用时**从当前环境查找。这让状态字段（如 `security_online`）自然反映运行时值，但也意味着注意同名遮蔽和关键字冲突。详见 `如何写scm场景文件/SKILL.md` 中的设计说明。
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

- encounter `:state` → 局部字段
- 读写世界状态需在 `:state` 导入：`(energy (world-attr 'energy))`、`(money (world-item 'money 0))`、`(case_done (world-value 'case_done false))`
- 可 include `common_world_bindings.scm` 使用 `(use-world-basics)` 等 helper
- 未导入的世界字段用 quoted key：`(effect 'add 'money 80)`
- `day` 特例：只用 `(effect 'advance-day)`

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
  :suits (list 知识 敏锐)
  :risk 'mid
  :factors (list
    (factor -1 :when security_online :label "监控")
    (factor 1 :when power_cut :label "断电"))
  :ok outcome
  :partial outcome
  :fail outcome)
```

- `:risk`：`'low` `'mid` `'high`
- `:suits`：`暴力` `魅力` `知识` `敏锐`（或英文 `force` `charm` `knowledge` `sense`）
- `include` 了 `enum-symbols.scm` 后可使用中文符号：`暴力` `魅力` `知识` `敏锐`
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
- `(effect 'set field value)` 支持字面值、字段引用和表达式。比如 `(effect 'set checked_day day)` 会在效果执行时读取当前 `day`，`(effect 'set due_day (+ day 6))` 会在效果执行时计算当前日期 +6。
- `(effect 'copy target source)` 仍可用，但新内容优先直接写 `(effect 'set target source)`，语义更接近 Scheme。
- 已废弃短名效果：不要写 `(effect 'health -1)` / `(effect 'stress 1)`
- 推荐写法：先在 `:state` 导入，再写 `(effect 'add health -1)`、`(effect 'add energy -1)`、`(effect 'add money 20)`

时钟查询：

```scheme
(clock-value clock-field)
(clock-max clock-field)
(clock-shift clock-field amount)
(clock-reset clock-field)
```

- 在 `effect-expr` 里，顶层 state clock 和 object 内嵌 clock 都按 clock value 处理。
- 因此可以写 `(set! alert (clock-shift alert 1))`，也可以写 `(update enemy (attack (clock-shift (enemy-attack enemy) 1)))`。
- 写回顶层 clock 时，`set!` 会自动把 clock value 存回当前数值，并限制在 `0..max`。

`common_clock_macros.scm`：

```scheme
(clock-half clock-field)
(clock-empty? clock-field)
(clock-filled? clock-field)
(clock-partial? clock-field)
(clock-at-least-half? clock-field)
(effect-reset-clock clock-field)
```

基础 Scheme 函数：

- **控制流** `if` `when` `cond` `and/or/not` `let` `let*` `lambda` `begin` `quote`
- **列表** `list` `car` `cdr` `cons` `append` `length` `list?` `pair?` `map` `filter` `member` `reverse` `apply`
- **alist** `assoc` `assoc-ref` `assoc-set` `assoc-remove`
- **数值/比较** `+` `-` `min` `max` `=` `<` `<=` `>` `>=`
- **判定** `null?` `number?` `string?` `boolean?` `symbol?`
- **调试** `(console-log ...)` 打印到终端，返回最后一个参数
- `let` 并行绑定，`let*` 顺序绑定
- 仅 `false`/`nil` 为假；`0` 和空列表为真
- `(- x)` 一元取负
