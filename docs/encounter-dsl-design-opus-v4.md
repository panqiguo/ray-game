# Encounter DSL 设计方案 v4

## 1. 核心结论

这一版 encounter DSL 采用下面这条主线：

```text
持久化的是事实（store），重新计算的是表现（view）。
```

运行方式是：

```text
静态 DSL 程序 + 持久化 store
    -> 每次根据 store 求值 view
    -> 得到当前 scene tree
    -> 玩家执行 action
    -> 应用 action 效果到 store
    -> 执行 react 规则
    -> 再次求值 view
```

它不再把 encounter 建模为“预先枚举好的 act/state/transition 状态机”，而是建模为：

- 一份静态 DSL 程序
- 一份运行时持久化 store
- 一个把 store 投影成当前 scene tree 的求值过程

这意味着：

- encounter 的编译产物是**程序对象**，不是“全量静态场景树”
- 运行时不再持久化 `current_act_id` / `current_state_id`
- 当前看到的场景、动作和局部树结构都由 `view` 动态求值

---

## 2. 为什么要这样设计

当前 [thug.py](/Users/usr/Documents/python/ray-game/src/raygame/encounters/thug.py) / [dsl.py](/Users/usr/Documents/python/ray-game/src/raygame/encounters/dsl.py) 的问题不只是语法冗长，而是模型本身把 encounter 当成静态状态机。

这会带来几个结构性问题：

1. 作者需要先把动态局面压扁成离散 state
2. 动作、局面、切换逻辑散落在多处
3. 很难直观看出“当前事实下会长出什么树”
4. 一旦出现更复杂的树形 encounter，静态 state 数量会迅速膨胀

而这个项目里的 encounter 有一个很重要的特征：

**它最终永远会表现为一棵场景树。**

既然输出永远是树，那么最自然的 DSL 就应该直接描述：

- encounter 内部有哪些持久化事实
- 在这些事实下，当前树应该长成什么样
- 动作如何改变事实
- 哪些自动规则会在动作结算后继续推进事实

---

## 3. 四个一等概念

新的 DSL 只保留四个一等概念：

1. `store`
2. `view`
3. `action`
4. `react`

### 3.1 Store

`store` 是 encounter 生命周期内持续保存的变量集合。

它只应该保存“会影响后续局面”的最小必要事实，例如：

- `clock`
- `flag`
- `value`

例如小混混 encounter 的 store 可以是：

```python
{
    "initiative": 1,
    "knife": 0,
    "enemy_hp": 2,
    "opening": 0,
}
```

如果后续某个 encounter 需要记忆“已经进入第二幕，不允许回退”，那么也可以显式保存：

```python
{
    "phase": "finish",
}
```

不应该放进 store 的内容：

- 当前 scene tree
- 当前可见 action 列表
- 当前描述文本
- 任何能从现有事实稳定推导出的派生表现

### 3.2 View

`view` 是一个纯求值过程：

```text
render(program, store) -> scene_tree
```

它根据当前 `store` 返回 encounter 此刻应该展示的一棵场景树。

### 3.3 Action

`action` 表示玩家可执行的动作。

动作分为两类：

- 无检定动作
- 有检定动作

动作执行流程：

1. 应用前置效果
2. 若有检定，则结算 `ok / partial / fail`
3. 应用 outcome 效果
4. 执行 `react`
5. 返回新的 `store` 与结果文本

### 3.4 React

`react` 是动作结算后自动执行的规则。

它的职责是：

- 自动结束 encounter
- 推进不可逆阶段
- 同步 once-only flag
- 基于阈值把 store 收敛到正确状态

`react` 替代了旧模型中的 `transition`。

---

## 4. 语法选择

这一版选择 **Lisp / S-expression** 作为内容 DSL。

原因：

1. 输出就是树，S-expression 天然适合表达树
2. 条件分支、局部拼接、嵌套节点都能自然写成表达式
3. 不需要发明太多额外标点
4. 解析器和校验器都可以保持很小
5. 很适合数据驱动和编译期 assert

不把 Ink 作为主语法的原因：

- Ink 更适合线性流和 divert
- 当前问题核心不是“沿文本流前进”，而是“每次重算当前树”

不把 Python 作为内容主语法的原因：

- Python 很适合做宿主实现
- 但对内容作者来说，还是会掉回 builder、参数名和样板代码

建议的分层是：

- 内容 DSL：Lisp / S-expression
- 宿主实现：Python

---

## 5. 语言结构

### 5.1 顶层结构

