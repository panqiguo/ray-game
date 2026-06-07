# 当前 Python 工程分层梳理计划

## 目标

这份文档先把当前 Python 游戏的真实结构梳理清楚，为后续重构和 Unity 迁移建立稳定边界。

当前目标不是改玩法，也不是立刻移动大量文件，而是先回答三个问题：

```text
1. 现在每一块实际负责什么？
2. 哪些职责混在了一起？
3. 未来应该按什么顺序拆，风险最低？
```

## 当前概念分层

```text
┌─────────────────────────────────────────────┐
│ 6. App / Platform                           │
│    窗口、主循环、字体、热重启、每帧 update   │
├─────────────────────────────────────────────┤
│ 5. Screens / Raylib UI                      │
│    屏幕、控件、布局、输入区域、调试面板       │
├─────────────────────────────────────────────┤
│ 4. Presentation Models                      │
│    把 LocationDef / ActionDef 整理成 UI 卡片 │
├─────────────────────────────────────────────┤
│ 3. Game Runtime / Rules                     │
│    动作、判定、Effect、Clock、React、流程     │
├─────────────────────────────────────────────┤
│ 2. Content Runtime                          │
│    SCM / Ink 编译、求值、动态生成内容快照     │
├─────────────────────────────────────────────┤
│ 1. Model / Definitions                      │
│    GameState、ActionDef、LocationDef 等数据  │
├─────────────────────────────────────────────┤
│ 0. Content Assets                           │
│    .scm、.ink、图片、剧本内容                 │
└─────────────────────────────────────────────┘
```

## 0. Content Assets

当前位置：

```text
src/sincity/scm/
src/sincity/dialogues/assets/
src/sincity/assets/
```

职责：

- 保存 SCM 城市内容、地点、动作、交锋场景。
- 保存 Ink 对话源文件和编译产物。
- 保存头像、图片等素材。

这一层是迁移价值最高的内容资产层。未来 Unity 中也应保留 SCM 作为主要内容来源。

需要梳理：

- 哪些 SCM 是城市入口。
- 哪些 SCM 是城市地点模块。
- 哪些 SCM 是交锋场景。
- 哪些 Ink 对话被 SCM 或规则引用。

## 1. Model / Definitions

当前位置：

```text
src/sincity/model/
```

核心文件：

```text
model/state.py      当前对局状态
model/defs.py       内容定义和快照数据结构
model/enums.py      枚举
model/items.py      物品定义
model/events.py     事件定义
model/commands.py   命令定义
```

当前主要数据：

```text
GameState
├── DeckState
├── AttributeState
├── PartyActorState
├── WorldState
├── ActiveEncounterState
├── ActiveDialogueState
├── ModalState
├── PendingResolutionState
└── RenderCacheState

Definitions
├── LocationDef
├── ActionDef
├── Effect
├── Condition
├── InputRequirement
├── CheckDef
├── OutcomeDef
└── ProgressClockSpec
```

需要梳理：

- 哪些状态是游戏权威状态。
- 哪些状态只是 UI 状态。
- 哪些状态是缓存或派生数据。
- `GameState` 中是否需要拆出 `UiState` / `PresentationState`。

## 2. Content Runtime

当前位置：

```text
src/sincity/content/
src/sincity/content_lang/
src/sincity/encounters/
src/sincity/dialogues/
```

职责：

- 解析和求值 SCM。
- 编译城市内容。
- 编译交锋内容。
- 根据 `GameState` 或 encounter store 动态生成当前快照。
- 编译、注册和运行 Ink 对话。
- 内容校验和热重载。

当前结构：

```text
Content Runtime
├── SCM 基础解释器
│   ├── encounters/lispy.py
│   ├── content_lang/runtime_core.py
│   └── content_lang/module_runtime.py
│
├── 城市内容
│   ├── content/city_1.py
│   ├── content/runtime.py
│   ├── content/validate.py
│   └── content/hot_reload.py
│
├── 交锋内容
│   ├── encounters/registry.py
│   ├── encounters/defs.py
│   └── encounters/runtime.py
│
└── 对话内容
    ├── dialogues/registry.py
    ├── dialogues/runtime.py
    └── dialogue_compile.py
```

关键数据流：

```text
.scm 文件
   │
   ▼
expand_includes / evaluate
   │
   ▼
LocationTemplate / ActionTemplate
   │
   ▼
render_world / render_encounter
   │
   ▼
LocationDef / ActionDef / Clock / React
```

需要梳理：

- 城市 runtime 和 encounter runtime 的公共部分。
- `LocationTemplate` 到 `LocationDef` 的转换边界。
- `define value`、`define function`、`define-fragment` 的求值时机。
- SCM 动态求值依赖哪些 `GameState` 字段。
- Ink external functions 是否应该继续直接改状态。

