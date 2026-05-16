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

# 内容系统（需要知道才能工作）

## 游戏世界定义（SCM DSL）
- 游戏内容使用自定义 Scheme 方言（`.scm` 文件）, 在 `src/sincity/scm/` 下
- 城市内容入口: `city_1.scm`，编译于 `content/city_1.py`
- 外出任务在 `scm/encounter/*.scm`
- 修改 `.scm` 后重新运行游戏即可生效（或按 Ctrl+R 热重启）
- 验证 SCM 语法: `python -m sincity.scm_lint src/sincity/scm/city_1.scm`
- Scheme 基础参考: `encounters/cheat-sheet.md`

### 修改 Schema / DSL 后的验证工作流
- 这里的 “Schema / DSL” 包括：
  - `src/sincity/content_lang/runtime_core.py`
  - `src/sincity/content/runtime.py`
  - `src/sincity/encounters/runtime.py`
  - `src/sincity/encounters/defs.py`
  - 以及任何新增/修改的 `.scm` authoring 形式
- 修改后至少按下面顺序验证，默认都使用 `uv run`：
  1. 对改过的单个 SCM 文件跑语法检查  
     - 城市内容：`uv run python -m sincity.scm_lint src/sincity/scm/city_1.scm`
     - 外出内容：`uv run python -m sincity.scm_lint src/sincity/scm/encounter/文件名.scm`
  2. 跑全量内容校验：`uv run python -m sincity.content.validate`
     - 这一步会编译 world / encounter 内容，并验证 action、effect、clock、react、task 等结构
  3. 如果改到了 Python 运行时或编译逻辑，再跑一次 `compileall`，确保没有明显语法错误  
     - 例如：`uv run python -m compileall -q src/sincity/content_lang/runtime_core.py src/sincity/content/runtime.py src/sincity/encounters/runtime.py src/sincity/rules/progression.py`
  4. 对新 Schema 做一个最小状态模拟
     - 用 `uv run python - <<'PY' ... PY` 直接导入真实运行时，构造最小状态，确认新字段/新 effect/新 react 的行为符合预期
     - 优先验证这类边界：
       - 新增 world 注入字段是否真的进入 encounter
       - 新增 task / react 是否在正确的日期或条件下触发
       - encounter 的 `:on-cycle`、clock 填满、失败阈值是否按预期跳转
- 如果只是改普通剧情文案或已有 SCM 数值，通常前两步就够了；如果改了 DSL 语义或 effect 解释器，四步都要跑。

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
- 每 cycle 行动槽位: health≤3 时 2 槽，否则 3 槽（初始）
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
