# SKILL: 如何撰写 .scm 场景文件

本 skill 用于撰写 ray-game 的 `.scm` encounter 场景脚本。
读完本文件后，你应该能独立写出一个完整可编译的场景。

---

## 一、文件整体结构

一个 `.scm` 文件由以下部分按顺序组成：

```
(include ...)          ← 可选，引入通用符号/宏
(define ...)           ← 定义行动、场景组件（可多个）
(meta ...)             ← 场景元数据（必填）
(on-fail ...)          ← 失败副作用（可选）
(on-success ...)       ← 成功副作用（可选）
(state ...)            ← 状态声明（必填）
(reacts ...)           ← 反应规则（可选）
<根视图表达式>          ← 文件末尾唯一一个非声明表达式（必填）
```

> **关键约束**：文件末尾必须有且只有一个"根视图表达式"，它决定当前渲染哪个 scene。所有 `define`、`meta`、`state`、`reacts` 都是声明，不算根视图。

---

## 二、内置构造函数：参数规格

### `(meta ...)` — 场景元数据

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `:key` | ✅ | symbol | 场景唯一 ID，用于 registry 索引 |
| `:title` | ✅ | string | 场景标题 |
| `:desc` | ❌ | string | 场景简介，默认空字符串 |

```scheme
(meta :key 'black_night :title "黑夜入宅" :desc "深夜潜入戒备森严的宅邸。")
```

---

### `(state ...)` — 状态声明块

整个文件只允许一个 `state` 块。每条绑定格式为 `(变量名 初始值)`。

初始值支持三种类型：

| 初始值写法 | 类型 | 示例 |
|-----------|------|------|
| `(clock ...)` | 进度时钟（整数+上限） | `(clock :title "警觉" :initial 0 :max 6)` |
| 整数字面量 | int | `5` |
| 布尔字面量 | bool | `true` / `false` |
| symbol 字面量 | string（枚举） | `'calm` / `none` |

```scheme
(state
  (alert   (clock :title "全局警觉度" :initial 0 :max 6))
  (patrol  (clock :title "保安巡逻"   :initial 0 :max 3))
  (phase   'yard)    ; 枚举变量
  (route   none)     ; none 等同于 nil
  (alive   true)     ; 布尔变量
  (coins   0)        ; 整数变量
)
```

#### `(clock ...)` 参数规格

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `:title` | ✅ | string | 显示名称 |
| `:initial` | ✅ | int | 初始值，必须 `0 ≤ initial ≤ max` |
| `:max` | ✅ | int | 上限（格子数） |
| `:persist` | ❌ | symbol | 持久化范围，默认 `encounter`（当前仅支持此值） |

---

### `(action ...)` — 行动定义

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `:title` | ✅ | string | 行动显示名 |
| `:desc` | ❌ | string | 行动描述，默认空字符串 |
| `:key` | ❌ | symbol | 行动唯一 key，省略则自动生成 hash |
| `:before` | ❌ | `(list effect ...)` | 执行前立即触发的副作用（无论是否有 check） |
| `:effects` | ❌ | `(list effect ...)` | 无 check 时触发的副作用（**与 `:check` 互斥**） |
| `:check` | ❌ | `(check ...)` | 检定，有此字段则 `:effects` 必须为空 |
| `:inputs` | ❌ | `(list input ...)` | 消耗资源/道具/卡牌的前置输入 |

> **`:before` vs `:effects` 区别**：
> - `:before`：点击行动后**立即**执行，然后再进行 check（若有）
> - `:effects`：只在**没有 check** 时使用，作为行动的最终结果
> - 有 `:check` 时，最终效果写在 check 的 `:ok` / `:partial` / `:fail` 里，不能同时写 `:effects`

**无检定行动（点击即生效）：**

```scheme
(define leave_action
  (action
    :title "收手离开"
    :desc  "你决定暂时撤退。"
    :before (list (effect 'finish 'abort))
  ))
```

**有检定行动：**

