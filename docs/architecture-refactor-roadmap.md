# 架构重构路线图

## 目标

这次重构的目标不是保守地修补当前结构，也不是为了迁移 Unity 做临时适配。

目标是把当前 Python 工程整理成一套更清晰、可靠、简单、可迁移的结构：

```text
内容是内容。
状态是状态。
规则是规则。
流程是流程。
表现是表现。
```

最终希望达到：

```text
1. 游戏核心逻辑可以脱离 Raylib UI 独立理解和测试。
2. SCM 继续作为高价值内容资产保留。
3. 所有权威状态修改有清楚入口。
4. UI 不再直接拼接复杂规则流程。
5. Python 工程结构能自然映射到未来 Unity/C# 工程。
6. 不引入不必要的框架、抽象、插件系统或复杂调度器。
```

## 不做什么

为了避免过度设计，明确不做这些：

```text
不做 ECS。
不做复杂依赖注入框架。
不做大型事件总线。
不做插件式规则系统。
不把每个小函数都拆成类。
不重写 SCM 语言。
不为了 Unity 提前把 Unity 概念塞进 Python 核心。
不一次性重写 UI。
不把目录调整当作目标本身。
```

好的目标状态应该是：

```text
函数还是函数。
dataclass 还是 dataclass。
只是每个函数待在它该待的位置。
```

## 最终目标结构

目标结构不是必须一次完成，但所有阶段都朝这个方向收敛。

```text
src/sincity/
├── model/
│   ├── state.py
│   ├── defs.py
│   └── enums.py
│
├── content/
│   ├── runtime.py
│   ├── city_1.py
│   ├── validate.py
│   └── hot_reload.py
│
├── content_lang/
│   ├── runtime_core.py
│   └── module_runtime.py
│
├── encounters/
│   ├── runtime.py
│   ├── registry.py
│   ├── defs.py
│   └── lispy.py
│
├── dialogues/
│   ├── runtime.py
│   ├── registry.py
│   └── defs.py
│
├── game/
│   ├── __init__.py
│   ├── session.py
│   ├── flow.py
│   ├── commands.py
│   ├── events.py
│   ├── queries.py
│   ├── fields.py
│   ├── conditions.py
│   ├── actions.py
│   ├── resolution.py
│   ├── effects.py
│   ├── reacts.py
│   ├── clocks.py
│   ├── encounters.py
│   └── dialogues.py
│
├── presentation/
│   ├── city_presenters.py
│   ├── encounter_presenters.py
│   ├── table_presenters.py
│   └── tags.py
│
├── screens/
│   ├── city_screen.py
│   ├── encounter_screen.py
│   ├── ending_screen.py
│   └── widgets.py
│
└── app.py
```

其中最关键的新边界是 `game/`。

当前 `rules/progression.py` 承担了太多职责。目标不是简单把它拆碎，而是建立一个清晰的游戏核心层：

```text
game/
├── session.py      新开局和 session 初始化
├── queries.py      当前内容快照、action、clock 查询
├── fields.py       状态字段统一读写
├── conditions.py   条件判断
├── actions.py      动作准备、输入装配
├── resolution.py   动作结算和 pending resolution
├── effects.py      Effect 执行
├── reacts.py       React 连锁
├── clocks.py       Clock 和 cycle
├── encounters.py   交锋生命周期
├── dialogues.py    对话生命周期
├── commands.py     外界请求游戏核心做什么
├── events.py       游戏核心执行后发生了什么
└── flow.py         轻量调度入口
```

## 当前到目标的关系

```text
当前
rules/progression.py
   ├── session
   ├── query
   ├── field access
   ├── condition
   ├── modal / UI state
   ├── action assembly
   ├── action resolution
   ├── effect execution
   ├── react
   ├── clock
   ├── encounter flow
   ├── dialogue flow
   ├── resources
   ├── growth
   └── ending

目标
game/
   ├── session.py
   ├── queries.py
   ├── fields.py
   ├── conditions.py
   ├── actions.py
   ├── resolution.py
   ├── effects.py
   ├── reacts.py
   ├── clocks.py
   ├── encounters.py
   ├── dialogues.py
   └── flow.py
```

