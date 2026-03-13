"""
Persistent FloodWait tracker.

Saves the FloodWait expiry timestamp to a small JSON file so that
scheduler runs (even after process restart) can skip Telegram API
calls while the account-level ban is still active.
"""
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

_TRACKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".flood_wait.json")


def record_flood_wait(seconds: int) -> None:
    """Persist a FloodWait expiry timestamp."""
    if seconds <= 0:
        return
    expires_at = time.time() + seconds
    try:
        with open(_TRACKER_FILE, "w") as f:
            json.dump({"expires_at": expires_at, "seconds": seconds}, f)
        logger.info("FloodWait recorded: %d s (expires at %.0f)", seconds, expires_at)
    except OSError as exc:
        logger.warning("Could not persist flood-wait tracker: %s", exc)


def get_flood_wait_remaining() -> int:
    """Return seconds remaining on the active FloodWait, or 0."""
    try:
        with open(_TRACKER_FILE, "r") as f:
            data = json.load(f)
        remaining = int(data.get("expires_at", 0) - time.time())
        return max(remaining, 0)
    except (OSError, json.JSONDecodeError, KeyError):
        return 0


def is_flood_wait_active() -> bool:
    return get_flood_wait_remaining() > 0


def clear_flood_wait() -> None:
    """Remove the tracker file (e.g. for manual reset)."""
    try:
        os.remove(_TRACKER_FILE)
    except OSError:
        pass
