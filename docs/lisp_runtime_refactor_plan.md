# Lisp Scene DSL 重构计划

## 目标

把当前 SCM 系统重构为更接近 Ink 哲学的作者语言：

```text
Lisp 写场景。
Ink 写对话。
Rules 管世界。
Host 演出来。
```

Lisp 不做万能游戏脚本，也不直接控制引擎。它负责表达一个场景当前是什么、玩家能做什么、行动之后场景局部状态如何变化，以及需要向外部系统提出哪些受控请求。

## 核心边界

```text
Lisp Scene Runtime
  场景结构、节点、行动、局部状态、局部规则、当前 snapshot。

Ink Runtime
  对话文本流、选择、对话变量、对话跳转、对话 tags。

Rules Layer / GameState
  全局权威状态：health、energy、money、inventory、relationships、day、flags、tasks。

Host / Engine
  渲染、输入、动画、音效、Timeline、存档 IO、场景加载、runtime 调度。
```

全局状态不归 Lisp scene runtime。Lisp 可以读取全局状态，也可以通过受控外部函数请求修改；最终修改由 Rules Layer 执行。

## Lisp 负责什么

Lisp 负责场景语义：

- scene / node / action / clock 的定义
- 行动标题、描述、条件、风险、结果文本
- 场景局部状态，例如 `alert`、`phase`、`enemies`、局部 clock
- 场景局部规则，例如 after-action、on-cycle、on-enter
- 当前场景 snapshot 的生成
- 对外部系统的受控调用，例如扣血、给钱、开始对话、播放表现 tag

Lisp 不负责：

- UI 布局和坐标
- Unity / Raylib / Host API
- asset loading
- 动画状态机
- 音频播放细节
- 存档文件 IO
- 物理、碰撞、寻路
- 全局状态合法性

## Host 负责什么

Host 负责运行和表现：

- 创建/恢复 Lisp scene runtime
- 注入外部函数
- 请求 scene snapshot
- 渲染节点、行动、clock、文本
- 接收玩家输入
- 调用 Rules Layer 做全局检定
- 把 outcome 传回 Lisp 执行对应行动逻辑
- 调用 Ink runtime
- 播放动画、音效、Timeline
- 存档和读档

## Rules Layer 负责什么

Rules Layer 是全局状态的唯一权威。

它负责：

- 修改 health / energy / money
- 管理 inventory
- 管理 relationships
- 管理 day
- 管理 flags 和 tasks
- 校验状态变化是否合法
- 处理死亡、结局、任务、副作用
- 处理城市和外出场景之间的全局状态同步

Lisp 不能直接写这些状态，只能通过外部函数请求。

## 局部状态与全局状态

Lisp scene runtime 可以直接修改自己的局部状态：

```scheme
(set! alert (clock+ alert 1))
(set! phase 'escape)
(set! enemies (map enemy-tick enemies))
```

全局状态必须通过外部函数：

```scheme
(add-resource! 'health -1)
(add-resource! 'money 20)
(set-flag! 'hotel_infiltrated true)
(start-dialogue! 'vera_phone)
```

判断标准：

```text
只影响当前场景如何运行 -> Lisp local state
影响整个游戏世界 -> Rules Layer / GameState
```

## 外部函数设计

外部函数类似 Ink external functions，由 Host / Rules Layer 注入 Lisp runtime。

### 查询函数

只读，返回普通 Lisp 值：

```scheme
(day)
(resource 'health)
(resource 'money)
(has-item? 'mysterious_item)
(flag? 'hotel_unlocked)
(relation 'police)
```

### 修改函数

带 `!`，通过 Rules Layer 修改全局状态：

```scheme
(add-resource! 'health -1)
(add-resource! 'money 18)
(add-item! 'key 1)
(remove-item! 'key 1)
(set-flag! 'vera_thread_unlocked true)
(change-relation! 'police -1)
```

### 表现/调度函数

由 Host 消费：

```scheme
(log! "敌人开火。")
(tag! 'sfx 'gunshot)
(presentation! 'office_promoted)
(start-dialogue! 'vera_phone)
(start-encounter! 'hotel_infiltration)
(finish-scene! 'success)
```

约束：

- 不注入 raw Unity / Raylib API。
- 不注入直接绕过 Rules Layer 的 raw setter。
- 不注入存档、文件、资源加载等底层能力。

## Scene Snapshot

Lisp 不创建 UI，只返回可展示数据。

示例：

```json
{
  "title": "仓库撤退",
  "desc": "敌人会一波波涌进来。",
  "clocks": [
    { "id": "alert", "title": "警觉", "value": 2, "max": 6 },
    { "id": "exit", "title": "出口", "value": 3, "max": 8 }
  ],
  "nodes": [
    {
      "id": "exit_node",
      "title": "被堵塞的出口",
      "desc": "铁架和碎玻璃压在门前。",
      "actions": [
        {
          "id": "push_exit",
          "title": "冲开出口",
          "desc": "用肩膀把路撞开。",
          "suit": "willpower",
          "risk": "mid",
          "enabled": true
        }
      ]
    }
  ]
}
```

