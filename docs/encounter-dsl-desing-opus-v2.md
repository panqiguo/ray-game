# Encounter DSL 设计方案 v2

## 1. 核心架构转变：反应式场景树

### 当前模型

```
静态定义（thug.py）
    → 编译为 CompiledEncounter
    → 运行时维护 (act_id, state_id, clock_values)  
    → 用 conditions 过滤出当前可见的节点/动作
```

问题：场景树是动态的，但定义是静态的。变化逻辑被压缩到 conditions 和 transitions 里，散落在三处。

### 新模型：`tree = f(state)`

```
encounter 函数 + 当前 state
    → 每次调用返回当前的场景树
    → 玩家执行动作 → state 更新 → 再次调用函数 → 新的场景树
```

这就是 React 的模型：**UI = f(state)**。

```
                    ┌──────────────┐
                    │   state      │
                    │  {clocks,    │◄──── 动作效果写回
                    │   flags}     │
                    └──────┬───────┘
                           │ 传入
                           ▼
                    ┌──────────────┐
                    │  encounter   │
                    │  函数 f(s)   │──── 每次重新计算
                    └──────┬───────┘
                           │ 返回
                           ▼
                    ┌──────────────┐
                    │  SceneTree   │──── 渲染到 UI
                    │  (actions)   │
                    └──────────────┘
```

**好处**：
- 不需要 act/state/transition 作为一等概念 — 它们只是控制流
- 不需要 conditions 来过滤可见性 — 函数直接只返回当前该看到的东西
- 不需要 `compile_encounter` 这层 — 没有静态编译步骤
- 逻辑集中 — 所有分支决策在一个地方

**运行时需要的元信息**（不属于场景树本身，但 UI 需要）：

```python
@dataclass
class EncounterDescriptor:
    id: str
    title: str
    description: str
    clocks: dict[str, ClockSpec]      # 所有可能出现的 clock
    build: Callable[[State], SceneTree]  # 场景树构建函数
    reward: tuple[Effect, ...]
```

---

## 2. 三种语法方案

下面用 **同一个 encounter（教训小混混）的同一段（Act 1, 徒手受压状态）** 来展示三种语法。

### 方案 A：Python

直接用 Python 函数。不需要解析器，不需要发明语法。IDE 自动补全、类型检查全部可用。

