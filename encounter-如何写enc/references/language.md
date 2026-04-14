# 当前语言边界

这是现在项目里**真实实现**的 encounter 语言，不是理想中的完整 Lisp。

## 它是什么

- 一门 **统一 expr + 强 schema IR 构造** 的 encounter 语言
- 语法表面是 **Lisp/S-expression**
- 目标是构造 encounter，再在运行时根据 store 重算场景树

## 它不是什么

- 不是完整 Scheme
- 不是通用 Lisp 方言
- 不是“任意 list 都能自由求值”的脚本语言

## 顶层真正支持的 form

- `include`
- `def`
- `defmacro`
- `encounter`

文件最后一个值必须是 `encounter`。

### `include`

`include` 只在顶层可用：

```lisp
(include "black_night/yard.enc")
```

语义是：把另一个文件里的顶层 form 并进当前文件。  
第一版限制：

- 路径必须是字符串字面量
- 路径相对当前文件解析
- 会直接按顶层 form 简单拼接
- 允许继续 include
- 整个展开后的文件最终必须且只能有一个 `encounter`

## 表达式里真正支持的 form

- `if`
- `when`
- `cond`
- `and`
- `or`
- `not`
- `= < <= > >=`
- `+ - min max`
- `clock-value`
- `clock-full`
- `clock-half`
- `quote`

## 对象构造 form

- `scene`
- `action`

它们不是普通 Lisp 值构造器，而是**按固定字段 schema 解释**的 special form。  
其中行动现在只有一个核心 form：`action`。需要检定时，在 `action` 里面写 `(check ...)` 子块。

## `when` 的统一语义

`when` 现在统一视为 expr 糖：

```lisp
(when cond expr)
```

等价于：

```lisp
(if cond expr nil)
```

只要当前位置允许 `nil` 作为“空结果”，就可以用 `when`。常见位置：

- `view`
- `children`
- `actions`
- `show-clocks`

## action 的核心字段

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

### inputs 语法

```lisp
(inputs
  (resource money 20 "金币")
  (item car_key 1 "车钥匙" false)
  (card any "手牌"))
```

- `resource`：资源需求
- `item`：物品需求，最后一个布尔值可选，表示是否消耗，默认 `true`
- `card`：额外手牌需求，目前支持 `any` 和 `negative`

## 宏系统边界

`defmacro` 现在是最小 template macro：

- 递归替换
- 支持 `quote`
- 不支持 quasiquote / unquote
- 不提供完整 Lisp 宏语义

所以它更适合结构复用，不适合复杂元编程。

## `def` 现在能绑定什么

`def` 可以绑定任意 expr 值。当前最实用的几类是：

- 一个完整的 `scene`
- 一个完整的 `action`
- 一个普通 expr

## 最重要的字面量规则

### 字符串

```lisp
"描述文本"
```

### 数字 / 布尔

```lisp
1
true
false
```

### symbol 字面量

必须显式 quote：

```lisp
'entry
'left
'success
```

不要再写裸的：

```lisp
entry
left
success
```

未绑定 symbol 现在会直接报错。

## 推荐心智

- `scene` 负责返回树节点
- `children` 里挂子地点
- `actions` 里挂动作
- `reacts` 负责动作后自动推进
- `store` 只保存事实，不保存当前 scene

## 错误信息

编译/校验报错会尽量带 encounter 上下文，例如：

- `binding foo`
- `view.actions[2]`
- `scene root.children[1]`
- `encounter.store[0]`

优先顺着这些路径修 DSL，不要先猜运行时。

## 哪些在求值，哪些在组织 IR

这门语言最容易混淆的一点是：它表面像 Lisp，但整体目标不是“直接执行脚本副作用”，而是**构造 encounter 的内部对象（IR）**。

### 主要在求值的 form

这些 form 的职责是“算出当前该用哪个值/哪个对象”：

- `if`
- `when`
- `cond`
- `and`
- `or`
- `not`
- `= < <= > >=`
- `+ - min max`
- `clock-value`
- `clock-full`
- `clock-half`
- `quote`
- `def` 引用出来的绑定

它们更像是在“选择”和“组合”。

### 主要在组织 IR 的 form

这些 form 的职责是“声明 encounter 的对象结构”：

- `encounter`
- `store`
- `clock`
- `flag`
- `value`
- `scene`
- `action`
- `inputs`
- `before`
- `ok`
- `partial`
- `fail`
- `reacts`
- `show-clocks`
- `actions`
- `children`
- 各种 effect form：`set`、`finish`、`health`、`money`、`reset-hand`、`(alert +1)` 这类

它们更像是在“定义对象”，不是立刻把游戏状态改掉。

### 最实用的判断法

可以这样快速区分：

- 如果一个 form 主要在回答“现在该选哪个分支/值/节点”，它更偏**求值**
- 如果一个 form 主要在回答“这个 encounter 节点长什么样、这个动作结算长什么样”，它更偏**IR**

### 一个直观例子

下面这段里：

```lisp
(def bedroom_act
  (if (= entry_method 'front)
    bedroom_front_scene
    bedroom_window_scene))
```

- `if` 和 `=` 在求值
- `bedroom_front_scene` / `bedroom_window_scene` 这两个绑定，指向的是已经定义好的 scene IR

而这段：

```lisp
(scene
  (id yard_root)
  (title "院墙缺口")
  (children ...))
```

主要是在组织 scene IR。
