Encounter / World SCM 速查

顶层：

```scheme
(include "common.scm")
(define name expr)

(content
  :meta meta-expr
  :state state-expr
  :reacts reacts-expr
  :on-success (list effect...)
  :on-fail (list effect...)
  :root node-expr)
```

`meta`：

```scheme
(meta :key 'escape :title "标题" :desc "描述")
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

- world 全局字段：`day` `health` `stress` `money` `cigarettes`
- world 还包括：world `:state` 绑定、初始 inventory 物品计数
- encounter 局部字段：encounter `:state` 绑定
- encounter 改全局字段时，推荐写 quoted symbol：`'money`、`'villa_job_taken`
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
  :before (list effect...)
  :effects (list effect...)
  :check check-expr)
```

- 必填：`:title`
- 选填：`:desc` `:position` `:conditions` `:inputs` `:before` `:effects` `:check`
- `:check` 与 `:effects` 互斥

`check`：

```scheme
(check
  :suits (list 'reason 'instinct)
  :risk 'mid
  :ok outcome
  :partial outcome
  :fail outcome)
```

- `:risk`：`'low` `'mid` `'high`
- `:suits`：`'reason` `'force` `'empathy` `'instinct`

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

`effects`：

```scheme
(effect 'clock+ clock-field amount)
(effect 'clock- clock-field amount)
(effect 'set field value)
(effect 'add field amount)
(effect 'health amount)
(effect 'stress amount)
(effect 'start-dialogue 'dialogue_id)
(effect 'start-quick-dialogue "对白内容")
(effect 'start-encounter 'encounter_id)
(effect 'end-encounter 'success)
(effect 'end-encounter 'fail)
(effect 'end-encounter 'abort)
(effect 'advance-day)
(effect 'end-game)
(effect 'reset-hand)
```

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
(lambda (args...) body)
(begin ...)
(quote x)
'x
(log ...)
```

- `(log ...)` 会打印到 Python 终端，返回最后一个参数；常用于调试脚本

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
