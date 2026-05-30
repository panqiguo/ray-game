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
6. 合理拆分文件，避免一个文件塞太多内容。
7. 不要把"是否出现"写成 `conditions`。
8. 不要为了复用先加底层专用语法。
9. 不要按旧 Python builder 思路平移。

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

## 三、顶层 `(content ...)`

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

---

## 四、常用构造器

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

- world `:state` → 全局。可读字段含 `day/health/stress/money` + world 自定义绑定 + Python inventory 物品（`clothes/gun/hotel_pass/lockpick`）
- encounter `:state` → 仅当前任务可见

encounter 里改全局字段用 quoted symbol：`(effect 'add 'money 80)`。  
`day` 特例：只用 `(effect 'advance-day)`，不要直接 `add/set`。

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
  :suits (list 'force 'charm)
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
- `:suits`：`'force` / `'charm` / `'knowledge` / `'sense`（或中文 `暴力`/`魅力`/`知识`/`敏锐`，需 include `enum-symbols.scm`）
- 不写 `:suits` 或写空列表时，不使用人物属性加成

---

### 8. `(outcome ...)`

```scheme
(outcome "结果文本" (list effect...))
```

第一个参数是文本，第二个参数是 effect 列表。

---

### 9. `(react ...)` / `(reacts ...)`

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

## 五、`conditions` 的语义

实际写法：

```scheme
:conditions (list
  (has-item 'clothes 1 "需要体面的衣服")
  (field-at-least 'money 20 "需要 20 美钞"))
```

语义：

- 节点或行动已经进入树里，但 `conditions` 不满足：可见、不可执行
- 要控制是否出现，用 `if / when / cond`

---

## 六、输入

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

## 七、effect

```scheme
(effect 'clock+ east_info 1)
(effect 'clock- alert 1)
(effect 'set hotel_pass true)
(effect 'add money -20)
(effect 'add health 1)
(effect 'add energy -1)
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
- 不再使用旧短名（`effect 'health`、`effect 'stress`）、`resource`、`start-content`

---

## 八、基础 Scheme 能力

- **控制流**: `if` `when` `cond` `and/or/not` `let` `let*` `lambda` `begin` `quote`
- **列表**: `list` `car` `cdr` `cons` `append` `length` `list?` `pair?` `map` `filter` `member` `reverse` `apply`
- **alist**: `assoc` `assoc-ref` `assoc-set` `assoc-remove`
- **数值/比较**: `+` `-` `min` `max` `=` `<` `<=` `>` `>=`
- **判定**: `null?` `number?` `string?` `boolean?` `symbol?`
- **调试**: `(log ...)` 打印到终端，返回最后一个参数
- `let` 并行绑定，`let*` 顺序绑定
- 仅 `false`/`nil` 为假；`0` 和空列表为真
- `(- x)` 一元取负

---

## 九、动态绑定（重要）

本 DSL 使用**动态绑定**：lambda 内的自由变量不在定义时捕获，而在**每次调用时**从当前环境中查找。

```scheme
(define x 1)
(define f (lambda () x))
(define x 2)
(f)  ; → 返回 2（不是 1）
```

**为什么：** 状态字段（如 `security_online`）必须在运行时取值，不能被编译时快照固定。

**注意事项：**

1. **同名遮蔽** — lambda 内的自由符号不要和状态字段名或其他 `define` 名重复。修饰符 lambda 用长名（`stealth-modifiers`），状态字段用下划线（`clue_a_done`）。
2. **避免使用 DSL 关键字做字段名** — 不要用 `factor`、`effect`、`check`、`action`、`clock` 作为状态字段名，它们会遮蔽 builtin。
3. **修饰符尽量扁平化** — 多层嵌套组合链里符号被遮蔽很难查，推荐 `append` 简单 lambda。

---

## 十、推荐写法

### 1. 用 helper 生成重复结构

```scheme
(define make-rest-action
  (lambda (title cost energy-up)
    (action
      :title title
      :inputs (list (item 'money cost "美钞"))
      :effects (list (effect 'add energy energy-up)))))
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

## 十一、一个最小骨架

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
