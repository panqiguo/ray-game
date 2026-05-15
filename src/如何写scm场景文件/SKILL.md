# SKILL: 如何撰写 `.scm` 场景文件

本 skill 用于撰写 sincity 的 `.scm` 内容脚本。  
现在城市与 encounter 走同一套 Scheme 内容语言，统一用 `(content ...)` 作为顶层入口。

目标不是“把 Python builder 翻译成 Scheme”，而是**直接用 Scheme 组织内容**。

---

## 一、核心原则

1. 先用 Scheme 组织内容，再考虑底层扩展。
2. 复用优先用 `define`、`lambda`、list/alist helper；动态节点/场景可用 `define-node` / `define-scene`。
3. 可见性优先用 `if / when / cond` 表达，不要把“显示/隐藏”塞进专门字段。
4. `conditions` 只表示“可见但不可执行”。
5. 顶层统一用 `(content ...)` 组装；只有 `meta :key` 是稳定标识。

---

## 二、文件整体结构

推荐结构：

```scheme
(include "common.scm")     ; 可选

(define scene-meta ...)
(define local-state ...)
(define local-reacts ...)
(define-node root-node
  (node ...))

(content
  :meta scene-meta
  :state local-state
  :reacts local-reacts
  :root (root-node))
```

关键点：

- 顶层允许 `include`
- 顶层允许多个 `define`，顶层 `define` 会在模块加载时立即求值
- `define-node` / `define-scene` 是零参数过程糖；引用时要写成调用：`(root-node)`
- `define-node` / `define-scene` 的直接 `(node ...)` / `(scene ...)` 没写 `:title` 时，会自动使用定义名作为标题
- 最终必须有一个 `(content ...)`
- 不再写旧式顶层 `meta/state/reacts` 裸声明

---

## 三、推荐文件划分

常见拆法：

- 一个主内容文件：当前场景/任务本体
- 一个通用工具文件：helper、时钟函数、重复动作模板
- 一个对白文件：Ink / quick dialogue 单独放

不要把所有区域、所有任务、所有对白硬塞进一个 `.scm` 文件。

---

## 四、顶层 `(content ...)`

```scheme
(content
  :meta meta-expr
  :state state-expr
  :reacts reacts-expr
  :on-success (list effect...)
  :on-fail (list effect...)
  :root node-expr)
```

参数说明：

| 参数 | 必填 | 说明 |
|------|------|------|
| `:meta` | ✅ | 内容元数据 |
| `:root` | ✅ | 根节点表达式 |
| `:state` | ❌ | 局部状态 |
| `:reacts` | ❌ | 自动规则 |
| `:on-success` | ❌ | encounter 成功后追加效果 |
| `:on-fail` | ❌ | encounter 失败后追加效果 |

说明：

- `:on-success` / `:on-fail` 更常用于 encounter；world 内容通常不需要
- 全局初始状态仍可放 Python，不必强行脚本化

---

## 五、常用构造器

### 1. `(meta ...)`

```scheme
(meta :key 'escape :title "逃离这里" :desc "场景描述")
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `:key` | ✅ | 内容唯一 ID |
| `:title` | ✅ | 标题 |
| `:desc` | ❌ | 描述 |

注意：

- 只有 `meta` 接受 `:key`
- `node/action/react/clock` 都不再写 `:key`

---

### 2. `(state ...)`

```scheme
(state
  (day 1)
  (hotel_pass false)
  (east_info (clock :title "东区探索" :initial 0 :max 4)))
```

每条绑定都写成：

```scheme
(name value)
```

支持的 value：

- `int`
- `bool`
- symbol / string
- `(clock ...)`

说明：

- 局部状态写在 `:state`
- 更适合“当前内容需要维护的变量”

---

### 3. `(clock ...)`

```scheme
(clock :title "警觉" :initial 0 :max 4)
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `:title` | ✅ | 显示名 |
| `:initial` | ✅ | 初始值 |
| `:max` | ✅ | 上限 |

注意：

- 不再接受 `:key`
- 不再接受 `:persist`

---

### 4. 字段作用域：全局 vs 局部

这条很重要：

- world 脚本里的 `:state` 绑定，是**本次 run 的全局状态**
- encounter 脚本里的 `:state` 绑定，是**当前任务的局部状态**

#### world 里的全局字段

固定可读字段：

