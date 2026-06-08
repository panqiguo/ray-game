# 架构重构路线图 — 实现进度审计（最终版）

> 审计日期: 2026-06-08
> 基线文档: `docs/architecture-refactor-roadmap.md`

---

## 总体状态 — 100%

| 阶段 | 完成度 |
|---|---|
| Phase 0: 建立共同地图 | **100%** |
| Phase 1: 建立 game facade 和依赖审计 | **100%** |
| Phase 2: 迁移低耦合查询、字段、条件 | **100%** |
| Phase 3: 统一字段写入和 Effect 边界 | **100%** |
| Phase 4: 整理动作执行主线 | **100%** |
| Phase 5: 整理 Clock/React/Cycle | **100%** |
| Phase 6A: 审计 Dialogue 外部函数 | **100%** |
| Phase 6B: 整理 Encounter 生命周期 | **100%** |
| Phase 7: 整理 Dialogue 生命周期 | **100%** |
| Phase 8: Screens 调用审计和 Command/Event | **100%** |
| Phase 9: 分离 Presentation Models | **100%** |
| Phase 10: 标注 GameState UI 状态 | **100%** |
| Phase 11: SCM Key 和 Presentation Cue | **100%** |

---

## 最终结构

```
src/sincity/
├── model/                    # 权威状态和数据定义
│   ├── state.py
│   ├── defs.py
│   └── enums.py
│
├── content/                  # 内容运行时（SCM → LocationDef/ActionDef/ClockSpec）
│   ├── runtime.py
│   ├── city_1.py
│   ├── validate.py
│   └── hot_reload.py
│
├── content_lang/             # SCM DSL 运行时
│   ├── runtime_core.py
│   └── module_runtime.py
│
├── encounters/               # 交锋系统
│   ├── runtime.py
│   ├── registry.py
│   ├── defs.py
│   └── lispy.py
│
├── dialogues/                # 对话系统 (Ink)
│   ├── runtime.py
│   ├── registry.py
│   └── defs.py
│
├── game/                     # ★ 游戏核心逻辑层（21 模块）
│   ├── session.py            # 开局初始化、debug 辅助、claim_growth
│   ├── flow.py               # 轻量调度入口 dispatch()（→ None）
│   ├── commands.py           # 15 个 GameCommand dataclass
│   ├── events.py             # 6 个 GameEvent + drain/consume/has_event
│   ├── queries.py            # 内容快照查询
│   ├── fields.py             # 状态字段统一读写
│   ├── conditions.py         # 条件判断
│   ├── actions.py            # 动作装配、slot/toggle
│   ├── resolution.py         # 动作结算、pending resolution
│   ├── effects.py            # Effect 执行
│   ├── reacts.py             # React 连锁
│   ├── clocks.py             # Clock 和 cycle
│   ├── encounters.py         # 交锋生命周期
│   ├── dialogues.py          # 对话生命周期
│   ├── judgment.py           # 判定表
│   ├── notifications.py      # 通知推送
│   ├── rng.py                # RandomSource
│   ├── deck.py               # 卡组管理
│   ├── debug_save.py         # 调试存档
│   └── __init__.py
│
├── presentation/             # ViewModel 层
│   ├── city_presenters.py
│   ├── encounter_presenters.py
│   ├── table_presenters.py
│   └── ...
│
├── screens/                  # Raylib UI 层
│   ├── city_screen.py
│   ├── encounter_screen.py
│   └── ...
│
└── app.py                    # 入口
```

---

## 事件系统

```
UI click → dispatch(Command) → pending_events  ←─ advance_pending_resolution()
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                 ▼
              screens 即时消费   app.update()       未来消费者
              (consume_event)   drain 残留事件     (Unity bridge)
```

- `dispatch()`: 返回 `None`，同步/异步事件统一写入 `state.pending_events`
- `consume_event(state, Type)`: 即时消费（screens 用于 `DialogueFastForwarded`）
- `drain_pending_events(state)`: 由 `app.update()` 在本帧更新结束时显式消费，并记录为 `last_frame_events`

---

## rules/ 旧兼容层 — 目录已完全删除

`src/sincity/rules/` 目录不存在。

| 原文件 | 去向 |
|---|---|
| `__init__.py` | 已删除 |
| `progression.py` | 已删除（→ game/ 各模块 facade） |
| `notifications.py` | 已删除（→ game/notifications） |
| `judgment.py` | 已删除（→ game/judgment） |
| `rng.py` | 迁入 `game/rng.py` |
| `deck.py` | 迁入 `game/deck.py` |
| `debug_save.py` | 迁入 `game/debug_save.py` |

`grep -rn "sincity.rules" src/sincity/ --include='*.py'` → 0 matches

---

## 验证状态

| 命令 | 结果 |
|---|---|
| `uv run python -m sincity.content.validate` | ✅ |
| `uv run python -m compileall -q src/sincity` | ✅ |
