from __future__ import annotations

import asyncio
import time

from pyray import *  # type: ignore

from raygame.constants import TARGET_FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from raygame.content.validate import validate_content
from raygame.rendering import configure_gui_theme, draw_text, load_ui_font
from raygame.rules.progression import start_new_run
from raygame.screens import draw_current_screen
from raygame.screens.debug_panel import draw_debug_panel
from raygame.screens.widgets import begin_ui_frame, draw_hud, finish_ui_frame


class GameApp:
    def __init__(self) -> None:
        self.state = None
        self.rng = None
        self.ui_font = None

    def start(self) -> None:
        configure_gui_theme()
        self.ui_font = load_ui_font()
        validate_content()
        self.reset_run()

    def reset_run(self) -> None:
        seed = int(time.time())
        self.state, self.rng = start_new_run(seed)

    def update(self) -> None:
        if is_key_pressed(KEY_F1):
            self.state.debug_open = not self.state.debug_open
        if is_key_pressed(KEY_F5):
            self.reset_run()

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
            unload_font(self.ui_font)
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
            while not window_should_close():
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
            while not window_should_close():
                self.update()
                self.draw()
                await asyncio.sleep(0)
        finally:
            self.stop()
            close_window()
