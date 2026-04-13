# 当前语言边界

这是现在项目里**真实实现**的 encounter 语言，不是理想中的完整 Lisp。

## 它是什么

- 一门 **Lisp/S-expression 表皮**
- 但本质是 **强 schema 的 encounter DSL**
- 目标是构造 encounter，再在运行时根据 store 重算场景树

## 它不是什么

- 不是完整 Scheme
- 不是通用 Lisp 方言
- 不是“任意 list 都能自由求值”的脚本语言

## 顶层真正支持的 form

- `def`
- `defmacro`
- `encounter`

文件最后一个值必须是 `encounter`。

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
- `check`

它们不是普通 Lisp 值构造器，而是**按固定字段 schema 解释**的 special form。

## 宏系统边界

`defmacro` 现在是最小 template macro：

- 递归替换
- 支持 `quote`
- 不支持 quasiquote / unquote
- 不提供完整 Lisp 宏语义

所以它更适合结构复用，不适合复杂元编程。

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
