# Architecture

本文描述当前 Python 工程在重构完成后的正式结构。

目标不是记录历史迁移过程，而是回答三个问题：

1. 现在工程的主要层次是什么
2. 每一层负责什么
3. 一次动作、一次对话、一次交锋是如何流动的

---

## 1. 总体结构

```text
src/sincity/
├── model/          权威状态与数据定义
├── content/        内容运行时（世界内容）
├── content_lang/   SCM DSL 运行时
├── encounters/     交锋内容运行时
├── dialogues/      Ink 对话运行时
├── game/           游戏核心逻辑层
├── presentation/   UI ViewModel / presenter 层
├── screens/        Raylib UI 层
└── app.py          应用入口
```

核心依赖方向：

```text
content_lang / content / encounters / dialogues
                    │
                    ▼
                  game
                    │
                    ▼
              presentation
                    │
                    ▼
                 screens
                    │
                    ▼
                  app.py
```

其中：

- `model/` 保存权威数据结构
- `game/` 保存规则、流程和状态推进
- `presentation/` 只负责把数据整理成 UI 可消费的形式
- `screens/` 只负责具体绘制和输入处理

---

## 2. 各层职责

## 2.1 `model/`

主要文件：

- `model/state.py`
- `model/defs.py`
- `model/enums.py`

职责：

- 定义 `GameState`
- 定义 `ActionDef`、`LocationDef`、`Effect`、`Condition`
- 定义枚举、判定结果、屏幕类型等

原则：

- `GameState` 是整个对局的权威状态
- 内容快照、UI 卡片、presenter 结果都不是权威状态

---

## 2.2 `content/` 与 `content_lang/`

主要文件：

- `content/runtime.py`
- `content/validate.py`
- `content/hot_reload.py`
- `content_lang/runtime_core.py`

职责：

- 解析和求值 SCM
- 根据当前状态生成世界内容
- 做内容校验和热重载

边界：

```text
输入：GameState
输出：LocationDef / ActionDef / Clock / React / Task
```

这里不做：

- UI 绘制
- 规则结算
- Raylib 表现
- Unity 表现

---

## 2.3 `encounters/`

职责：

- 交锋内容的编译和运行时支持
- 交锋场景的 DSL 数据解释

注意：

- `encounters/` 负责“交锋内容是什么”
- `game/encounters.py` 负责“交锋流程怎么推进”

---

## 2.4 `dialogues/`

职责：

- Ink 对话内容加载
- 对话运行时
- 外部函数绑定

注意：

- `dialogues/runtime.py` 只负责对话运行时桥接
- 真正的游戏状态修改仍通过 `game/` 层完成

---

## 2.5 `game/`

这是当前工程最重要的一层。

