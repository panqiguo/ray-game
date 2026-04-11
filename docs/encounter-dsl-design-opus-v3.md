# Encounter DSL 设计方案 v3（合并稿）

## 1. 对 Codex 方案的评价

Codex 方案（`encounter-dsl-design-v2.md`）在架构上有三个关键洞察，比 opus-v2 更深刻：

### 1.1 做对了的

| 洞察 | 意义 |
|------|------|
| **显式 `store`** | 明确区分"持久化事实"和"派生表现"。opus-v2 的 Lisp 草案把 clock 声明混在顶层，没有单独命名"这些是你的持久化状态"。 |
| **`react` 规则** | 把"动作后的自动推进"从"渲染逻辑"里分离出来。opus-v2 把结束条件写在 `cond` 的 `else` 分支里（`(end success)`），这混淆了视图和副作用。 |
| **`scene` 是树节点** | 明确 `scene` 可以有 `children`，为未来多层 encounter 留了口。opus-v2 只有扁平的 `scene`。 |
| **编译产物是程序对象** | `CompiledEncounterProgram` 保留 AST，运行时每次求值。比 opus-v2 的"编译为静态 EncounterScript"在概念上更干净。 |

一句话：Codex 把 **"持久化的是事实，重新计算的是表现"** 这个核心原则贯彻得比 opus-v2 彻底。

### 1.2 需要改进的

| 问题 | 表现 |
|------|------|
| **view 中散落的 `(if ...)`** | 完整示例里，一个 `scene` 内部散布了 6 个独立的 `(if ...)` 来控制不同动作的可见性。这让内容作者无法一眼看到"在某个具体局面下，玩家到底能做什么"。需要上下扫描并心算所有 `if` 条件才能拼出完整画面。 |
| **`defaction` 不支持参数** | `knee_kick_normal` 和 `knee_kick_finish` 只有 `desc` 不同，但必须写成两个独立定义。应该支持参数化：`(defaction (knee_kick desc) ...)`。 |
| **手动 `phase` 增加了概念层** | 用 `(value phase pressed)` + `react` 规则来管理阶段，但对于 thug 这类 encounter，阶段完全由 clock 值决定（`initiative < 2` = 压制阶段）。引入 `phase` 变量是多余的间接层。 |
| **`check` 内部用 `(title ...) (desc ...)` 关键字形式** | 与 `defaction` 的结构不一致，增加学习成本。应该统一为位置参数（第一个字符串 = 标题，第二个 = 描述）。 |

### 1.3 核心分歧：散落 `if` vs 完整 `cond` 分支

这是两个方案最大的风格差异。用 thug 的"第一幕"来对比：

**Codex 风格**：一个 scene，内部用多个 `if` 切换局部动作

```lisp
(scene pressure
  (desc (if (< knife 2) "打手把你逼在墙边..." "刀终于到了你手里..."))
  (actions
    counter
    breathe
    (if (< knife 2) (check "直接挥拳" ...))
    (if (< knife 2) (check "扑向折刀" ...))
    (if (>= knife 2) (check "持刀逼退" ...))))
```

**Opus 风格**：用 `cond` 分出两个完整 scene

```lisp
(cond
  ((< knife 2)
   (scene "徒手受压" "打手把你逼在墙边..."
     (actions
       (check "防守反击" ...) (check "直接挥拳" ...) (check "扑向折刀" ...) breathe)))
  (else
   (scene "持刀逼退" "刀终于到了你手里..."
     (actions
       (check "防守反击" ...) (check "持刀逼退" ...) breathe))))
```

**推荐 opus 风格**，理由：

1. 每个 scene 是自包含的，不需要心算条件
2. 标题和描述跟着场景走，不需要 `(if ...)` 包裹
3. 共享动作通过 `defaction` 复用，不会导致重复
4. 读法是"如果 knife < 2，玩家看到的是这个完整场景"，而不是"玩家看到的场景由这些零散的 if 拼出来"

但 `if` 在局部小变化时仍然有用（比如只改一行描述文本），不应禁止。

---

## 2. 合并后的架构

### 2.1 核心运行模型

沿用 codex 的模型，一字不改：

```
持久化的是事实（store），重新计算的是表现（view）。
```

```
静态 DSL 程序 + 持久化 store
    → 每次根据 store 重新求值 view
    → 得到当前 scene tree
    → 玩家执行 action
    → 应用效果到 store
    → 执行 react 规则（可能进一步修改 store）
    → 再次求值 view → 新的 scene tree
```

### 2.2 四个一等概念

| 概念 | 职责 |
|------|------|
| **store** | encounter 生命周期内的持久化变量（clock, flag, value） |
| **view** | 纯函数：`f(store) → scene_tree`，根据 store 投影出当前场景 |
| **action** | 玩家可执行的动作，产生效果修改 store |
| **react** | 动作结算后自动执行的规则，用于阶段推进和自动结束 |

### 2.3 不再需要的老概念

