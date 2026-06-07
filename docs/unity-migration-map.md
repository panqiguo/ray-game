# Python 到 Unity 的迁移对照

## 目标

这份文档描述当前 Python 工程中每一层未来在 Unity/C# 中的对应位置。

迁移时不要把 Python 目录机械翻译成 C# 目录，而应该按职责迁移。

```text
Python 当前结构       -> Unity 目标结构
------------------------------------------
model                -> Core/Model
content + encounters -> Content/Runtime
rules                -> Core/Rules
screens presenters   -> Presentation/ViewModels
screens widgets      -> Presentation/UI
app                  -> Application
scm / ink            -> GameContent
```

## 总体映射

```text
Python
┌──────────────────────────────────────────┐
│ app.py                                   │
├──────────────────────────────────────────┤
│ screens/                                 │
├──────────────────────────────────────────┤
│ screens/*presenters.py                   │
├──────────────────────────────────────────┤
│ rules/                                   │
├──────────────────────────────────────────┤
│ content/ + content_lang/ + encounters/   │
├──────────────────────────────────────────┤
│ model/                                   │
├──────────────────────────────────────────┤
│ scm/ + dialogues/assets/                 │
└──────────────────────────────────────────┘

Unity
┌──────────────────────────────────────────┐
│ Application/                             │
├──────────────────────────────────────────┤
│ Presentation/UI + Scene + Sequences      │
├──────────────────────────────────────────┤
│ Presentation/ViewModels                  │
├──────────────────────────────────────────┤
│ Core/Rules                               │
├──────────────────────────────────────────┤
│ Content/Runtime                          │
├──────────────────────────────────────────┤
│ Core/Model                               │
├──────────────────────────────────────────┤
│ GameContent/Scm + Dialogues + Assets     │
└──────────────────────────────────────────┘
```

## GameContent

来自 Python：

```text
src/sincity/scm/
src/sincity/dialogues/assets/
src/sincity/assets/
```

Unity 目标：

```text
Assets/GameContent/
├── Scm/
├── Dialogues/
├── Portraits/
└── Localization/
```

迁移策略：

- SCM 继续作为核心内容脚本。
- Ink 继续负责长对话。
- 图片、头像和视频资产交给 Unity 管理。
- SCM 不直接引用 Unity 路径，使用稳定 key 或 presentation cue。

## Core/Model

来自 Python：

```text
src/sincity/model/state.py
src/sincity/model/defs.py
src/sincity/model/enums.py
src/sincity/model/items.py
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
├── ProgressClock.cs
└── Enums.cs
```

迁移重点：

- 先迁移数据形状，不急着迁移行为。
- 区分权威状态、派生快照、UI 状态。
- `GameState` 应可以独立序列化。
- `LocationDef` / `ActionDef` 不应包含 Unity 对象引用。

建议边界：

```text
Core/Model 只包含普通 C# 数据。
不能依赖 UnityEngine、Timeline、Cinemachine、MonoBehaviour。
```

## Content/Runtime

来自 Python：

```text
src/sincity/content/
src/sincity/content_lang/
src/sincity/encounters/
src/sincity/dialogues/
src/sincity/scm_lint.py
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
│   ├── EncounterContentRuntime.cs
│   ├── ContentDatabase.cs
│   └── SnapshotCache.cs
│
├── Dialogue/
│   ├── DialogueRegistry.cs
│   └── DialogueRuntime.cs
│
└── Validation/
    ├── ContentValidator.cs
    └── SceneBindingValidator.cs
```

迁移重点：

- C# 中实现 SCM 子集或加载 Python 编辑期导出的 AST。
- `render_world` 和 `render_encounter` 的语义要保持。
- 城市和交锋都输出地点、动作、clock、react。
- 内容 runtime 只生成定义和快照，不播放 Unity 表现。

关键边界：

```text
Content Runtime
   输入: GameState / Encounter store
   输出: WorldSnapshot / EncounterSnapshot
```

不要让 Content Runtime 直接控制 Unity 场景。

## Core/Rules

来自 Python：

```text
src/sincity/rules/progression.py
src/sincity/rules/deck.py
src/sincity/rules/judgment.py
src/sincity/rules/rng.py
src/sincity/rules/notifications.py
```

Unity 目标：

```text
Assets/Game/Core/Rules/
├── GameSession.cs
├── ContentQueries.cs
├── FieldAccessor.cs
├── ConditionEvaluator.cs
├── ActionAssembler.cs
├── ActionResolver.cs
├── PendingResolutionRunner.cs
├── EffectExecutor.cs
├── ReactResolver.cs
├── ClockResolver.cs
├── EncounterResolver.cs
├── DialogueResolver.cs
├── DeckService.cs
├── JudgmentResolver.cs
├── ActorResourceService.cs
└── EndingResolver.cs
```

迁移重点：

- 不要创建一个巨大的 `Progression.cs`。
- 先把 Python `progression.py` 按职责拆清楚，再逐块移植。
- 所有权威状态修改最终都应该进入规则层。
- Timeline、UI、视频不能直接修改 `GameState`。

核心流程：

```text
ExecuteActionCommand
   │
   ▼
ActionResolver
   │
   ├── ConditionEvaluator
   ├── JudgmentResolver
   ├── EffectExecutor
   ├── ReactResolver
   └── ClockResolver
   │
   ▼
GameEvent[]
```

## Presentation/ViewModels

来自 Python：

