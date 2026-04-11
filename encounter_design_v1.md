# Encounter 设计稿 V1

## 目标

本稿定义 `Encounter` 系统的内容模型与工程组织方式，用于支持：

- 多幕切换
- 同幕内状态变化导致可用行动变化
- 局部时钟目标
- 行动结果触发状态/幕切换
- 完成后回到世界并发放奖励

设计要求：

- 内容 authoring 顺手，不要大量手写底层条件
- 运行时结构清晰，可校验、可调试
- 一个 encounter 一个文件，作为独立数据来源，便于管理
- 不引入过重脚本系统，仍保持声明式为主
- 尽量复用现有 `LocationNode / ActionDef / ProgressClock / Effect / Condition`


## 核心判断

### 1. Encounter 是独立内容对象，但不是第二套内容系统

它不应继续硬塞在普通 `Location -> Action` 里。

原因：

- encounter 有自己的幕
- 有自己的状态
- 有自己的局部时钟
- 可用行动集合会变化

所以它应该是与 `Scenario` 并列的一类内容数据。

但它不应该复制一整套新的地点/行动模型。

更好的做法是：

- encounter 只新增少量壳层结构
- 幕内内容继续复用现有 `LocationNode` 与 `ActionDef`
- encounter 更像“新的桌面上下文”，不是“第二套世界系统”

### 2. “动作替换”不做成一等机制

所谓：

- `"顶肘反打" -> "持刀逼退"`
- `"重拳追击" -> "终结一击"`

本质上不是替换，而是：

- 当前 state 改了
- 新 state 下可见动作不同了

因此底层不需要 `replace_action` 系统。

更好的抽象是：

- `current_act`
- `current_state`
- `visible_if`

### 3. 内容 authoring 不应大量手写 `visible_if`

运行时仍然保留 declarative 条件，但内容层不应直接在每个 action 上手写：

- `in_encounter_act(...)`
- `in_encounter_state(...)`

更好的 authoring 方式是：

- `act(...)`
- `state(...)`
- `state` 下面直接持有一棵 `root: LocationNode`

编译阶段再对这棵树里的全部节点自动补上：

- `in_encounter_act(...)`
- `in_encounter_state(...)`


## 推荐目录结构

```text
src/raygame/encounters/
  __init__.py
  defs.py
  registry.py
  thug.py
  ...
```

说明：

- `defs.py`
  - Encounter dataclass / runtime-facing schema
- `registry.py`
  - 收集 encounter 内容，按 id 注册
- `thug.py`
  - 一个 encounter 一个文件

推荐规则：

- 每个 encounter 文件只定义一个顶层 `ENCOUNTER`
- 文件名就是 encounter 的主题，例如：
- `thug.py`
- `warehouse_case.py`
- `hotel_client.py`

第一版先不强制单独做 `builders.py`。

原因：

- 现有 content builder 已有不少可复用部分
- encounter 语义还在收敛
- 太早抽专门 builder 容易把 authoring 方式锁死

更稳的顺序是：

- 先有 `defs.py`
- 再有具体 encounter 文件
- 等 encounter 数量多了，再抽薄 helper


## 入口规划

### 世界入口

世界中的某个行动可通过 effect 进入 encounter：

```python
effect("start_encounter", "teach_thug")
```

执行后：

- 当前世界状态挂起
- 写入 `active_encounter`
- 切到 `ScreenName.ENCOUNTER`

### 结束出口

Encounter 结束后：

- 应用奖励/结局 effects
- 清空 `active_encounter`
- 回到世界桌面

建议支持：

- `finish_encounter("success")`
- `finish_encounter("fail")`
- `finish_encounter("abort")`


## Dataclass 草案

### EncounterDef

```python
@dataclass(frozen=True)
class EncounterDef:
    id: str
    title: str
    description: str
    acts: tuple["EncounterActDef", ...]
    rewards: tuple[Effect, ...] = ()
    fail_effects: tuple[Effect, ...] = ()
```

说明：

- `description` 用作开场与整体简介
- `rewards` 是成功结束后应用的 effects
- `fail_effects` 是失败结束后应用的 effects

### EncounterActDef

