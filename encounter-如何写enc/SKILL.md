---
name: encounter-script-to-scene
description: 把已经整理好的 encounter 剧本或分幕设计稿，翻译成 ray-game 里的 `.enc` 脚本。适用于设计 store、scene tree、actions/checks、reacts，并在需要时直接编写或重构 `src/raygame/encounters/*.enc`。
---

# Encounter Script To Scene

这个 skill 用在“剧本已经相对清楚，现在要把它落实成 `.enc`”的阶段。

如果用户现在只有一个模糊点子，还没整理成分幕剧本，先用“如何写剧本”那个 skill。

## 目标

把剧本翻译成：

- `store`
- `reacts`
- `view`
- `scene / children / actions`
- `action / check / before / outcomes`

并保持“返回一棵场景树”的心智：

- 地点可以包含地点
- 地点可以包含行动
- 同一时刻的 encounter 直接返回当前树，而不是靠进入/返回动作去模拟地点

## 强约束

- 把 `.md` / 剧本转成 `.enc` 时，优先参考现有示例和模板：`teach_thug.enc`、`black_night.enc`、`references/templates.md`、`references/examples.md`
- 不要先读底层实现或旧设计材料来“猜语法”
- 只有在校验失败、或不确定某个 form 是否真实受支持时，才去看实现

## 工作流

1. 先列事实，再写场景。
2. 先搭大幕分支，再填具体动作。
3. 优先把“局面变化”写清楚，再调数值。
4. 长 encounter 先按模板写，不要自由发挥括号结构。

## 固定转换流程

把剧本/Markdown 转成 `.enc` 时，默认按这 6 步做：

1. 提取幕：先写清楚有哪几幕，每一幕的目标、阻碍、结束条件是什么。
2. 提取事实：把持续变化的量放进 `clock`，一次性真假放进 `flag`，阶段/路径记忆放进 `value`。
3. 提取树：为每一幕确定 root scene、子地点、各地点下的行动，不要用“进入/返回”动作模拟地点。
4. 提取方法：把玩家解决问题的方法写成 `action` / `check`，优先保证每个关键地点至少有两种方法。
5. 提取自动推进：把切幕、成功、失败、局面自动收束写进 `reacts`。
6. 落地接线：写入 `.enc`、接入 `registry.py`、补游戏内入口，独立侦探任务默认接到告示板。

## 告示板接入步骤

如果这是独立侦探任务，且用户没指定别的入口，默认按这几步接入告示板：

1. 在 `registry.py` 注册新的 encounter 文件。
2. 找到告示板地点的定义位置。
3. 给告示板添加一个“开始该任务”的 action。
4. 让这个 action 进入对应 encounter。
5. 校验后确认玩家确实能从告示板进入该任务。

## 核心映射

- 持续推进量：`clock`
- 一次性真假事实：`flag`
- 阶段/历史记忆：`value`
- 自然推进/自动收束：`reacts`
- 当前画面和可做的事：`scene`
- 玩家方法：`action` 或 `check`

## 语言心智

这门语言不是“任意副作用脚本”，而是“用少量求值来组织 IR”：

- `if / when / cond / and / or / not / clock-value` 这些主要在**求值**
- `scene / action / check / ok / partial / fail / effects` 这些主要在**声明和组织 IR**
- 写 `.enc` 时，优先把自己当成在“组装 encounter 对象树”，不是在“随便写 Lisp 程序”

## 必须遵守的写法

- clock 当前值用 `(clock-value ...)`
- clock 上限用 `(clock-full ...)`
- 枚举/阶段/结局字面量用 quoted symbol，例如 `'entry`、`'left`、`'success`
- 条件出现某个子节点，优先用 `(when cond expr)`
- 只有明确需要两个分支时才用 `(if cond a b)`
- `before` 只写动作前置效果
- `ok / partial / fail` 后面直接平铺 effects
- `show-clocks` / `actions` / `children` 里，每一项都应该是一个表达式

## 先看模板

遇到下面这些情况，先读参考文件，不要直接生成：

- 需要从零开始写 `.enc`
  读 [references/templates.md](references/templates.md)
- 需要一个复杂树状样例或错误对照
  读 [references/examples.md](references/examples.md)
- 需要知道“这门语言现在到底支持什么”
  读 [references/language.md](references/language.md)
- 需要知道“哪些 form 在求值，哪些 form 在组织 IR”
  也读 [references/language.md](references/language.md)

## 什么时候需要看实现

默认不要先钻 `runtime.py` / `defs.py` / `sexp.py`。只有下面几种情况才去看：

- `validate_content()` 或 encounter 校验报错，需要定位真实受支持的语法边界
- 不确定某个 form、字段名、字面量规则是否已经实现
- registry、入口接线、UI 表现需要和现有代码对齐

如果只是“从剧本生成一个新 encounter”，优先靠语言参考、模板和现有 `.enc` 示例完成。

## 产出顺序

默认按这个顺序输出：

1. 剧本到系统的映射
2. `store`
3. `reacts`
4. `view` 主结构
5. 每个 scene 的 actions/checks
6. 写入 `.enc`，并接入 `registry.py`
7. 检查游戏内入口；如果这是独立侦探任务且用户没指定别的入口，默认接到告示板

## 写作原则

- 保持数据驱动
- 保持 scene tree 心智
- 不回退到静态状态机
- 不为了实现方便发明新语法
- 优先让 scene 结构清楚，再追求文案华丽
- “完成”不只等于文件能编译；默认还要能从游戏里进入
- 设计 actions 时，默认检查是否需要一个“休息/调整/重抽”类动作，让玩家能主动换节奏
