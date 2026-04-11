# Encounter DSL 设计方案 v2

## 1. 设计结论

这一版不再把 encounter 设计成“预先枚举所有状态，再编译为静态 `CompiledEncounter`”。

新的核心模型是：

```text
静态 DSL 程序 + 持久化 store
    -> 每次根据 store 重新求值
    -> 得到当前 scene tree
    -> 玩家执行 action
    -> 更新 store
    -> 执行自动 react 规则
    -> 再次求值 scene tree
```

其中：

- `store` 是 encounter 的持久化运行时状态
- `scene tree` 是每次根据 `store` 动态投影出来的当前表现
- DSL 本身是静态的，但它不会被编译成“全量静态场景树”
- encounter 运行时不再以 `act/state/transition` 作为核心心智模型

一句话总结：

**持久化的是事实，重新计算的是表现。**

---

## 2. 为什么要放弃静态状态树

当前 [thug.py](/Users/usr/Documents/python/ray-game/src/raygame/encounters/thug.py) / [dsl.py](/Users/usr/Documents/python/ray-game/src/raygame/encounters/dsl.py) 的核心问题，不只是语法不够好写，而是模型上把 encounter 当成“静态状态机”。

这会带来几个结构性问题：

1. 内容作者需要手动枚举局面
2. 同一个局面的变化要拆散到 action、state、transition 三处
3. “当前树为什么长这样”不直观，因为真实规则被压进了 state 切换
4. 如果后续 encounter 出现并行局面、局部节点替换、动态长出子树，会越来越别扭

而这个项目里，encounter 的外在表现始终是一棵树。

既然输出永远是树，更自然的做法就是：

- DSL 定义“如何根据 store 构造树”
- 每次重新求值
- 不持久化派生出来的 scene/state

---

## 3. 核心运行模型

### 3.1 四个一等概念

新的 encounter 运行时只保留四个核心概念：

1. `store`
2. `view`
3. `action`
4. `react`

### 3.2 Store

`store` 是 encounter 生命周期内持续保存的变量集合。

它应该只保存“会影响后续局面”的最小必要事实，例如：

- `clock`
- `flag`
- `value`
- `enum`

例如小混混 encounter 的 store 可以是：

```python
{
    "phase": "pressed",
    "initiative": 1,
    "knife": 0,
    "enemy_hp": 2,
    "opening": 0,
}
```

不应该放进 store 的内容：

- 当前 scene tree
- 当前可见 action 列表
- 当前描述文本
- 可以由现有变量推导出来的冗余 state 名称

### 3.3 View

`view` 是一个纯求值过程：

```text
render(program, store) -> scene_tree
```

它根据当前 `store`，返回 encounter 此刻应该展示给玩家的一棵场景树。

### 3.4 Action

`action` 表示玩家可执行的动作。

动作分为两类：

- 无检定动作
- 有检定动作

动作执行时：

1. 应用前置效果
2. 如果有检定，结算 `ok / partial / fail`
3. 应用结果效果
4. 运行 `react`
5. 得到新的 `store`

### 3.5 React

`react` 是动作后自动执行的规则集合，用来表达：

- 阶段推进
- 自动结束
- 某些 flag / value 的自动同步
- 某些 invariant 的收束

`react` 替代了当前 encounter 里的 `transition` 概念。

它不负责“渲染什么”，只负责“当事实满足条件时，自动把 store 收敛到正确状态”。

---

## 4. 语法选择

这一版选择 **Lisp / S-expression** 作为 DSL 主语法。

原因：

1. 输出本身就是树，S-expression 天然适合表达树
2. 条件渲染、局部拼接、嵌套节点都可以自然写成表达式
3. 几乎不需要发明额外专用标点
4. 解析器和校验器都可以保持很简单
5. 数据驱动、可断言、可扩展

不选择以 Ink 作为主语法的原因：

- Ink 更擅长线性流和 divert
- 我们的问题核心不是“沿文本流前进”，而是“每次重算当前树”
- 如果硬套 Ink，最终会写出很多像 Ink 但本质上不是 Ink 的特殊规则

不选择以 Python 作为内容主语法的原因：

- Python 很适合做宿主实现
- 但不适合做内容作者主语法
- 内容会重新落回 builder、参数名、函数嵌套、样板代码