```scheme
(define pick_lock
  (action
    :title "撬锁进入"
    :desc  "从正门进去，尽量不留动静。"
    :check (check
      :suits   (list reason instinct)
      :risk    mid
      :ok      (outcome "门锁被撬开了。" (list (effect 'set entry_method 'front)))
      :partial (outcome "进去了，但有点动静。" (list (effect 'set entry_method 'front) (effect 'clock+ alert 1)))
      :fail    (outcome "锁发出一声轻响。" (list (effect 'clock+ alert 1)))
    )
  ))
```

**有前置副作用 + 检定：**

```scheme
(define start_patrol
  (action
    :title "扔石子"
    :desc  "引开保安，巡逻从此刻开始计数。"
    :before (list (effect 'set route 'left) (effect 'set patrol 1))
    :check (check ...)
  ))
```

---

### `(check ...)` — 检定规格

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `:suits` | ✅ | `(list suit ...)` | 可用花色，至少一个 |
| `:risk` | ✅ | symbol | 风险等级：`low` / `mid` / `high` |
| `:ok` | ✅ | `(outcome ...)` | 完全成功结果 |
| `:partial` | ✅ | `(outcome ...)` | 部分成功/代价成功结果 |
| `:fail` | ✅ | `(outcome ...)` | 失败结果 |

**可用花色（`:suits`）：**

| 符号 | 含义 |
|------|------|
| `reason` | 理智 |
| `force` | 力量 |
| `empathy` | 共情 |
| `instinct` | 本能 |

---

### `(outcome ...)` — 结果描述

```scheme
(outcome "结果文本。" (list effect1 effect2 ...))
; 或无副作用：
(outcome "只有文本，没有效果。" (list))
```

| 参数 | 必填 | 类型 |
|------|------|------|
| 第一个参数（文本） | ✅ | string |
| 第二个参数（effect 列表） | ❌ | `(list ...)` 或省略 |

---

### `(effect ...)` — 副作用

所有副作用都通过 `(effect 'kind ...)` 构造。

| 写法 | 必填参数 | 说明 |
|------|---------|------|
| `(effect 'clock+ 时钟名 数值)` | 时钟变量, 正整数 | 推进时钟 N 格 |
| `(effect 'clock- 时钟名 数值)` | 时钟变量, 正整数 | 回退时钟 N 格 |
| `(effect 'set 变量名 值)` | 状态变量, 新值 | 设置状态变量（支持 symbol/int/bool/none） |
| `(effect 'health 数值)` | 整数（可为负） | 改变生命值，负数扣血 |
| `(effect 'stress 数值)` | 整数 | 改变压力值 |
| `(effect 'resource 键 数值)` | string key, 整数 | 改变指定资源 |
| `(effect 'finish 'success)` | — | 结束场景，标记成功 |
| `(effect 'finish 'fail)` | — | 结束场景，标记失败 |
| `(effect 'finish 'abort)` | — | 结束场景，中止 |
| `(effect 'reset-hand)` | — | 重置手牌 |

```scheme
; 示例组合
(list
  (effect 'clock+ alert 1)
  (effect 'set phase 'entry)
  (effect 'health -1)
  (effect 'finish 'fail)
)
```

---

### `(scene ...)` — 场景节点

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `:title` | ✅ | string | 场景标题 |
| `:desc` | ❌ | string | 场景描述，默认空字符串 |
| `:key` | ❌ | symbol | 场景唯一 key，省略则自动生成 hash |
| `:show-clocks` | ❌ | `(list 时钟名 ...)` | 在此场景界面显示的时钟 |
| `:actions` | ❌ | `(list action ...)` | 该节点的行动列表 |
| `:children` | ❌ | `(list scene ...)` | 子场景列表（嵌套地点） |

> **`:actions` 与 `:children` 的关系**：
> - 父 scene 通常只写 `:children`，自己不写 `:actions`（作为容器节点）
> - 叶子 scene（无 children）写 `:actions`
> - 也可以父节点同时有 `:actions` 和 `:children`，但少见

```scheme
(define lobby_scene
  (scene
    :key   'lobby
    :title "大厅"
    :desc  "灯光昏暗，两条路摆在你面前。"
    :show-clocks (list alert)
    :actions (list )
    :children (list left_scene right_scene)
  ))
```