Host 决定它们显示成卡片、按钮、热点或其他 UI。

## 行动流程

```text
1. Host 请求 Lisp render，得到 snapshot。
2. Host 渲染 action。
3. 玩家选择 action。
4. Rules Layer 根据 action 的 suit/risk/card/modifier 计算 outcome。
5. Host 调用 Lisp resolve-action(action-id, outcome)。
6. Lisp 执行对应 outcome 逻辑：
   - 修改局部状态
   - 调用外部函数请求全局修改或表现
7. Rules Layer / Host 处理外部函数的真实效果。
8. Host 再次请求 Lisp render。
```

检定规则保持在 Rules Layer，Lisp 只声明行动的 `suit`、`risk`、modifier 等作者信息。

## 场景切换

城市主场景和外出场景是不同的 Lisp scene runtime，但共享同一个 GameState 投影。

进入外出场景：

```text
城市 Lisp 调用 start-encounter!
Host 创建外出 Lisp runtime
Rules Layer 提供全局状态投影
外出场景运行自己的局部状态
外出完成后通过外部函数修改全局状态
Host 切回城市
城市 Lisp 根据最新 GameState 重新 render
```

全局状态不在两个 Lisp runtime 之间同步。它只存在于 Rules Layer / GameState。

## Ink 交互

Lisp 和 Ink 都不直接互相控制。Host 负责调度。

```text
Lisp 调用 start-dialogue!
Host 启动 Ink runtime
Ink 输出文本和 choices
玩家选择
Ink 输出 tags 或 external calls
Host / Rules Layer 应用结果
Host 回到 Lisp scene render
```

Ink tags 可以映射到同一组外部能力，例如：

```text
set-flag
add-resource
tag sfx
presentation
```

## 存档

存档应拆分：

```json
{
  "game_state": {
    "health": 8,
    "money": 42,
    "inventory": [],
    "flags": {},
    "relationships": {},
    "day": 5
  },
  "scene_states": {
    "active_scene_id": "hotel_infiltration",
    "local_state": {
      "alert": { "kind": "clock", "value": 2, "max": 6 },
      "phase": "second_floor"
    }
  },
  "ink_state": {},
  "host_state": {
    "screen": "encounter"
  }
}
```

Rules Layer 保存全局状态。Lisp scene runtime 保存局部状态。Ink 保存对话状态。Host 保存表现状态。

## 迁移步骤

## 当前已确认的过渡改动

下面这些是当前工程为了修正语义不一致，已经做过或已经确认的过渡性改动。它们不是最终形态，但应在后续重构中被吸收，而不是丢失。

### `effect` 改为 special form

过去 `effect` 像普通函数一样先求值参数，导致：

```scheme
(effect 'set checked-day (+ day 1))
```

可能在构造模板时提前求值。现在 `effect` 应保留作者表达式的语义，避免在错误时机折叠。

最终目标不是让 Host eval 这段表达式，而是让 Lisp runtime 在行动/规则真正执行时 eval Lisp，然后只把已经解析好的外部函数调用交给 Rules Layer / Host。

### `react :then` 需要运行时求值

`react :then` 中的 `if`、`when`、`append`、`cond` 应按触发时状态执行，而不是在内容加载时生成固定 effect list。

这条规则会保留到新架构里：

```scheme
(react
  :when condition
  :then
  (lambda ()
    ...))
```

或者等价的运行时 body。核心是：`then` 是场景逻辑，不是静态数据。

### 顶层 helper lambda 必须读取运行时状态

类似：

```scheme
(define salary
  (lambda ()
    (+ 18 (* rank 8))))
```

应该在调用时读取当前 runtime state，而不是捕获内容加载时的初始 state。

这和 Ink 的变量/函数直觉一致：脚本函数在运行时根据当前状态产生结果。

### 结构化 payload 是过渡层

当前系统引入过：

```text
FieldRef
DynamicValue
SetFieldPayload
AddFieldPayload
ShiftClockPayload
```

它们用于修补旧架构中 Python 解释 effect 字符串的问题。

在最终架构中，Host 不应再 eval Lisp 表达式。Lisp runtime 应执行作者逻辑，并通过外部函数直接调用 Rules Layer / Host。也就是说，这些 payload 可以作为迁移期兼容层，但不应成为最终核心模型。

### `node/action/scene/clock` 是 Lisp 内建构造器

这些不是 Host external functions。

它们只构造 snapshot 数据：

```scheme
(node ...)
(action ...)
(clock ...)
```