```python
@dataclass(frozen=True)
class EncounterActDef:
    id: str
    title: str
    description: str
    objective_clock: ProgressClockSpec
    initial_state_id: str
    states: tuple["EncounterStateDef", ...]
    transitions: tuple["EncounterTransitionDef", ...] = ()
```

说明：

- 每幕只有一个主目标钟
- 每个 state 都持有一棵自己的内容树
- `transitions` 通常用于：
  - clock 满时进入下一幕
  - clock 归零时结束

### EncounterStateDef

```python
@dataclass(frozen=True)
class EncounterStateDef:
    id: str
    title: str
    description: str
    root: LocationNode
```

说明：

- 这是内容 authoring 最重要的层
- 内容作者主要在这里思考：
  - 这个状态下，这张桌面长什么样
  - 这张桌面里有哪些地点、子地点和行动

### EncounterTransitionDef

```python
@dataclass(frozen=True)
class EncounterTransitionDef:
    kind: str
    source: str
    effects: tuple[Effect, ...]
```

推荐 `kind`：

- `clock_full`
- `clock_empty`
- `flag_present`

说明：

- `source` 用来指向 clock id 或 flag id
- `effects` 负责：
  - `set_act`
  - `set_state`
  - `finish_encounter`


## Runtime State 草案

```python
@dataclass
class ActiveEncounterState:
    encounter_id: str
    current_act_id: str
    current_state_id: str
    clocks: dict[str, int]
    flags: set[str]
    modifiers: dict[str, int]
    result_tags: tuple[str, ...] = ()
```

说明：

- `clocks`
  - encounter 本地时钟
  - 例如 `initiative`, `enemy_hp`
- `flags`
  - 局部状态标记
  - 例如 `thug_off_balance`
- `modifiers`
  - 临时数值修正
  - 例如 `next_action:+1`
- `result_tags`
  - 用于成功后的额外奖励标签


## 内容 authoring 方式

第一版推荐：

- encounter 自己只用很薄的 dataclass
- 幕内内容继续使用现有：
  - `location(...)`
  - `action(...)`
  - `clock(...)`
  - `effect(...)`
  - `condition(...)`

也就是说 encounter 第一版不追求专门的厚 builder。

作者主要写的是：

- `EncounterDef`
- `EncounterActDef`
- `EncounterStateDef`
- `EncounterTransitionDef`

而幕内桌面内容，继续用普通地点树来表达。

如果后面 encounter 数量多了，再追加很薄的 helper，例如：

```python
def when_clock_full(clock_id: str, *effects: Effect) -> EncounterTransitionDef: ...
def when_clock_empty(clock_id: str, *effects: Effect) -> EncounterTransitionDef: ...
def set_encounter_state(state_id: str) -> Effect: ...
def set_encounter_act(act_id: str) -> Effect: ...
```

但这不是第一版必须有的。


## Content Authoring 示例

```python
ACT_1_PRESSED_ROOT, _ = location(
    id="thug_act_1_pressed_root",
    title="摆脱压制",
    description="打手已经贴到你面前，把你逼在墙边。地上有一把折刀，但伸手去拿会冒风险。",
    actions=(
        action(id="thug_defend", ...),
        action(id="thug_elbow_strike", ...),
        action(id="thug_grab_knife", ...),
    ),
)

ACT_1_KNIFE_ROOT, _ = location(
    id="thug_act_1_knife_root",
    title="持刀逼退",
    description="你已经拿到刀，对方开始后撤。",
    actions=(
        action(id="thug_defend", ...),
        action(id="thug_knife_pushback", ...),
    ),
)

ENCOUNTER = EncounterDef(
    id="teach_thug",
    title="教训一个小混混",
    description="拿人钱财，帮人把这件事办干净。",
    rewards=(effect("change_money", 80),),
    acts=(
        EncounterActDef(
            id="act_1",
            title="摆脱压制",
            description="你先得从墙边和压制里脱出来。",
            objective_clock=clock("initiative", "主动权", 2),
            initial_state_id="pressed_unarmed",
            states=(
                EncounterStateDef(
                    id="pressed_unarmed",
                    title="徒手受压",
                    description="地上有一把折刀，但伸手去拿会冒风险。",
                    root=ACT_1_PRESSED_ROOT,
                ),
                EncounterStateDef(
                    id="knife_advantage",
                    title="持刀逼退",
                    description="你已经拿到刀，对方开始后撤。",
                    root=ACT_1_KNIFE_ROOT,
                ),
            ),
            transitions=(
                EncounterTransitionDef(
                    kind="clock_full",
                    source="initiative",
                    effects=(
                        effect("set_encounter_act", "act_2"),
                        effect("set_encounter_state", "duel"),
                    ),
                ),
            ),
        ),
    ),
)
```

