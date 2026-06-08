# Unity Migration Map

本文基于当前**已经完成重构后的 Python 结构**，说明未来迁移到 Unity 时，每一层应如何对应。

重点不是逐文件机械翻译，而是保持语义边界：

```text
内容是内容。
状态是状态。
规则是规则。
表现是表现。
```

---

## 1. 迁移总原则

当前 Python 工程已经具备清晰边界：

```text
model/          权威数据
content/        内容运行时
game/           游戏核心逻辑
presentation/   ViewModel / presenter
screens/        Raylib UI
app.py          应用入口
```

Unity 迁移时应保持同样的层次：

```text
Python                  -> Unity
---------------------------------------------
model/                  -> Core/Model
content/ + content_lang -> Content/Runtime
encounters/             -> Content/EncounterRuntime
dialogues/              -> Content/DialogueRuntime
game/                   -> Core/Rules + Application
presentation/           -> Presentation/ViewModels
screens/                -> Presentation/UI + Scene logic
app.py                  -> Application/GameController
scm + ink assets        -> GameContent
```

不要再以 `rules/progression.py` 作为迁移中心。  
那个过渡层已经删除，未来 Unity 应以 `game/` 作为直接参考对象。

---

## 2. 总体映射图

```text
Python
┌────────────────────────────────────────────┐
│ app.py                                     │
├────────────────────────────────────────────┤
│ screens/                                   │
├────────────────────────────────────────────┤
│ presentation/                              │
├────────────────────────────────────────────┤
│ game/                                      │
├────────────────────────────────────────────┤
│ content/ + content_lang/ + encounters/     │
│ + dialogues/                               │
├────────────────────────────────────────────┤
│ model/                                     │
├────────────────────────────────────────────┤
│ scm/ + dialogues/assets/                   │
└────────────────────────────────────────────┘

Unity
┌────────────────────────────────────────────┐
│ Application/                               │
├────────────────────────────────────────────┤
│ Presentation/UI + Scene + Sequences        │
├────────────────────────────────────────────┤
│ Presentation/ViewModels                    │
├────────────────────────────────────────────┤
│ Core/Rules                                 │
├────────────────────────────────────────────┤
│ Content/Runtime                            │
├────────────────────────────────────────────┤
│ Core/Model                                 │
├────────────────────────────────────────────┤
│ GameContent/Scm + Dialogues + Assets       │
└────────────────────────────────────────────┘
```

---

## 3. `model/` -> `Core/Model`

Python：

```text
src/sincity/model/
├── state.py
├── defs.py
└── enums.py
```

Unity 目标：

```text
Assets/Game/Core/Model/
├── GameState.cs
├── WorldState.cs
├── EncounterState.cs
├── DialogueState.cs
├── LocationDef.cs
├── ActionDef.cs
├── Effect.cs
├── Condition.cs
├── ProgressClockSpec.cs
└── Enums.cs
```

迁移原则：

- 先迁移**数据形状**
- 不要把 Unity 对象引用塞进数据定义
- `GameState` 应保持可序列化、可保存、可独立测试

尤其要保留这几个概念区分：

```text
GameState        权威状态
LocationDef      内容定义
ActionDef        内容定义
pending_events   运行时事件队列
```

---

## 4. `content/` + `content_lang/` -> `Content/Runtime`

Python：

```text
src/sincity/content/
src/sincity/content_lang/
```

Unity 目标：

```text
Assets/Game/Content/
├── Scm/
│   ├── ScmParser.cs
│   ├── ScmEvaluator.cs
│   ├── ScmEnvironment.cs
│   └── ScmBuiltins.cs
│
├── Runtime/
│   ├── WorldContentRuntime.cs
│   ├── SnapshotCache.cs
│   └── ContentValidator.cs
```

当前 Python 里的关键语义边界是：

```text
输入：GameState
输出：LocationDef / ActionDef / Clock / React / Task
```

Unity 中也应保持：