```python
from raygame.encounters.dsl import *

# ── 可复用片段 ──

def breathe():
    return action("喘息一下",
        "你强行拉开半口气，重新整理手里的节奏，但也会挨上一下。",
        do=[reset_hand, hp(-1)])

def knee_kick(desc):
    return check("踹膝脱身", desc,
        [REASON, FORCE], MID,
        ok("你一下踹垮了他。", clock("enemy_hp", -2)),
        partial("你踹实了一下。", clock("enemy_hp", -1)),
        fail("你动作慢了。", hp(-1)))


# ── 场景树构建函数 ──

@encounter("teach_thug", "教训一个小混混",
    desc="拿人钱财，帮人把这件事办干净。",
    clocks={"initiative": ("主动权", 2), "knife": ("夺刀", 2),
            "enemy_hp": ("敌人血量", 2), "opening": ("破绽", 2)},
    reward=[money(80)])
def teach_thug(s):

    if s.initiative < 2:
        # ═══ 摆脱压制 ═══
        if s.knife < 2:
            return scene("徒手受压",
                "打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。",

                check("防守反击", "你先稳住头脸和脚步，再找机会把他顶开。",
                    [REASON, EMPATHY], LOW,
                    ok("你稳稳顶住了节奏。", clock("initiative", +1)),
                    partial("你至少没有继续吃亏。", clock("initiative", +1)),
                    fail("你还是没完全顶住。", hp(-1))),

                check("直接挥拳", "你不跟他磨，直接狠狠干出一步空间。",
                    [FORCE], HIGH,
                    ok("你狠狠干出了一步空间。", clock("initiative", +2)),
                    partial("你砸中了他，但也只是暂时逼开。", clock("initiative", +1)),
                    fail("你被他顶了回来。", hp(-1))),

                check("扑向折刀", "你冒险扑向地上的折刀，想先把局势翻过来。",
                    [INSTINCT, FORCE], HIGH,
                    ok("你手已经摸到刀柄了。", clock("knife", +1)),
                    partial("你拖着伤抢到了第一步位置。", clock("knife", +1)),
                    fail("你扑过去了，但还没真正把刀抢出来。"),
                    do=[hp(-1)]),

                breathe(),
                show_clocks=["initiative", "knife"])

        else:  # knife >= 2
            return scene("持刀逼退",
                "刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。",

                check("防守反击", "你先稳住头脸和脚步，再找机会把他顶开。",
                    [REASON, EMPATHY], LOW,
                    ok("你稳稳顶住了节奏。", clock("initiative", +1)),
                    partial("你至少没有继续吃亏。", clock("initiative", +1)),
                    fail("你还是没完全顶住。", hp(-1))),

                check("持刀逼退", "刀一到手，你立刻逼他后撤，把主动权压回来。",
                    [FORCE, REASON], MID,
                    ok("你借着刀势一口气压住了他。", clock("initiative", +2)),
                    partial("你逼得他后退了一步。", clock("initiative", +1)),
                    fail("他还是硬顶了上来。", hp(-1))),

                breathe(),
                show_clocks=["initiative", "knife"])

    elif s.enemy_hp > 0:
        # ═══ 拿到优势后终结 ═══
        if s.opening < 2:
            return scene("对峙",
                "对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。",

                check("重拳追击", "你不给他喘气空间，直接压上去狠狠干。",
                    [FORCE], MID,
                    ok("你狠狠干中了一拳。", clock("enemy_hp", -1)),
                    partial("你打实了一下，但他还撑着。", clock("enemy_hp", -1)),
                    fail("你被他架住了。", hp(-1))),

                check("假动作试探", "你做一个假动作，先试着把他的防守骗开一层。",
                    [EMPATHY, INSTINCT], MID,
                    ok("他的防守被你骗得动了一下。", clock("opening", +1)),
                    partial("他开始有点被你带着走。", clock("opening", +1)),
                    fail("他没上当。")),

                knee_kick("你不追求漂亮，而是直接踹他的支撑腿。"),
                breathe(),
                show_clocks=["enemy_hp", "opening"])

        else:  # opening >= 2
            return scene("空门大开",
                "他的防守空档已经完全露出来了。狠狠干净地结束这场架。",

                check("终结一击", "你抓住空门，一击把他放倒。",
                    [FORCE], LOW,
                    ok("你干净利落地结束了这场架。", clock("enemy_hp", -2)),
                    partial("你一击放倒了他。", clock("enemy_hp", -2)),
                    fail("没打实，但已经足够。", clock("enemy_hp", -1))),

                knee_kick("你直接踹他的支撑腿，狠狠干净利落地结束。"),
                breathe(),
                show_clocks=["enemy_hp", "opening"])

    else:
        # ═══ 结束 ═══
        return end("success")
```

**为什么这比当前 thug.py 好**：

| 维度 | 当前 thug.py | 方案 A |
|------|-------------|--------|
| 动作在哪 | 单独的 dict，状态用字符串引用 | 直接在分支内 inline |
| 转换逻辑 | `on_clock_full` 在 act 尾部 | Python `if/else`，就在上下文里 |
| 需要理解几个概念 | encounter, act, state, transition, clock, condition | scene, check, clock, if/else |
| 加一个新状态 | 改 dict + 加 state + 加 transition | 加一个 `elif` 分支 |
| 复用动作 | 函数返回 ActionDef | 函数返回 action（一样） |
| 需要编译步骤 | 是（compile_encounter_script） | 否（直接调用函数） |

