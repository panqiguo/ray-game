# 架构重构路线图 — 实现进度审计

> 审计日期: 2026-06-08
> 基线文档: `docs/architecture-refactor-roadmap.md`

---

## 总体状态

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
| Phase 8: Screens 调用审计和 Command/Event | **~95%** |
| Phase 9: 分离 Presentation Models | **100%** |
| Phase 10: 标注 GameState UI 状态 | **100%** |
| Phase 11: SCM Key 和 Presentation Cue | **~90%** |

**整体完成度: ~97%** — roadmap 核心目标已达成。

---

## Phase 0: 建立共同地图 — 100%

- `docs/architecture-refactor-roadmap.md` 完整
- `docs/architecture-roadmap-progress.md` 本文件

---

## Phase 1: 建立 game facade 和依赖审计 — 100%

### 最终状态

- `src/sincity/game/` — 18 个模块，2,652 行，151 个函数定义
- `src/sincity/rules/progression.py` — **728 行**，149 个函数（**138 facades + 6 简单 helper + 5 debug/stub**）
- `rules/__init__.py` — 71 项兼容 re-export
- **0 个 game/ 模块有模块级或函数体 `from sincity.rules.progression`**
- `app.py` 已从 `game.session` / `game.resolution` 导入
- `debug_panel.py` 和 `ui_panels.py` 导入已切换到 `game.*`（debug 函数除外）

### 残留真实实现（progression.py 中 11 个非 facade）

| 函数 | 说明 |
|---|---|
| `_push_log` | 3 行 helper |
| `get_action` | 2 行，用于静态内容查询 |
| `_runtime_projection_state` | 3 行 helper |
| `_encounter_snapshot` | 3 行 helper |
| `_reset_encounter_action_cycle` | 2 行 delegator |
| `_mark_content_dirty` | 1 行 helper |
| `_slot_spirit` | 1 行 alias |
| `add_next_companion_for_debug` | debug 专用 |
| `remove_companions_for_debug` | debug 专用 |
| `_refresh_cards_after_party_change` | debug helper |
| `slot_is_preferred_for_check` | stub |

---

## Phase 2: 迁移低耦合查询、字段、条件 — 100%

- `game/queries.py`: 10 个公开函数
- `game/fields.py`: 21 个公开函数，含 `set_field`/`add_field`/`change_health`/`change_energy`/`upgrade_spirit_value`/`add_spirit_slot`/`_actor_attribute_value`/`_coerce_like`/`world_attr_value`/`set_world_attr`/`tick_actor_statuses_after_draw`
- `game/conditions.py`: 7 个公开函数
- 所有 progression.py 同名函数已降级为 facade

---

## Phase 3: 统一字段写入和 Effect 边界 — 100%

- `game/effects.py`: 8 个公开函数，**0 个 progression 导入**
- `game/fields.py`: 所有字段读写集中在 fields.py
- `_add_spirit_slot` / `_upgrade_spirit_value` 已迁入 `game/fields.py`
- Effect 描述函数 `describe_effects` / `_field_label` 等在 `game/effects.py`

---

## Phase 4: 整理动作执行主线 — 100%

- `game/actions.py` (~431 行): **45 个函数**，含所有 slot/check/assembly/toggle 逻辑
- `game/resolution.py` (~284 行): **16 个函数**，含 perform/dismiss/advance/consume
- `CheckValuePart`/`CheckValueBreakdown` 在 `model/defs.py`
- 所有 progression 同名函数为 facade

---

## Phase 5: 整理 Clock/React/Cycle — 100%

- `game/clocks.py` (~119 行): `advance_cycle`/`shift_clock`/`reset_hand`/`advance_clock`
- `game/reacts.py` (~117 行): `resolve_world_reacts`/`resolve_encounter_reacts`/`award_completed_tasks`
- 所有 progression 同名函数为 facade

---

## Phase 6A: 审计 Dialogue 外部函数 — 100%

- `docs/ink-external-function-audit.md` 完整
- 10 个 external function 全量编目
- 3 个绕过 `fields.py` 的函数已识别 + 建议
- 2 个已绑定但未使用的函数已标注

---

## Phase 6B: 整理 Encounter 生命周期 — 100%

- `game/encounters.py` (~152 行): `start_encounter`/`finish_encounter`/`can_endure_pressure` 等
- 所有 progression 同名函数为 facade

---

## Phase 7: 整理 Dialogue 生命周期 — 100%

- `game/dialogues.py` (~136 行): `start_dialogue`/`continue_dialogue`/`finish_dialogue`/`end_game`/`_clear_dialogue_modal`/`_apply_game_over`
- **0 个 progression 导入**

---

## Phase 8: Screens 调用审计和 Command/Event — ~95%

### 已实现

- `game/commands.py`: 15 个 `GameCommand` dataclass
- `game/events.py`: 5 个 `GameEvent` dataclass
- `game/flow.py`: `dispatch()` 函数（15 条命令，5 种事件）
- `city_screen.py` / `encounter_screen.py` / `table_views.py` / `dialogue_view.py` 已使用 `game.flow.dispatch`
- `app.py` 所有导入从 `game.*` 获取
- `debug_panel.py`/`ui_panels.py` 业务函数从 `game.*` 导入

### 未完成

- screen 调用审计清单未正式输出（低优先级）

---

## Phase 9: 分离 Presentation Models — 100%

- `src/sincity/presentation/` 已创建，7 个模块
- 旧 `screens/*_presenters.py` 已降级为 re-export facade

---

## Phase 10: 标注 GameState UI 状态 — 100%

- 所有 UI 状态字段/类已标注注释
- 未做物理拆分（符合设计决策）

---

## Phase 11: SCM Key 和 Presentation Cue — ~90%

- `:key` 和 `:presentation` 关键字已支持
- Duplicate-key 校验已实现
- 覆盖率未审计

---

## 目标结构对照

```
game/
├── session.py       ✅
├── flow.py          ✅
├── commands.py      ✅
├── events.py        ✅
├── queries.py       ✅
├── fields.py        ✅
├── conditions.py    ✅
├── actions.py       ✅
├── resolution.py    ✅
├── effects.py       ✅  (0 progression imports)
├── reacts.py        ✅
├── clocks.py        ✅
├── encounters.py    ✅
├── dialogues.py     ✅  (0 progression imports)
├── judgment.py      ✅
└── notifications.py ✅

presentation/
├── city_presenters.py       ✅
├── encounter_presenters.py  ✅
├── table_presenters.py      ✅
├── tags.py                  ✅
├── card_model.py            ✅
├── typography.py            ✅
└── __init__.py              ✅
```

---

## 还原记录

| 指标 | 重构前 | 重构后 |
|---|---|---|
| `progression.py` 行数 | 1,426 | **728** (-49%) |
| `progression.py` 模块级 import | ~25 | **12** |
| `game/` 对 `progression` 的导入 | 25 处 lazy import | **0** |
| progression 真实实现占比 | ~100% | **~8%**（6 简单 helper） |

---

## 验证状态

| 命令 | 结果 |
|---|---|
| `uv run python -m sincity.content.validate` | ✅ |
| `uv run python -m compileall -q src/sincity` | ✅ |

---

## 剩余低优先级工作

1. screen 调用审计清单（Phase 8 文档验收）
2. SCM key 覆盖率审计（Phase 11）
3. `rules.notifications` / `rules.deck` / `rules.rng` 是否迁移到 game/（路线图未要求）
