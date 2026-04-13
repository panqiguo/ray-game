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

## 工作流

1. 先列事实，再写场景。
2. 先搭大幕分支，再填具体动作。
3. 优先把“局面变化”写清楚，再调数值。
4. 长 encounter 先按模板写，不要自由发挥括号结构。

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

## 产出顺序

默认按这个顺序输出：

1. 剧本到系统的映射
2. `store`
3. `reacts`
4. `view` 主结构
5. 每个 scene 的 actions/checks
6. 如有需要，给出 `.enc` 草稿或直接修改文件

## 写作原则

- 保持数据驱动
- 保持 scene tree 心智
- 不回退到静态状态机
- 不为了实现方便发明新语法
- 优先让 scene 结构清楚，再追求文案华丽