因此推荐分层是：

- **内容 DSL**：Lisp / S-expression
- **宿主实现**：Python

---

## 5. 和现有 Lisp 草案的关系

已有的 Lisp 草案方向是对的，因为它已经抓住了“根据变量动态求值当前 scene”的核心。

但需要做四个结构收敛：

1. 加显式 `store`
2. 加显式 `react`
3. 让 `scene` 成为真正的树节点，支持 `children`
4. 支持动作复用定义 `defaction`，但保留就地定义能力

这四点的原因分别是：

- `store`：明确哪些变量是 encounter 的持久化事实
- `react`：把“局面推进”从“渲染条件”里分离出来
- `children`：让 DSL 真的表达树，而不是只有单个主场景
- `defaction`：避免复杂 encounter 里反复复制动作定义

---

## 6. 语言骨架

### 6.1 顶层结构

建议 encounter 文件组织为：

```lisp
(encounter <id>
  (title <text>)
  (desc <text>)
  (reward ...)
  (store ...)
  (defs ...)
  (reacts ...)
  (view ...))
```

其中：

- `(title ...)` 必选
- `(desc ...)` 可选
- `(reward ...)` 可选
- `(store ...)` 必选
- `(defs ...)` 可选
- `(reacts ...)` 可选
- `(view ...)` 必选

### 6.2 Store

```lisp
(store
  (clock initiative "主动权" 0 2)
  (clock knife "夺刀" 0 2)
  (clock enemy_hp "敌人血量" 2 2)
  (clock opening "破绽" 0 2)
  (value phase pressed)
  (flag saw_knife false))
```

建议内建三种存储单元：

- `(clock <id> <title> <initial> <max>)`
- `(value <id> <initial>)`
- `(flag <id> <bool>)`

约束：

- `clock` 的上下界在编译期可校验
- `value` / `flag` 只能保存简单原子值
- 避免把派生状态存进 store

### 6.3 Defs

可复用定义放在 `(defs ...)` 中。

```lisp
(defs
  (defaction breathe
    (title "喘息一下")
    (desc "你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。")
    (do
      (reset_hand)
      (health -1)))

  (defaction counter
    (title "防守反击")
    (desc "你先稳住头脸和脚步，再找机会把他顶开。")
    (check (suits reason empathy) (risk low)
      (ok "你稳稳顶住了节奏。" (initiative +1))
      (partial "你至少没有继续吃亏。" (initiative +1))
      (fail "你还是没完全顶住。" (health -1)))))
```

同时也允许在 `scene` 里直接就地写动作，不强制所有动作都提到 `defs`。

### 6.4 Reacts

```lisp
(reacts
  ((and (= phase pressed) (>= initiative 2))
   (set phase finish))

  ((and (= phase finish) (<= enemy_hp 0))
   (finish success)))
```

规则语义：

- 动作结算后，按顺序执行 `react`
- 一轮 `react` 可能修改 store
- 如果本轮有改动，则重新从第一条规则开始检查
- 直到没有规则继续触发，或 encounter 结束

这可以保证结算后的 store 收敛到稳定状态。

### 6.5 View

`view` 负责根据当前 store 返回树。

```lisp
(view
  (scene root
    (children
      ...)))
```

`scene` 是真正的树节点，而不只是“单个状态块”。

建议 `scene` 节点支持：

- `(title ...)`
- `(desc ...)`
- `(actions ...)`
- `(children ...)`
- `(show_clocks ...)`

---

## 7. 完整示例：教训一个小混混