- `day`
- `health`
- `stress`
- `money`
- `cigarettes`

除此之外，下面这些也属于 world 全局字段：

- 当前 world `:state` 里定义的所有绑定
- Python 初始 inventory 里的物品计数  
  当前主场景是：`clothes`、`gun`、`hotel_pass`、`lockpick`

例如在 world 里可以直接写：

```scheme
(effect 'add money 20)
(effect 'set villa_job_taken true)
(effect 'add clothes 1)
```

#### encounter 里的局部字段

encounter `:state` 里定义的字段，只属于当前任务：

```scheme
(state
  (escaped false)
  (local_score 0)
  (alert (clock :title "警觉" :initial 0 :max 6)))
```

这里的：

- `escaped`
- `local_score`
- `alert`

都只是这个 encounter 的局部字段。

所以可以直接写：

```scheme
(effect 'add local_score 10)
(effect 'set escaped true)
(effect 'clock+ alert 1)
```

#### 在 encounter 里改全局字段

如果 encounter 里要改全局字段，推荐显式写 quoted symbol：

```scheme
(effect 'add 'money 80)
(effect 'set 'villa_job_taken true)
```

这样不会和 encounter 局部绑定混淆。

#### `day` 是特例

`day` 虽然是全局字段，但不要把它当普通 `add/set` 字段。  
推进日期只用：

```scheme
(effect 'advance-day)
```

不要写：

```scheme
(effect 'add day 1)
(effect 'set day 2)
```

---

### 5. `(node ...)` / `(scene ...)`

`scene` 与 `node` 等价，推荐统一写 `node`。

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

| 参数 | 必填 | 说明 |
|------|------|------|
| `:title` | ✅ | 标题 |
| `:desc` | ❌ | 描述 |
| `:position` | ❌ | 地图位置 |
| `:show-clocks` | ❌ | 显示哪些时钟 |
| `:conditions` | ❌ | 满足时才可执行 |
| `:actions` | ❌ | 行动列表 |
| `:children` | ❌ | 子节点列表 |

说明：

- 节点是否出现，优先用 `if / when / cond`
- `:conditions` 不是显隐系统
- 所有节点都可以带 `:position`
- 所有节点都可以带 `:show-clocks`

---

### 6. `(action ...)`

```scheme
(action
  :title "点一杯酒"
  :desc "花点钱让自己缓下来。"
  :conditions (list ...)
  :inputs (list ...)
  :always (list effect...)
  :effects (list effect...)
  :check (check ...))
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `:title` | ✅ | 行动标题 |
| `:desc` | ❌ | 行动描述 |
| `:position` | ❌ | 位置 |
| `:conditions` | ❌ | 可执行条件 |
| `:inputs` | ❌ | 输入消耗 |
| `:always` | ❌ | 执行时先触发 |
| `:effects` | ❌ | 无检定行动的结果 |
| `:check` | ❌ | 检定结果 |

规则：

- `:check` 与 `:effects` 互斥
- 有 `:check` 时，结果写在 `:ok / :partial / :fail`
- `:always` 可与两者任意一种共存

---

### 7. `(check ...)`

```scheme
(check
  :suits (list 'logic 'perception)
  :risk 'mid
  :ok outcome
  :partial outcome
  :fail outcome)
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `:suits` | ✅ | 花色列表 |
| `:risk` | ✅ | 风险等级 |
| `:ok` | ✅ | 成功结果 |
| `:partial` | ✅ | 中等结果 |
| `:fail` | ✅ | 失败结果 |

合法值：

- `:risk`：`'low` / `'mid` / `'high`
- `:suits`：`'logic` / `'perception` / `'willpower`
- 不写 `:suits` 或写空列表时，三种基础精力都可以放

---

### 8. `(outcome ...)`

```scheme
(outcome "结果文本" (list effect...))
```

第一个参数是文本，第二个参数是 effect 列表。

---

### 8. `(react ...)` / `(reacts ...)`

```scheme
(react
  :when expr
  :then (list effect...))

(reacts
  (react ...)
  some-react
  (when cond (react ...)))
```

规则：

- `react` 返回一个 react 值
- `reacts` 接受任意求值成 `react` 或 `nil` 的表达式
- 可以先 `define` helper，再在 `reacts` 里组合

---

## 六、`conditions` 的语义

实际写法：

