# Encounter DSL 设计方案

## 1. 当前方案的问题

`thug.py` 用 Python 函数调用构造一棵静态的 encounter 定义树，再编译为 `CompiledEncounter`。对内容作者来说有几个痛点：

| 问题 | 表现 |
|------|------|
| **动作与状态分离** | `ACT_1_ACTIONS` 是一个平铺的 dict，状态里用字符串 key 引用。要理解一个状态提供什么选择，必须在两处来回跳。 |
| **转换规则远离上下文** | `on_clock_full("knife", ...)` 写在 act 末尾的 `transitions` 元组里，离 knife clock 被推进的那个 `rush_knife` 动作很远。 |
| **看不到"流"** | 读 Python 代码时，无法顺着一条路径追踪：如果我连续两次 rush_knife 成功，接下来会发生什么？整个流散落在定义、状态、转换三处。 |
| **模板代码太多** | `encounter_action()`, `check()`, `outcome()`, `effect()` 每个动作都要嵌套 4-5 层调用。 |
| **状态的激活条件不在状态旁边** | `knife_advantage` 什么时候出现？要到 `transitions` 里才能找到答案。 |

核心矛盾：**场景树是随玩家行动不断变化的，但定义格式是静态、声明式的，中间的变化逻辑被压缩到了几行 transition 规则里。**

---

## 2. 设计目标

1. **像读故事一样从上往下读** —— encounter 的流程在文件里是清晰可追踪的
2. **动作就在状态里** —— 不需要跳到别处查"这个状态能做什么"
3. **变化可见** —— clock 驱动的状态切换就写在它发生的地方附近
4. **紧凑的检定语法** —— 一个动作不需要 15 行嵌套
5. **可复用的片段** —— 常用动作（如"喘息"）定义一次，到处引用
6. **编译到现有运行时** —— DSL 是源格式，编译产物仍是 `EncounterDef` / `CompiledEncounter`

---

## 3. 从 Ink 借鉴了什么

| Ink 概念 | 在本 DSL 中的对应 | 为什么借鉴 |
|----------|-------------------|------------|
| **Knot** (`=== knot_name`) | **Act** (`== act_id`) | 大的叙事阶段 |
| **Stitch** (`= stitch_name`) | **State** (`= state_id`) | 阶段内的场景切面 |
| **Choice** (`+ [text]`) | **Action** (`+ 动作标题`) | 玩家可执行的选择 |
| **Divert** (`-> target`) | **Transition** (`-> state_id` / `-> act_id`) | 流向控制 |
| **Conditional content** (`{var: ...}`) | **When 子句** (`@ when clock full`) | 基于状态的内容切换 |
| **Variable** (`VAR x = 0`) | **Clock 声明** (`~ clock id "名称" /N`) | 可跟踪的进度状态 |
| **Gather** (`-`) | **（不借鉴）** | 我们的场景是循环式的，不是线性收拢 |

**关键差异**：Ink 是线性叙事中的分支与合流。我们的 encounter 是**循环式**的 —— 玩家反复从当前状态的动作池中选择动作，直到 clock 触发状态转换。所以我们不照搬 Ink 的"流"，而是保留 **"状态 + 动作池"** 的循环模型，但用 Ink 的排版直觉让它可读。

---

## 4. DSL 语法设计

### 4.1 完整示例：教训一个小混混