## 3. Game Runtime / Rules

当前位置：

```text
src/sincity/rules/
```

核心文件：

```text
rules/progression.py     当前最大规则总入口
rules/deck.py            行动手牌和槽位
rules/judgment.py        判定结果表
rules/rng.py             随机源
rules/notifications.py   通知状态推进
rules/debug_save.py      调试存档
```

`progression.py` 当前职责过多，可以先按以下概念分区梳理：

```text
progression.py
├── Session
│   └── start_new_run
│
├── Content Queries
│   ├── current_world_snapshot
│   ├── current_encounter_snapshot
│   ├── get_action_for_state
│   └── get_clock_value
│
├── State Fields
│   ├── _field_value
│   ├── _set_field
│   ├── _add_field
│   └── _world_attr_value
│
├── Conditions
│   ├── action_is_visible
│   ├── action_is_available
│   ├── location_is_visible
│   ├── all_met
│   └── evaluate_condition
│
├── Input Assembly
│   ├── focus_action
│   ├── slot_card
│   ├── toggle_requirement_input
│   ├── action_ready_to_execute
│   └── current_action
│
├── Action Resolution
│   ├── perform_current_action
│   ├── perform_instant_action
│   ├── perform_reveal_action
│   └── advance_pending_resolution
│
├── Effects
│   ├── _apply_effects
│   ├── _apply_effect
│   ├── _describe_effects
│   └── _evaluate_dynamic_value
│
├── React
│   ├── _resolve_world_reacts
│   ├── _resolve_encounter_reacts
│   └── _resolve_encounter_reaction_die
│
├── Clock / Cycle
│   ├── shift_clock
│   ├── advance_clock
│   ├── advance_cycle
│   └── reset_hand
│
├── Encounter Flow
│   ├── start_encounter
│   ├── finish_encounter
│   └── endure_pressure_during_encounter
│
├── Dialogue Flow
│   ├── start_dialogue
│   ├── start_quick_dialogue
│   ├── continue_dialogue
│   ├── choose_dialogue_option
│   └── finish_dialogue
│
├── Resources / Actors
│   ├── change_health
│   ├── change_energy
│   ├── change_actor_pressure
│   ├── add_actor_status
│   └── tick_actor_statuses_after_draw
│
├── Growth / Ending
│   ├── claim_growth
│   └── _check_endings
│
└── UI Modal State
    ├── open_modal
    ├── open_overlay
    ├── close_modal
    ├── clear_assembly
    └── clear_selected_input
```

需要梳理：

- 哪些函数是纯查询。
- 哪些函数会修改 `GameState`。
- 哪些修改会让 content snapshot dirty。
- 哪些函数只是 Raylib UI 流程需要。
- Effect 执行是否是唯一状态修改入口。

## 4. Presentation Models

当前位置：

```text
src/sincity/screens/*presenters.py
```

职责：

- 把规则层和内容层的数据转成 UI 可画的卡片、标签、槽位、预览。
- 尽量不直接负责绘制。
- 尽量不修改核心状态。

当前结构：

```text
Presentation Models
├── city_presenters.py
├── encounter_presenters.py
└── table_presenters.py
```

数据流：

```text
GameState + LocationDef + ActionDef
        │
        ▼
PresentedLocationCard / PresentedActionCard
        │
        ▼
table_views / widgets 绘制
```

需要梳理：

- 哪些 presenter 逻辑可以迁移到 Unity ViewModel。
- 哪些 UI 标签逻辑应该属于规则层还是表现层。
- 哪些 presenter 现在依赖了规则函数。

## 5. Screens / Raylib UI

当前位置：

```text
src/sincity/screens/
src/sincity/rendering.py
src/sincity/labels.py
```

职责：

- 绘制城市、交锋、结局三个屏幕。
- 绘制 HUD、手牌、地点表、动作卡、对话框、通知、调试面板。
- 处理少量屏幕级输入。

结构：

```text
Screens
├── router.py
├── city_screen.py
├── encounter_screen.py
├── ending_screen.py
├── widgets.py
├── table_views.py
├── ui_panels.py
├── ui_cards.py
├── ui_tags.py
├── dialogue_view.py
├── task_panel.py
├── debug_panel.py
└── notifications.py
```

需要梳理：

- 屏幕级输入是否应该移到 application/controller 层。
- 哪些 UI 组件只是 Raylib 实现细节。
- 哪些 UI 行为是未来 Unity 也需要保留的产品逻辑。

## 6. App / Platform

当前位置：

```text
src/sincity/main.py
src/sincity/app.py
```

职责：

