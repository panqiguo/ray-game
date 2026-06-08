# Ink External Function 审计

> 审计日期: 2026-06-08
> 关联: `docs/architecture-refactor-roadmap.md` Phase 6A

---

## 绑定位置

所有 external function 在 `src/sincity/dialogues/runtime.py` 的 `_bind_story()` 中绑定（约第 145-155 行）。

---

## 外部函数清单

| # | Ink 名称 | Python Handler | 读/写 | 修改的 GameState 字段 | 调用频率 |
|---|---|---|---|---|---|
| 1 | `give_item(item_id, amount)` | `_give_item` | **写** | `world.inventory` (+=), `world.seen_items` (add) | 多次 |
| 2 | `remove_item(item_id, amount)` | `_remove_item` | **写** | `world.inventory` (`max(0, current - N)`) | **未被任何 .ink 调用** |
| 3 | `change_money(amount)` | `_change_money` | **写** | `world.inventory["money"]` (clamp 0), `world.seen_items` (add) | 1 次 |
| 4 | `change_health(amount)` | `_change_health` | **写** | → `game.fields.change_health` → `player_actor.health`, `attributes.health`, trauma sync, game over | 3 次 |
| 5 | `change_energy(amount)` | `_change_energy` | **写** | → `game.fields.change_energy` → `player_actor.energy`, `attributes.energy`, pressure overflow | 1 次 |
| 6 | `set_value(key, value)` | `_set_value` | **写** | → `game.fields.set_field` → 路由到 encounter store / world attrs / relations / `world.values` / `world.inventory` | **最多** (15+ 次) |
| 7 | `add_value(key, amount)` | `_add_value` | **写** | → `game.fields.add_field` → 同 set_value 路由但累加 | 6 次 |
| 8 | `start_encounter(id)` | `_start_encounter` | **写 (状态跳转)** | → `game.encounters.start_encounter_from_dialogue` → 清 active_dialogue, 创建 active_encounter, 切 screen | 2 次 |
| 9 | `finish_encounter(outcome)` | `_finish_encounter` | **写 (状态跳转)** | → `game.encounters.finish_encounter_from_dialogue` → 清 active_dialogue, 清 active_encounter, 切 screen | **未被任何 .ink 调用** |
| 10 | `log(text)` | lambda | **写** | `action_log.append(text)` | 3 次 |

**所有 10 个外部函数均为写操作，无只读函数。**

---

## 绕过 fields.py / effects.py 分析

| 函数 | 绕过 fields.py? | 绕过 effects.py? | 建议 |
|---|---|---|---|
| `give_item` | **是** — 直接操作 `state.world.inventory` | n/a (非 effect) | 保留为 dialogue 专用操作，或通过 `set_field` 路由 |
| `remove_item` | **是** — 直接操作 `state.world.inventory` | n/a (非 effect) | 同上；当前未被任何 ink 调用 |
| `change_money` | **是** — 直接操作 `state.world.inventory["money"]` | n/a (非 effect) | 保留或通过 `add_field` 路由 |
| `change_health` | **否** — 通过 `game.fields.add_field` → `change_health` | n/a | 已通过 fields.py，无需改动 |
| `change_energy` | **否** — 通过 `game.fields.add_field` → `change_energy` | n/a | 已通过 fields.py，无需改动 |
| `set_value` | **否** — 通过 `game.fields.set_field` | n/a | 已通过 fields.py，无需改动 |
| `add_value` | **否** — 通过 `game.fields.add_field` | n/a | 已通过 fields.py，无需改动 |
| `start_encounter` | n/a — 状态跳转 | n/a | 已通过 `game.encounters`，无需改动 |
| `finish_encounter` | n/a — 状态跳转 | n/a | 同上；当前未被任何 ink 调用 |
| `log` | **是** — 直接 `state.action_log.append` | n/a | 低风险，保留 |

**绕过 fields.py 的 3 个函数:** `give_item`, `remove_item`, `change_money`。它们都直接操作 `world.inventory` 字典。建议：如果要严格统一状态入口，应改为通过 `game.fields.set_field` 或 `game.fields.add_field`。

---

## .ink 文件调用点

### `开篇.ink`
| 行 | 调用 |
|---|---|
| 6 | `~ start_encounter("逃离疗养院")` |

### `first_scene_doctor_office.ink`
| 行 | 调用 |
|---|---|
| 73 | `~ give_item("money", 50)` |
| 74 | `~ give_item("gun", 1)` |

### `frederick_phone_intro.ink`
| 行 | 调用 |
|---|---|
| 64 | `~ log("德雷福雷委托：在老街一带寻找薇拉的下落。")` |