```lisp
(encounter teach_thug
  (title "教训一个小混混")
  (desc "拿人钱财，帮人把这件事办干净。")
  (reward (money +80))

  (store
    (clock initiative "主动权" 0 2)
    (clock knife "夺刀" 0 2)
    (clock enemy_hp "敌人血量" 2 2)
    (clock opening "破绽" 0 2)
    (value phase pressed))

  (defs
    (defaction breathe
      (title "喘息一下")
      (desc "你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。")
      (do
        (reset_hand)
        (health -1)))

    (defaction counter
      (title "防守反击")
      (desc "你先稳住头脸和脚步，再找机会把他顶开。")
      (check (suits reason empathy) (risk low)
        (ok "你稳稳顶住了节奏。" (initiative +1))
        (partial "你至少没有继续吃亏。" (initiative +1))
        (fail "你还是没完全顶住。" (health -1))))

    (defaction knee_kick_normal
      (title "踹膝脱身")
      (desc "你不追求漂亮，而是直接踹他的支撑腿。")
      (check (suits reason force) (risk mid)
        (ok "你一下踹垮了他。" (enemy_hp -2))
        (partial "你踹实了一下。" (enemy_hp -1))
        (fail "你动作慢了。" (health -1))))

    (defaction knee_kick_finish
      (title "踹膝脱身")
      (desc "你直接踹他的支撑腿，狠狠干净利落地结束。")
      (check (suits reason force) (risk mid)
        (ok "你一下踹垮了他。" (enemy_hp -2))
        (partial "你踹实了一下。" (enemy_hp -1))
        (fail "你动作慢了。" (health -1)))))

  (reacts
    ((and (= phase pressed) (>= initiative 2))
     (set phase finish))

    ((and (= phase finish) (<= enemy_hp 0))
     (finish success)))

  (view
    (scene root
      (children
        (cond
          ((= phase pressed)
           (scene pressure
             (title "摆脱压制")
             (desc
               (if (< knife 2)
                 "打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。"
                 "刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。"))
             (show_clocks initiative knife)
             (actions
               counter
               breathe
               (if (< knife 2)
                 (check
                   (title "直接挥拳")
                   (desc "你不跟他磨，直接狠狠干出一步空间。")
                   (suits force)
                   (risk high)
                   (ok "你狠狠干出了一步空间。" (initiative +2))
                   (partial "你砸中了他，但也只是暂时逼开。" (initiative +1))
                   (fail "你被他顶了回来。" (health -1))))
               (if (< knife 2)
                 (check
                   (title "扑向折刀")
                   (desc "你冒险扑向地上的折刀，想先把局势翻过来。")
                   (do (health -1))
                   (suits instinct force)
                   (risk high)
                   (ok "你手已经摸到刀柄了。" (knife +1))
                   (partial "你拖着伤抢到了第一步位置。" (knife +1))
                   (fail "你扑过去了，但还没真正把刀抢出来。")))
               (if (>= knife 2)
                 (check
                   (title "持刀逼退")
                   (desc "刀一到手，你立刻逼他后撤，把主动权压回来。")
                   (suits force reason)
                   (risk mid)
                   (ok "你借着刀势一口气压住了他。" (initiative +2))
                   (partial "你逼得他后退了一步。" (initiative +1))
                   (fail "他还是硬顶了上来。" (health -1)))))))

          ((= phase finish)
           (scene finish
             (title "拿到优势后终结")
             (desc
               (if (< opening 2)
                 "对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。"
                 "他的防守空档已经完全露出来了。狠狠干净地结束这场架。"))
             (show_clocks enemy_hp opening)
             (actions
               (check
                 (title "重拳追击")
                 (desc "你不给他喘气空间，直接压上去狠狠干。")
                 (suits force)
                 (risk mid)
                 (ok "你狠狠干中了一拳。" (enemy_hp -1))
                 (partial "你打实了一下，但他还撑着。" (enemy_hp -1))
                 (fail "你被他架住了。" (health -1)))
               breathe
               (if (< opening 2)
                 (check
                   (title "假动作试探")
                   (desc "你做一个假动作，先试着把他的防守骗开一层。")
                   (suits empathy instinct)
                   (risk mid)
                   (ok "他的防守被你骗得动了一下。" (opening +1))
                   (partial "他开始有点被你带着走。" (opening +1))
                   (fail "他没上当。")))
               (if (< opening 2) knee_kick_normal)
               (if (>= opening 2)
                 (check
                   (title "终结一击")
                   (desc "你抓住空门，一击把他放倒。")
                   (suits force)
                   (risk low)
                   (ok "你干净利落地结束了这场架。" (enemy_hp -2))
                   (partial "你一击放倒了他。" (enemy_hp -2))
                   (fail "没打实，但已经足够。" (enemy_hp -1))))
               (if (>= opening 2) knee_kick_finish))))))))
```