而这些才是 external functions：

```scheme
(add-resource! 'health -1)
(log! "...")
(tag! 'sfx 'gunshot)
(start-dialogue! 'vera_phone)
```

### 局部状态和全局状态必须分离

已经确认的规则：

```text
局部状态：Lisp runtime 直接 set!
全局状态：通过 Host 注入的外部函数进入 Rules Layer
```

这也是城市主场景和外出场景可以自然切换的基础。

### 外部函数路线优先于消息队列路线

当前设计选择更接近 Ink external functions：

```scheme
(add-resource! 'health -1)
```

这会调用 Host / Rules Layer 注入的函数，真实修改 GameState。

暂不采用复杂的 message queue / transaction / preview 体系。需要测试时，可以用 mock external functions 记录调用。

```python
calls = []
runtime.inject("add-resource!", lambda key, amount: calls.append((key, amount)))
```

这样既保持简单，也保留可测试性。

### 1. 建立新的 runtime 边界

定义最小 API：

```text
render(global_projection) -> snapshot
resolve_action(action_id, outcome, global_projection)
advance_cycle(global_projection)
export_local_state()
import_local_state(state)
```

### 2. 建立外部函数白名单

先实现少量函数：

```text
day
resource
has-item?
flag?
add-resource!
set-flag!
log!
tag!
start-dialogue!
start-encounter!
finish-scene!
```

### 3. 选择一个小场景试点

先不要迁移整座城市。选择一个独立外出场景，验证：

- local state
- render snapshot
- action outcome
- external function
- cycle/react
- save/load local state

### 4. 迁移更多场景

优先迁移机制清晰的场景：

- 仓库撤退
- 茶楼搜刮
- 关系张力测试

### 5. 再迁城市模块

城市模块涉及长期状态，应在 Rules Layer 边界稳定后再迁。

### 6. 逐步废弃旧 Effect 解释

旧 `Effect` / `ActionTemplate` / Python `_apply_effect` 先作为兼容层保留。

新内容优先走：

```text
Lisp runtime eval outcome
external function 修改全局状态
snapshot 供 Host 渲染
```

## 设计原则

1. Lisp eval Lisp，Host 不 eval Lisp 表达式。
2. Lisp 直接修改局部状态。
3. Lisp 通过外部函数请求全局修改。
4. Rules Layer 是全局状态权威。
5. Host 只负责表现和调度。
6. node / action / scene / clock 是 Lisp 内建构造器，不是外部函数。
7. 外部函数必须白名单注册。
8. 带 `!` 的外部函数才允许产生外部副作用。
9. 不暴露 raw engine API。
10. 新架构应能在 Python/Raylib 和 Unity Host 间复用 SCM 内容。

## 一个最小例子

```scheme
(scene-module warehouse-escape
  :title "仓库撤退"

  :state
  (state
    (exit (clock :title "出口" :current 0 :max 5))
    (alert (clock :title "警觉" :current 0 :max 3)))

  :render
  (lambda ()
    (scene
      :title "仓库撤退"
      :desc "铁门被杂物堵住，外面有人正在靠近。"
      :show-clocks (list exit alert)
      :nodes
      (list
        (node
          :id 'exit-node
          :title "被堵塞的出口"
          :desc "木箱、铁架和碎玻璃压在门前。"
          :actions
          (list
            (action
              :id 'push-exit
              :title "冲开出口"
              :desc "用肩膀和手里的铁棍硬推出一条路。"
              :check (check :suit 'willpower :risk 'mid))))))))

  :actions
  (actions
    (on 'push-exit
      :ok
      (lambda ()
        (set! exit (clock+ exit 2))
        (log! "你把堵门的铁架撞开了一截。"))

      :partial
      (lambda ()
        (set! exit (clock+ exit 1))
        (set! alert (clock+ alert 1))
        (log! "你推进了一点，但动静也传了出去。"))

      :fail
      (lambda ()
        (set! alert (clock+ alert 1))
        (add-resource! 'health -1)
        (tag! 'sfx 'metal_hit)
        (log! "你撞在铁架上，肩膀一阵发麻。"))))))
```

这个例子里：

- `scene`、`node`、`action`、`clock` 是 Lisp 内建构造器。
- `exit`、`alert` 是 Lisp runtime 局部状态。
- `add-resource!`、`tag!`、`log!` 是外部函数。
- Host 负责检定和渲染。
- Rules Layer 负责真正修改 health。

## 最终目标

最终系统应形成清晰边界：

```text
Lisp Scene DSL
  可运行的场景手稿。

Ink
  可运行的对话手稿。

Rules Layer
  全局游戏事实和合法性。

Host
  舞台、演员、灯光、输入和存档。
```

这能让当前 Python/Raylib 原型继续工作，也为未来 Unity Host 保留迁移路径。
