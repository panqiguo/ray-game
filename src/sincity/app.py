from __future__ import annotations

import asyncio
import os
import time
import sys

from pyray import *  # type: ignore

from sincity.constants import TARGET_FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from sincity.content.hot_reload import HOT_RELOADER
from sincity.dialogue_compile import compile_dialogues
from sincity.content.validate import validate_content
from sincity.rendering import configure_gui_theme, draw_text, load_ui_font, unload_ui_font
from sincity.rules.progression import advance_pending_resolution, start_new_run
from sincity.screens import draw_current_screen
from sincity.screens.debug_panel import draw_debug_panel
from sincity.screens.widgets import begin_ui_frame, draw_hud, finish_ui_frame


class GameApp:
    def __init__(self) -> None:
        self.state = None
        self.rng = None
        self.ui_font = None
        self.should_exit = False

    def start(self) -> None:
        configure_gui_theme()
        self.ui_font = load_ui_font()
        compile_dialogues()
        validate_content()
        self.reset_run()

    def reset_run(self) -> None:
        seed = int(time.time())
        self.state, self.rng = start_new_run(seed)

    def update(self) -> None:
        HOT_RELOADER.reload_if_changed(self.state)
        if is_key_pressed(KEY_F1):
            self.state.debug_open = not self.state.debug_open
        if is_key_pressed(KEY_F5):
            self.reset_run()
        if is_key_pressed(KEY_R) and (is_key_down(KEY_LEFT_CONTROL) or is_key_down(KEY_RIGHT_CONTROL)):
            self.restart_process()
        if self._command_q_pressed() or self._control_w_pressed():
            self.request_exit()
            return
        advance_pending_resolution(self.state, self.rng, get_frame_time())

    def restart_process(self) -> None:
        os.execv(sys.executable, [sys.executable, *sys.argv])

    def request_exit(self) -> None:
        self.should_exit = True
        setter = globals().get("set_window_should_close")
        if setter is not None:
            setter(True)

    def _command_q_pressed(self) -> bool:
        key_q = globals().get("KEY_Q")
        left_super = globals().get("KEY_LEFT_SUPER")
        right_super = globals().get("KEY_RIGHT_SUPER")
        if key_q is None or (left_super is None and right_super is None):
            return False
        return is_key_pressed(key_q) and (
            (left_super is not None and is_key_down(left_super))
            or (right_super is not None and is_key_down(right_super))
        )

    def _control_w_pressed(self) -> bool:
        key_w = globals().get("KEY_W")
        left_control = globals().get("KEY_LEFT_CONTROL")
        right_control = globals().get("KEY_RIGHT_CONTROL")
        if key_w is None or (left_control is None and right_control is None):
            return False
        return is_key_pressed(key_w) and (
            (left_control is not None and is_key_down(left_control))
            or (right_control is not None and is_key_down(right_control))
        )

    def draw(self) -> None:
        begin_drawing()
        clear_background(Color(10, 12, 16, 255))
        begin_ui_frame()
        draw_hud(self.ui_font, self.state)
        draw_current_screen(self.ui_font, self.state, self.rng)
        draw_debug_panel(self.ui_font, self.state)
        finish_ui_frame()
        end_drawing()

    def stop(self) -> None:
        if self.ui_font is not None:
            unload_ui_font(self.ui_font)
            self.ui_font = None

    def run(self) -> None:
        set_config_flags(FLAG_WINDOW_RESIZABLE)
        init_window(WINDOW_WIDTH, WINDOW_HEIGHT, "乌鸦的去向")
        set_exit_key(KEY_NULL)
        set_target_fps(TARGET_FPS)
        # 确保窗口尺寸正确初始化，避免首帧布局错误
        set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.start()
        try:
            while not window_should_close() and not self.should_exit:
                self.update()
                self.draw()
        finally:
            self.stop()
            close_window()

    async def run_async(self) -> None:
        set_config_flags(FLAG_WINDOW_RESIZABLE)
        init_window(WINDOW_WIDTH, WINDOW_HEIGHT, "乌鸦的去向")
        set_exit_key(KEY_NULL)
        set_target_fps(TARGET_FPS)
        # 确保窗口尺寸正确初始化，避免首帧布局错误
        set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.start()
        try:
            while not window_should_close() and not self.should_exit:
                self.update()
                self.draw()
                await asyncio.sleep(0)
        finally:
            self.stop()
            close_window()
