# 工程风格偏好

- 游戏内容以数据驱动为主
- 保持工程结构清晰、可靠、可拓展，避免大量的类临时堆放在同一个大型文件中，在当前内容范围内有清晰的抽象层次，既不过度设计，也不过度耦合
- 减少混乱的兼容或对错误的容忍；对于可能存在的边缘情况，宁可assert确保正确也不要过分兼容，确保游戏的健壮性。
- 代码内部逻辑/命名保持英文，玩家可见的文案使用中文。数据的 key 使用英文，value 可以使用中文

# UI 偏好
- UI 以代码驱动, 使用IMGUI风格，保持清晰排版和可读性
- Raylib/Python 渲染中文字体时，优先“多字号、少字形”：按实际 UI 字号加载字体，但字形集只收集当前内容需要的字符。避免用单一大字号 atlas 缩放所有字号；虽然更快，但小字号可能发虚、发硬或不够清晰。新增/热重载 SCM 内容时要确保新中文字符会进入字形收集。

# 工具约定
- 默认使用 `uv` 运行 Python 命令
- Web 导出相关命令都在 Makefile 中（`make web`, `make web-serve`, `make web-upload`）

# 项目架构

- 入口: `main.py` → `sincity.app.GameApp`（`run_async`）
- 三个屏幕: `CITY`（城市层）、`ENCOUNTER`（外出任务）、`ENDING`（结局），由 `screens/router.py` 分发

# 内容系统

## SCM DSL
- `.scm` 文件在 `src/sincity/scm/`，城市入口 `city_1.scm`，外出任务在 `encounter/` 下
- 修改后重新运行游戏或 Ctrl+R 热重启即生效
- Scheme 参考: `encounters/cheat-sheet.md`
- `:suits` 只写一个最适属性，环境修正用 modifier 表达

## 内容术语
- 地点：城市地图上的可进入空间，对应 SCM 里的 `node` / `scene`。
- 动作：地图或地点内可点击执行的行为，对应 SCM 里的 `action`；动作可以是纯对话，也可以需要投入行动手牌判定。
- 交锋场景：进入特殊片段后的独立情境，对应工程里的 `encounter`；它可以有自己的地点、动作、压力条/进度条和结算。
- 压力条/进度条：对应 SCM 里的 `clock`。
- 设计讨论中优先使用上述中文术语；工程代码暂时保留 `node`、`action`、`encounter`、`clock` 等英文名。

## 验证流程（按顺序，uv run 前缀）
1. **语法检查** — `python -m sincity.scm_lint <file.scm>`
2. **括号平衡**（lint 报括号错误时精确定位）— `python scripts/check_parens.py <file.scm>`
3. **全量内容校验** — `python -m sincity.content.validate`（编译 + 校验 action/effect/clock/react/task 结构）
4. **compileall**（仅当改到 Python 运行时/编译逻辑）— `python -m compileall -q src/sincity/content_lang/runtime_core.py src/sincity/content/runtime.py src/sincity/encounters/runtime.py src/sincity/rules/progression.py`
5. **最小状态模拟**（仅当新增 DSL 语义/effect/react）— `python - <<'PY' ... PY` 直接导入运行时构造状态验证边界行为

> 更改剧情文案或已有数值通常前两步就够，改了 DSL 语义或 effect 解释器需要全走。

## 对话系统（Ink）
- 对话用 Ink 语言, 文件在 `dialogues/assets/*.ink`
- 编译需要 `inklecate` 或 `npx inkjs`
- 编译产物为 `.ink.json` 放在同目录

# 运行时调试
- F1 = 打开调试面板
- F5 = 重置当前对局
- Ctrl+R = 重启进程（热重载修改过的 Python 文件）
- 内容热重载: 修改 `.scm` 文件会自动在 update 循环中重新加载（通过 `content/hot_reload.py`）

# 核心游戏系统
- 资源: health（健康）、energy/stress（精力）、money（金钱）
- 行动骰子精神值: logic=2, perception=1, willpower=1（初始值）
- 每 cycle 行动槽位: health≤3 时 3 槽，否则 4 槽（初始）
- 判定: 行动值 = 精神值 + 骰子点数（含修正）→ 查结果表（judgment.py）
- 时钟 clock 系统: 各任务/进度的填条机制
- React 系统: 世界条件触发器，在每次行动后自动检查并触发连锁效果
- 主驱动: 黑帮债务（15天倒计时）

# 模型层
- `GameState` 是整个游戏的核心状态（`model/state.py`）
- `ActionDef` / `Effect` / `Condition` 等定义在 `model/defs.py`
- 三条势力关系: gang_relation, finance_relation, police_relation（范围 -3 到 +3）

# 注意
- 没有测试框架或测试文件
- 没有 CI/CD 配置
- 没有格式化/lint 工具配置
