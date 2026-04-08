# 系统设计稿 V1

## 目标

本稿定义新的底层机制与内容抽象边界，用于支持新的“逃亡生存 + 探索解锁 + 委托脱身”流程。

目标：

- 保持玩家语义简单：玩家只看到`地点`、`行动`、`进度钟`、`手牌`、`物品`
- 保持系统原子性：底层只有少量稳定概念，通过组合表达上层玩法
- 保持内容可改性：地点、行动、钟表、解锁关系可频繁调整，不要求修改底层规则
- 保持动态语言风格：内容 authoring 自然、简洁，但运行时仍然有明确校验和集中 mutation API


## 设计原则

### 1. 底层只保留少量原子概念

引擎正式承认的原子概念只有：

- `Location`
- `Action`
- `ProgressClock`
- `Input`
- `Effect`
- `Condition`

其他高级语义都由这些原子概念组合得到，不进入引擎核心概念层。

### 2. 内容层允许动态，schema 层保持稳定

- 稳定的是 schema、状态结构、运行时 mutation API
- 动态的是地点树、行动列表、钟表注册、解锁链、任务链

### 3. 玩家语义优先于内部技术语义

- 删除 `ActionMethod`
- “破门的三种方式”在内容层表达为三个独立行动
- “打工赚钱”在不同地点是不同的行动，不共享“方法”层

### 4. 内容 authoring 用树，运行时用索引

- 内容层用嵌套地点树书写
- 加载时编译为扁平 registry
- 校验时 assert 地点嵌套深度最多为 2


## 核心概念

### Location

地点节点。内容层允许结构：

- `地点 -> 行动`
- `地点 -> 子地点 -> 行动`

不允许：

- `地点 -> 子地点 -> 子地点`

地点本身不承担复杂规则，只承载：

- 标题与描述
- 初始可见条件
- 子地点
- 行动
- UI 位置信息

### Action

行动是唯一的可执行节点。

行动可以：

- 要求放入若干输入
- 推进一个或多个 Progress Clock
- 改变地点/行动可见性
- 给钱、扣钱、给物品、扣物品
- 休息、推进追击、抽牌
- 进行牌判定
- 不进行牌判定

行动本身不分“方法”。

### ProgressClock

Progress Clock 是通用进度机制，不是写死的全局字段。

可用于表达：

- 被追击进度
- 区域探索进度
- 某行动剩余次数
- 某任务推进度
- 酒店许可
- 老板信任度

Progress Clock 在内容层可注册，在运行时存入统一 registry。

### Input

Input 表示行动装配时可被“放入”的东西。

它统一了 UI 交互语义，但不要求底层数据结构完全一致。

可放入输入分三类：

- `card`
- `resource`
- `item`

不可放入：

- `health`
- `stress`

### Effect

一切状态变化都通过 Effect 执行。

Effect 必须由集中 runner 执行，禁止在各 screen 或内容逻辑里到处直接修改 state。

### Condition

一切可见性、可执行性、解锁条件都通过 Condition 表达。


## 数据分层

### Attributes

角色属性，不可放入：

- `health`
- `max_health`
- `stress`
- `max_stress`

### Resources

可计数、可放入的资源：

- `money`
- `cigarettes`

### Inventory

可拥有、可放入的物品：

- `clothes`
- `gun`
- `car_key`
- `task_item_*`

建议数据形态：

- `resources: ResourceState`
- `inventory: dict[str, int]`


## 内容 Schema

### LocationNode

内容层 authoring 使用嵌套结构：

```python
LocationNode(
    id="slum",
    title="贫民窟街道",
    description="这里的每一双眼睛都认识别人的饥饿。",
    children=(
        LocationNode(
            id="slum_corner",
            title="街角",
            actions=(...),
        ),
    ),
    actions=(...),
)
```

编译后形成：

- `locations_by_id`
- `parent_by_id`
- `children_by_id`
- `actions_by_location`

### ActionDef

建议字段：

```python
ActionDef(
    id: str,
    title: str,
    description: str,
    check: CheckDef | None,
    inputs: tuple[InputRequirement, ...],
    effects: tuple[Effect, ...],
    conditions: tuple[Condition, ...],
    clocks: tuple[ClockAdvance, ...],
    ui_tags: tuple[str, ...] = (),
)
```

说明：

- `check is None` 表示无牌判定行动
- `inputs` 统一描述牌、资源、物品需求
- `effects` 表示执行后状态变化
- `clocks` 表示推进哪些 Progress Clock
- `ui_tags` 只用于展示，不承担规则语义

### CheckDef