```ink
=== teach_thug: 教训一个小混混
/// 拿人钱财，帮人把这件事办干净。
~ reward: money +80

# ─── 可复用动作片段 ───

@ breathe: 喘息一下
  你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。
  {reset_hand} {health -1}

@ knee_kick(desc): 踹膝脱身
  {desc}
  ? REASON FORCE @mid
    >> 你一下踹垮了他。 {enemy_hp -2}
    >  你踹实了一下。 {enemy_hp -1}
    X  你动作慢了。 {health -1}


# ─── 第一幕：摆脱压制 ───

== act_1: 摆脱压制
/// 先从墙边和压制里脱出来，夺回主动权。
~ clock initiative "主动权" /2  [objective]
~ clock knife "夺刀" /2

= pressed_unarmed: 徒手受压  [initial]
打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。

  + 防守反击
    你先稳住头脸和脚步，再找机会把他顶开。
    ? REASON EMPATHY @low
      >> 你稳稳顶住了节奏。 {initiative +1}
      >  你至少没有继续吃亏。 {initiative +1}
      X  你还是没完全顶住。 {health -1}

  + 直接挥拳
    你不跟他磨，直接狠狠干出一步空间。
    ? FORCE @high
      >> 你狠狠干出了一步空间。 {initiative +2}
      >  你砸中了他，但也只是暂时逼开。 {initiative +1}
      X  你被他顶了回来。 {health -1}

  + 扑向折刀
    你冒险扑向地上的折刀，想先把局势翻过来。
    {health -1}
    ? INSTINCT FORCE @high
      >> 你手已经摸到刀柄了。 {knife +1}
      >  你拖着伤抢到了第一步位置。 {knife +1}
      X  你扑过去了，但还没真正把刀抢出来。

  + @breathe

--- knife full -> knife_advantage

= knife_advantage: 持刀逼退
刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。

  + 防守反击
    你先稳住头脸和脚步，再找机会把他顶开。
    ? REASON EMPATHY @low
      >> 你稳稳顶住了节奏。 {initiative +1}
      >  你至少没有继续吃亏。 {initiative +1}
      X  你还是没完全顶住。 {health -1}

  + 持刀逼退
    刀一到手，你立刻逼他后撤，把主动权压回来。
    ? FORCE REASON @mid
      >> 你借着刀势一口气压住了他。 {initiative +2}
      >  你逼得他后退了一步。 {initiative +1}
      X  他还是硬顶了上来。 {health -1}

  + @breathe

--- initiative full -> act_2.duel


# ─── 第二幕：终结 ───

== act_2: 拿到优势后终结
/// 你已经摆脱压制，现在要狠狠干净地收尾。
~ clock enemy_hp "敌人血量" /2  [objective]
~ clock opening "破绽" /2

= duel: 对峙  [initial]
对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。

  + 重拳追击
    你不给他喘气空间，直接压上去狠狠干。
    ? FORCE @mid
      >> 你狠狠干中了一拳。 {enemy_hp -1}
      >  你打实了一下，但他还撑着。 {enemy_hp -1}
      X  你被他架住了。 {health -1}

  + 假动作试探
    你做一个假动作，先试着把他的防守骗开一层。
    ? EMPATHY INSTINCT @mid
      >> 他的防守被你骗得动了一下。 {opening +1}
      >  他开始有点被你带着走。 {opening +1}
      X  他没上当。

  + @knee_kick("你不追求漂亮，而是直接踹他的支撑腿。")

  + @breathe

--- opening full -> guard_open

= guard_open: 空门大开
他的防守空档已经完全露出来了。狠狠干净地结束这场架。

  + 终结一击
    你抓住空门，一击把他放倒。
    ? FORCE @low
      >> 你干净利落地结束了这场架。 {enemy_hp -2}
      >  你一击放倒了他。 {enemy_hp -2}
      X  没打实，但已经足够。 {enemy_hp -1}

  + @knee_kick("你直接踹他的支撑腿，狠狠干净利落地结束。")

  + @breathe

--- enemy_hp empty -> END success
```

### 4.2 语法元素速查

#### 结构层级

```
=== encounter_id: 标题        # Encounter（全局唯一）
== act_id: 标题               # Act（幕）
= state_id: 标题  [initial]   # State（状态），[initial] 标记入口状态
```

这三级结构直接映射到 `EncounterDef → EncounterActDef → EncounterStateDef`。

#### 描述文本

```
/// 这是 encounter/act 的描述（紧跟在标题行之后）
```

状态的描述直接写为标题行下方的普通文本段落（无前缀），直到遇到第一个 `+` 动作。

#### Clock 声明

```
~ clock <id> "<显示名>" /<segments>  [objective]
```

- `[objective]` 标记表示这是该 act 的目标时钟
- 没有标记的是局部辅助时钟
- clock id 在整个 encounter 内唯一

#### 动作定义

```
+ 动作标题
  动作描述文本（可多行）
  {effect_kind value}             # 无条件效果（执行即触发）
  ? SUIT1 SUIT2 @risk_level       # 技能检定行
    >> 成功文本 {effect} {effect}  # success outcome
    >  代价文本 {effect}           # cost outcome
    X  失败文本 {effect}           # fail outcome
```

