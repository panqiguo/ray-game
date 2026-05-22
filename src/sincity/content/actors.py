from __future__ import annotations

from dataclasses import dataclass

from sincity.model.state import PartyActorState


@dataclass(frozen=True)
class PartyActorDef:
    id: str
    name: str
    max_health: int
    max_energy: int
    logic: int
    perception: int
    willpower: int
    is_player: bool = False

    def instantiate(self, *, health: int | None = None, energy: int | None = None) -> PartyActorState:
        return PartyActorState(
            id=self.id,
            name=self.name,
            health=self.max_health if health is None else health,
            max_health=self.max_health,
            energy=self.max_energy if energy is None else energy,
            max_energy=self.max_energy,
            logic=self.logic,
            perception=self.perception,
            willpower=self.willpower,
            is_player=self.is_player,
        )


PLAYER_ACTOR_ID = "cole"
DEBUG_COMPANION_ORDER: tuple[str, ...] = ("lena", "marco")

PARTY_ACTOR_DEFS: dict[str, PartyActorDef] = {
    "cole": PartyActorDef(
        id="cole",
        name="科尔",
        max_health=10,
        max_energy=5,
        logic=2,
        perception=1,
        willpower=1,
        is_player=True,
    ),
    "lena": PartyActorDef(
        id="lena",
        name="莉娜",
        max_health=6,
        max_energy=3,
        logic=0,
        perception=2,
        willpower=1,
    ),
    "marco": PartyActorDef(
        id="marco",
        name="马可",
        max_health=8,
        max_energy=2,
        logic=1,
        perception=0,
        willpower=2,
    ),
}


def build_initial_party(*, player_health: int, player_energy: int) -> dict[str, PartyActorState]:
    party: dict[str, PartyActorState] = {}
    for actor_id, actor_def in PARTY_ACTOR_DEFS.items():
        if actor_def.is_player:
            party[actor_id] = actor_def.instantiate(health=player_health, energy=player_energy)
        else:
            party[actor_id] = actor_def.instantiate()
    return party
