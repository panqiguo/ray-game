# Encounter DSL 设计方案 v4 Patch

这份 patch 不重写 v3 的整体方向，只修补会直接影响实现落地的四个关键缺口：

1. `scene` 需要稳定 id
2. 动态树中的 action 需要实例级 handle，而不是单个字符串 id
3. `react` 需要明确的防循环与收敛策略
4. `phase` 不能被简单视为“默认多余”，需要给出更稳的使用准则

v3 里其余大方向保持不变：

- `store` 持久化事实
- `view` 动态重算 scene tree
- `action` 修改 store
- `react` 做动作后的自动推进
- Lisp / S-expression 作为主 DSL

---

## 1. Patch 目标

v3 已经把 encounter 的核心模型收敛到了正确方向，但如果直接按 v3 实现，会在下面几个地方碰到具体问题：

- 节点和动作缺少稳定身份，动态树运行时无法可靠寻址
- `resolve_action(program, store, action_id, ...)` 无法区分同模板动作在不同节点中的实例
- `react` 允许写出互相翻转的规则，可能导致结算死循环
- 对 `phase` 的描述过于乐观，容易诱导作者把“不可逆推进事实”写成可推导条件

这份 patch 的目标就是把这些边界补齐，但不改变 v3 的作者体验主轴。

---

## 2. Patch A：`scene` 必须有稳定 id

### 2.1 为什么必须改

v3 中的 `scene` 语法是：

```lisp
(scene <title> <desc>
  ...)
```

这对“写内容”看起来很顺，但对运行时不够。

动态重算 tree 时，运行时需要稳定身份来做这些事：

- 父子映射
- clock display 锚定
- 当前选择保持
- 测试断言
- 调试输出
- 同标题节点并存时的区分

所以节点身份不能依赖玩家可见文案。

### 2.2 改法

把 `scene` 改成显式带 id：

```lisp
(scene <scene-id> <title> <desc>
  ...)
```

例如：

```lisp
(scene pressure_unarmed
  "徒手受压"
  "打手把你逼在墙边。你得先决定，是稳着反顶、直接狠狠干、还是冒险把折刀夺到手。"
  ...)
```

### 2.3 语义约束

- `scene-id` 在 encounter 内全局唯一
- `scene-id` 是作者可控的稳定符号，不参与本地化
- 玩家可见 title/desc 允许随文案迭代变化，不影响运行时身份

### 2.4 对 v3 的最小替换

原：

```lisp
(scene "徒手受压" "描述..." ...)
```

改：

```lisp
(scene pressure_unarmed "徒手受压" "描述..." ...)
```

---

## 3. Patch B：Action 需要实例级 handle，而不是字符串 id

### 3.1 为什么 v3 的 action id 不够

v3 的策略是：

- `defaction` -> 定义级 id
- 内联 action -> `scene_title_hash + action_index`

这个方案在动态树里不稳，原因有三类：

1. 同一个 `defaction` 可以同时出现在多个 scene 中
2. title/desc 改动会让内联 action id 漂移
3. 单个字符串 id 无法表达“这是树上哪一个动作实例”

换句话说，运行时真正需要的不是“动作定义 id”，而是“当前渲染结果里的动作实例句柄”。

### 3.2 改法

把运行时选择对象从 `action_id: str` 改成 `ActionHandle`。

建议形态：

```python
@dataclass(frozen=True)
class ActionHandle:
    scene_path: tuple[str, ...]
    slot_index: int
    template_ref: str | None
    inline_key: str | None
```

说明：

- `scene_path`
  标识这个动作出现在哪条渲染路径上，例如 `("root", "pressure_unarmed")`
- `slot_index`
  是该 scene 的 `actions` 列表中求值后的稳定位置
- `template_ref`
  若动作来自 `defaction`，记录其定义名
- `inline_key`
  若动作是内联定义，记录编译期稳定键

### 3.3 编译期和运行时如何分工

编译期：

- `defaction` 仍有定义名
- 内联 action 仍可生成稳定内部 key
- 这些用于模板查找和校验

运行时：

- 真正交给 UI 和 `resolve_action()` 的不是定义 id，而是 `ActionHandle`
- handle 由本次 render 产出，绑定到当前 tree 实例

### 3.4 接口修正

原 v3：

```python
render(program, store) -> SceneTree
resolve_action(program, store, action_id, check_result) -> StepResult
```

改为：

```python
render(program, store) -> RenderedEncounter
resolve_action(program, store, handle, check_result) -> StepResult
```

其中：

```python
@dataclass(frozen=True)
class RenderedEncounter:
    root: RenderedScene
    action_handles: dict[str, ActionHandle]


@dataclass(frozen=True)
class RenderedScene:
    scene_id: str
    title: str
    description: str
    shown_clock_ids: tuple[str, ...]
    actions: tuple["RenderedAction", ...]
    children: tuple["RenderedScene", ...]


@dataclass(frozen=True)
class RenderedAction:
    handle: ActionHandle
    title: str
    description: str
    check: object | None
```

说明：

- UI 不需要自己再拼 action id
- `handle` 是当前渲染快照的一部分
- 同一 `defaction` 出现在两个节点里时，也能自然区分

### 3.5 对 DSL 作者的影响

无影响。

这是纯运行时/编译器层修正，不会增加内容语法复杂度。

---

## 4. Patch C：`react` 需要明确的防循环策略

### 4.1 为什么 v3 当前语义不够