**行动列表里可用 `when` 做条件过滤：**

```scheme
:actions (list
  (when (clock-empty? patrol) start_patrol_action)
  (when (and (= route 'left) (not (clock-filled? traverse))) advance_action)
  always_visible_action
)
```

`when` 返回 action 或 `nil`，nil 会被自动过滤掉。

---

### `(reacts ...)` — 反应规则块

每轮状态变化后自动检查所有 react，条件成立则触发。

```scheme
(reacts
  (react :key 'react_0
    :when (clock-filled? alert)
    :then (list (effect 'finish 'fail)))
  (react :key 'react_1
    :when (clock-filled? truth)
    :then (list (effect 'finish 'success)))
  (react :key 'react_2
    :when (and (= phase 'yard) (clock-filled? traverse))
    :then (list (effect 'set phase 'entry) (effect 'set traverse 0)))
)
```

#### `react` 参数规格

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `:key` | ❌ | symbol | 规则唯一 key，省略则自动生成 |
| `:when` | ✅ | 布尔表达式 | 触发条件 |
| `:then` | ✅ | `(list effect ...)` | 触发后的副作用列表 |

---

### `(inputs ...)` — 前置输入（资源/道具/卡牌消耗）

在 `:inputs (list ...)` 中使用，执行行动前需要玩家提供资源。

```scheme
; 消耗资源
(resource 资源键 数量)
(resource 资源键 数量 "显示标签")

; 消耗道具
(item 道具键)
(item 道具键 数量)
(item 道具键 数量 "显示标签")
(item 道具键 数量 "标签" false)  ; 最后一个参数 false 表示不消耗（借用）

; 消耗卡牌
(card 卡牌键)
(card 卡牌键 "显示标签")
; 特殊 key：'negative（负面牌）、其他自定义
```

```scheme
(define use_tool_action
  (action
    :title "使用工具"
    :desc  "消耗一把撬锁工具。"
    :inputs (list (item 'lockpick 1 "撬锁工具"))
    :check (check ...)
  ))
```

---

## 三、状态查询函数（运行时可用）

### 时钟相关

| 函数 | 说明 |
|------|------|
| `(clock-filled? 时钟名)` | 时钟是否已满（= max） |
| `(clock-empty? 时钟名)` | 时钟是否为空（= 0） |
| `(clock-partial? 时钟名)` | 时钟非空且未满 |
| `(clock-value 时钟名)` | 当前值（整数） |
| `(clock-full 时钟名)` | 上限值（整数） |
| `(clock-half 时钟名)` | 上限的一半（向上取整） |

> `clock-filled?`、`clock-empty?`、`clock-partial?` 来自 `common_clock_macros.scm`，需要 `(include "common_clock_macros.scm")` 才可用。

### 变量比较

| 表达式 | 说明 |
|--------|------|
| `(= 变量 值)` | 等值比较 |
| `(< a b)` / `(> a b)` | 大小比较 |
| `(<= a b)` / `(>= a b)` | 大小比较 |

### 逻辑运算

| 表达式 | 说明 |
|--------|------|
| `(and expr ...)` | 全部为真 |
| `(or expr ...)` | 任一为真 |
| `(not expr)` | 取反 |

### 算术

| 表达式 | 说明 |
|--------|------|
| `(+ a b ...)` | 求和 |
| `(- a b ...)` | 减法 |
| `(min a b ...)` | 最小值 |
| `(max a b ...)` | 最大值 |

---

## 四、根视图表达式写法

文件末尾的根视图决定"当前显示哪个 scene"，支持静态或动态：

**静态（直接引用 define 的场景）：**

```scheme
my_root_scene
```

**条件分支（多幕切换）：**

```scheme
(cond
  ((clock-filled? alert)  exposed_scene)
  ((= phase 'yard)        yard_act)
  ((= phase 'entry)       entry_act)
  (else                   bedroom_act))
```

**二选一：**

```scheme
(if (= entry_method 'front) front_scene window_scene)
```

---

## 五、`on-success` / `on-fail`

场景结束时追加的全局副作用：