**Builder API 设计**（仅 7 个函数）：

```python
# 构建场景树
scene(title, desc, *actions, show_clocks=[])  -> SceneTree

# 构建动作
action(title, desc, do=[...])                  -> Action（无检定）
check(title, desc, suits, risk, ok, partial, fail, do=[])  -> Action（有检定）

# 构建检定结果
ok(text, *effects)       -> Outcome（完全成功）
partial(text, *effects)  -> Outcome（有代价成功）
fail(text, *effects)     -> Outcome（失败）

# 构建效果
clock(id, delta)   -> Effect（推进/消耗 clock）
hp(delta)          -> Effect（生命变化）
money(delta)       -> Effect（金钱变化）
reset_hand         -> Effect（常量，重置手牌）

# 结束 encounter
end(outcome)       -> EndSignal
```

---

### 方案 B：Lisp S-expression

用 S-expression 编写。需要一个小型解析器 + 求值器（~200 行 Python），但语法绝对统一 — 只有括号和原子。

```lisp
(encounter teach_thug "教训一个小混混"
  (desc "拿人钱财，帮人把这件事办干净。")
  (reward (money 80))
  (clocks
    (initiative "主动权" 2)
    (knife      "夺刀"   2)
    (enemy_hp   "敌人血量" 2)
    (opening    "破绽"   2))

  (cond
    ;; ═══ 第一幕：摆脱压制 ═══
    ((< initiative 2)
     (cond
       ((< knife 2)
        (scene "徒手受压"
          "打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。"

          (check "防守反击"
            "你先稳住头脸和脚步，再找机会把他顶开。"
            (suits reason empathy) (risk low)
            (ok      "你稳稳顶住了节奏。"             (initiative +1))
            (partial "你至少没有继续吃亏。"           (initiative +1))
            (fail    "你还是没完全顶住。"             (hp -1)))

          (check "直接挥拳"
            "你不跟他磨，直接狠狠干出一步空间。"
            (suits force) (risk high)
            (ok      "你狠狠干出了一步空间。"         (initiative +2))
            (partial "你砸中了他，但也只是暂时逼开。" (initiative +1))
            (fail    "你被他顶了回来。"               (hp -1)))

          (check "扑向折刀"
            "你冒险扑向地上的折刀，想先把局势翻过来。"
            (suits instinct force) (risk high)
            (do (hp -1))
            (ok      "你手已经摸到刀柄了。"           (knife +1))
            (partial "你拖着伤抢到了第一步位置。"     (knife +1))
            (fail    "你扑过去了，但还没真正把刀抢出来。"))

          (breathe)))

       (else
        (scene "持刀逼退"
          "刀终于到了你手里。现在你可以借着这口气把主动权彻底抢回来。"

          (check "防守反击"
            "你先稳住头脸和脚步，再找机会把他顶开。"
            (suits reason empathy) (risk low)
            (ok      "你稳稳顶住了节奏。"   (initiative +1))
            (partial "你至少没有继续吃亏。" (initiative +1))
            (fail    "你还是没完全顶住。"   (hp -1)))

          (check "持刀逼退"
            "刀一到手，你立刻逼他后撤，把主动权压回来。"
            (suits force reason) (risk mid)
            (ok      "你借着刀势一口气压住了他。" (initiative +2))
            (partial "你逼得他后退了一步。"       (initiative +1))
            (fail    "他还是硬顶了上来。"         (hp -1)))

          (breathe)))))

    ;; ═══ 第二幕：终结 ═══
    ((> enemy_hp 0)
     (cond
       ((< opening 2)
        (scene "对峙"
          "对方后退半步，准备再扑上来。你可以直接狠狠干，也可以先撬开他的破绽。"

          (check "重拳追击"
            "你不给他喘气空间，直接压上去狠狠干。"
            (suits force) (risk mid)
            (ok      "你狠狠干中了一拳。"           (enemy_hp -1))
            (partial "你打实了一下，但他还撑着。"   (enemy_hp -1))
            (fail    "你被他架住了。"               (hp -1)))

          (check "假动作试探"
            "你做一个假动作，先试着把他的防守骗开一层。"
            (suits empathy instinct) (risk mid)
            (ok      "他的防守被你骗得动了一下。" (opening +1))
            (partial "他开始有点被你带着走。"     (opening +1))
            (fail    "他没上当。"))

          (knee_kick "你不追求漂亮，而是直接踹他的支撑腿。")
          (breathe)))

       (else
        (scene "空门大开"
          "他的防守空档已经完全露出来了。狠狠干净地结束这场架。"

          (check "终结一击"
            "你抓住空门，一击把他放倒。"
            (suits force) (risk low)
            (ok      "你干净利落地结束了这场架。" (enemy_hp -2))
            (partial "你一击放倒了他。"           (enemy_hp -2))
            (fail    "没打实，但已经足够。"       (enemy_hp -1)))

          (knee_kick "你直接踹他的支撑腿，狠狠干净利落地结束。")
          (breathe)))))

    ;; ═══ 结束 ═══
    (else (end success))))
```