```text
game/
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

### `session.py`

职责：

- 新开局初始化
- 调试辅助
- `claim_growth`

权威入口：

```python
state, rng = start_new_run(seed)
```

### `queries.py`

职责：

- 当前世界快照查询
- 当前交锋快照查询
- action / clock / location 查询

这是“读当前世界”的主要入口。

### `fields.py`

职责：

- 统一字段读写
- health / energy / pressure / relations / inventory 的修改
- 一些资源与 actor 状态辅助逻辑

这是最底层的状态写入边界。

### `conditions.py`

职责：

- 条件求值
- 地点/动作是否可见、可用

### `actions.py`

职责：

- modal / assembly / input selection
- action 装配
- card / requirement / slot 切换

### `resolution.py`

职责：

- 执行动作
- pending resolution 生命周期
- reveal 生命周期
- dismiss pending

### `effects.py`

职责：

- `Effect` 的真正执行入口
- effect 文案描述
- dynamic value 求值

### `reacts.py`

职责：

- 世界 react
- 交锋 react
- react die 等连锁逻辑

### `clocks.py`

职责：

- clock 推进
- cycle 推进
- reset hand

### `encounters.py`

职责：

- 进入/结束交锋
- 交锋 store 初始化
- 交锋资源同步

### `dialogues.py`

职责：

- 开始/推进/结束对话
- 对话相关流程控制

### `flow.py`

职责：

- 轻量命令调度入口

形式：

```python
dispatch(state, command, rng)
```

`dispatch()` 本身不返回事件；事件统一写入 `state.pending_events`。

### `commands.py`

职责：

- 定义 UI / app 可以发出的命令

例如：

- `OpenLocation`
- `OpenAction`
- `ExecuteAction`
- `DismissPendingResolution`
- `FastForwardDialogue`

### `events.py`

职责：

- 定义事件类型
- 提供事件消费工具

当前事件系统是单通道：

```text
state.pending_events
```

生产者：

- `dispatch()`
- `advance_pending_resolution()`

消费者：

- `screens/*` 即时消费必要事件
- `app.py` 在本帧 update 结束时消费剩余事件，并写入 `last_frame_events`

---

## 2.6 `presentation/`

职责：

- 把 `game/queries` 和 `model/defs` 组织成 UI 友好的 presenter 数据

例如：

- 地点卡
- 动作卡
- slot 显示
- factor 预览
- 标签/角标

这里不做：

- 状态推进
- effect 执行
- SCM 求值

---

## 2.7 `screens/`

职责：

- Raylib 具体绘制
- 输入处理
- 调用 `dispatch()` 或局部消费事件

原则：

- screen 不直接实现规则
- screen 可以发 command
- screen 可以消费少量即时事件，例如 `DialogueFastForwarded`

---

## 2.8 `app.py`

职责：

- 应用生命周期
- update loop
- draw loop
- 统一驱动 pending resolution / reveal / notifications
- 消费本帧剩余事件

当前 `update()` 的核心顺序：

```text
1. hot reload
2. 输入级全局快捷键
3. advance_pending_resolution
4. advance_action_reveal
5. advance_notifications
6. consume remaining pending_events -> last_frame_events
```

---

## 3. 事件系统

当前事件系统采用单通道：

```text
state.pending_events
```

示意：

```text
UI click
  │
  ▼
dispatch(Command)
  │
  ├── 直接状态变化
  └── append GameEvent -> state.pending_events
                           │
                           ├── screens 立即 consume_event(...)
                           └── app.update() 末尾 drain 剩余事件
```

事件类型包括：

- `ActionStarted`
- `ResolutionSettled`
- `DialogueStarted`
- `DialogueFastForwarded`
- `EncounterStarted`
- `GameEnded`

`GameApp.last_frame_events` 保存本帧由 app 统一消费掉的剩余事件，方便调试和未来桥接。

---

## 4. 一次动作如何流动

```text
玩家点击动作
  │
  ▼
screen 调用 dispatch(ExecuteAction)
  │
  ▼
game.flow.dispatch()
  │
  ▼
game.resolution.perform_current_action()
  │
  ├── consume inputs
  ├── roll / compute result
  ├── build PendingResolution
  └── append ActionStarted
  │
  ▼
app.update()
  │
  ▼
advance_pending_resolution()
  │
  ├── apply_effects()
  ├── resolve reacts
  ├── update last_resolution
  └── append ResolutionSettled
```

---

## 5. 一次对话如何流动

```text
screen / action 触发对话
  │
  ▼
game.dialogues.start_dialogue()
  │
  ▼
dialogues/runtime.py 驱动 Ink
  │
  ├── continue
  ├── choose option
  └── 调 external function
          │
          ▼
        game.fields / game.encounters / game.dialogues
```

原则：

- 对话可以影响游戏状态
- 但状态写入仍走 `game/` 边界

---

## 6. 一次交锋如何流动

```text
某个 effect / dialogue / action 触发 start_encounter
  │
  ▼
game.encounters.start_encounter()
  │
  ▼
screen 切到 ENCOUNTER
  │
  ▼
queries/presenters 生成交锋内地点、动作、clock
  │
  ▼
玩家执行交锋动作
  │
  ▼
resolution / effects / reacts / clocks 推进
  │
  ▼
finish_encounter()
  │
  ▼
回到城市或进入下一状态
```

---

## 7. `:key` / `:presentation`

SCM 现在支持可选稳定标识：

- `:key`
- `:presentation`

原则：

- 不写 `:key` 时，继续使用旧 ID 生成逻辑
- 旧内容不需要一次性迁移
- 只有需要稳定外部绑定的内容才建议写显式 `:key`

这为未来 Unity 绑定提供了稳定语义入口，但不强迫当前内容全部改写。

---

## 8. 迁移意义

当前结构已经可以自然映射到 Unity：

```text
Python model/         -> Unity Core/Model
Python game/          -> Unity Core/Rules + Application flow
Python content/       -> Unity Content runtime
Python presentation/  -> Unity Presentation/ViewModels
Python screens/       -> Unity UI 实现（不直接复用）
```

因此，未来迁移重点不再是“先把 Python 拆清楚”，而是：

1. 保持 `game/` 规则语义一致
2. 保持 SCM 内容资产可复用
3. 在 Unity 中重建 presentation / screen 层

