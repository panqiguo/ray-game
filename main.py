from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from raygame.app import GameApp


async def main() -> None:
    app = GameApp()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