`rules/progression.py` 在过渡期保留为兼容 facade：

```text
旧代码继续:
from sincity.rules import current_world_snapshot

内部逐步变成:
from sincity.game.queries import current_world_snapshot
```

这样可以避免一次性改爆所有 import。

## 设计原则

### 1. 以权威状态为中心

`GameState` 是当前对局的权威状态。

内容快照、UI 卡片、可见地点、可见动作都应该是派生数据。

```text
GameState
   │
   ▼
Content Runtime
   │
   ▼
WorldSnapshot / EncounterSnapshot
   │
   ▼
Presentation Model
   │
   ▼
Screen / Unity UI
```

### 2. 状态修改必须有清楚入口

现在状态可能从这些地方被修改：

```text
Action effect
React effect
Encounter completion
Ink external function
Debug panel
Cycle start
Resource helper
```

目标是让它们尽量收束到：

```text
game.fields
game.effects
game.clocks
game.encounters
game.dialogues
```

不是所有修改都必须强行包装成 Effect，但所有修改都应该可以追踪到明确模块。

### 3. 内容运行时只生成内容，不执行表现

SCM runtime 的边界：

```text
输入：GameState 或 encounter store
输出：LocationDef / ActionDef / Clock / React / Task
```

SCM 可以提供语义 key，例如：

```scheme
:presentation 'theater.catch_shadow
```

但不直接调用 Raylib、Unity、Timeline 或视频 API。

### 4. UI 发命令，不拼规则

UI 可以读取 ViewModel，可以发 command。

UI 不应该自己拼完整的动作结算逻辑。

目标流程：

```text
UI click
   │
   ▼
Command
   │
   ▼
game.flow / game.actions / game.resolution
   │
   ▼
GameState + Events
   │
   ▼
UI refresh / presentation
```

### 5. 简单优先

如果一个模块只需要函数，就用函数。

如果一个 event 只是 dataclass，就保持 dataclass。

如果 facade 能兼容旧调用，就不要急着全项目重写 import。

## 分阶段计划

## Phase 0: 建立共同地图

目标：

- 明确当前结构。
- 明确目标结构。
- 不改运行逻辑。

已完成或应完成文档：

```text
docs/current-architecture-plan.md   (计划中，待编写)
docs/unity-migration-map.md         (计划中，待编写)
docs/architecture-refactor-roadmap.md
```

验收标准：

```text
1. 能说清每个现有目录负责什么。
2. 能说清 progression.py 中每类函数未来属于哪里。
3. 能说清 Python 到 Unity 的模块映射。
```

验证命令：

```bash
uv run python -m sincity.content.validate
```

## Phase 1: 建立 game facade 和依赖审计

目标：

- 新建 `src/sincity/game/`。
- 不创建大量空抽象。
- 先建立目标 API 边界，不急着复制复杂实现。
- 审计 `progression.py` 中查询、字段、条件函数的隐式依赖。
- `rules/progression.py` 保持兼容。

建议新建：

```text
src/sincity/game/__init__.py
src/sincity/game/queries.py
src/sincity/game/fields.py
src/sincity/game/conditions.py
```

第一阶段不是直接把函数实现搬过去，而是先建立 facade。

原因：

```text
queries / fields / conditions 看起来基础，但当前依赖 progression.py 中大量隐式 helper：

_encounter
_current_content
_mark_content_dirty
_player_actor
_set_world_attr
change_health
change_energy
sync_trauma_cards_with_health
location_for_action
current_world_snapshot
```

直接复制函数容易漏掉隐式依赖，也容易制造循环 import。

第一批 facade API：

```text
queries.py
├── get_action
├── get_action_for_state
├── current_world_snapshot
├── current_encounter_snapshot
├── current_encounter_reaction_table
├── get_clock_value
├── get_clock_spec_for_state
└── sync_world_progress_clocks

fields.py
├── field_value
├── set_field
├── add_field
├── world_attr_value
├── set_world_attr
├── player_actor
├── party_actor
└── actor_name

conditions.py
├── action_is_visible
├── action_is_available
├── location_is_visible
├── location_is_available
├── all_met
├── evaluate_condition
└── requirements_affordable
```