**实现需要什么**：

```python
# 1. 解析器：text → S-expression 树（~50行，递归下降）
def parse_sexp(text: str) -> list: ...

# 2. 求值器：S-expression + State → SceneTree（~150行）
#    内置 form：cond, scene, check, action, suits, risk, ok, partial, fail, hp, etc.
def eval_encounter(sexp: list, state: State) -> SceneTree: ...

# 3. 可复用片段用 define
# (define (breathe)
#   (action "喘息一下" "..." (do reset_hand (hp -1))))
# (define (knee_kick desc)
#   (check "踹膝脱身" desc ...))
```

---

### 方案 C：Ink 子集

用 Ink 的标准语法来编写条件分支和选择。问题是 Ink 没有技能检定的概念，我们需要用 Ink 的 **tag 系统** 来携带游戏机械信息。

```ink
VAR initiative = 0
VAR knife = 0
VAR enemy_hp = 2
VAR opening = 0

=== teach_thug ===
# ENCOUNTER: 教训一个小混混
# DESC: 拿人钱财，帮人把这件事办干净。
# REWARD: money 80

{
  - initiative < 2:
    { knife < 2: -> pressed_unarmed | else: -> knife_advantage }
  - enemy_hp > 0:
    { opening < 2: -> duel | else: -> guard_open }
  - else:
    -> end_success
}

= pressed_unarmed
# STATE: 徒手受压
打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。
+ [防守反击] 你先稳住头脸和脚步，再找机会把他顶开。 # CHECK: reason empathy, low
  { check_result:
    - success: 你稳稳顶住了节奏。 # EFFECT: initiative +1
    - cost: 你至少没有继续吃亏。 # EFFECT: initiative +1
    - fail: 你还是没完全顶住。 # EFFECT: hp -1
  }
  -> teach_thug
+ [直接挥拳] 你不跟他磨，直接狠狠干出一步空间。 # CHECK: force, high
  { check_result:
    - success: 你狠狠干出了一步空间。 # EFFECT: initiative +2
    - cost: 你砸中了他，但也只是暂时逼开。 # EFFECT: initiative +1
    - fail: 你被他顶了回来。 # EFFECT: hp -1
  }
  -> teach_thug
+ [扑向折刀] 你冒险扑向地上的折刀，想先把局势翻过来。 # EFFECT: hp -1 | CHECK: instinct force, high
  { check_result:
    - success: 你手已经摸到刀柄了。 # EFFECT: knife +1
    - cost: 你拖着伤抢到了第一步位置。 # EFFECT: knife +1
    - fail: 你扑过去了，但还没真正把刀抢出来。
  }
  -> teach_thug
+ [喘息一下] 你强行拉开半口气... # EFFECT: reset_hand, hp -1
  -> teach_thug

= knife_advantage
# ...后续类似...
```

