from .cards import CARD_DEFS
from .growth import GROWTH_DEFS
from .city_1 import SCENARIO


def validate_content() -> None:
    from .validate import validate_content as _validate_content

    _validate_content()