这个例子体现了几个关键点：

- `phase` 是持久化事实，不是派生出来的 scene id
- 当前场景内容完全由 `view` 根据 store 求值决定
- “摆脱压制 -> 终结” 由 `reacts` 推进，而不是由静态 transition 切换
- `knife` / `opening` 控制的是同一树节点中的局部表现变化

---

## 8. 建议的内建 form

建议第一版只支持少量内建 form，避免 DSL 过早膨胀。

### 8.1 结构类

- `encounter`
- `title`
- `desc`
- `reward`
- `store`
- `defs`
- `reacts`
- `view`
- `scene`
- `actions`
- `children`
- `show_clocks`

### 8.2 定义类

- `clock`
- `value`
- `flag`
- `defaction`

### 8.3 控制流类

- `cond`
- `if`
- `and`
- `or`
- `not`
- `=`
- `<`
- `<=`
- `>`
- `>=`

### 8.4 动作类

- `check`
- `do`
- `suits`
- `risk`
- `ok`
- `partial`
- `fail`

### 8.5 效果类

- `health`
- `stress`
- `money`
- `reset_hand`
- `set`
- `finish`

以及：

- `(clock_id +N)` / `(clock_id -N)` 这种对已声明 clock 的简写更新

---

## 9. 编译与运行时边界

### 9.1 编译产物

这一版 DSL 会编译成 **静态程序对象**，但不会编译成全量静态场景树。

建议编译目标类似于：

```python
@dataclass(frozen=True)
class CompiledEncounterProgram:
    id: str
    title: str
    description: str
    store_spec: EncounterStoreSpec
    defs: dict[str, CompiledActionTemplate]
    react_rules: tuple[CompiledReactRule, ...]
    view_ast: SceneExpr
    rewards: tuple[Effect, ...]
```

### 9.2 运行时状态

运行时只保存：

```python
@dataclass
class ActiveEncounterState:
    encounter_id: str
    store: dict[str, int | bool | str]
```

而不再保存：

- `current_act_id`
- `current_state_id`
- `hidden_actions`
- `hidden_locations`

这些都应该改为从 `view` 和 `store` 动态得出。

### 9.3 运行时接口

建议运行时只暴露这几个核心接口：

```python
render_encounter(program, store) -> SceneTree
resolve_action(program, store, action_id, resolution) -> EncounterStepResult
apply_reacts(program, store) -> EncounterReactResult
```

其中：

```python
@dataclass
class EncounterStepResult:
    text: str
    store: dict[str, int | bool | str]
    finished: bool
    outcome: str | None
```

---

## 10. 为什么这一版更适合内容作者

相对于静态 `act/state/transitions` 模型，这一版更接近作者真实想表达的内容：

- 现在有哪些局面片段存在
- 这些片段各自有哪些动作
- 哪些事实会让树长出、替换或消失
- 哪些条件会让整个 encounter 自动进入下一阶段

作者看到的不再是：

- “我要先造一个 state，再登记 transition，再确保 action id 对得上”

而是：

- “如果现在是这种局面，就渲染这棵树；做完动作后如果满足条件，就更新事实；然后重新渲染”

这更像是在写一个随事实变化的内容系统，而不是在手写状态机。

---

## 11. 实施路径

### Phase 1

先做最小求值器：

- 解析 S-expression
- 编译 `store / reacts / view`
- 支持单根 `scene`
- 支持最基本的 `check` / `if` / `cond`

目标：

- 用小混混 encounter 跑通整条链路

### Phase 2

补齐树能力：

- `children`
- 多节点组合
- clock 展示控制

### Phase 3

补齐复用能力：

- `defaction`
- 参数化 helper
- 更好的编译期校验

### Phase 4

再考虑作者体验：

- 语法高亮
- lint
- encounter 可视化调试工具

---

## 12. 最终判断

这版 DSL 的核心取舍是：

- 选择 **Lisp/S-expression**
- 选择 **持久化 store**
- 选择 **每次动态重算当前 scene tree**
- 选择 **react 规则驱动的自动收敛**
- 放弃 **预编译全量静态状态树**

这不是“把现有 Python DSL 改写成另一种文本语法”，而是 encounter 模型本身的一次重设计。