```scheme
:conditions (list
  (has-item 'clothes 1 "需要体面的衣服")
  (field-at-least 'money 20 "需要 20 美钞"))
```

语义：

- 节点或行动已经进入树里，但 `conditions` 不满足：可见、不可执行
- 要控制是否出现，用 `if / when / cond`

常用条件：

- `(has-item 'clothes 1 "提示")`
- `(field-at-least 'money 20 "提示")`
- `(field-truthy 'hotel_pass "提示")`
- `(condition 'clock_at_least "alert:2" "提示")`

---

## 七、输入

输入只保留两类：

```scheme
(item 'money 20 "美钞")
(item 'lockpick 1 "开锁器")
(card 'any)
(card 'negative "负面牌")
```

说明：

- `item` / `card` 作为 input 时默认消耗
- 不消耗的门槛不要写成 input，而是写进 `conditions`

---

## 八、effect

```scheme
(effect 'clock+ east_info 1)
(effect 'clock- alert 1)
(effect 'set hotel_pass true)
(effect 'add money -20)
(effect 'add health 1)
(effect 'add stress -1)
(effect 'start-dialogue 'intro)
(effect 'start-quick-dialogue "一段短对白")
(effect 'start-encounter 'villa_infiltration)
(effect 'end-encounter 'success)
(effect 'end-encounter 'fail)
(effect 'end-encounter 'abort)
(effect 'advance-day)
(effect 'end-game)
(effect 'reset-hand)
```

说明：

- 统一使用最准确的 effect 名称
- 修改字段统一用 `(effect 'set field value)` / `(effect 'add field amount)`
- 不再使用 `(effect 'health amount)` / `(effect 'stress amount)` 短名
- 不再使用 `resource`
- 不再使用 `start-content`

---

## 九、基础 Scheme 能力

### 控制流

- `if`
- `when`
- `cond`
- `and` / `or` / `not`
- `let`
- `let*`
- `lambda`
- `begin`
- `quote` / `'`

### 列表

- `list`
- `car` `cdr` `cons`
- `append`
- `length`
- `list?` `pair?`
- `map`
- `filter`
- `member`
- `reverse`
- `apply`

### alist

- `assoc`
- `assoc-ref`
- `assoc-set`
- `assoc-remove`

### 数值 / 比较

- `+` `-`
- `min` `max`
- `=` `<` `<=` `>` `>=`

### 判定

- `null?`
- `number?`
- `string?`
- `boolean?`
- `symbol?`

### 调试

- `log`
- `(log ...)` 会打印到 Python 终端，返回最后一个参数；适合临时排查脚本状态
- `let` 是标准并行绑定；`let*` 是顺序绑定
- 只有 `false` 和 `nil` 为假；`0` 和空列表都是真
- `(- x)` 是一元取负

---

## 十、推荐写法

### 1. 用 helper 生成重复结构

```scheme
(define make-paid-relief-action
  (lambda (title cost stress-down)
    (action
      :title title
      :inputs (list (item 'money cost "美钞"))
      :effects (list (effect 'add stress (- 0 stress-down))))))
```

### 2. 用 `when` 在列表里做条件插入

```scheme
(list
  base-action
  (when (>= (clock-value east_info) 2) bar-node))
```

### 3. 用 alist 存轻量配置

```scheme
(define east-config
  '((title "东区")
    (x 120)
    (y 80)))
```

适合：

- 小型配置表
- helper 参数较多但不想一项项平铺

---

## 十一、不推荐写法

- 为了复用先加底层专用语法
- 把“是否出现”写成 `conditions`
- 继续按旧 Python builder 思路平移
- 一个文件里塞太多完整区域，导致 helper 无法复用

---

## 十二、一个最小骨架

```scheme
(include "common.scm")

(define my-meta
  (meta :key 'escape :title "逃离这里"))

(define my-state
  (state
    (day 1)
    (intro_played false)
    (alert (clock :title "警觉" :initial 0 :max 4))))

(define my-reacts
  (reacts
    (when (and (>= day 2) (not intro_played))
      (react
        :when true
        :then (list
          (effect 'set intro_played true)
          (effect 'start-dialogue 'day2_intro))))))

(define root-node
  (node
    :title "桥洞"
    :show-clocks (list alert)
    :actions (list)))

(content
  :meta my-meta
  :state my-state
  :reacts my-reacts
  :root root-node)
```