**检定行 `?`**：
- 花色用空格分隔：`REASON`, `FORCE`, `EMPATHY`, `INSTINCT`
- 风险等级用 `@` 前缀：`@low`, `@mid`, `@high`

**结果行前缀**：
- `>>` = 完全成功 (success)
- `>`  = 有代价的成功 (cost)
- `X`  = 失败 (fail)

**效果 `{}`**：
- `{clock_id +N}` → advance_encounter_clock（推进 clock）
- `{clock_id -N}` → damage_encounter_clock（消耗 clock）
- `{health -N}` → change_health
- `{reset_hand}` → reset_hand
- `{money +N}` → change_resource money

#### 转换规则

```
--- <clock_id> full -> <target>        # clock 填满时转换
--- <clock_id> empty -> <target>       # clock 清空时转换
--- <clock_id> full -> END success     # 结束 encounter
```

`<target>` 可以是：
- `state_id` — 同 act 内切换状态
- `act_id.state_id` — 跨 act 切换（同时切换 act 和目标 state）
- `END success` / `END fail` / `END abort` — 结束整个 encounter

**转换规则的位置至关重要**：它写在触发它的那些动作的下方、下一个状态的上方，这样阅读时能自然地看到"做完这些动作 → clock 满了 → 进入下一个状态"的流。

#### 可复用动作片段

```
@ fragment_name: 动作标题
  描述和检定...

@ fragment_name(param1, param2): 动作标题
  {param1} ...
```

引用：
```
+ @fragment_name
+ @fragment_name("具体描述文本")
```

片段定义在 encounter 顶部（`===` 之后、第一个 `==` 之前），作用域为整个 encounter。

---

## 5. 编译模型

```
┌─────────────────────┐
│   .encounter 文件    │  ← 内容作者编写
│  (DSL 源文件)        │
└────────┬────────────┘
         │ parse
         ▼
┌─────────────────────┐
│  EncounterScript     │  ← 现有的中间表示 (dsl.py 中的 dataclass)
│  ├─ ActScript        │
│  │  ├─ StateScript   │
│  │  │  └─ actions    │
│  │  └─ transitions   │
│  └─ fragments        │
└────────┬────────────┘
         │ compile_encounter_script()  (现有逻辑)
         ▼
┌─────────────────────┐
│  EncounterDef        │  ← 现有的运行时定义
│  └─ CompiledEncounter│
└─────────────────────┘
```

**关键设计决策**：DSL 编译的产物就是现有的 `EncounterScript`。这意味着：
- 不需要修改运行时（`registry.py`、screen 层面、效果处理等）
- DSL 只是 `thug.py` 的另一种写法
- Python DSL 和文本 DSL 可以共存

---

## 6. 解析器实现思路

### 6.1 文件格式

文件扩展名：`.enc`（或 `.encounter`）

字符编码：UTF-8

### 6.2 解析策略

逐行解析，基于行首标记分发：

```python
LINE_PATTERNS = {
    r'^===\s+'  : 'encounter_header',   # encounter 声明
    r'^==\s+'   : 'act_header',         # act 声明
    r'^=\s+'    : 'state_header',       # state 声明
    r'^///'     : 'description',        # 描述行
    r'^~\s+'    : 'directive',          # 指令（clock, reward 等）
    r'^\+\s+'   : 'action',            # 动作开始
    r'^\?\s+'   : 'check',            # 检定行
    r'^>>'      : 'success_outcome',   # 成功结果
    r'^>\s'     : 'cost_outcome',      # 代价结果
    r'^X\s'     : 'fail_outcome',      # 失败结果
    r'^\{.*\}'  : 'effect',            # 效果
    r'^---\s+'  : 'transition',        # 转换规则
    r'^@\s+'    : 'fragment_def',      # 片段定义
    r'^#'       : 'comment',           # 注释
}
```

### 6.3 效果语法的映射

| DSL 写法 | 编译产物 |
|----------|---------|
| `{initiative +1}` | `effect("advance_encounter_clock", "initiative:1")` |
| `{enemy_hp -2}` | `effect("damage_encounter_clock", "enemy_hp:2")` |
| `{health -1}` | `effect("change_health", -1)` |
| `{money +80}` | `effect("change_resource", "money:80")` |
| `{reset_hand}` | `effect("reset_hand", True)` |
| `{set_flag xxx}` | `effect("set_encounter_flag", "xxx")` |

