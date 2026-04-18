from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class RandomSource:
    seed: int
    _random: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def shuffle(self, values: list[str]) -> None:
        self._random.shuffle(values)

    def d6(self) -> int:
        return self._random.randint(1, 6)

