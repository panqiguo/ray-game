# 《乌鸦的去向》工程方案 v3

## 1. 文档目标

本文档用于把当前 Demo 的讨论结果落实为一个可执行的工程方案。

目标不是先做一个通用游戏框架，而是先完成一个**可完整玩通的原型级垂直切片**，用于验证 [`design.md`](/Users/usr/Documents/python/ray-game/design.md) 中定义的核心玩法问题：

1. 手牌匹配与非匹配选择是否产生有意义的决策
2. 牌库污染是否形成可感知的情绪曲线
3. 城市整备是否真实影响任务表现
4. 成长系统是否让玩家逐步塑造自己的解题方式

当前阶段的优先级：

1. 可读性
2. 简单但好用
3. 规则正确
4. 迭代速度
5. 再考虑长期泛化

## 2. 工程原则

### 2.1 总体原则

- 整个工程就是一个游戏工程，只保留一个正式包。
- 当前阶段不做通用引擎，不做过早抽象。
- 先做垂直切片，再扩内容，不先横向铺满系统。
- 强约束优先，非法内容和非法状态尽早失败，不做宽松兼容。
- 规则层尽量纯逻辑，UI 层不直接改核心状态。

### 2.2 数据策略

- 内容数据当前阶段优先放在 Python 模块中，而不是 JSON。
- 内容定义保持数据形态，不把流程逻辑硬编码进 screen 或 app 主循环。
- 使用 `dataclass`、常量表、少量 `TypedDict` 提高可读性与可修改性。
- 等内容稳定且数量明显增大后，再考虑把纯静态表迁移到 JSON。
- 条件原语、效果原语、结局判定核心逻辑继续保留在 Python 中。

### 2.3 命名与文本原则

- 内部逻辑、类型、字段名使用英文。
- 玩家可见文本使用中文。
- 数据 key 使用英文，value 可以使用中文。

### 2.4 UI 原则

- UI 以代码驱动，使用 IMGUI 风格。
- 按 screen 组织，而不是过早搭建复杂组件体系。
- 重点保证排版清晰、状态可读、信息反馈直接。

## 3. 包与目录方案

正式代码统一放在 `src/raygame/` 下。

```text
src/raygame/
  main.py
  app.py
  constants.py
  rendering.py

  model/
    enums.py
    defs.py
    state.py
    commands.py
    events.py

  content/
    cards.py
    city.py
    mission_slaughterhouse.py
    growth.py
    endings.py
    validate.py

  rules/
    rng.py
    deck.py
    judgment.py
    conditions.py
    effects.py
    progression.py
    ending_rules.py

  screens/
    router.py
    city_screen.py
    mission_screen.py
    ending_screen.py
    widgets.py
    debug_panel.py
```

目录职责说明：

- `model/`：核心数据结构和运行时状态，不写具体玩法规则。
- `content/`：玩法内容定义与内容校验。
- `rules/`：纯规则计算、状态推进、条件和效果应用。
- `screens/`：IMGUI 界面与交互展示。

## 4. 运行时结构

### 4.1 Def / State 分层

必须明确区分静态定义和运行时状态。

静态定义放在 `model/defs.py`，例如：

- `CardDef`
- `ActionMethodDef`
- `ActionPointDef`
- `LocationDef`
- `GrowthDef`
- `EndingDef`

运行时状态放在 `model/state.py`，例如：

- `DeckState`
- `ClockState`
- `ResourceState`
- `MissionState`
- `RunState`
- `GameState`

这样可以清楚地区分：

- 一张牌“是什么”
- 当前 run 中“哪一张牌被升级过”
- 某个行动点“定义上存在”
- 当前任务里“它是否已经完成或解锁”

### 4.2 Command -> Apply -> Event

当前阶段保留这个边界，但不搭复杂事件框架。

推荐形式：

- UI 发出命令
- 规则层统一处理命令
- 规则层返回状态变化和少量事件供 UI 演出

典型命令：

- `PlayCard`
- `ConfirmAction`
- `UseConsumable`
- `EndDay`
- `PushThrough`
- `EnterMission`

典型事件：

- `CardPlayed`
- `ClockAdvanced`
- `StressOverflowed`
- `ActionResolved`
- `EndingReached`

约束：

- UI 不直接写业务状态
- Screen 不自行结算玩法逻辑
- 所有核心推进都收敛到规则层

### 4.3 RNG 统一入口

所有随机行为统一走 `rules/rng.py`：

