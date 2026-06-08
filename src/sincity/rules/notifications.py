# Transitional facade — delegates to game/notifications.
# New code should import from sincity.game.notifications directly.
from sincity.game.notifications import push_notification, advance_notifications  # noqa: F401
