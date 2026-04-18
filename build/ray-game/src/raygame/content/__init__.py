from .cards import CARD_DEFS, STARTING_DECK
from .growth import GROWTH_DEFS
from .scenario_escape import SCENARIO


def validate_content() -> None:
    from .validate import validate_content as _validate_content

    _validate_content()
