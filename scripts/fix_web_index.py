from __future__ import annotations

import re
import sys
from pathlib import Path


WEB_WIDTH = 1440
WEB_HEIGHT = 900


def main() -> None:
    assert len(sys.argv) == 2, "Usage: fix_web_index.py <index.html>"
    path = Path(sys.argv[1])
    assert path.exists(), f"Missing web index: {path}"
    text = path.read_text(encoding="utf-8")
    text = _replace_once(text, 'Screen  : 1280x720', f"Screen  : {WEB_WIDTH}x{WEB_HEIGHT}")
    text = _replace_once(text, 'platform.document.body.style.background = "#7f7f7f"', 'platform.document.body.style.background = "#0a0c10"')
    text = _replace_once(text, 'gui_divider : 2', 'gui_divider : 1')
    text = _replace_once(text, 'fb_width : "1280"', f'fb_width : "{WEB_WIDTH}"')
    text = _replace_once(text, 'fb_height : "720"', f'fb_height : "{WEB_HEIGHT}"')
    text = _replace_canvas_css(text)
    text = _replace_body_css(text)
    text = re.sub(r'(<canvas class="emscripten" id="canvas"\s*)width="[^"]+"\s*height="[^"]+"', rf'\1width="{WEB_WIDTH}"\nheight="{WEB_HEIGHT}"', text)
    text = re.sub(r'(<canvas class="emscripten" id="canvas3d"\s*)width="[^"]+"\s*height="[^"]+"', rf'\1width="{WEB_WIDTH}"\nheight="{WEB_HEIGHT}"', text)
    path.write_text(text, encoding="utf-8")


def _replace_once(text: str, old: str, new: str) -> str:
    assert old in text, f"Expected web template fragment not found: {old}"
    return text.replace(old, new, 1)


def _replace_canvas_css(text: str) -> str:
    replacement = f"""canvas.emscripten {{
            border: 0px none;
            background-color: transparent;
            width: {WEB_WIDTH}px;
            height: {WEB_HEIGHT}px;
            z-index: 5;

            padding: 0;
            margin: 0;

            position: absolute;
            top: 0;
            left: 0;
            right: auto;
            bottom: auto;
            transform: none;
        }}"""
    next_text, count = re.subn(r"canvas\.emscripten\s*\{.*?\n\s*\}", replacement, text, count=1, flags=re.S)
    assert count == 1, "Expected exactly one canvas.emscripten CSS block."
    return next_text


def _replace_body_css(text: str) -> str:
    replacement = """body {
            font-family: arial;
            margin: 0;
            padding: 0;
            background-color: #0a0c10;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }

        html {
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: #0a0c10;
        }"""
    next_text, count = re.subn(r"body\s*\{.*?\n\s*\}", replacement, text, count=1, flags=re.S)
    assert count == 1, "Expected exactly one body CSS block."
    return next_text


if __name__ == "__main__":
    main()