facade 可以先这样写：

```python
# sincity/game/queries.py
from sincity.rules import progression

def current_world_snapshot(state):
    return progression.current_world_snapshot(state)
```

同时为每个 API 记录：

```text
1. 是否修改 GameState。
2. 依赖哪些 progression helper。
3. 被 screens / presenters / rules 哪些模块调用。
4. 迁移实现时是否可能产生循环 import。
```

兼容策略：

```text
progression.py 继续导出旧名字。
game facade 先调用 progression.py。
等 Phase 2 之后再逐步把实现从 progression.py 移到 game/*。
```

示意：

```python
# 初期:
screens -> rules/progression.py -> 原实现
game/queries.py -> rules/progression.py -> 原实现

# 稳定后:
screens -> rules/progression.py -> game/queries.py -> 新实现
```

注意：

- 第一阶段不要引入 command/event。
- 第一阶段不要动 UI 文件。
- 第一阶段不要改 SCM 语义。
- 第一阶段不要强行减少 `progression.py` 体积，重点是建立边界和依赖图。

验收标准：

```text
1. 游戏启动行为不变。
2. 内容校验通过。
3. compileall 通过。
4. 新的 game facade API 可被导入。
5. 查询、字段、条件函数的依赖清单完成。
6. 明确哪些函数可以安全迁移实现，哪些必须等 Effect / Clock / Encounter 拆分后再迁移。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

## Phase 2: 迁移低耦合查询、字段、条件

目标：

- 按 Phase 1 依赖审计清单，选择入度为 0 或仅依赖已迁模块的函数优先迁移。
- 把低耦合实现真正迁入 `game/`。
- 字段读写开始形成清楚入口。
- 条件判断和内容快照查询开始脱离 `progression.py`。

迁移顺序：

```text
1. queries.py 中纯查询且不依赖字段写入的函数。
2. fields.py 中只读函数。
3. conditions.py 中只依赖 queries/fields 的函数。
4. fields.py 中写入函数，但暂时保留复杂资源修改 helper 在 progression.py。
```

候选迁移：

```text
queries.py
├── current_world_snapshot
├── current_encounter_snapshot
├── current_encounter_reaction_table
├── get_action_for_state
├── get_clock_value
└── get_clock_spec_for_state

fields.py
├── field_value
├── world_attr_value
├── player_actor
├── party_actor
└── actor_name

conditions.py
├── action_is_visible
├── action_is_available
├── location_is_visible
├── location_is_available
├── all_met
├── evaluate_condition
└── requirements_affordable
```

暂缓迁移：

```text
set_field / add_field
change_health / change_energy
sync_trauma_cards_with_health
shift_clock
start_encounter / finish_encounter

这些函数涉及 Effect、Clock、Encounter、资源同步，等后续阶段拆清楚再移。
```

需要同步梳理：

```text
fields.py
├── health / energy / pressure 到底走哪个 actor
├── world values 与 inventory 如何区分
├── encounter store persist 如何同步 world
└── set_field 是否总是 mark content dirty
```

验收标准：

```text
1. game/queries.py、game/fields.py、game/conditions.py 中已有真实实现，而不只是 facade。
2. progression.py 继续 re-export 旧 API。
3. 查询/条件行为不变。
4. 没有新增复杂对象或调度框架。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

如果迁移字段写入函数，需要增加最小状态模拟。

## Phase 3: 统一字段写入和 Effect 边界

目标：

- 状态字段读写有清楚入口。
- Effect 执行从 `progression.py` 中独立出来。
- 后续 Action、React、Dialogue 都可以依赖同一个 Effect 边界。

建议新建：

```text
src/sincity/game/effects.py
```

迁移内容：

```text
fields.py
├── set_field
├── add_field
└── set_world_attr

effects.py
├── apply_effects
├── apply_effect
├── resolve_set_field_payload
├── resolve_add_field_payload
├── resolve_shift_clock_payload
├── evaluate_dynamic_value
├── describe_effects
└── describe_set_field_payload
```