```lisp
(encounter <id>
  (title <text>)
  (desc <text>)
  (reward ...)        ;; 可选
  (store ...)         ;; 必选
  (defs ...)          ;; 可选
  (reacts ...)        ;; 可选
  (view ...))         ;; 必选
```

顶层块的职责：

- `(title ...)`
  encounter 标题
- `(desc ...)`
  encounter 说明
- `(reward ...)`
  成功奖励
- `(store ...)`
  持久化状态声明
- `(defs ...)`
  可复用动作模板
- `(reacts ...)`
  动作后的自动规则
- `(view ...)`
  当前 scene tree 的构造表达式

### 5.2 Store

```lisp
(store
  (clock <id> <title> <initial> <max>)
  (flag <id> <bool>)
  (value <id> <initial>))
```

建议第一版支持三种存储单元：

- `(clock ...)`
  带上下界的进度条
- `(flag ...)`
  布尔标记
- `(value ...)`
  简单原子值，例如字符串或数字

约束：

- store 只保存最小必要事实
- clock 上下界在编译期校验
- 不保存当前 scene、当前 action 列表等派生表现

### 5.3 Defs

`defs` 用于定义可复用动作。

```lisp
(defs
  (defaction breathe
    (action "喘息一下" "你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。"
      (do (reset_hand) (health -1))))

  (defaction counter
    (check "防守反击" "你先稳住头脸和脚步，再找机会把他顶开。"
      (suits reason empathy) (risk low)
      (ok      "你稳稳顶住了节奏。"   (initiative +1))
      (partial "你至少没有继续吃亏。" (initiative +1))
      (fail    "你还是没完全顶住。"   (health -1))))

  (defaction (knee_kick desc)
    (check "踹膝脱身" desc
      (suits reason force) (risk mid)
      (ok      "你一下踹垮了他。" (enemy_hp -2))
      (partial "你踹实了一下。"   (enemy_hp -1))
      (fail    "你动作慢了。"     (health -1)))))
```

`defaction` 支持两种形式：

- 无参定义：`(defaction breathe ...)`
- 带参定义：`(defaction (knee_kick desc) ...)`

body 必须是：

- `(action ...)`
- `(check ...)`

这样读到定义时就能立刻知道它是不是检定动作。

### 5.4 Reacts

```lisp
(reacts
  (<condition> <effect> ...)
  ...)
```

示例：

```lisp
(reacts
  ((<= enemy_hp 0)
   (finish success)))
```

语义：

1. 动作结算后，按顺序检查每条 `react`
2. 条件满足则执行该规则的效果
3. 若某条规则导致 store 变化，则重新从第一条规则开始检查
4. 直到没有规则继续触发，或 encounter 结束

### 5.5 React 的收敛要求

`react` 必须设计为**可收敛**。

推荐用途：

- 结束条件
- 不可逆阶段推进
- once-only flag 设置
- 基于阈值的事实同步

不推荐用途：

- 在两个状态之间来回翻转
- 对同一 clock 来回推拉
- 依赖随机性
- 依赖玩家输入

实现上采用三层防护：

1. 设计约束：鼓励 `react` 只做单调推进
2. 编译期校验：拒绝明显的循环依赖
3. 运行时保护：设置硬上限，例如 `MAX_REACT_STEPS = 64`

编译器第一版不需要做完整形式化证明，但至少要拒绝明显危险的写法。

### 5.6 View

```lisp
(view
  <scene-expr>)
```

`<scene-expr>` 是一个求值后返回 scene 的表达式。可以是：

- `(scene ...)`
- `(cond ...)`
- `(if <cond> <then> <else>)`

### 5.7 Scene

`scene` 是树节点，必须带稳定 id：

```lisp
(scene <scene-id> <title> <desc>
  (show_clocks <id> ...)
  (actions <action-expr> ...)
  (children <scene-expr> ...))
```

例如：

```lisp
(scene pressure_unarmed
  "徒手受压"
  "打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。"
  ...)
```

为什么 `scene-id` 必须显式存在：

- 运行时需要稳定身份来做父子映射
- 测试和调试需要可断言的节点标识
- clock 展示和交互状态需要稳定锚点
- 节点身份不能依赖本地化文案

约束：

- `scene-id` 在 encounter 内全局唯一
- `scene-id` 不参与玩家显示

### 5.8 Action 表达式

`actions` 列表中可以出现：