```text
src/sincity/screens/city_presenters.py
src/sincity/screens/encounter_presenters.py
src/sincity/screens/table_presenters.py
src/sincity/screens/ui_tags.py
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

迁移重点：

- ViewModel 可以读 `GameState` 和 snapshot。
- ViewModel 不应该执行规则。
- Unity UI 组件只绑定 ViewModel，不直接理解复杂规则。

数据流：

```text
WorldSnapshot + GameState
          │
          ▼
LocationViewModel / ActionViewModel
          │
          ▼
Unity UI
```

## Presentation/UI

来自 Python：

```text
src/sincity/screens/
src/sincity/rendering.py
src/sincity/labels.py
```

Unity 目标：

```text
Assets/Game/Presentation/
├── Screens/
├── HUD/
├── Locations/
├── Actions/
├── Hand/
├── Dialogue/
├── Tasks/
├── Notifications/
└── Debug/
```

迁移重点：

- Raylib 绘制代码不需要逐行迁移。
- 需要迁移的是功能结构：
  - 城市层
  - 交锋层
  - 结局层
  - 手卡
  - 动作面板
  - 对话框
  - 任务面板
  - 通知
  - 调试面板

UI 只发命令：

```text
Button Click
   │
   ▼
ExecuteActionCommand / OpenLocationCommand
   │
   ▼
Application Controller
```

UI 不直接改 `GameState`。

## Presentation/Scene And Sequences

这是 Unity 新增的表现层，Python 中没有完全对应模块。

建议结构：

```text
Assets/Game/Presentation/
├── Locations/
│   ├── LocationAnchor.cs
│   ├── LocationRegistry.cs
│   └── LocationPresenter.cs
│
├── Camera/
│   ├── CameraFocusController.cs
│   └── CameraPresetBinding.cs
│
└── Sequences/
    ├── SequenceBinding.cs
    ├── SequenceDirector.cs
    └── SequenceRequest.cs
```

职责：

- Unity 场景放置地点锚点。
- Timeline、视频、动画通过 presentation cue 绑定。
- 表现层消费规则层事件，但不决定规则结果。

绑定方式：

```text
SCM
  action :presentation 'theater.catch_shadow

Unity Scene
  SequenceBinding.cueKey = theater.catch_shadow.success
```

## Application

来自 Python：

```text
src/sincity/app.py
src/sincity/main.py
```

Unity 目标：

```text
Assets/Game/Application/
├── GameBootstrap.cs
├── GameController.cs
├── GameSessionRunner.cs
├── CommandDispatcher.cs
├── GameEventDispatcher.cs
└── SaveLoadController.cs
```

职责：

- 创建和持有当前 session。
- 调用 Content Runtime 生成 snapshot。
- 接收 UI command。
- 调用 Core/Rules。
- 分发 GameEvent 给 UI 和 SequenceDirector。
- 处理存档、读档、新游戏。

典型流程：

```text
UI Command
   │
   ▼
GameController
   │
   ├── Core/Rules 修改 GameState
   ├── Content/Runtime 重新生成 Snapshot
   ├── Presentation/ViewModels 刷新
   └── Presentation/Sequences 播放表现
```

## Authoring / Validation

来自 Python：

```text
src/sincity/content/validate.py
src/sincity/scm_lint.py
scripts/check_parens.py
```

Unity 目标：

```text
Assets/Game/Authoring/
├── ContentValidator.cs
├── SceneBindingValidator.cs
├── ScmDebugWindow.cs
├── SnapshotPreviewWindow.cs
└── MigrationTestRunner.cs
```

职责：

- 检查 SCM 语法和结构。
- 检查 action/effect/clock/react/task 合法性。
- 检查 Unity 场景中是否存在对应地点锚点。
- 检查 presentation cue 是否有绑定。
- 在编辑器中预览当前 snapshot。

## 建议迁移顺序

```text
1. Python 内先拆清 progression.py 职责。
2. 给 SCM 的 node/action 补稳定 key。
3. 定义 C# Core/Model DTO。
4. 建 Content Runtime 最小链路。
5. 用一个城市地点跑通 snapshot。
6. 接 Unity LocationAnchor。
7. 接 ActionResolver 和 EffectExecutor。
8. 接一个 Timeline presentation cue。
9. 迁移 Encounter。
10. 迁移 Dialogue。
11. 迁移存档和编辑器校验。
```

## 每块迁移时的判定标准

```text
Model
  能否独立序列化？
  是否不依赖 UnityEngine？

Content Runtime
  同一 GameState 下是否生成和 Python 相同的 snapshot？

Rules
  同一动作输入下是否得到和 Python 相同的 GameState 变化？

Presentation
  是否只消费 snapshot / event？
  是否没有直接改 GameState？

Sequences
  是否只由 presentation cue 驱动？
  是否不拥有剧情分支逻辑？

Application
  是否是唯一调度命令、规则、刷新和表现的地方？
```

## 最小垂直切片

第一条 Unity 验证链路建议选择：

```text
城市地点: 剧院
动作: 追上那个戴面具的人
表现: theater.catch_shadow
结果: end_encounter / set world value
```

目标：

```text
SCM 生成地点和动作
   │
   ▼
Unity 场景找到 LocationAnchor
   │
   ▼
Action UI 显示动作
   │
   ▼
Core/Rules 执行动作
   │
   ▼
GameEvent 触发 Timeline
   │
   ▼
刷新 snapshot
```