- 内容 runtime 只生成世界内容
- 不播放动画
- 不控制 Timeline
- 不操作场景 GameObject

---

## 5. `encounters/` -> `Content/EncounterRuntime`

Python：

```text
src/sincity/encounters/
```

Unity 目标：

```text
Assets/Game/Content/EncounterRuntime/
├── EncounterRegistry.cs
├── EncounterRuntime.cs
├── EncounterDefs.cs
└── LispyRuntime.cs
```

要点：

- `encounters/` 是交锋内容解释层
- `game/encounters.py` 是交锋生命周期规则层
- Unity 里也要保持这个分工

不要把交锋 DSL 内容和交锋状态推进混在一个大类里。

---

## 6. `dialogues/` -> `Content/DialogueRuntime`

Python：

```text
src/sincity/dialogues/
```

Unity 目标：

```text
Assets/Game/Content/DialogueRuntime/
├── DialogueRegistry.cs
├── DialogueRuntime.cs
└── DialogueExternalBridge.cs
```

当前 Python 的原则是：

- Ink 负责对话内容推进
- 对话中的状态变更仍通过 `game/` 层完成

Unity 中也应保持：

- 不让 Ink 直接修改 Unity Scene
- 外部函数最终落到规则层/状态层

---

## 7. `game/` -> `Core/Rules` + `Application`

Python：

```text
src/sincity/game/
├── session.py
├── flow.py
├── commands.py
├── events.py
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
├── judgment.py
├── notifications.py
├── rng.py
├── deck.py
└── debug_save.py
```

Unity 目标建议：

```text
Assets/Game/Core/Rules/
├── Session/
│   └── GameSession.cs
├── Flow/
│   ├── GameCommand.cs
│   ├── GameEvent.cs
│   └── GameFlow.cs
├── Queries/
│   └── ContentQueries.cs
├── Fields/
│   └── FieldAccessor.cs
├── Conditions/
│   └── ConditionEvaluator.cs
├── Actions/
│   └── ActionAssembler.cs
├── Resolution/
│   ├── ActionResolver.cs
│   └── PendingResolutionRunner.cs
├── Effects/
│   └── EffectExecutor.cs
├── Reacts/
│   └── ReactResolver.cs
├── Clocks/
│   └── ClockResolver.cs
├── Encounters/
│   └── EncounterResolver.cs
├── Dialogues/
│   └── DialogueResolver.cs
├── Deck/
│   └── DeckService.cs
├── Judgment/
│   └── JudgmentResolver.cs
└── Notifications/
    └── NotificationService.cs
```

### 7.1 `commands.py` / `flow.py`

当前 Python：

```text
UI -> dispatch(state, command, rng)
```

Unity 中建议：

```text
UI / Scene / Timeline trigger
    │
    ▼
GameFlow.Dispatch(command)
    │
    ▼
修改 GameState
append GameEvent
```

### 7.2 `events.py`

当前 Python 已经完成单通道事件系统：

```text
state.pending_events
```

Unity 中建议直接保留这个思想：

```text
GameState.PendingEvents
```

或：

```text
GameEventBuffer
```

然后：

- 表现层消费事件
- 规则层只生产事件

### 7.3 `fields.py` / `effects.py`

这两个模块是 Unity 重写时最关键的部分。

原则：

- 所有权威状态写入都应有明确入口
- 对话、Timeline、UI 都不要绕过它直接改 `GameState`

### 7.4 `resolution.py`

当前 Python 有：

- `ActionStarted`
- `ResolutionSettled`
- `pending_resolution`

Unity 中这个模型很有价值，因为它天然适配：

- Timeline
- 延迟结算
- 动画后落地 effect

建议不要把“点击动作立即修改状态”写死在 Unity 里，保留 pending-resolution 语义。

---

## 8. `presentation/` -> `Presentation/ViewModels`

Python：