用于取代旧 `ActionMethod`，但保持单层行动。

```python
CheckDef(
    suits: tuple[Suit, ...],
    difficulty: int,
    risk: Risk,
    success: OutcomeDef,
    cost: OutcomeDef,
    fail: OutcomeDef,
)
```

如果一个地点有三种破门方式，则写三个 `ActionDef`，每个行动各自带一个 `CheckDef`。

### InputRequirement

```python
InputRequirement(
    kind: "card" | "resource" | "item",
    key: str,
    amount: int = 1,
    tags: tuple[str, ...] = (),
    label: str = "",
)
```

例子：

- 1 张手牌：`kind="card", key="any"`
- 1 张负面牌：`kind="card", key="negative"`
- 10 金币：`kind="resource", key="money", amount=10`
- 1 件衣服：`kind="item", key="clothes", amount=1`

### ProgressClockSpec

```python
ProgressClockSpec(
    id: str,
    title: str,
    segments: int,
    thresholds: tuple[ClockThreshold, ...] = (),
    tags: tuple[str, ...] = (),
    hidden: bool = False,
    display: ProgressClockDisplay = ProgressClockDisplay(scope="auto"),
)
```

### ProgressClockDisplay

```python
ProgressClockDisplay(
    scope: "auto" | "global" | "location" | "action",
    anchor_id: str | None = None,
)
```

说明：

- `global`：显示在 HUD / 全局状态区
- `location`：显示在某个地点层
- `action`：显示在某个行动节点上
- `auto`：由编译阶段自动推导

自动推导规则：

- 若 clock 只被 1 个 action 推进：显示在 `action`
- 若 clock 被多个 action 推进，且它们同属 1 个 location：显示在 `location`
- 若 clock 被多个不同 location 下的 action 推进：显示在 `global`

如果内容显式提供 `display`，则覆盖自动推导。

### ClockThreshold

```python
ClockThreshold(
    at: int,
    effects: tuple[Effect, ...],
)
```

阈值只声明效果，不声明特殊规则。


## 运行时状态

建议新的运行时状态结构：

```python
WorldState(
    visible_locations: set[str],
    hidden_actions: set[str],
    progress_clocks: dict[str, ProgressClockState],
)
```

```python
ActionAssemblyState(
    action_id: str,
    slotted_card_id: str | None,
    slotted_resources: dict[str, int],
    slotted_items: dict[str, int],
)
```

GameState 建议拆分为：

- `attributes`
- `resources`
- `inventory`
- `world`
- `deck`
- `assembly`
- `logs`
- `ending`

旧的 `MissionState` 应逐步删除，不再保留屠宰场专用状态。


## 行动执行管线

所有行动必须走同一条执行管线：

1. 检查地点可见
2. 检查行动可见
3. 检查输入是否满足
4. 扣除已放入输入
5. 执行牌判定（如果有）
6. 应用 outcome effects
7. 推进 Progress Clock
8. 触发阈值 effects
9. 处理 reveal/hide/disable
10. 检查胜利/失败
11. 清理 assembly

不得跳过统一执行入口。


## Mutation API

运行时状态变化必须通过集中 API，而不是四处分散改 state。

建议 API：

- `change_health(amount)`
- `change_stress(amount)`
- `change_money(amount)`
- `change_resource(key, amount)`
- `grant_item(item_id, amount=1)`
- `consume_item(item_id, amount=1)`
- `register_clock(spec)`
- `advance_clock(clock_id, amount=1)`
- `set_clock(clock_id, value)`
- `reveal_location(location_id)`
- `hide_location(location_id)`
- `hide_action(action_id)`
- `disable_action(action_id)`
- `open_sub_location(location_id)`
- `start_rest(rest_profile_id)` 或直接作为 `Effect("rest")`

这些 API 应放入独立 rules 模块中。


## 生命与创伤规则

### 规则

- 生命总上限为 10
- 每失去 1 点生命，牌库中总创伤牌数量 +1
- 每恢复 1 点生命，牌库中总创伤牌数量 -1
- 起始牌库定义按满血状态书写，不直接写创伤牌
- 开局残局通过先设置生命，再调用同步逻辑生成创伤牌

### 实现要求

必须存在集中同步函数，例如：

- `sync_trauma_cards_with_health(state)`

任何 `change_health` 之后都自动调用它。


## 压力代偿规则

### 规则

- 当一次事件增加压力时：
  - 如果角色压力已满，或本次会达到满压
  - 则额外代偿扣 1 点生命
- 无论本次增加多少压力，代偿永远只扣 1

### 实现要求

不得把这条规则散落在单个行动里。

