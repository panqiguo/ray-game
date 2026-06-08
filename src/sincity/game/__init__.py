# game/ — Core game logic layer
#
# docs/architecture-refactor-roadmap.md Phase 1–8 主战场.
# screens/ 已通过 dispatch() + 直接 game.* 导入消除对 sincity.rules 主外观的依赖.
#
# 模块状态 (2026-06-08):
#
# - session.py     1 公开函数 (start_new_run) ✅
# - queries.py     9 公开函数,  0 facade,  9 直接实现 ✅
# - fields.py     16 公开函数,  0 facade, 16 直接实现 ✅（含 upgrade_spirit_value / add_spirit_slot）
# - conditions.py  7 公开函数,  0 facade,  7 直接实现 ✅
# - effects.py     8 公开函数,  0 facade,  8 直接实现 ✅
# - actions.py    35 公开函数,  1 模块级导入 (model.defs),  35 直接实现 ✅
# - resolution.py  7 公开函数,  0 facade,  7 直接实现 ✅
# - clocks.py      6 公开函数,  0 facade,  6 直接实现 ✅
# - reacts.py      5 公开函数,  0 facade,  5 直接实现 ✅
# - encounters.py  9 公开函数,  0 facade,  9 直接实现 ✅
# - dialogues.py   7 公开函数,  0 facade,  7 直接实现 ✅
# - judgment.py    3 函数 + RESULT_TABLE 常量, 0 facade ✅
# - notifications  2 公开函数,  0 facade,  2 直接实现 ✅
# - commands.py   15 dataclass (GameCommand union)
# - events.py      5 dataclass (GameEvent union)
# - flow.py        1 公开函数 dispatch (15 条命令, 5 种事件)
#
# 总计 113 公开函数, 0 facade, 113 直接实现 ✅
#
# 0 个 game/ 模块仍有模块级 `from sincity.rules import progression` ✅ (actions.py 从 model.defs 导入)
# 所有 game/ 模块通过函数体内 lazy import 引用 progression/deck/rng 辅助函数.
#
# 详见 docs/architecture-roadmap-progress.md

from sincity.game import queries, fields, conditions, effects

__all__ = ["queries", "fields", "conditions", "effects"]