这版写法的重点是：

- 这一幕有哪些 state
- 每个 state 对应一张怎样的桌面
- 桌面里有哪些地点/行动
- 这一幕的目标钟是什么
- 满足条件后如何跳转

作者不需要在每个 action 上重复写 act/state 条件。


## 编译期展开规则

编译 encounter 时，编译器会遍历每个 `EncounterStateDef.root`，对整棵树里所有节点自动补 encounter 作用域条件：

- `Condition(kind="in_encounter_act", value=act_id)`
- `Condition(kind="in_encounter_state", value=state_id)`

如果节点本身已经带了其他业务条件，则合并，而不是覆盖。

例如：

```python
EncounterStateDef(
    id="knife_advantage",
    root=ACT_1_KNIFE_ROOT,
)
```

编译后，`ACT_1_KNIFE_ROOT` 下面所有：

- 子地点
- 行动

都会自动带上：

```python
Condition("in_encounter_act", "act_1")
Condition("in_encounter_state", "knife_advantage")
```

这样：

- 内容层写起来轻
- runtime 仍然是 declarative condition
- act/state 作用域不会散到每个 action 上


## Validate 规则

Encounter compile 阶段建议 assert：

- encounter id 唯一
- act id 唯一
- state id 在 encounter 内唯一
- 每幕 `initial_state_id` 必须存在
- 每个 transition 的 source 必须存在
- 每幕必须至少有 1 个 state
- 每个 state 必须有 `root`
- 每个 state 的 root 树深度必须满足现有 Location 规则
- 所有状态树内 action id 在 encounter 内唯一
- 所有状态树内 location id 在 encounter 内唯一
- 所有 `set_state` 的目标 state 必须存在
- 所有 `set_act` 的目标 act 必须存在
- 每幕 objective clock id 唯一


## UI 对接建议

Encounter screen 继续沿用现在的“桌面 + 卡”风格，不另起视觉语法。

### header

显示：

- encounter 标题
- 当前幕标题
- 当前 state 描述
- 当前幕目标钟

### content

显示当前 state 对应 root 桌面的内容。

也就是：

- 顶层地点
- 子地点
- 行动卡

都继续走现有桌面渲染逻辑。

### 行动结果

继续沿用现有 attachment 交互：

- 卡内显示判定预览
- 卡下显示结果块
- 状态变化和幕变化也写进结果块

例如：

- `状态变化：徒手受压 -> 持刀逼退`
- `进入下一幕：拿到优势后终结`


## 为什么不先做脚本 / 图编辑器

### 不建议脚本承载主流程

缺点：

- 难校验
- 难可视化
- 难测试
- 逻辑容易散进任意函数

脚本只适合：

- 少量特殊效果
- 调试辅助

### 不建议现在先做图编辑器

缺点：

- 成本高
- 当前 schema 还在收敛
- 过早编辑器化容易把结构锁死

更好的顺序：

1. 先做 dataclass
2. 再做 compile/validate
3. 再做 graph/debug export
4. 如果 encounter 数量多了，再补薄 helper
5. 最后如果确实有需要，再考虑编辑器


## 推荐下一步

实现顺序建议：

1. 新建 `src/raygame/encounters/`
2. 落 `defs.py`
3. 落一个样例 `thug.py`
4. 落 `registry.py`
5. 在 compile 阶段实现“state.root 自动补 encounter 条件”
6. 在世界规则里支持 `start_encounter / finish_encounter`
7. 新增 `ScreenName.ENCOUNTER`
8. 新增 `encounter_screen.py`

第一版只要把 `thug.py` 这个样例跑通，就足够验证抽象是否顺手。
