from .actors import DEBUG_COMPANION_ORDER, INITIAL_COMPANION_ID, PARTY_ACTOR_DEFS, PLAYER_ACTOR_ID, build_initial_party
from .cards import CARD_DEFS
from .growth import GROWTH_DEFS
from .city_1 import SCENARIO


def validate_content() -> None:
    from .validate import validate_content as _validate_content

    _validate_content()