**问题**：
- Ink tag（`#` 后面的部分）只是字符串，我们在里面发明了 `CHECK:`、`EFFECT:` 等微语法 — 本质上还是在发明新语法，只是藏在了 tag 里
- Ink 的流控制（divert `->`, gather `-`, tunnel `->->`) 是为线性叙事设计的，我们的循环式 encounter 要 `-> teach_thug` 回到入口重新求值，这不是 Ink 的惯用法
- 需要一个修改过的 Ink 运行时来处理 `check_result` 这种非标准 construct

---

## 3. 对比与推荐

| 维度 | Python (A) | Lisp (B) | Ink (C) |
|------|-----------|---------|---------|
| 需要解析器 | ❌ 不需要 | ✅ 需要（~50行） | ✅ 需要（Ink 解析器很大） |
| 语法发明量 | 零（全是合法 Python） | 零（标准 S-expression） | 中（tag 里藏了微语法） |
| IDE 支持 | ✅ 自动补全+类型检查 | ❌ 需要自己做 | 🔶 有 Ink 插件，但不识别自定义 tag |
| 中文内容友好 | ✅ 字符串即可 | ✅ 字符串即可 | ✅ 字符串即可 |
| 条件逻辑 | `if/elif/else` | `(cond ...)` | `{- condition: ...}` |
| 复用片段 | Python `def` | `(define ...)` | Ink `=== knot` |
| 可读性（内容作者） | 🔶 需要基础 Python | 🔶 需要接受括号 | ✅ 叙事部分最自然 |
| 适合树结构 | ✅ 函数调用天然是树 | ✅ S-exp 天然是树 | ❌ Ink 是线性流，不是树 |
| 技能检定表达 | ✅ 原生支持 | ✅ 原生支持 | ❌ 需要 hack tag |
| 项目融合成本 | 最低 | 中 | 最高 |

### 我的推荐：**方案 A（Python）**

理由：
1. **零基建成本** — 不需要写解析器，今天就能开始写内容
2. **零语法发明** — 全部是合法 Python，只有 7 个 builder 函数需要学
3. **反应式模型天然契合** — encounter 就是一个 Python 函数，`if/else` 就是条件分支
4. **复用就是函数** — `breathe()` 和 `knee_kick(desc)` 已经展示了这一点
5. **类型安全** — IDE 能检查参数类型，写错了立即报红

Python 唯一的代价是"看起来不像脚本"，但对于你这个项目（你自己就是主要内容作者 + 开发者），Python 的工程优势远大于这个代价。

如果未来需要非程序员作者来写 encounter，那时再考虑方案 B（Lisp），因为 S-expression 解析器极简（50 行），且语法完全统一。

---

## 4. 实现计划（方案 A）

### Phase 1：Builder API（~100行）

```
src/raygame/encounters/
├── builders.py       # NEW: scene(), check(), action(), ok(), partial(), fail(), clock(), hp(), ...
├── descriptor.py     # NEW: EncounterDescriptor, State, SceneTree 定义
├── thug.py           # REWRITE: 用新 API 重写
├── registry.py       # SIMPLIFY: 去掉 compile_encounter 逻辑
└── dsl.py            # DELETE: 不再需要
```

### Phase 2：运行时适配

当前运行时（screen 层、效果处理）期望 `CompiledEncounter`。需要适配为：

```python
# 旧：从 CompiledEncounter 里查 act, state, location, actions
root = encounter.locations_by_id[root_by_state[(act_id, state_id)]]
actions = [encounter.actions_by_id[aid] for aid in encounter.actions_by_location[root.id]]

# 新：直接调用函数
tree = descriptor.build(current_state)
# tree 就是一个 SceneTree，里面直接包含当前的 actions
```

### Phase 3：验证

用新 API 重写 thug encounter，确保运行效果与当前版本一致。