**规则**：
- 如果 id 匹配当前 encounter 的某个 clock → 生成 clock 操作效果
- `health`, `stress` → 生成 `change_health` / `change_stress`
- `money`, `cigarettes` 等资源 → 生成 `change_resource`
- 其他 → 按 `effect(id, value)` 原样传递

---

## 7. 为什么这比 Python DSL 好

### 7.1 对比阅读

**Python DSL（56行来表达 act_1 的一个状态 + 3个动作）**：
```python
ACT_1_ACTIONS = {
    "counter": encounter_action(
        id="thug_counter", title="防守反击",
        description="你先稳住头脸和脚步...",
        check=check(
            suits=(Suit.REASON, Suit.EMPATHY), risk=Risk.LOW,
            success=outcome("你稳稳顶住了节奏。", effect("advance_encounter_clock", "initiative:1")),
            cost=outcome("你至少没有继续吃亏。", effect("advance_encounter_clock", "initiative:1")),
            fail=outcome("你还是没完全顶住。", effect("change_health", -1)),
        ),
    ),
    # ... more actions ...
}
# ... 30 lines later ...
state(
    id="pressed_unarmed", title="徒手受压",
    description="打手把你逼在墙边...",
    actions=("counter", "breathe", "punch", "rush_knife"),
),
# ... 10 lines later ...
on_clock_full("knife", effect("set_encounter_state", "knife_advantage")),
```

**新 DSL（同样内容，20行）**：
```
= pressed_unarmed: 徒手受压  [initial]
打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。

  + 防守反击
    你先稳住头脸和脚步，再找机会把他顶开。
    ? REASON EMPATHY @low
      >> 你稳稳顶住了节奏。 {initiative +1}
      >  你至少没有继续吃亏。 {initiative +1}
      X  你还是没完全顶住。 {health -1}

  + 直接挥拳
    ...

--- knife full -> knife_advantage
```

### 7.2 改善了什么

| 维度 | Python DSL | 新 DSL |
|------|-----------|--------|
| 动作找状态 | 跳两处 | 直接在状态内 |
| 状态转换 | 在 act 尾部集中声明 | 就在两个状态之间 |
| 效果语法 | `effect("advance_encounter_clock", "initiative:1")` | `{initiative +1}` |
| 读懂一个状态需要看几处 | 3处（dict, state, transitions） | 1处 |
| 新增一个动作 | 改 dict + 改 state.actions 元组 | 加一个 `+` 块 |

---

## 8. 扩展点

### 8.1 条件动作

某些动作只在特定条件下出现（比如必须有某个物品）：

```
+ 用折刀威胁  [when: has_item knife]
  你亮出折刀，让他知道继续硬来的代价。
  ...
```

### 8.2 叙事文本穿插

在状态描述或动作结果中插入条件性叙事：

```
= duel: 对峙  [initial]
对方后退半步，准备再扑上来。
{? has_item knife}
  你手里的折刀在路灯下闪了一下。
{/}
你可以直接狠狠干，也可以先撬开他的破绽。
```

### 8.3 多文件 include

大型 encounter 可以拆分：

```
~ include "thug_act1.enc"
~ include "thug_act2.enc"
```

### 8.4 自动生成 action id

当前 Python DSL 要求每个 action 有全局唯一 id（如 `thug_counter`）。新 DSL 可以自动生成：
- 规则：`{encounter_id}_{act_id}_{state_id}_{action_index}`
- 或者用 action 标题的拼音/hash
- 内容作者不需要关心 id

---

## 9. 实现路径

| 阶段 | 内容 | 产出 |
|------|------|------|
| **Phase 1** | 解析器原型 | `parse_encounter(text) -> EncounterScript` |
| **Phase 2** | 用新 DSL 重写 thug.py | `thug.enc` + 验证与现有 Python 版产出一致 |
| **Phase 3** | Fragment 系统 | 支持 `@` 定义和引用 |
| **Phase 4** | 编辑器支持 | VS Code 语法高亮 + 基础 LSP |
| **Phase 5** | 条件/叙事扩展 | `[when:]` 和 `{? }` 语法 |

Phase 1-2 就足以替代当前 Python DSL，后续按需迭代。