```scheme
(on-success (list (effect 'resource gold 3)))
(on-fail    (list (effect 'stress 2)))
```

---

## 六、`include` — 引入外部文件

```scheme
(include "enum-symbols.scm")          ; 引入通用枚举符号
(include "common_clock_macros.scm")   ; 引入 clock-filled? 等宏
```

- 路径相对于当前文件所在目录
- 支持多个 include
- 不允许循环引用

---

## 七、Scheme 表达式备忘

`.scm` 文件支持完整的 Lisp-style 表达式：

```scheme
; 条件
(if condition then-expr else-expr)
(when condition expr)
(cond (cond1 expr1) (cond2 expr2) (else default))

; 局部绑定
(let ((x 1) (y 2)) (+ x y))

; 列表
(list a b c)

; 引用（不求值，返回 symbol 本身）
'symbol
(quote symbol)

; 定义（顶层）
(define name value)

; 匿名函数
(lambda (x y) (+ x y))
```

---

## 八、完整文件骨架

```scheme
(include "enum-symbols.scm")
(include "common_clock_macros.scm")

;;; ── 行动定义 ────────────────────────────────────────────────

(define action_sneak
  (action
    :title "贴墙潜行"
    :desc  "压低呼吸，贴着阴影往前挪。"
    :check (check
      :suits   (list instinct reason)
      :risk    mid
      :ok      (outcome "你无声滑过了。" (list (effect 'clock+ traverse 1)))
      :partial (outcome "你挪过去了，但碰出了点动静。" (list (effect 'clock+ traverse 1) (effect 'clock+ alert 1)))
      :fail    (outcome "你被发现了。" (list (effect 'clock+ alert 2)))
    )
  ))

(define action_abort
  (action
    :title "撤退"
    :desc  "现在离开还来得及。"
    :before (list (effect 'finish 'abort))
  ))

;;; ── 场景定义 ────────────────────────────────────────────────

(define root_scene
  (scene
    :key   'root
    :title "走廊"
    :desc  "灯光昏暗，出口就在前方。"
    :show-clocks (list alert traverse)
    :actions (list action_sneak action_abort)
  ))

(define fail_scene
  (scene
    :key   'exposed
    :title "暴露"
    :desc  "警报拉响，你已无路可走。"
    :show-clocks (list alert)
    :actions (list )
  ))

;;; ── 元数据 ──────────────────────────────────────────────────

(meta :key 'my_encounter :title "场景标题" :desc "一句话简介。")

;;; ── 全局副作用 ──────────────────────────────────────────────

(on-fail (list (effect 'stress 1)))

;;; ── 状态 ────────────────────────────────────────────────────

(state
  (alert    (clock :title "警觉度" :initial 0 :max 4))
  (traverse (clock :title "穿越进度" :initial 0 :max 3))
)

;;; ── 反应规则 ────────────────────────────────────────────────

(reacts
  (react :key 'r_fail    :when (clock-filled? alert)    :then (list (effect 'finish 'fail)))
  (react :key 'r_success :when (clock-filled? traverse) :then (list (effect 'finish 'success)))
)

;;; ── 根视图（最后一行）──────────────────────────────────────

(if (clock-filled? alert) fail_scene root_scene)
```

---

## 九、常见错误与注意事项

| 问题 | 原因 | 解决 |
|------|------|------|
| `:check` 和 `:effects` 同时存在 | 互斥字段 | 有 check 时移除 `:effects`，结果写在 outcome 里 |
| `clock-filled?` 未识别 | 缺少 include | 加 `(include "common_clock_macros.scm")` |
| 文件没有根视图表达式 | 编译器找不到入口 | 末尾加一个 scene 引用或 cond 表达式 |
| `state` 块里的 clock `:initial` 超出 `:max` | 越界断言 | 确保 `0 ≤ initial ≤ max` |
| `:actions` 里的 `when` 返回 nil 报错 | 不会报错 | nil 会被自动过滤，可以放心用 `when` |
| 同一文件两个 `state` 块 | 只允许一个 | 合并成一个 `state` 块 |
| `:key` 重复 | 场景/行动 ID 冲突 | 保证每个 `:key` 在文件内唯一 |