| 形式 | 含义 |
|------|------|
| `breathe` | 引用无参 `defaction` |
| `(knee_kick "描述文本")` | 引用带参 `defaction` |
| `(check "标题" "描述" ...)` | 内联检定动作 |
| `(action "标题" "描述" ...)` | 内联简单动作 |
| `(if <cond> <action-expr>)` | 条件动作，不满足时不出现 |

### 5.9 Scene 子节点

`children` 中可以放：

- 直接 `scene-expr`
- `(if <cond> <scene-expr>)`
- `(cond ...)`

这让 encounter 真正能够表达“始终是一棵树，只是树会随着事实变化而改写”。

### 5.10 条件表达式

```lisp
(< x 2)
(<= x 2)
(> x 2)
(>= x 2)
(= x 2)
(and ...)
(or ...)
(not ...)
```

### 5.11 效果

建议第一版支持这些效果：

| 写法 | 语义 |
|------|------|
| `(initiative +1)` | 推进已声明 clock |
| `(enemy_hp -2)` | 消耗已声明 clock |
| `(health -1)` | 修改生命值 |
| `(stress +1)` | 修改压力 |
| `(money +80)` | 修改金钱 |
| `(reset_hand)` | 重置手牌 |
| `(set <id> <value>)` | 设置 store 变量 |
| `(finish success)` | 结束 encounter |

约束：

- 被当作 clock 更新的 id 必须已在 `store` 中声明
- `set` 只能写入已声明 store 项

---

## 6. 完整示例：教训一个小混混

```lisp
(encounter teach_thug
  (title "教训一个小混混")
  (desc "拿人钱财，帮人把这件事办干净。")
  (reward (money +80))

  (store
    (clock initiative "主动权"  0 2)
    (clock knife      "夺刀"    0 2)
    (clock enemy_hp   "敌人血量" 2 2)
    (clock opening    "破绽"    0 2))

  (defs
    (defaction breathe
      (action "喘息一下" "你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。"
        (do (reset_hand) (health -1))))

    (defaction (knee_kick desc)
      (check "踹膝脱身" desc
        (suits reason force) (risk mid)
        (ok      "你一下踹垮了他。" (enemy_hp -2))
        (partial "你踹实了一下。"   (enemy_hp -1))
        (fail    "你动作慢了。"     (health -1)))))

  (reacts
    ((<= enemy_hp 0)
     (finish success)))

  (view
    (cond
      ((< initiative 2)
       (cond
         ((< knife 2)
          (scene pressure_unarmed
            "徒手受压"
            "打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。"
            (show_clocks initiative knife)
            (actions
              (check "防守反击" "你先稳住头脸和脚步，再找机会把他顶开。"
                (suits reason empathy) (risk low)
                (ok      "你稳稳顶住了节奏。"   (initiative +1))
                (partial "你至少没有继续吃亏。" (initiative +1))
                (fail    "你还是没完全顶住。"   (health -1)))

              (check "直接挥拳" "你不跟他磨，直接狠狠干出一步空间。"
                (suits force) (risk high)
                (ok      "你狠狠干出了一步空间。"         (initiative +2))
                (partial "你砸中了他，但也只是暂时逼开。" (initiative +1))
                (fail    "你被他顶了回来。"               (health -1)))

              (check "扑向折刀" "你冒险扑向地上的折刀，想先把局势翻过来。"
                (do (health -1))
                (suits instinct force) (risk high)
                (ok      "你手已经摸到刀柄了。"           (knife +1))
                (partial "你拖着伤抢到了第一步位置。"     (knife +1))
                (fail    "你扑过去了，但还没真正把刀抢出来。"))

              breathe)))

         (else
          (scene pressure_with_knife
            "持刀逼退"
            "刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。"
            (show_clocks initiative knife)
            (actions
              (check "防守反击" "你先稳住头脸和脚步，再找机会把他顶开。"
                (suits reason empathy) (risk low)
                (ok      "你稳稳顶住了节奏。"   (initiative +1))
                (partial "你至少没有继续吃亏。" (initiative +1))
                (fail    "你还是没完全顶住。"   (health -1)))

              (check "持刀逼退" "刀一到手，你立刻逼他后撤，把主动权压回来。"
                (suits force reason) (risk mid)
                (ok      "你借着刀势一口气压住了他。" (initiative +2))
                (partial "你逼得他后退了一步。"       (initiative +1))
                (fail    "他还是硬顶了上来。"         (health -1)))

              breathe)))))

      (else
       (cond
         ((< opening 2)
          (scene duel
            "对峙"
            "对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。"
            (show_clocks enemy_hp opening)
            (actions
              (check "重拳追击" "你不给他喘气空间，直接压上去狠狠干。"
                (suits force) (risk mid)
                (ok      "你狠狠干中了一拳。"         (enemy_hp -1))
                (partial "你打实了一下，但他还撑着。" (enemy_hp -1))
                (fail    "你被他架住了。"             (health -1)))

              (check "假动作试探" "你做一个假动作，先试着把他的防守骗开一层。"
                (suits empathy instinct) (risk mid)
                (ok      "他的防守被你骗得动了一下。" (opening +1))
                (partial "他开始有点被你带着走。"     (opening +1))
                (fail    "他没上当。"))

              (knee_kick "你不追求漂亮，而是直接踹他的支撑腿。")
              breathe)))

         (else
          (scene guard_open
            "空门大开"
            "他的防守空档已经完全露出来了。狠狠干净地结束这场架。"
            (show_clocks enemy_hp opening)
            (actions
              (check "终结一击" "你抓住空门，一击把他放倒。"
                (suits force) (risk low)
                (ok      "你干净利落地结束了这场架。" (enemy_hp -2))
                (partial "你一击放倒了他。"           (enemy_hp -2))
                (fail    "没打实，但已经足够。"       (enemy_hp -1)))

              (knee_kick "你直接踹他的支撑腿，狠狠干净利落地结束。")
              breathe)))))))
```

