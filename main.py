from __future__ import annotations

import asyncio
import sys
import traceback
from pathlib import Path

# Keep this import at module top-level so pygbag can detect and bundle the
# browser-compatible pyray/raylib runtime when building the web package.
import pyray  # type: ignore  # noqa: F401

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

async def main() -> None:
    try:
        from sincity.app import GameApp

        app = GameApp()
        await app.run_async()
    except Exception:
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