| 废弃概念 | 替代方式 |
|----------|----------|
| `act` / `state` | view 中的 `cond` 分支 |
| `transition` | `react` 规则 |
| `condition` | `cond` / `if` 表达式 |
| `compile_encounter` | 编译为程序对象，运行时求值 |

---

## 3. 语言设计

### 3.1 顶层结构

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

### 3.2 Store

```lisp
(store
  (clock <id> <title> <initial> <max>)   ;; 带上下界的进度条
  (flag <id> <bool>)                      ;; 布尔标记
  (value <id> <initial>))                 ;; 自由值（字符串/数字）
```

约束：
- store 只保存**最小必要事实**
- 不保存派生状态（当前 scene、可见 action 列表等）
- clock 的上下界在编译期校验

### 3.3 Defs（可复用动作定义）

```lisp
(defs
  ;; 无参定义：简单动作
  (defaction breathe
    (action "喘息一下" "你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。"
      (do (reset_hand) (health -1))))

  ;; 无参定义：检定动作
  (defaction counter
    (check "防守反击" "你先稳住头脸和脚步，再找机会把他顶开。"
      (suits reason empathy) (risk low)
      (ok      "你稳稳顶住了节奏。"   (initiative +1))
      (partial "你至少没有继续吃亏。" (initiative +1))
      (fail    "你还是没完全顶住。"   (health -1))))

  ;; 带参定义：desc 是参数
  (defaction (knee_kick desc)
    (check "踹膝脱身" desc
      (suits reason force) (risk mid)
      (ok      "你一下踹垮了他。" (enemy_hp -2))
      (partial "你踹实了一下。"   (enemy_hp -1))
      (fail    "你动作慢了。"     (health -1)))))
```

**`defaction` 的形式**：
- 名称是原子 → 无参：`(defaction breathe ...)`
- 名称是列表 → 带参：`(defaction (knee_kick desc) ...)`

**body 必须是 `(action ...)` 或 `(check ...)`**：
- `(action title desc (do ...))` — 无检定动作
- `(check title desc (suits ...) (risk ...) (ok ...) (partial ...) (fail ...))` — 检定动作

### 3.4 Reacts

```lisp
(reacts
  (<condition> <effect> ...)
  ...)
```

语义：
- 动作结算后，按顺序检查每条 react 规则
- 条件满足则执行效果
- 一轮中若 store 有变化，则重新从第一条开始检查
- 直到没有规则继续触发，或 encounter 结束

示例：
```lisp
(reacts
  ((<= enemy_hp 0) (finish success)))
```

### 3.5 View

```lisp
(view
  <scene-expr>)
```

`<scene-expr>` 是一个求值后返回 `scene` 的表达式。可以是：

- 直接 `(scene ...)` 节点
- `(cond ...)` 条件分支
- `(if <cond> <then> <else>)` 二分支

**`scene` 节点**：

```lisp
(scene <title> <desc>
  (show_clocks <id> ...)        ;; 可选：展示哪些 clock
  (actions <action-expr> ...)   ;; 动作列表
  (children <scene-expr> ...))  ;; 可选：子节点
```

title 和 desc 是位置参数（前两个字符串）。

**`actions` 列表中可以出现**：

| 形式 | 含义 |
|------|------|
| `breathe` | 引用无参 defaction |
| `(knee_kick "描述文本")` | 引用带参 defaction |
| `(check "标题" "描述" ...)` | 内联检定动作 |
| `(action "标题" "描述" ...)` | 内联简单动作 |
| `(if <cond> <action-expr>)` | 条件动作（条件不满足时该动作不出现） |

### 3.6 表达式与效果

**条件表达式**：

```lisp
(< x 2)  (<= x 2)  (> x 2)  (>= x 2)  (= x 2)
(and ...)  (or ...)  (not ...)
```

**效果**：

| 写法 | 语义 |
|------|------|
| `(initiative +1)` | 推进已声明 clock（正数） |
| `(enemy_hp -2)` | 消耗已声明 clock（负数） |
| `(health -1)` | 修改生命值 |
| `(money +80)` | 修改金钱 |
| `(reset_hand)` | 重置手牌 |
| `(set <id> <value>)` | 设置 store 变量 |
| `(finish success)` | 结束 encounter |

clock 效果的约束：clock id 必须在 `store` 中已声明。编译期可校验。

---

## 4. 完整示例：教训一个小混混

```lisp
(encounter teach_thug
  (title "教训一个小混混")
  (desc "拿人钱财，帮人把这件事办干净。")
  (reward (money 80))

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
      ;; ═══ 第一幕：摆脱压制 ═══
      ((< initiative 2)
       (cond
         ((< knife 2)
          (scene "徒手受压"
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
          (scene "持刀逼退"
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

      ;; ═══ 第二幕：拿到优势后终结 ═══
      (else
       (cond
         ((< opening 2)
          (scene "对峙"
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
          (scene "空门大开"
            "他的防守空档已经完全露出来了。狠狠干净地结束这场架。"
            (show_clocks enemy_hp opening)
            (actions
              (check "终结一击" "你抓住空门，一击把他放倒。"
                (suits force) (risk low)
                (ok      "你干净利落地结束了这场架。" (enemy_hp -2))
                (partial "你一击放倒了他。"           (enemy_hp -2))
                (fail    "没打实，但已经足够。"       (enemy_hp -1)))

              (knee_kick "你直接踹他的支撑腿，狠狠干净利落地结束。")
              breathe))))))))
```