这个例子刻意没有显式 `phase`，因为它当前确实可以由 clock 阈值直接分段。

但这只是一个例子，不是默认规则。

如果以后这个 encounter 允许阶段回退，或者需要记忆“已经进入第二幕”，那就应该把 `phase` 显式存进 `store`。

---

## 7. 编译产物与运行时接口

### 7.1 编译产物

这套 DSL 会编译成静态程序对象，但不会编译成全量静态 scene tree。

建议的编译产物：

```python
@dataclass(frozen=True)
class CompiledEncounterProgram:
    id: str
    title: str
    description: str
    store_spec: StoreSpec
    defs: dict[str, ActionTemplate]
    react_rules: tuple[ReactRule, ...]
    view_expr: ViewExpr
    rewards: tuple[Effect, ...]
```

### 7.2 运行时状态

运行时只持久化：

```python
@dataclass
class ActiveEncounterState:
    encounter_id: str
    store: dict[str, int | bool | str]
```

不再持久化：

- `current_act_id`
- `current_state_id`
- `hidden_actions`
- `hidden_locations`

这些都应该改为从 `store + view` 动态得出。

### 7.3 Rendered 结果

`render()` 的返回值应当是“当前渲染快照”，而不只是裸 `SceneTree`。

建议：

```python
@dataclass(frozen=True)
class RenderedEncounter:
    root: "RenderedScene"


@dataclass(frozen=True)
class RenderedScene:
    scene_id: str
    title: str
    description: str
    shown_clock_ids: tuple[str, ...]
    actions: tuple["RenderedAction", ...]
    children: tuple["RenderedScene", ...]


@dataclass(frozen=True)
class ActionHandle:
    scene_path: tuple[str, ...]
    slot_index: int
    action_key: str


@dataclass(frozen=True)
class RenderedAction:
    handle: ActionHandle
    title: str
    description: str
    check: object | None
```

这里的重点是：

- `scene_id` 是稳定节点身份
- `ActionHandle` 是动作实例身份
- 运行时真正 resolve 的对象是 handle，而不是单个字符串 action id

### 7.4 为什么需要 ActionHandle

单个字符串 action id 不够表达动态树里的动作实例，因为：

1. 同一个 `defaction` 可能同时出现在多个 scene 中
2. 内联动作不能用玩家文案当身份
3. 运行时需要知道“这是本次渲染结果中的哪一个动作”

因此：

- 编译期仍可为 defaction / inline action 生成稳定内部 key
- 运行时交给 UI 和 `resolve_action()` 的必须是实例级 `ActionHandle`

`action_key` 的建议来源：

- `defaction`：`def:<name>`
- 内联 action：`inline:<ast-path>`

这些 key 只用于内部寻址，不暴露给内容作者。

### 7.5 运行时接口

```python
render(program, store) -> RenderedEncounter
resolve_action(program, store, handle, check_result) -> StepResult
```

其中：

```python
@dataclass
class StepResult:
    text: str
    store: dict[str, int | bool | str]
    finished: bool
    outcome: str | None
```

---

## 8. 设计决策记录