命名策略：

```text
新模块使用公开名字：
apply_effects
apply_effect
describe_effects

progression.py 兼容旧名字：
_apply_effects = apply_effects
_apply_effect = apply_effect
```

重点检查：

- `start_dialogue` / Ink external function 是否绕过字段入口。
- `change_health` / `change_energy` 是否和 `set_field` 规则一致。
- encounter store 的 `persist` 行为是否集中。
- `set_field` 是否总是按需 mark content dirty。

验收标准：

```text
1. 所有 Effect 执行逻辑在 effects.py 中可读。
2. fields.py 是状态字段读写的主入口。
3. progression.py 不再包含大段 Effect dispatch。
4. 现有 SCM effect 行为不变。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

如果改到 effect 语义，再增加最小状态模拟。

## Phase 4: 整理动作执行主线

目标：

- 把“准备动作”和“结算动作”分开。
- 让一次行动的生命周期变得清楚。

建议新建：

```text
src/sincity/game/actions.py
src/sincity/game/resolution.py
```

`actions.py` 负责：

```text
open_action
focus_action
select_card_input
select_item_input
slot_card
toggle_action_energy_slot
toggle_action_requirement_slot
toggle_requirement_input
requirement_is_slotted
action_slot_ready
action_can_accept_selected_input
action_ready_to_execute
current_action
clear_assembly
clear_selected_input
```

`resolution.py` 负责：

```text
perform_current_action
perform_instant_action
perform_reveal_action
advance_pending_resolution
dismiss_pending_resolution
advance_action_reveal
clear_action_reveal
consume_inputs
compose_resolution_text
```

目标流程：

```text
focus/open action
   │
   ▼
select inputs
   │
   ▼
action_ready_to_execute
   │
   ▼
perform_current_action
   │
   ▼
PendingResolutionState
   │
   ▼
advance_pending_resolution
   │
   ▼
apply_effects
   │
   ▼
resolve reacts
```

验收标准：

```text
1. 动作输入装配逻辑集中在 actions.py。
2. 动作结算和 pending resolution 集中在 resolution.py。
3. resolution.py 只通过 effects.py 结算效果。
4. UI 行为不变。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

建议手动验证：

```text
1. 打开城市地点。
2. 执行一个 instant action。
3. 执行一个 check action。
4. 执行一个 reveal action。
5. 进入一个 encounter。
```

## Phase 5: 整理 Clock、React、Cycle

目标：

- 把状态变化后的连锁逻辑独立出来。
- 让 Clock 和 Cycle 不混在动作结算里。

建议新建：

```text
src/sincity/game/clocks.py
src/sincity/game/reacts.py
```

`clocks.py` 负责：

```text
advance_clock
advance_encounter_clock
damage_encounter_clock
shift_clock
reset_hand
advance_cycle
sync_trauma_cards_with_health
```

`reacts.py` 负责：

```text
resolve_world_reacts
resolve_encounter_reacts
resolve_encounter_reaction_die
react_non_convergence_message
award_completed_tasks
```

边界原则：

```text
effects.py 可以调用 reacts.py。
reacts.py 可以调用 effects.py，但必须避免无限递归。
Clock 修改应统一 mark content dirty。
React non-convergence 必须继续有 assert 或明确错误。
```

验收标准：

```text
1. React 链路集中。
2. Clock 修改集中。
3. advance_cycle 流程可独立阅读。
4. 新旧内容校验行为一致。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

建议手动验证：

```text
1. 睡觉推进天数。
2. 触发一个 world react。
3. 触发一个 encounter react。
4. 触发 clock filled 后的后续效果。
```

## Phase 6A: 审计 Dialogue 外部函数（调研先行）

目标：

- 对 Dialogue 和 Ink external function 做调用审计。
- 在同一阶段前先摸清状态修改盲区，再安排后续搬移。

审计内容：

```text
1. 列出 dialogues/runtime.py 当前绑定的 external function。
2. 搜索 .ink 中每个 external function 的调用点。
3. 标注每个 external function 修改哪些状态。
4. 判断它应映射到 Effect、Command，还是保留为 Dialogue 专用操作。
```

输出物：

```text
Ink external function 清单
├── 函数名
├── 修改的状态字段
├── 调用频率（首次 / 每次对话）
├── 是否绕过 fields.py / effects.py
└── 建议迁移路径
```

验收标准：

```text
1. Ink external function 调用清单完成。
2. 标出哪些 external function 绕过 Effect 边界。
3. 现有对话行为不变。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