- 初始化 Raylib 窗口。
- 加载字体和主题。
- 编译 Ink。
- 校验内容。
- 创建新对局。
- 每帧推进 pending resolution、action reveal、notification。
- 每帧绘制当前 screen。
- 热重启和 SCM 热重载。

需要梳理：

- 哪些是平台细节，Unity 会替换。
- 哪些是游戏 session 生命周期，Unity 应复用概念。
- 热重载如何在 Unity 编辑器中对应。

## 当前主要耦合点

```text
1. progression.py 是规则、流程、UI 状态和对话入口的混合体。

2. dialogues/runtime.py 的 Ink external functions 会直接改 GameState，
   这绕过了 EffectExecutor 的统一边界。

3. screens 里有屏幕级输入和状态推进调用，
   UI 与 rules 的边界还不够明确。

4. content/runtime.py 与 encounters/runtime.py 高度相似，
   两者共享 SCM 底座，但公共抽象还没有完全显式。

5. GameState 同时包含权威游戏状态、UI 状态和 render cache。
```

## 建议的低风险梳理顺序

### Phase 1: 文档化和函数分区

不移动代码，只完成：

- 给 `progression.py` 建立职责索引。
- 画三条主流程图。
- 标注状态修改入口。
- 标注 UI-only 状态。

验证：

```bash
uv run python -m sincity.content.validate
```

### Phase 2: 抽纯查询

优先抽出不会改变行为的查询模块：

```text
rules/content_queries.py
rules/conditions.py
rules/fields.py
```

候选函数：

- `current_world_snapshot`
- `current_encounter_snapshot`
- `get_action_for_state`
- `get_clock_value`
- `_field_value`
- `action_is_visible`
- `location_is_visible`
- `evaluate_condition`

### Phase 3: 抽 Effect 执行边界

目标模块：

```text
rules/effects.py
```

候选函数：

- `_apply_effects`
- `_apply_effect`
- `_resolve_set_field_payload`
- `_resolve_add_field_payload`
- `_resolve_shift_clock_payload`
- `_describe_effects`

目标是让所有状态变化都更容易追踪。

### Phase 4: 抽 Action Flow

目标模块：

```text
rules/actions.py
rules/resolution.py
```

候选函数：

- `focus_action`
- `slot_card`
- `toggle_requirement_input`
- `perform_current_action`
- `perform_instant_action`
- `perform_reveal_action`
- `advance_pending_resolution`
- `dismiss_pending_resolution`

### Phase 5: 抽 Clock / React / Encounter / Dialogue

目标模块：

```text
rules/clocks.py
rules/reacts.py
rules/encounter_flow.py
rules/dialogue_flow.py
```

先从最少依赖的函数开始，保持 `progression.py` 作为 facade 兼容旧 import。

### Phase 6: 分离 UI 状态

评估是否把以下内容从 `GameState` 主体中拆出：

```text
ModalState
SelectedInputState
ActionAssemblyState
RenderCacheState
CardHintFlashState
task_panel_scroll
debug_open
notifications
```

这一步风险较高，应该等规则边界清楚后再做。

## 三条主流程

### 城市内容刷新

```text
GameState
   │
   ▼
current_world_snapshot
   │
   ▼
render_world(SCENARIO, state)
   │
   ▼
CompiledScenario
   │
   ▼
city_presenters
   │
   ▼
city_screen / table_views
```

### 执行动作

```text
UI 点击 action
   │
   ▼
open_action / focus_action
   │
   ▼
slot_card / toggle_requirement_input
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
_apply_effects
   │
   ├── _apply_effect
   ├── _resolve_world_reacts
   └── _resolve_encounter_reacts
   │
   ▼
mark content dirty
   │
   ▼
重新 render snapshot
```

### 进入交锋

```text
World Action / Dialogue
   │
   ▼
Effect: start_encounter
   │
   ▼
start_encounter
   │
   ▼
ActiveEncounterState
   │
   ▼
current_encounter_snapshot
   │
   ▼
render_encounter(program, store)
   │
   ▼
encounter_presenters
   │
   ▼
encounter_screen
```

## 目标状态

短期目标：

```text
progression.py 继续作为 facade，但每个职责有清晰归属。
```

中期目标：

```text
rules/
├── session.py
├── content_queries.py
├── fields.py
├── conditions.py
├── actions.py
├── resolution.py
├── effects.py
├── reacts.py
├── clocks.py
├── encounter_flow.py
├── dialogue_flow.py
└── progression.py
```

长期目标：

```text
Python 结构可以自然映射到 Unity/C#：

model              -> Core/Model
content runtime    -> Content/Runtime
rules              -> Core/Rules
presenters         -> Presentation/ViewModels
screens            -> Unity Presentation
app                -> Unity Application
```

