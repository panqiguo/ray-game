Encounter / World SCM 速查

顶层：

```scheme
(include "common.scm")
(define name expr)
(define (name params) body...)
(define-fragment name body...)
(content
  :meta meta-expr
  :state state-expr
  :reacts reacts-expr
  :on-success (list effect...)
  :on-fail (list effect...)
  :root node-expr)
```

### define 语义（city 和 encounter 统一）

```text
define value     = 模块加载时求值一次，之后引用同一值
define function  = 调用时求值函数体
define-fragment  = 内容片段构造器，语法糖，等价于零参数函数
```

- `(define price 10)` → 静态值，编译时求值。
- `(define (make-action title desc) (action ...))` → 函数，每次调用时构造。
- `(define-fragment loan-action (when active? (action ...)))` → 等价于 `(define (loan-action) (when active? (action ...)))`，使用时显式调用 `(loan-action)`。

> ⚠️ **不要**把动态 node/action/desc/title 写成 top-level value define：
>
> ```scheme
> ;; 错误：这个 define 只求值一次，不会随状态变化
> (define loan-action
>   (when black_loan_active
>     (action ...)))
> ```
>
> ```scheme
> ;; 正确：写成函数或 define-fragment，每次引用时求值
> (define-fragment loan-action
>   (when black_loan_active
>     (action ...)))
>
> ;; 使用时显式调用
> :actions (list (loan-action))
> ```

- ⚠️ **函数闭包重新绑定**：顶层 `define` / `define-fragment` 声明的函数在每次渲染时会重新绑定到当前环境，因此其自由变量（如 `security_online`）在每次调用时从当前状态查找。嵌套 lambda（函数内创建的闭包）仍然使用标准词法作用域。
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
- 读写世界状态需在 `:vars` 导入：`(import-world-attr 'health)`、`(import-world-item 'money)`、`(import-world-value 'case_done false)`
- 也可 include `common_world_bindings.scm` 使用 `world-basics-vars` 等 helper
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
  :suit 知识
  :risk 'mid
  :factors (list
    (factor -1 :when security_online :label "监控")
    (factor 1 :when power_cut :label "断电"))
  :ok outcome
  :partial outcome
  :fail outcome)
```

- `:risk`：`'low` `'mid` `'high`
- `:suit`：`暴力` `魅力` `知识` `敏锐`（或英文 `force` `charm` `knowledge` `sense`）
- `include` 了 `enum-symbols.scm` 后可使用中文符号：`暴力` `魅力` `知识` `敏锐`
- `:suit` 只写一个花色（不写时表示不使用人物属性加成）
- 写了 `:suit` 时，行动卡本身仍然无属性；最终值 = 行动卡点数 + 使用者对应属性 + 启用的 `:factors`
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