- 抽牌
- 洗牌
- 掷骰

要求：

- 每局记录 seed
- 尽量保留简短 action log
- 所有随机入口可复现

这是调试和测试的基础设施，不后置。

## 5. 内容组织策略

### 5.1 为什么当前阶段不用 JSON

原型阶段内容变化快，且设计中存在大量条件联动：

- 持有线索才显示行动点
- 钟表达到阈值才触发变化
- 成功后解锁其他行动
- 结局由多个变量组合决定

这类内容如果过早塞进 JSON，会迅速演变成：

- 大量字符串 key
- 嵌套结构过深
- 条件与效果解释器变复杂
- 内容可读性下降

因此当前阶段优先使用 Python 模块表达内容。

### 5.2 内容文件建议

- [`content/cards.py`](/Users/usr/Documents/python/ray-game/content/cards.py)：基础牌、负面牌、消耗品相关牌定义
- [`content/city.py`](/Users/usr/Documents/python/ray-game/content/city.py)：城市地点、行动点、第 1 天到第 3 天开放内容
- [`content/mission_slaughterhouse.py`](/Users/usr/Documents/python/ray-game/content/mission_slaughterhouse.py)：屠宰场任务内容
- [`content/growth.py`](/Users/usr/Documents/python/ray-game/content/growth.py)：成长节点定义
- [`content/endings.py`](/Users/usr/Documents/python/ray-game/content/endings.py)：结局定义和展示文本
- [`content/validate.py`](/Users/usr/Documents/python/ray-game/content/validate.py)：启动时统一校验

注：这里路径表示目标文件位置，当前仓库尚未创建对应文件。

### 5.3 Condition / Effect 小词表

内容是数据驱动，但不做通用 DSL。

第一版仅支持设计实际需要的小词表。

建议首批 condition：

- `has_clue`
- `clock_at_least`
- `flag_set`
- `action_done`
- `mode_is`

建议首批 effect：

- `gain_money`
- `add_stress`
- `lose_health`
- `insert_card`
- `remove_card`
- `advance_clock`
- `freeze_clock`
- `unlock_action`
- `set_flag`
- `give_item`
- `fail_run`

原则：

- 内容只能组合有限原语
- 复杂玩法逻辑仍写在 Python 规则层
- 不为“理论通用性”提前扩展原语集

## 6. 核心模块职责

### 6.1 `model/`

- `enums.py`：花色、风险等级、模式、结果类型等枚举
- `defs.py`：静态定义数据结构
- `state.py`：运行时状态数据结构
- `commands.py`：UI 发往规则层的命令模型
- `events.py`：规则层给 UI 的反馈事件模型

### 6.2 `rules/`

- `rng.py`：种子、骰子、洗牌与可复现随机接口
- `deck.py`：抽牌、弃牌、洗牌、牌库循环、污染牌塞入和移除
- `judgment.py`：行动值计算、判定表映射、结果输出
- `conditions.py`：内容条件求值
- `effects.py`：效果应用
- `progression.py`：天数推进、任务推进、硬撑、成长应用
- `ending_rules.py`：结局变量收集与结局判定

### 6.3 `screens/`

- `router.py`：城市、任务、结局页面切换
- `city_screen.py`：城市地图、场所层、行动面板入口
- `mission_screen.py`：任务蓝图、区域、行动点、警报与行动结算入口
- `ending_screen.py`：结局展示
- `widgets.py`：HUD、卡牌、钟表、骰面条等通用绘制辅助
- `debug_panel.py`：调试入口

## 7. 里程碑计划

### M1：工程切换与骨架建立

目标：从示例工程切到正式游戏工程。

任务：

- 新建 `src/raygame/`
- 把脚本入口切到新包
- 建立最小 `GameState`
- 建立 `defs` / `state` / `rng` / `validate_content`
- 迁移最少量 raylib 启动壳

验收标准：

- 新入口可运行
- 程序能进入空白或占位主界面
- 启动时能加载最小内容并通过校验

### M2：最小垂直切片

目标：尽快验证核心循环，而不是先铺完整城市和任务。

只做最小内容：

- 1 个城市地点
- 2 个城市行动
- 1 个任务区域
- 2 个任务行动点
- 1 张负面牌
- 1 个消耗品
- 1 个结局
- 2 个钟表

需要跑通：

- 抽牌
- 选行动方式
- 选手牌
- 实时显示行动值和六面结果
- 掷骰
- 应用风险与代价
- 钟表推进
- 进入任务
- 通关或失败

