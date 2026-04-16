# 如何写 `.scm` 场景文件

用于 ray-game 的统一内容语言：城市与 encounter 都走同一套 Scheme 模块。

## 核心原则

- 优先用 Scheme 组织内容，再考虑底层扩展。
- 复用优先用 `define` 和 `lambda`，不要堆重复节点。
- 顶层统一用 `(content ...)` 组装；

## 推荐文件划分

- 一个主内容文件：定义 `meta`、`state`、`reacts`、`root`，最后 `(content ...)`。
- 一个通用工具文件：放共享 helper，例如路径动作、时钟 helper、条件组合等高度复用的函数。

常见结构：

```scheme
(include "common.scm")

(define scene-meta ...)
(define local-state ...)
(define local-reacts ...)
(define world-root ...)

(content
  :meta scene-meta
  :state local-state
  :reacts local-reacts
  :root world-root)
```

## 顶层结构

```scheme
(content
  :meta meta-expr
  :state state-expr
  :reacts reacts-expr
  :on-success (list effect...)
  :on-fail (list effect...)
  :root node-expr)
```

- `:meta`、`:root` 必填
- `:state`、`:reacts`、`:on-success`、`:on-fail` 选填

## 常用构造

### `meta`

```scheme
(meta :key 'escape :title "逃离这里" :desc "描述")
```

- 必填：`:key` `:title`
- 选填：`:desc`

### `state`

```scheme
(state
  (day 1)
  (hotel_pass false)
  (east_info (clock :title "东区探索" :initial 0 :max 4)))
```

- 每项写成 `(name value)`
- `value` 可以是 `int / bool / string(symbol) / (clock ...)`

### `clock`

```scheme
(clock :title "警觉" :initial 0 :max 4)
```

- 必填：`:title` `:initial` `:max`
- 不再接受 `:key` `:persist`

### `node` / `scene`

```scheme
(node
  :title "东区"
  :desc "沿河的旧街区。"
  :position '(120 80)
  :show-clocks (list east_info)
  :conditions (list ...)
  :actions (list ...)
  :children (list ...))
```

- 必填：`:title`
- 选填：`:desc` `:position` `:show-clocks` `:conditions` `:actions` `:children`
- `scene` 与 `node` 等价

### `action`

```scheme
(action
  :title "点一杯酒"
  :desc "花点钱让自己缓下来。"
  :conditions (list ...)
  :inputs (list ...)
  :before (list effect...)
  :effects (list effect...)
  :check (check ...))
```

- 必填：`:title`
- 选填：`:desc` `:position` `:conditions` `:inputs` `:before` `:effects` `:check`
- `:check` 与 `:effects` 互斥

### `check`

```scheme
(check
  :suits (list 'reason 'instinct)
  :risk 'mid
  :ok outcome
  :partial outcome
  :fail outcome)
```

- 必填：`:suits` `:risk` `:ok` `:partial` `:fail`
- `:risk`：`'low` / `'mid` / `'high`
- `:suits`：`'reason` / `'force` / `'empathy` / `'instinct`

### `outcome`

```scheme
(outcome "结果文本" (list effect...))
```

### `react` / `reacts`

```scheme
(react
  :when expr
  :then (list effect...))

(reacts
  (react ...)
  some-react
  (when cond (react ...)))
```

- `reacts` 接受任意求值成 `react` 或 `nil` 的表达式

## `conditions` 语义

```scheme
:conditions (list
  (has-item 'clothes 1 "需要体面的衣服")
  (field-at-least 'money 20 "需要 20 美钞"))
```

- 节点或行动已经进入树里，但 `conditions` 不满足：可见、不可执行
- 要控制是否出现，用 `if / when / cond`

常用条件：

- `(has-item 'clothes 1 "提示")`
- `(field-at-least 'money 20 "提示")`
- `(field-truthy 'hotel_pass "提示")`
- `(condition 'clock_at_least "alert:2" "提示")`

## 输入

```scheme
(item 'money 20 "美钞")
(item 'lockpick 1 "开锁器")
(card 'any)
(card 'negative "负面牌")
```

- 输入只保留 `item` / `card`
- 作为 input 的东西默认消耗
- 不消耗的门槛写进 `conditions`

## effect

```scheme
(effect 'clock+ east_info 1)
(effect 'clock- alert 1)
(effect 'set hotel_pass true)
(effect 'add money -20)
(effect 'health 1)
(effect 'stress -1)
(effect 'start-dialogue 'intro)
(effect 'start-quick-dialogue "一段短对白")
(effect 'start-encounter 'villa_infiltration)
(effect 'finish 'success)
(effect 'advance-day)
(effect 'end-run 'escape_success)
(effect 'reset-hand)
```

## 现在可用的基础 Scheme

控制流：

- `if`
- `when`
- `cond`
- `and` `or` `not`
- `let`
- `lambda`
- `begin`
- `quote` / `'`

列表：

- `list`
- `car` `cdr` `cons`
- `append`
- `length`
- `list?` `pair?`
- `map` `filter`
- `member`
- `reverse`
- `apply`

alist：

- `assoc`
- `assoc-ref`
- `assoc-set`
- `assoc-remove`

数值/比较：

- `+` `-` `min` `max`
- `=` `<` `<=` `>` `>=`

判定：

- `null?`
- `number?`
- `string?`
- `boolean?`
- `symbol?`

## 推荐写法

- 用 helper 生成重复节点或动作
- 用 alist/list 存轻量配置
- 用 `when` 在列表里条件插入节点或动作
- 用局部 `state` 描述当前内容需要的状态，不把全局状态搬进脚本

## 不推荐写法

- 为了复用去加底层专用语法
- 把“是否出现”写成 `conditions`
- 在一个文件里塞太多完整区域，导致无法复用 helper