建议手动验证：

```text
1. SCM action start-quick-dialogue。
2. SCM action start-dialogue。
3. Dialogue external start_encounter。
```

## Phase 6B: 整理 Encounter 生命周期

目标：

- 交锋是流程系统，不应该散在 progression.py。
- 把 Encounter 生命周期集中到 game/ 边界。
- 依赖 Phase 6A 审计结果决定 encounter–dialogue 交互方式。

建议新建：

```text
src/sincity/game/encounters.py
```

`encounters.py` 负责：

```text
start_encounter
start_encounter_from_dialogue
finish_encounter
finish_encounter_from_dialogue
initial_encounter_store
can_endure_pressure_during_encounter
endure_pressure_during_encounter
encounter_action_cards
sync_encounter_action_cycle
```

验收标准：

```text
1. start/finish encounter 逻辑集中在 encounters.py。
2. 现有交锋行为不变。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

建议手动验证：

```text
1. SCM action start-quick-dialogue。
2. SCM action start-dialogue。
3. Dialogue external start_encounter。
4. Encounter end_encounter success/fail。
```

## Phase 7: 整理 Dialogue 生命周期

目标：

- 把对话生命周期从 `progression.py` 中移出。
- 保持现有 Ink external function 兼容。
- 为后续 Effect/Command 化打基础。

建议新建：

```text
src/sincity/game/dialogues.py
```

`dialogues.py` 负责：

```text
start_dialogue
start_quick_dialogue
open_dialogue_session
continue_dialogue
fast_forward_dialogue
choose_dialogue_option
finish_dialogue
clear_dialogue_modal
```

实施策略：

```text
1. 先移动 dialogue flow，不改 Ink external API。
2. dialogues/runtime.py 中的 external function 暂时继续工作。
3. 新增注释或文档标明哪些 external function 是状态修改入口。
4. 后续再逐步把 external function 映射到 effects 或 commands。
```

验收标准：

```text
1. start/continue/finish dialogue 逻辑集中。
2. progression.py 不再直接承载 dialogue flow。
3. 现有 quick dialogue 和 Ink dialogue 行为不变。
```

验证命令：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

## Phase 8: Screens 调用审计和轻量 Command / Event

目标：

- 让 UI 和未来 Unity 表现层通过 command/event 与游戏核心沟通。
- 不做复杂 dispatcher。
- 不引入大型事件总线。
- 先审计 screens 调用模式，再决定哪些入口 command 化。

建议新建：

```text
src/sincity/game/commands.py
src/sincity/game/events.py
src/sincity/game/flow.py
```

在引入 Command/Event 前，先输出 screens 调用表：

```text
city_screen.py
├── close_modal
├── current_action
├── current_world_snapshot
├── dismiss_pending_resolution
└── fast_forward_dialogue

encounter_screen.py
├── close_modal
├── current_action
├── current_encounter_reaction_table
├── dismiss_pending_resolution
└── fast_forward_dialogue

table_views.py / ui_panels.py / widgets.py
├── open_modal
├── open_action
├── toggle_requirement_input
├── perform_current_action
└── select_card_input
```

命令可以先很少：

```python
@dataclass(frozen=True)
class OpenLocation:
    location_id: str

@dataclass(frozen=True)
class OpenAction:
    action_id: str

@dataclass(frozen=True)
class ExecuteAction:
    pass

@dataclass(frozen=True)
class ContinueDialogue:
    pass

