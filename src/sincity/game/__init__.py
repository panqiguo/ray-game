# game/ — 游戏核心逻辑层（最终版）
#
# 全工程唯一运行时入口层。screen / app / dialogue 都直接从 game/ 导入。
#
# 事件系统：单通道 state.pending_events。
#   - 生产者：dispatch() / advance_pending_resolution()
#   - 消费者：screens (consume_event) + app.update (_consume_pending_events)
#   - app.update() 在本帧更新结束时显式消费剩余事件，并记录到 last_frame_events
#
# 模块清单:
#   session.py         start_new_run, debug companion helpers, claim_growth
#   flow.py            dispatch (→ None)
#   commands.py        15 GameCommand dataclasses
#   events.py          6 GameEvent dataclasses, drain/consume/has_event
#   queries.py         current_world_snapshot, current_encounter_snapshot, ...
#   fields.py          set_field, add_field, change_health, change_energy, ...
#   conditions.py      action_is_available, location_is_visible, all_met, ...
#   actions.py         open_action, toggle_*, slot_*, ...
#   resolution.py      perform_*, advance_pending_resolution, dismiss_*, ...
#   effects.py         apply_effect, apply_effects, describe_effects
#   reacts.py          resolve_world_reacts, resolve_encounter_reacts, ...
#   clocks.py          advance_cycle, shift_clock, reset_hand
#   encounters.py      start_encounter, finish_encounter, ...
#   dialogues.py       start_dialogue, continue_dialogue, finish_dialogue, ...
#   judgment.py        RESULT_TABLE, compute_action_value, roll_result
#   notifications.py   push_notification, advance_notifications
#   rng.py             RandomSource
#   deck.py            list_spirit_slots, make_starting_deck, start_city_day
#   debug_save.py      debug_load, debug_save, slot_path

from sincity.game import queries, fields, conditions, effects

__all__ = ["queries", "fields", "conditions", "effects"]