### `police_interview.ink`
| 行 | 调用 |
|---|---|
| 15 | `~ change_health(-2)` |
| 23 | `~ change_energy(-2)` |
| 28 | `~ change_health(-2)` |
| 40 | `~ set_value("police_investigation_done", "true")` |
| 41 | `~ set_value("police_knows_true_info", "true")` |
| 42 | `~ set_value("police_choice_ready", "false")` |
| 43 | `~ add_value("police_relation", 1)` |
| 56 | `~ set_value("police_investigation_done", "true")` |
| 57 | `~ set_value("police_got_fake_info", "true")` |
| 58 | `~ set_value("police_choice_ready", "false")` |
| 59 | `~ add_value("police_relation", -1)` |
| 72 | `~ set_value("police_investigation_done", "true")` |
| 73 | `~ set_value("police_refused_info", "true")` |
| 74 | `~ set_value("police_choice_ready", "false")` |
| 75 | `~ add_value("police_relation", -1)` |

### `bar_bartender_intro.ink`
| 行 | 调用 |
|---|---|
| 13 | `~ log("你从酒保嘴里听到了一点街上的风声。")` |
| 18 | `~ change_money(-10)` |
| 19 | `~ log("你塞给了酒保一点钱。")` |
| 41 | `~ give_item("clothes", 1)` |
| 42 | `~ log("酒保顺手塞给了你一件能撑场面的衣服。")` |

### `forced_item_recovery.ink`
| 行 | 调用 |
|---|---|
| 22 | `~ start_encounter("取回神秘物品")` |

### `forced_police_interview.ink`
| 行 | 调用 |
|---|---|
| 15 | `~ change_health(-1)` |
| 39 | `~ set_value("police_investigation_done", "true")` |
| 40 | `~ set_value("police_knows_true_info", "true")` |
| 41 | `~ set_value("police_choice_ready", "false")` |
| 42 | `~ add_value("police_relation", -1)` |
| 52 | `~ set_value("police_investigation_done", "true")` |
| 53 | `~ set_value("police_got_fake_info", "true")` |
| 54 | `~ set_value("police_choice_ready", "false")` |
| 55 | `~ set_value("police_suspicious", "true")` |
| 56 | `~ add_value("police_relation", -1)` |
| 69 | `~ set_value("police_investigation_done", "true")` |
| 70 | `~ set_value("police_refused_info", "true")` |
| 71 | `~ set_value("police_choice_ready", "false")` |
| 72 | `~ add_value("police_relation", -2)` |

---

## 被绑定但未被 .ink 调用的函数

| 函数 | 说明 |
|---|---|
| `remove_item(item_id, amount)` | 预留：未来可用于对话中消耗物品 |
| `finish_encounter(outcome)` | 预留：理论上可由 Ink 控制交锋结算，但当前通过 encounter runtime 内部处理 |

---

## 状态修改总览

| GameState 子路径 | 写入函数 | 可通过 Ink key 访问 |
|---|---|---|
| `world.inventory` | `give_item`, `remove_item`, `change_money`, `set_value`, `add_value` | `"money"`, 任意物品 ID |
| `world.seen_items` | `give_item`, `change_money` | — |
| `attributes.health` | `change_health`, `set_value`(`"health"`) | `"health"` |
| `attributes.energy` | `change_energy`, `set_value`(`"energy"`) | `"energy"` |
| `player_actor.health` | `change_health` → `add_field` → `change_health` | — |
| `player_actor.energy` | `change_energy` → `add_field` → `change_energy` | — |
| `world.values` | `set_value`, `add_value` | `"police_investigation_done"`, `"police_knows_true_info"`, `"police_got_fake_info"`, `"police_refused_info"`, `"police_choice_ready"`, `"police_suspicious"`, `"gang_relation"`, `"finance_relation"`, `"police_relation"` 等 |
| `action_log` | `log` | — |
| `active_dialogue` / `active_encounter` / `screen` | `start_encounter`, `finish_encounter` | — |

---

## 建议迁移路径

1. **低优先级**: 将 `give_item` / `remove_item` / `change_money` 改为通过 `game.fields.add_field` / `set_field` 路由 — 当前直接操作 inventory 已足够简单
2. **不迁移**: `change_health` / `change_energy` / `set_value` / `add_value` 已通过 `game.fields`，符合架构目标
3. **不迁移**: `start_encounter` / `finish_encounter` 已通过 `game.encounters`，符合架构目标
4. **保留**: `log` 是纯调试辅助，无需迁移