@dataclass(frozen=True)
class ChooseDialogueOption:
    index: int
```

事件也先很少：

```python
@dataclass(frozen=True)
class ActionResolved:
    action_id: str
    result: ResultType | None

@dataclass(frozen=True)
class EncounterStarted:
    encounter_id: str

@dataclass(frozen=True)
class DialogueStarted:
    dialogue_id: str

@dataclass(frozen=True)
class GameEnded:
    ending_id: str | None
```

`flow.py` 可以先只是轻量函数：

```python
def dispatch(state: GameState, command: GameCommand, rng: RandomSource) -> tuple[GameEvent, ...]:
    ...
```

边界：

```text
UI 可以继续暂时调用旧函数。
新 UI 或新功能优先用 dispatch。
不要一次性改完所有 screens。
第一批只 command 化动作执行链路或对话推进链路中的一个，不同时改全部 UI。
```

验收标准：

```text
1. screens 调用 rules/game API 的清单完成。
2. 至少一个高价值入口可以通过 Command 触发。
3. 至少一个结果可以返回 Event。
4. 旧 UI 行为不变。
5. Unity 迁移有明确对接点。
```

## Phase 9: 分离 Presentation Models

目标：

- 把 `screens/*presenters.py` 移出 Raylib 层。
- 明确它们是 ViewModel，而不是绘制代码。

建议新建：

```text
src/sincity/presentation/
├── __init__.py
├── city_presenters.py
├── encounter_presenters.py
├── table_presenters.py
└── tags.py
```

迁移：

```text
screens/city_presenters.py       -> presentation/city_presenters.py
screens/encounter_presenters.py  -> presentation/encounter_presenters.py
screens/table_presenters.py      -> presentation/table_presenters.py
screens/ui_tags.py               -> presentation/tags.py
```

兼容策略：

```text
旧 screens 模块先 re-export，避免一次性改所有 import。
```

目标边界：

```text
presentation/
   读 GameState 和 snapshot
   生成可展示模型
   不直接绘制 Raylib
   不执行规则

screens/
   只负责 Raylib 绘制和输入
```

验收标准：

```text
1. presenter 逻辑不再物理放在 screens。
2. Raylib-specific 代码留在 screens。
3. Unity 可以复用 presenter 思路或逐步移植 ViewModel。
```

## Phase 10: 标注和隔离 GameState 中的 UI 状态

目标：

- 先标注和隔离，不默认物理拆分。
- 只有收益明确时才拆出独立 `UiState`。

当前 `GameState` 中混有：

```text
权威游戏状态:
├── deck
├── attributes
├── party
├── world
├── screen
├── day
├── active_encounter
├── active_dialogue
├── ending
└── seed

UI / Presentation 状态:
├── modal
├── selected_input
├── assembly
├── render_cache
├── action_reveal
├── card_hint_flash
├── task_panel_scroll
├── notifications
└── debug_open
```

可选目标：

```text
GameState
├── WorldState
├── PartyState
├── DeckState
├── EncounterState
├── DialogueState
└── ProgressionState

UiState
├── ModalState
├── SelectionState
├── RenderCacheState
├── NotificationState
└── DebugState
```

是否执行这一步，取决于前面阶段完成后：

```text
1. UI 状态是否继续阻碍核心测试。
2. 存档是否需要排除 UI 状态。
3. Unity 迁移是否需要更纯净的 GameState。
```

如果收益不明显，可以只在代码注释和文档中分区，不做物理拆分。

本阶段默认交付：

```text
1. 在文档中列出 GameState 中权威状态和 UI 状态。
2. 在代码附近增加简短注释或分组。
3. 新增状态时明确归属。
4. 不强制移动字段。
```

## Phase 11: SCM Key 和 Presentation Cue

目标：

- 为 Unity 场景绑定准备稳定身份。
- 不改变 SCM 的核心语义。

当前风险：

```text
location/action id 可能与标题、路径、顺序相关。
这对 Raylib 足够，但不适合 Unity 场景锚点和 Timeline 绑定。
```

目标语法：

```scheme
(node
  :key 'theater
  :title "剧院"
  ...)

(action
  :key 'catch-shadow
  :title "追上戴面具的人"
  :presentation 'theater.catch-shadow
  ...)
```

实施策略：

```text
1. DSL 先支持可选 :key。
2. 没写 :key 时继续使用旧生成逻辑。
3. validate 检查同一父级 key 是否重复。
4. 逐步给重要地点和特殊动作补 key。
5. presentation cue 只作为语义字符串，不绑定引擎资源。
```

验收标准：

```text
1. 旧 SCM 不需要一次性全改。
2. 新 key 稳定且可校验。
3. Unity 可根据 key 绑定 LocationAnchor / SequenceBinding。
```

## 每阶段通用验收

每阶段完成后至少运行：

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

如果改到 SCM 语法或 runtime：

```bash
uv run python -m sincity.scm_lint src/sincity/scm/city_1.scm
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity/content_lang/runtime_core.py src/sincity/content/runtime.py src/sincity/encounters/runtime.py src/sincity/rules/progression.py
```

如果改到 effect / react / encounter：

```text
增加最小状态模拟：
1. 构造 GameState。
2. 执行目标 Effect 或 Action。
3. assert 关键字段变化。
```

## 风险控制

### 保留 facade

在迁移期间：

```text
rules/progression.py 继续存在。
rules/__init__.py 继续导出旧 API。
src/sincity/game/* 先作为新边界存在，必要时可暂时调用 progression.py。
```

这样 UI 和其他模块可以逐步迁移。

facade-first 的意义：

```text
1. 先让新边界稳定下来。
2. 再迁移实现。
3. 最后切换旧 import。
```

不要为了“看起来已经拆出来”而复制带有隐式依赖的复杂函数。

### 一次只移动一个问题域

不要同一个 PR 同时做：

```text
移动文件 + 改命名 + 改语义 + 改 UI
```

推荐：

```text
1. 先建立 facade，保持行为。
2. 再移动低耦合实现。
3. 再整理命名。
4. 最后改善语义。
```

### 不追求零循环一次到位

短期可能存在：

```text
game.effects -> game.reacts
game.reacts -> game.effects
```

如果通过局部 import 或明确调用可以保持简单，可以接受。

不要为了消除所有循环依赖引入复杂对象图。

### 不强行类化

如果函数足够清楚，就保持函数。

只有当需要共享依赖、缓存或状态时，才引入类。

## 推荐首个实施切片

建议第一轮实际代码改动做：

```text
1. 新建 game/
2. 建立 queries.py / fields.py / conditions.py facade
3. 每个 facade 函数先调用 progression.py 旧实现
4. 输出依赖审计清单
5. 不改 screens、不改 SCM、不改 Effect 语义
```

原因：

```text
1. 直接搬 queries / fields / conditions 可能漏掉 progression.py 的隐式依赖。
2. facade 能先固定未来 API，不引入行为风险。
3. 依赖审计会告诉我们哪些实现可以安全迁移。
4. Unity 迁移时这些 API 仍然是一一对应的 Core/Rules 基础服务。
```

首个切片完成后的目标状态：

```text
src/sincity/game/
├── __init__.py
├── queries.py
├── fields.py
└── conditions.py

rules/progression.py
├── 保留所有旧实现
└── 继续兼容 screens 当前 import

docs 或代码注释
└── 记录 queries / fields / conditions 的隐式依赖
```

## 最终迁移价值

当这条路线完成后，Python 工程会自然对应到 Unity：

```text
Python model/          -> Unity Core/Model
Python content/        -> Unity Content/Runtime
Python game/           -> Unity Core/Rules
Python presentation/   -> Unity Presentation/ViewModels
Python screens/        -> Unity Presentation/UI
Python app.py          -> Unity Application/GameController
Python scm/            -> Unity GameContent/Scm
```

这时迁移不是“照着旧代码翻译”，而是按清晰模块逐块实现：

```text
1. 先移植 Model。
2. 再移植 Content Runtime。
3. 再移植 Game Core。
4. 最后接 Unity Presentation。
```
