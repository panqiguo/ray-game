# QA Guide For Refactored Game

本文件面向两类 QA：

1. 人工测试工程师
2. 使用大模型辅助探索式测试的工程师

目标不是证明“游戏能启动”，而是验证这次重构后：

- 核心规则仍然正确
- `game/` 新边界没有破坏旧行为
- UI 到 `dispatch()/event` 的关键链路可用
- SCM 内容、对话、交锋、时钟、结局仍然正常

---

## 1. 当前测试重点

这次重构后的高风险区，不是美术表现，而是这些结构性问题：

```text
1. 新的 game/ 模块与旧 progression 逻辑是否一致
2. command/event 路径是否和旧直调路径行为一致
3. pending resolution / reveal / auto-dismiss 是否仍正确
4. encounter / dialogue 生命周期是否被拆坏
5. SCM :key / :presentation 引入后是否影响旧内容
6. 热重载后中文字体字形集是否更新
```

QA 的主要任务是围绕这些点打回归。

---

## 2. 测试方式

建议分三层执行。

### A. 静态校验

适合每次提交后先跑一遍。

```bash
uv run python -m sincity.content.validate
uv run python -m compileall -q src/sincity
```

如果改了某个 SCM 文件，先补：

```bash
uv run python -m sincity.scm_lint src/sincity/scm/<file>.scm
```

如果 lint 报括号问题，再跑：

```bash
uv run python scripts/check_parens.py src/sincity/scm/<file>.scm
```

### B. 脚本级最小状态验证

适合验证运行时边界，没有现成测试框架也能做。

重点验证：

- `start_new_run()`
- `current_world_snapshot()`
- `dispatch()`
- `advance_pending_resolution()`
- `dialogue/encounter` 进入退出

建议每次改动后至少写 1 到 3 个临时脚本做 smoke。

示例：

```bash
uv run python - <<'PY'
from sincity.game.session import start_new_run
from sincity.game.queries import current_world_snapshot

state, rng = start_new_run(0)
world = current_world_snapshot(state)
print("locations", len(world.locations_by_id))
print("screen", state.screen)
PY
```

### C. 真机探索式测试

直接运行游戏：

```bash
uv run python -m sincity.main
```

重点测试输入、界面状态切换、结算、对话、热重载。

---

## 3. 冒烟测试基线

每次较大改动后，至少确认以下项目：

### 启动

- 游戏能正常启动
- 开局不会报异常
- 城市层能正常显示
- F1 调试面板可开关
- F5 或重置流程可正常开始新局
- Ctrl+R 重启进程后可重新进入游戏

### 内容加载

- `validate` 通过
- 起始城市地点能正常出现
- 地点标题、描述、动作文案正常
- 中文显示无缺字、无明显乱码

### 核心交互

- 点击地点可进入地点面板
- 点击动作可打开动作卡
- 可以放入手牌 / 需求输入
- 可以执行动作
- 执行动作后会进入 pending resolution
- 结算后结果、effect 文案、状态变化正确

### 生命周期

- 对话可进入、继续、结束
- 交锋场景可进入、执行动作、退出
- clock 会推进
- react 会在动作后触发
- 到达结局条件时能切到结局屏

---

## 4. 重点回归矩阵

下面这些是这次重构后最该测的模块。

### 4.1 `game/queries.py`

验证目标：

- 当前世界快照与旧行为一致
- 可见地点、可见动作、clock 数据正确

重点检查：

- 新开局时有哪些地点
- 满足条件前地点是否隐藏
- 满足条件后地点是否出现
- 交锋内 snapshot 是否只显示当前交锋内容

失败信号：

- 地点突然消失或多出
- 动作列表与之前不一致
- 错误地点上显示错误动作

### 4.2 `game/fields.py` / `game/effects.py`

验证目标：

- 权威状态写入正确
- effect 执行没有漏字段、写错字段、重复写入

重点检查：

- health / energy / money 变化
- world flag 设置
- faction relation 变化
- inventory 变化
- spirit/slot 升级
- clock shift

失败信号：

- 资源数值不对
- 同一 effect 执行两次
- 结算文案说改了，但状态没改

### 4.3 `game/actions.py` / `game/resolution.py`

验证目标：

- 动作装配、执行、pending、reveal、auto-dismiss 正常

重点检查：

- 直接动作 vs 判定动作
- reveal 动作
- 需要 energy slot 的动作
- 需要 requirement 输入的动作
- 执行后是否正确生成 `pending_resolution`
- 结算后是否正确落到 `last_resolution`

失败信号：

- 明明可执行却不能执行
- 明明没准备好却能执行
- 结果条不结束
- 结算后 UI 卡死在旧状态

### 4.4 `game/encounters.py`

验证目标：

- 交锋生命周期在拆分后仍然完整

重点检查：

- 从城市进入交锋
- 交锋中 action cycle 正常
- 压力/进度机制正常
- 交锋结束后返回正确 screen

失败信号：

- 交锋入口消失
- 交锋结束后回不到城市
- 交锋 root/location 错乱

### 4.5 `game/dialogues.py` + `dialogues/runtime.py`

验证目标：

- Ink 对话仍然能正确驱动状态
- external function 没有被重构破坏

重点检查：

- 开始对话
- 连续推进对话
- 选择分支
- 快速结束
- 对话中修改世界状态、进入交锋、结束游戏

失败信号：

- 选项点了没反应
- 对话结束不了
- 对话触发的状态变化丢失

### 4.6 `game/flow.py` / command/event

验证目标：

- 新 command 边界可用
- event 至少在关键链路上语义正确

重点检查：

- `OpenLocation`
- `OpenAction`
- `ExecuteAction`
- `ToggleEnergySlot`
- `ToggleRequirementSlot`
- `DismissPendingResolution`

