"""Simulation logic (no Qt dependencies)."""

import random

from .config import (
    ALERT_SEVERITIES,
    MAX_ACTIVE_USERS,
    MODE_AUTO,
    MODE_NORMAL,
    MODE_SUSPICIOUS,
    MODE_TO_EVENT_TYPE,
    NORMAL_EVENT_PROBABILITY,
)


def next_event(generator, mode):
    """Return the next event according to the selected generation mode."""
    if mode == MODE_NORMAL:
        return generator.generate_normal()

    if mode == MODE_AUTO:
        if random.random() < NORMAL_EVENT_PROBABILITY:
            return generator.generate_normal()
        return generator.generate()

    if mode == MODE_SUSPICIOUS:
        return generator.generate()

    return generator.generate(MODE_TO_EVENT_TYPE[mode])


class Telemetry:
    """Simulates network traffic and active users."""

    def __init__(self):
        self.active_users = set()

    def sample_traffic(self, event):
        traffic = max(15, random.gauss(75 + len(self.active_users) * 2, 16))

        if event["severity"] in ALERT_SEVERITIES:
            traffic += random.randint(10, 60)

        return int(traffic)

    def update_users(self, event):
        if event["severity"] in ALERT_SEVERITIES:
            if random.random() < 0.25:
                self.active_users.discard(event["user"])
        else:
            self.active_users.add(event["user"])

        while len(self.active_users) > MAX_ACTIVE_USERS:
            self.active_users.pop()

        return len(self.active_users)
