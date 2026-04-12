from __future__ import annotations

import asyncio

from pyray import *  # type: ignore


async def main() -> None:
    set_config_flags(FLAG_WINDOW_RESIZABLE)
    init_window(960, 540, "pyray web probe")
    set_target_fps(60)
    try:
        while not window_should_close():
            begin_drawing()
            clear_background(Color(20, 24, 32, 255))
            draw_text("pyray web probe", 40, 40, 32, RAYWHITE)
            draw_text("If you can see this, pyray basic rendering works in web.", 40, 92, 20, LIGHTGRAY)
            draw_fps(40, 132)
            end_drawing()
            await asyncio.sleep(0)
    finally:
        close_window()


if __name__ == "__main__":
    asyncio.run(main())
