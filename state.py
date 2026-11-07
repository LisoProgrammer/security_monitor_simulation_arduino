"""Security state and statistics helpers (no Qt dependencies)."""

from collections import Counter

from .config import (
    ACTION_BLOCK_IP,
    ACTION_DEACTIVATE_USER,
    ACTION_ISOLATE_EMAIL,
    ACTION_QUARANTINE,
    NORMAL_EVENT_TYPE,
)


class SecurityState:
    """Accumulates the effect of simulated response actions."""

    def __init__(self):
        self.blocked_ips = set()
        self.inactive_users = set()
        self.quarantined = 0

    def apply_action(self, event):
        action = event["action"]

        if action == ACTION_BLOCK_IP:
            self.blocked_ips.add(event["source"])
        elif action == ACTION_DEACTIVATE_USER:
            self.inactive_users.add(event["user"])
        elif action in (ACTION_ISOLATE_EMAIL, ACTION_QUARANTINE):
            self.quarantined += 1

    def reset(self):
        self.blocked_ips.clear()
        self.inactive_users.clear()
        self.quarantined = 0


def count_by_severity(events, severity):
    return sum(event["severity"] == severity for event in events)


def count_by_category(events, limit=7):
    counts = Counter(
        event["type"] for event in events if event["type"] != NORMAL_EVENT_TYPE
    )
    return dict(counts.most_common(limit))