### 4.1 对比原版

| 维度 | 原 thug.py (222行) | v3 Lisp (~100行) |
|------|-------|------|
| 理解一个局面需要看几处 | 3处（actions dict, state, transitions） | 1处（cond 分支内的 scene） |
| 转换逻辑 | `on_clock_full` + `compile_encounter` | `react` 规则 + `cond` 分支 |
| 复用动作 | Python 函数，仍需在 dict 和 state 两处登记 | `defaction` 定义一次，直接用名称引用 |
| 参数化复用 | 可以（Python 函数参数） | 可以（`(defaction (name param) ...)`） |
| 效果语法 | `effect("advance_encounter_clock", "initiative:1")` | `(initiative +1)` |

---

## 5. 编译与运行时

### 5.1 编译产物

```python
@dataclass(frozen=True)
class CompiledEncounterProgram:
    id: str
    title: str
    description: str
    store_spec: StoreSpec              # clock/flag/value 声明
    defs: dict[str, ActionTemplate]    # defaction 定义
    react_rules: tuple[ReactRule, ...]
    view_expr: ViewExpr                # AST，每次求值
    rewards: tuple[Effect, ...]
```

### 5.2 运行时状态

```python
@dataclass
class ActiveEncounterState:
    encounter_id: str
    store: dict[str, int | bool | str]  # 只有这个被持久化
```

不再保存 `current_act_id`、`current_state_id`、`hidden_actions` 等。

### 5.3 运行时接口

```python
# 求值 view → 当前场景树
render(program, store) -> SceneTree

# 玩家执行动作 → 应用效果 → 运行 react → 返回结果
resolve_action(program, store, action_id, check_result) -> StepResult

# StepResult 包含：新 store、结果文本、是否结束、结束类型
```

### 5.4 Action ID 自动生成

内容作者不需要手写 action id。编译器自动生成：

- defaction：`{encounter_id}_{defaction_name}`
- 内联 action：`{encounter_id}_{scene_title_hash}_{action_index}`

---

## 6. 内建 form 清单

### 结构

`encounter` `title` `desc` `reward` `store` `defs` `reacts` `view` `scene` `actions` `children` `show_clocks`

### 定义

`clock` `flag` `value` `defaction` `action` `check`

### 动作内部

`do` `suits` `risk` `ok` `partial` `fail`

### 控制流

`cond` `if` `else` `and` `or` `not` `=` `<` `<=` `>` `>=`

### 效果

`health` `stress` `money` `reset_hand` `set` `finish` + clock id 简写 `(clock_id ±N)`

**总计约 35 个 form**，其中控制流和比较运算符是标准 Lisp，领域特有的约 20 个。

---

## 7. 设计决策记录

### Q: 为什么不用显式 `phase` 变量？

对于 thug 这类 encounter，阶段完全由 clock 值推导：`initiative < 2` = 压制阶段。引入 `phase` 是多余的间接层。

但如果未来有 encounter 的阶段不能由 clock 推导（比如依赖历史路径），可以在 store 中声明 `(value phase pressed)` 配合 `react` 使用。**语言支持但不强制。**

### Q: 散落 `if` 还是完整 `cond` 分支？

推荐 `cond` 分支（每个分支返回一个完整 scene），因为：
- 自包含，不需要心算
- 标题和描述跟着场景走

但 `if` 仍可用于 scene 内部的小变化（如条件性多显示一句话）。

### Q: `defaction` 的 body 为什么要显式用 `(action ...)` 或 `(check ...)`？

让类型在语法上可见。读到 `(check ...)` 就知道有骰子检定，读到 `(action ...)` 就知道是直接效果。不需要看内部结构来判断动作类型。

---

## 8. 实施路径

| 阶段 | 内容 | 产出 |
|------|------|------|
| **Phase 1** | S-expression 解析器（~50行） + 最小求值器 | `parse_sexp()` + `eval_view()` |
| **Phase 2** | 用 thug encounter 跑通完整链路 | `teach_thug.enc` + 与原版行为一致的测试 |
| **Phase 3** | `defaction` 复用 + 参数化 | 通过 thug 的 `breathe` 和 `knee_kick` 验证 |
| **Phase 4** | 接入现有 encounter screen | 替换 `registry.py` 的加载逻辑 |
| **Phase 5** | 编辑器支持 | 语法高亮 + 基础校验 |

Phase 1-2 是最小可用版本，后续按需迭代。