验收标准：

- 玩家能完整结束一局
- 核心循环已经可体验

### M3：核心规则闭环

目标：补全玩法系统的基础规则。

任务：

- 完成抽牌、弃牌、洗牌、重洗
- 完成负面牌塞入和清理
- 完成判定表
- 完成风险层与判定层分离
- 完成 Stress 满载处理
- 完成硬撑机制

验收标准：

- 规则层可以脱离 UI 进行测试
- 边界情况有明确处理

### M4：城市整备完整化

目标：实现 2 到 3 天的完整城市整备。

任务：

- 完成两层城市交互
- 完成钱、烟卷、买醉、诊所、整理思绪
- 完成线索 A / B / C
- 完成宿醉与乌鸦时间钟递减
- 完成第一版侦探独白模板

验收标准：

- 玩家能稳定玩完城市阶段
- 城市选择会实质影响任务前状态

### M5：屠宰场任务完整化

目标：实现完整任务流程。

任务：

- 完成外围、走廊、冷库三段区域
- 完成 Heat 联动
- 完成屠宰场警报钟
- 完成灯控室、证据台、暗门、账本、头目、乌鸦相关联动

验收标准：

- 任务完整可玩
- 至少存在 3 条明显不同路径

### M6：成长与结局

目标：实现玩法塑形能力和结局分支。

任务：

- 完成 `记案本`
- 完成 `预先踩点`
- 完成 `偏执专长`
- 完成 `冷静习惯`
- 完成 `老伤钝化`
- 完成 `闪回`
- 完成结局变量收集与结算

验收标准：

- 至少 3 个不同结局可稳定触发
- 至少 2 个成长明显改变打法

### M7：打磨与验证

目标：提升可玩性和调试效率。

任务：

- 完成 HUD 和骰面反馈
- 完成钟表变化演出
- 完成调试面板
- 调整数值与风险反馈

验收标准：

- 支持快速调试
- 支持稳定试玩

## 8. 测试与调试策略

### 8.1 优先测试范围

规则层优先覆盖以下内容：

- 判定表 1 到 6 的结果分布
- 行动值边界处理
- 抽牌与重洗循环
- 负面牌打出规则
- 风险结算
- Stress 满载处理
- 硬撑规则
- 线索联动
- Heat 联动
- 结局判定

### 8.2 调试面板要求

`screens/debug_panel.py` 建议尽早加入，至少支持：

- 加钱
- 加 Stress
- 减 Health
- 塞入负面牌
- 解锁线索
- 推进或回退钟表
- 固定 seed
- 直接进入任务

### 8.3 内容校验要求

启动时统一执行 `validate_content()`，发现以下问题直接失败：

- 引用不存在的卡牌、地点、线索、行动点
- 非法花色
- 非法风险等级
- 不合法的条件原语或效果原语
- 不合法的结局依赖关系

## 9. 包迁移策略

迁移策略需要明确执行，避免旧新两套并行太久。

执行规则：

1. 从 M1 开始，所有新代码只写进 `src/raygame/`
2. `pyproject.toml` 的脚本入口切到 `raygame`
3. 原 `src/raygame_demo/` 只作为短期参考
4. M2 跑通后删除 `src/raygame_demo/`

这意味着：

- 当前工程不再被视为“raylib 示例项目”
- 而是正式切换为“游戏原型项目”

## 10. 当前阶段明确不做

为了防止计划膨胀，当前阶段不做以下内容：

- 通用事件编辑器
- ECS
- 多章节通用剧情框架
- 可视化数据编辑器
- 多槽位正式存档系统
- 全量 JSON / DSL 化
- 复杂动画系统
- 正向状态牌体系

## 11. 首批落地建议

若按 v3 直接开始开发，建议第一批工作顺序如下：

1. 新建 `src/raygame/`
2. 切脚本入口
3. 建立最小 `GameState`
4. 建立 `content/cards.py`
5. 建立最小城市行动内容
6. 跑通一次“抽牌 -> 选行动 -> 掷骰 -> 结算”

## 12. 总结

v3 的核心决策如下：

- 单一正式包
- 内容先放 Python 模块
- 规则与 UI 分层，但不过度框架化
- 小词表条件和效果原语
- 强校验与 assert 优先
- 先做垂直切片，再扩完整内容

这是当前阶段最符合项目目标、可读性要求和迭代效率的工程方案。