失败信号：

- 通过 UI 点按钮正常，但通过 command 不正常
- `ActionStarted` 和 `ResolutionSettled` 时序错误
- event 有发出但状态没同步

### 4.7 `presentation/`

验证目标：

- presenter 分离后，显示内容不变

重点检查：

- 城市地点卡
- 动作卡
- slot 状态
- 标签、风险、花色
- pending / reveal 附件区域

失败信号：

- 标签错位
- 动作状态和真实可执行性不一致
- pending UI 与真实状态不一致

---

## 5. 推荐手工测试场景

建议每次版本至少过下面 8 类场景。

### 场景 1：开局基础流程

```text
启动游戏
→ 进入城市
→ 打开一个地点
→ 打开一个动作
→ 关闭动作
→ 再打开另一个地点
```

验证：

- modal 切换正常
- 同一个 action 的 toggle 行为正常
- 不会残留旧 assembly

### 场景 2：普通判定动作

```text
进入地点
→ 选择一个需要行动卡的动作
→ 放入行动卡
→ 执行动作
→ 等待结算
```

验证：

- pending 进度条出现
- 结算结果与资源变化一致
- pending 自动关闭条件正确

### 场景 3：需求输入动作

```text
进入需要 item/other input 的动作
→ 选中输入
→ 执行动作
```

验证：

- requirement slot 高亮正确
- 已放入输入可取消
- 不满足条件时不能执行

### 场景 4：reveal 动作

```text
执行一个 reveal 类型动作
→ 等待 reveal 文案展示
→ reveal 结束
```

验证：

- reveal 文本和标题正常
- pending → reveal → 恢复正常状态 的链路正确

### 场景 5：对话驱动状态变化

```text
进入对话
→ 推进几句
→ 选择一个分支
→ 结束对话
```

验证：

- 分支跳转正常
- 对话中触发的状态变化生效
- 对话结束后 UI 返回正确上下文

### 场景 6：交锋完整流程

```text
从城市进入交锋
→ 在交锋内做动作
→ 触发 clock / pressure 变化
→ 退出交锋
```

验证：

- 交锋中的地点和动作正确
- 交锋结束后 world 状态正确同步

### 场景 7：热重载

```text
启动游戏
→ 修改一个 SCM 文案
→ 等待热重载
→ 查看界面
```

验证：

- 不重启进程即可生效
- 新中文字符正常进入字形集
- 不出现缺字或空白方块

### 场景 8：结局触发

```text
通过调试手段推进到结局条件
→ 等待结局切屏
```

验证：

- `ENDING` screen 正常切换
- 标题、正文正确
- 结束后能重新开局

---

## 6. 大模型辅助测试方法

可以让大模型充当探索式 QA，但前提是给它明确范围和证据要求。

### 6.1 适合让大模型做的事

- 根据 roadmap 和当前代码列高风险回归点
- 读取 diff 后设计回归用例
- 写最小 smoke 脚本
- 对具体模块做 code review
- 对一次手工测试记录进行一致性审查

### 6.2 不适合只依赖大模型的事

- 代替真实运行结果
- 主观判断 UI 手感
- 证明没有 bug
- 覆盖所有 Ink / SCM 内容分支

### 6.3 给大模型的推荐任务模板

#### 模板 A：回归用例设计

```text
请基于以下改动范围设计回归测试：
1. 列出高风险模块
2. 给出最小 smoke case
3. 给出手工测试步骤
4. 标注每个 case 的预期结果
5. 优先找状态机、事件时序、内容热重载方面的问题
```

#### 模板 B：代码审查

```text
请按 code review 方式检查以下改动：
1. 只报真实风险，不报风格偏好
2. 优先找状态不同步、事件时序、重复逻辑、路径未切换干净的问题
3. 给出文件和行号
4. 最后判断距离 roadmap 目标还有多远
```

#### 模板 C：测试结果复核

```text
以下是我执行测试的记录。
请判断：
1. 哪些行为符合预期
2. 哪些可能是 bug
3. 哪些还需要补测
4. 哪些现象需要开发确认是设计如此还是实现问题
```

---

## 7. 缺陷记录要求

每个 bug 至少记录这些内容：

```text
标题:
模块:
严重级别:
版本/提交:
前置条件:
复现步骤:
实际结果:
预期结果:
截图/日志:
是否稳定复现:
```

建议严重级别定义：

- `P0`: 无法启动 / 存档损坏 / 规则严重错误 / 主流程阻断
- `P1`: 核心交互错误 / 状态错误 / 交锋或对话无法正常完成
- `P2`: 显示错误 / 非主线异常 / 可绕过问题
- `P3`: 文案、细节、低风险一致性问题

---

## 8. 本轮重构后的特别关注点

这是本轮最值得盯的缺陷类型：

```text
1. 同一个行为，旧直调路径和新 dispatch 路径结果不一致
2. pending_resolution 结算后状态没落地，但 UI 已经继续
3. ResolutionSettled 已入队，但没有被消费或消费顺序错误
4. encounter / dialogue 结束后 screen 或 modal 残留
5. 热重载后 snapshot 更新了，但 presenter/UI 仍显示旧内容
6. SCM :key / :presentation 存在，但运行时仍回退旧 ID 导致绑定不稳定
```

---

## 9. 最小通过标准

如果要判断“这轮重构可以继续往下走”，至少满足：

- `content.validate` 通过
- `compileall` 通过
- 新开局正常
- 城市 → 地点 → 动作 → 结算 主链路正常
- 至少 1 条对话链路正常
- 至少 1 条交锋链路正常
- 至少 1 个 reveal 动作正常
- 热重载文案生效且中文不缺字
- 结局切换正常

如果这些都没过，不应继续推进下一阶段重构。

