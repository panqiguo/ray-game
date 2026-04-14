# 当前语言边界

这是现在项目里**真实实现**的 encounter 语言。它长得像 Lisp，但不是完整 Scheme；更准确地说，它是一门 **统一 expr + 强 schema IR 构造** 的 encounter 语言。

## 先记 5 句

1. 所有代码都是 S-expression。
2. 裸 symbol 永远先 lookup；quoted symbol 永远是字面量。
3. `store` 是“名字绑定值”。
4. `if / when / cond` 负责选择；`scene / action / reacts` 负责组织 IR。
5. 目标不是“自由写脚本”，而是构造 encounter，然后在运行时根据 store 重算场景树。

如果这 5 句已经够你用，可以直接去看模板和示例。下面只保留真正容易绊倒人的边界。

## 一眼看懂的最小模型

顶层只需要记住：

- `include`
- `def`
- `defmacro`
- `encounter`

文件最后一个值必须是 `encounter`。

最小 encounter 长这样：

```lisp
(include "enum-symbols.enc")

(encounter
  (id example_id)
  (title "标题")
  (desc "一句话说明这个 encounter。")

  (store
    (progress (clock "进度" 0 3))
    (phase 'intro))

  (reacts
    ((>= (clock-value progress) (clock-full progress))
     (finish success)))

  (view
    (scene
      (id root)
      (title "当前局面")
      (desc "玩家现在看到的画面。")
      (show-clocks progress)
      (actions)
      (children))))
```

## 真正需要记住的语法边界

### 1. `store` 是名字绑定值

- `(name (clock "标题" initial maximum))`：声明一个 clock
- `(name true/false)`：声明一个布尔 store 槽位
- `(name 'entry)`：声明一个枚举/阶段值
- `(name 1)`、`(name "text")`：声明普通标量初始值

`store` 中声明的名字会自动进入当前 encounter 环境：

- clock 名字在 `show-clocks` 里直接当 clock ref 用
- 非 clock 名字在 value / bool context 里会读当前 store 值
- 通用常量如 `low / reason / success / none / abort` 推荐来自 `(include "enum-symbols.enc")`
- 场景内部自己的阶段、路径、状态通常直接写 quoted symbol，例如 `'entry`、`'left`、`'calm`

### 2. symbol 规则只有一条

> 裸 symbol 先 lookup；quoted symbol 才是字面量。

例如：

```lisp
(= phase 'intro)
(set phase 'entry)
(show-clocks alert)
(finish success)
```

- `phase` / `alert` 都是 lookup 出来的名字
- `'intro` / `'entry` 是显式字面量
- `success` 是来自 `enum-symbols.enc` 的通用常量绑定

如果找不到某个裸 symbol，编译器会直接报错；如果你本来想写局部剧情字面量，就给它加 `'`。如果是项目里反复使用的通用常量，优先放到共享 include 文件里。

### 3. `when` 就是 `if ... nil`

```lisp
(when cond expr)
```

等价于：

```lisp
(if cond expr nil)
```

常见位置：

- `view`
- `children`
- `actions`
- `show-clocks`

### 4. `action` 是唯一的行动 form

`action` 现在可以组合这些字段：

- `title`
- `desc`
- `inputs`
- `before`
- `check`

其中：

- `before` 表示无条件前置效果
- `check` 表示这是不是一个需要手牌检定的行动
- `inputs` 表示这个行动还需要哪些资源 / 物品 / 手牌输入

### 5. 宏是轻量模板，不是完整 Scheme 宏

`defmacro` 现在是最小 template macro：

- 递归替换
- 支持 `quote`
- 不支持 quasiquote / unquote
- 不提供完整 Lisp 宏语义

它适合结构复用，不适合复杂元编程。

## 推荐心智

- `scene` 负责返回树节点
- `children` 里挂子地点
- `actions` 里挂动作
- `reacts` 负责动作后自动推进
- `store` 只保存事实，不保存当前 scene
- `store` 里的名字和 `def` 的名字都会进入同一个 lookup 心智：先 lookup，再由上下文决定能不能用

## 最常见的错误就 3 类

1. 把字面量写成裸 symbol  
   如果你想写阶段、路径、结局这种局部剧情字面量，请直接写 `'entry`、`'left`、`'calm`。只有 `success`、`abort`、`low`、`reason` 这种通用常量，才推荐从共享 include 文件拿名字。

2. 把 clock 当普通值直接用  
   如果你要读 clock 当前值，请写 `(clock-value alert)`，不要直接把 `alert` 放进比较里。

3. 把对象 form 当普通脚本  
   `scene` / `action` 是强 schema 对象构造，不是随意组合副作用的脚本块。

## 最后只记一句

这门语言最好用的心智是：

> 用少量 expr（`if/when/cond`）去选择，  
> 用少量 schema form（`store/scene/action/reacts`）去组织 IR。