```text
src/sincity/presentation/
├── city_presenters.py
├── encounter_presenters.py
├── table_presenters.py
├── tags.py
├── card_model.py
└── typography.py
```

Unity 目标：

```text
Assets/Game/Presentation/ViewModels/
├── LocationViewModel.cs
├── ActionViewModel.cs
├── ClockViewModel.cs
├── TaskViewModel.cs
├── HandViewModel.cs
└── TagViewModel.cs
```

这一层的意义是：

- Unity UI 不直接读复杂 `GameState`
- UI 只读整理好的显示模型

这在未来切换 UI 样式时会很重要。

---

## 9. `screens/` -> Unity `Presentation/UI`

Python：

```text
src/sincity/screens/
```

Unity 中不应“迁移实现”，而应“迁移交互职责”。

建议拆成：

```text
Assets/Game/Presentation/
├── UI/
│   ├── CityScreenController.cs
│   ├── EncounterScreenController.cs
│   ├── DialoguePanelController.cs
│   ├── HandPanelController.cs
│   └── NotificationController.cs
├── Scene/
│   ├── LocationAnchor.cs
│   ├── SceneLocationBinder.cs
│   └── SequenceBinding.cs
└── Sequences/
    └── SequenceDirector.cs
```

要点：

- `screens/` 的 Raylib 绘制不直接迁移
- 迁移的是：
  - 地点层
  - 动作层
  - 手牌层
  - 对话层
  - 交锋层
  - 结算层

---

## 10. `app.py` -> `Application/GameController`

Python：

```text
GameApp.update()
├── hot reload
├── advance_pending_resolution
├── advance_action_reveal
├── advance_notifications
└── consume remaining pending_events
```

Unity 目标：

```text
Assets/Game/Application/
├── GameBootstrap.cs
├── GameController.cs
└── EventBridge.cs
```

Unity 中这个层的职责应是：

- 驱动一帧内规则推进
- 驱动事件消费
- 协调 UI / Scene / Timeline

不要把这些逻辑塞回 UI Controller。

---

## 11. `:key` / `:presentation` 如何用于 Unity

当前 Python 已支持：

- 可选 `:key`
- 可选 `:presentation`
- 不写时保留旧 ID 生成逻辑

Unity 中建议这样使用：

### `:key`

用于稳定外部绑定：

- `LocationAnchor`
- 特定 action lookup
- 存档中稳定引用

### `:presentation`

用于语义化表现绑定：

```text
theater.catch-shadow
theater.catch-shadow.success
theater.catch-shadow.fail
```

Unity 中由：

```text
SequenceBinding
```

把这个 cue 映射到：

- Timeline
- Camera shot
- Video clip
- 特殊动画

而不是让 SCM 直接引用 Unity 资源路径。

---

## 12. 不该迁移的东西

这些不应该直接带进 Unity：

- Raylib 绘制细节
- IMGUI 布局代码
- 过于 Python 风格的 facade 思路
- 调试用临时文案/表格输出

要迁移的是：

- 数据定义
- 规则语义
- 内容求值语义
- 事件流
- 交互层级

---

## 13. 推荐迁移顺序

### Step 1

迁移 `Core/Model`

### Step 2

迁移 `game/fields.py`、`effects.py`、`conditions.py`

### Step 3

迁移 `queries.py`、`content runtime`

### Step 4

迁移 `resolution.py`、`clocks.py`、`reacts.py`

### Step 5

迁移 `encounters.py`、`dialogues.py`

### Step 6

实现 Unity `Presentation/ViewModels`

### Step 7

实现 Unity UI / Scene / Timeline 绑定

---

## 14. 结论

当前 Python 工程已经不再需要先“继续拆清楚”才能迁移。  
它已经具备了清晰的迁移基线。

未来 Unity 迁移的重点不是再改 Python 架构，而是：

1. 保持 `game/` 语义不变
2. 保持 SCM / Ink 内容资产可复用
3. 在 Unity 中重建表现层和场景层