v3 的 `react` 语义是：

- 条件满足则执行
- 如果 store 有变化，就从第一条重新检查
- 直到没有规则触发，或 encounter 结束

这个语义本身没错，但少了一个重要限制：

**没有定义什么样的 `react` 是合法的、可收敛的。**

于是很容易写出这种规则：

```lisp
(reacts
  ((flag a) (set b true))
  ((flag b) (set a false)))
```

或者更隐蔽的 clock 来回推拉规则。

### 4.2 建议的策略

采用“三层防护”：

1. 设计约束：鼓励 `react` 只做单调推进
2. 编译期校验：拒绝明显的非收敛规则
3. 运行时保护：超过硬上限立即 assert 失败

### 4.3 设计约束

推荐把 `react` 的用途限制为：

- 结束 encounter
- 推进不可逆阶段变量
- 设置 once-only flag
- 基于阈值同步派生事实

不推荐在 `react` 里写：

- 两个状态之间反复切换
- 对同一个变量的来回增减
- 依赖随机性
- 依赖玩家输入

### 4.4 编译期校验

编译器至少应做下面几类 assert：

1. 同一条 `react` 中，不能同时读写同一个布尔/枚举变量并可能翻转
2. 对 `phase` 这类枚举推进，若声明为单调域，则只允许沿预定义顺序前进
3. 对 `clock`，若某条 `react` 会降低另一个也会触发 react 的 clock，需要显式报高风险
4. 若两条规则互相写入对方的触发条件，且不存在单调上界，应拒绝编译

第一版不必做完整形式化证明，但至少要覆盖“明显危险”的环。

### 4.5 运行时保护

运行时增加硬上限：

```python
MAX_REACT_STEPS = 64
```

语义：

- 每次 `resolve_action()` 进入 react 阶段时，从 0 开始计数
- 每触发一条 rule，计数 +1
- 超过上限立即 assert，报 encounter 设计错误

这是最后一道保险，不替代编译期校验。

### 4.6 v4 推荐表述

把 v3 的 react 语义段落改成：

```text
react 规则必须设计为可收敛。
推荐只表达单调推进、结束条件和 once-only 同步。
编译器会拒绝明显的循环依赖，运行时也会设置 react 步数硬上限。
```

---

## 5. Patch D：`phase` 的使用准则需要更稳

### 5.1 为什么不能简单说“默认不用 phase”

v3 里对 thug 的判断在当前例子里是成立的：

- `initiative < 2` 时是压制阶段
- `initiative >= 2` 后进入收尾阶段

但这个结论有前提：

- 阶段真的能由当前数值唯一推导
- 数值不会因为其他效果再次回退
- 设计上不需要记忆历史路径

一旦 encounter 更复杂，这些前提就可能失效。

例如：

- 玩家已经“进入第二幕”，但某个效果又把 `initiative` 打回 1
- 某个分支要求记住“你是否已经暴露过刀”
- 某阶段是不可逆推进，而不是由现值决定的可逆局面

这时如果不用显式 `phase`，view 会错误回退到早期局面。

### 5.2 更稳的准则

推荐把 v3 的表述改成：

**当阶段能由单调事实唯一推导时，可以省略显式 `phase`；凡是需要不可逆推进、记忆历史路径、避免回退，或对同一数值存在多重语义解释时，应把阶段作为显式 store 事实。**

### 5.3 推荐的经验法则

可以不用 `phase` 的情况：

- 纯阈值切换
- 阈值只会单向推进
- 没有历史依赖

应该显式引入 `phase` 的情况：

- 进入下一幕之后不允许回退
- 阶段受多个条件共同控制
- 阶段还承担叙事记忆作用
- 同一个 clock 在不同阶段语义不同

### 5.4 对 thug 的建议

thug 这个例子可以继续不显式存 `phase`，因为它目前确实能由数值直接分段。

但文档层面不应把它写成普适建议，更好的写法是：

```text
thug 只是一个“可以不用 phase”的例子，不是默认规则。
```

---

## 6. 汇总后的关键语法与接口

### 6.1 更新后的 `scene`

```lisp
(scene <scene-id> <title> <desc>
  (show_clocks <id> ...)
  (actions <action-expr> ...)
  (children <scene-expr> ...))
```

### 6.2 更新后的运行时接口

```python
render(program, store) -> RenderedEncounter
resolve_action(program, store, handle, check_result) -> StepResult
```

### 6.3 更新后的 `react` 规则要求

```text
react 必须可收敛。
编译期拒绝明显循环，运行时设置硬上限。
```

### 6.4 更新后的 `phase` 指南

```text
phase 不是默认多余，也不是默认必需。
是否引入 phase，取决于阶段是否能由单调事实稳定推导。
```

---

## 7. 建议如何合入 v3

如果把这份 patch 合回 v3，我建议只改下面四块：

1. 第 3.5 节 `scene` 语法
2. 第 5.3 / 5.4 节运行时接口与 action id 方案
3. 第 3.4 节 `react` 语义
4. 第 7 节关于 `phase` 的设计决策记录

这样改动最小，也不会把 v3 已经形成的整体风格打散。

---

## 8. 最终判断

v3 的大方向已经足够好，不需要推翻重来。

这份 patch 的意义不是重新设计语言，而是把它从“思路可行”推进到“实现边界清楚、不会在运行时细节上翻车”。

如果这四个点补上，v3 就可以作为一个很扎实的最小可行 encounter DSL 方案继续推进。