### 8.1 为什么推荐完整 `cond` 分支，而不是在一个 scene 里散落很多 `if`

推荐优先写成“一个条件分支返回一个完整 scene”，因为：

- 内容作者能一眼看出某个局面下玩家到底看到什么
- 标题、描述、动作跟着局面一起走
- 不需要心算多个局部 `if`

例如更推荐：

```lisp
(cond
  ((< knife 2)
   (scene pressure_unarmed "徒手受压" "..."
     (actions ...)))
  (else
   (scene pressure_with_knife "持刀逼退" "..."
     (actions ...))))
```

而不是：

```lisp
(scene pressure
  "..."
  (actions
    counter
    (if (< knife 2) punch)
    (if (>= knife 2) knife_press)))
```

但局部 `if` 依然有用，例如：

- 某句描述文本按条件多一行
- 某个小动作只在很细的条件下出现

结论：

- 大结构优先 `cond`
- 小变化允许 `if`

### 8.2 什么时候该显式使用 `phase`

`phase` 不是默认多余，也不是默认必需。

当阶段能由**单调事实唯一推导**时，可以不显式存 `phase`。

当 encounter 有下面这些特征时，应该把 `phase` 放进 `store`：

- 进入下一幕之后不允许回退
- 阶段需要记忆历史路径
- 阶段受多个条件共同控制
- 同一个 clock 在不同阶段语义不同
- 即使数值回退，叙事上也不能回到旧局面

### 8.3 为什么 `scene` 一定要有 id

因为动态树运行时必须可靠寻址：

- 节点身份不能依赖文案
- 同标题节点可能并存
- 测试和调试需要稳定标识
- 后续如果做 UI 动画或选中保持，也需要节点锚点

### 8.4 为什么不再强调“自动 action id”

因为动态树里更重要的是“动作实例身份”。

真正需要保证的是：

- 编译期有稳定内部 action key
- 运行时有实例级 `ActionHandle`

而不是给内容作者暴露一个全局字符串 action id。

### 8.5 为什么要对 react 做收敛限制

因为 encounter 的目标是“可靠、可 assert”，不是“尽量宽松容错”。

如果允许作者随意写互相翻转的 `react`，那 action 结算就可能卡死。

所以：

- DSL 层面鼓励单调推进
- 编译器拒绝明显循环
- 运行时设置 hard cap 并 assert 失败

这比默默吞掉错误更符合项目风格。

---

## 9. 内建 form 清单

### 结构

`encounter` `title` `desc` `reward` `store` `defs` `reacts` `view` `scene` `actions` `children` `show_clocks`

### 定义

`clock` `flag` `value` `defaction` `action` `check`

### 动作内部

`do` `suits` `risk` `ok` `partial` `fail`

### 控制流

`cond` `if` `else` `and` `or` `not` `=` `<` `<=` `>` `>=`

### 效果

`health` `stress` `money` `reset_hand` `set` `finish` + 已声明 clock 的 `(<clock-id> ±N)` 简写

---

## 10. 实施路径

### Phase 1

实现最小解析与求值链路：

- S-expression 解析器
- `store` / `defs` / `reacts` / `view` 的 AST
- 单根 scene 渲染
- `check` / `action` 执行
- `react` 基础循环与硬上限

目标：

- 用小混混 encounter 跑通最小闭环

### Phase 2

补齐稳定寻址：

- `scene_id`
- `ActionHandle`
- render 快照对象
- 测试断言工具

### Phase 3

补齐树能力：

- `children`
- 多层 scene 渲染
- clock 展示锚定

### Phase 4

接入现有 UI 与 rules：

- 替换 encounter 加载方式
- 接入当前 screen 层
- 用回归测试对齐 thug 行为

### Phase 5

补作者体验：

- 语法高亮
- lint
- 基础校验提示

---

## 11. 最终判断

这版 v4 的核心取舍是：

- 选择 Lisp / S-expression
- 选择持久化 `store`
- 选择每次动态重算当前 scene tree
- 选择 `react` 做动作后的自动收敛
- 选择 `scene id` 和 `ActionHandle` 作为动态树运行时身份
- 放弃预编译全量静态状态树

它不是“把现有 Python encounter DSL 改写成另一种文本语法”，而是 encounter 模型本身的一次重设计。

这套设计更贴近作者真正想表达的东西：

- 现在世界里有哪些事实
- 在这些事实下，当前树长成什么样
- 玩家做一件事后，事实如何变化
- 变化之后，树如何重新被投影出来