必须通过统一压力入口处理，例如：

- `change_stress(amount, source="...")`


## Progress Clock 用法约定

### 一次性行动

组合方式：

- 行动推进一个 `segments=1` 的 Progress Clock
- 满值阈值触发 `hide_action`

### 可做三次的行动

组合方式：

- 行动推进一个 `segments=3` 的 Progress Clock
- 满值阈值触发 `hide_action`

### 探索地点

组合方式：

- 探索行动推进 `ProgressClock`
- 在某些阈值触发 `reveal_location`
- 满值时可 `hide_location`

### 永久可重复行动

组合方式：

- 不绑定封顶时钟
- 或仅绑定展示用 clock，不含 hide effect

说明：

引擎不需要 `ActionRepeatRule` 作为核心规则。  
UI 可以根据 clock 配置推导展示标签，如“单次”“三次”“探索”“可重复”。

### Clock 显示层级

一个行动可能推进多个 Progress Clock，例如：

- 自己的一次性/限次 clock
- 全局追击 clock
- 某条地点探索 clock

UI 只显示与当前层级最相关的 clock：

- 行动节点左上角显示 `action` 级 clock
- 地点卡/地点面板显示 `location` 级 clock
- HUD/右侧状态区显示 `global` 级 clock

这样可以避免一个行动节点同时塞进多个不同语义的进度钟。


## 世界流程内容约定

### 开局

- 角色已重伤逃出
- 初始生命低于满值
- 初始金钱为 0
- 初始追击时钟为 0/6
- 初始可见地点有限

### 休息

休息是普通行动，不是全局按钮。

休息行动通常包含：

- 推进一天
- 推进追击时钟 +1
- 重抽手牌
- 可能回血
- 可能加压
- 可能花钱

### 探索地点

- 贫民窟街道：探索进度 4
- 居民区：探索进度 4
- 阈值解锁新地点
- 满值可隐藏原探索点

### 修理厂主线

离开这里由两个行动达成：

- 交 300 块钱
- 交任务道具

两者任一达成即可获得离开条件，最终触发离开结局。


## 内容 Authoring 建议

内容层应允许使用 helper，而不是每次手写原始 dict。

建议 helper：

- `single_use_action(...)`
- `repeatable_job(...)`
- `explore_action(...)`
- `delivery_action(...)`
- `rest_action(...)`
- `clock(...)`
- `reveal_at(...)`

原则：

- helper 只生成标准 schema
- helper 不引入新的运行时概念


## 校验规则

内容加载时必须 assert：

- 所有 id 唯一
- 地点树深度 <= 2
- action 引用的地点存在
- action 引用的 Progress Clock 存在，或在运行时注册点合法
- threshold 按 `at` 严格递增
- effect kind 合法
- condition kind 合法
- 输入需求 kind 合法
- item/resource key 合法
- reveal/hide 的目标存在

动态语言中的可靠性主要依赖这一层硬校验。


## 推荐模块拆分

- `model/defs.py`
  - schema definitions
- `model/state.py`
  - runtime state
- `rules/actions.py`
  - action visible / assembly / execute
- `rules/clocks.py`
  - Progress Clock register / advance / threshold
- `rules/resources.py`
  - health / stress / money / cigarettes / trauma sync
- `rules/world.py`
  - reveal / hide / location traversal
- `rules/rest.py`
  - rest / day advance / pursuit clock
- `rules/outcomes.py`
  - victory / failure
- `content/scenario_*.py`
  - scenario builders


## 迁移顺序

### 第一阶段：底层重构

- 删除 `ActionMethodDef`
- 引入 `ProgressClockSpec / ProgressClockState`
- 引入 `ActionAssemblyState`
- 引入 `inventory`
- 引入 `WorldState`

### 第二阶段：规则重构

- 实现统一 mutation API
- 实现创伤同步
- 实现压力代偿
- 实现 Progress Clock 系统
- 实现地点 reveal/hide

### 第三阶段：内容重建

- 写新的开局场景
- 写新的地点树
- 写探索与解锁链
- 写修理厂主线与委托链

### 第四阶段：UI 对接

- 地图按地点树显示
- 底部左侧手牌
- 底部右侧物品栏
- 当前行动只显示需求
- 消息区在右侧显示


## 最终判断标准

方案是否达标，按下面五条判断：

- 内容作者能自然地写地点树和行动，而不需要理解过多底层细节
- 引擎只保留少量稳定原子概念
- 上层玩法主要通过组合表达，而不是通过新增引擎特例表达
- 运行时状态变化都经过统一 API
- 内容错误在加载期尽可能 assert 出来
