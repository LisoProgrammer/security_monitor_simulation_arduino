"""Simulated security event generator."""

import random
from datetime import datetime

from .config import (
    ACTION_BLOCK_IP,
    ACTION_DEACTIVATE_USER,
    ACTION_FORCE_REVIEW,
    ACTION_ISOLATE_EMAIL,
    ACTION_NONE,
    ACTION_QUARANTINE,
    DEPARTMENTS,
    EVENT_MALICIOUS_EMAIL_LINK,
    EVENT_OFF_HOURS_USER,
    EVENT_RAPID_PASSWORD_CHANGE,
    EVENT_REPEATED_FAILED_LOGIN,
    EVENT_SUSPICIOUS_EMAIL_DOCUMENT,
    EVENT_TYPES,
    EVENT_UNTRUSTED_IP,
    MALICIOUS_DOMAINS,
    NORMAL_EVENT_TYPE,
    NORMAL_MESSAGES,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_MEDIUM,
    USERS,
)


class EventGenerator:
    def __init__(self):
        self.sequence = 0
        self.login_failures = {}
        self.password_changes = {}

        # Event type -> method that builds its specific fields
        self._builders = {
            EVENT_REPEATED_FAILED_LOGIN: self._failed_login,
            EVENT_RAPID_PASSWORD_CHANGE: self._password_change,
            EVENT_UNTRUSTED_IP: self._untrusted_ip,
            EVENT_OFF_HOURS_USER: self._off_hours_user,
            EVENT_MALICIOUS_EMAIL_LINK: self._malicious_link,
            EVENT_SUSPICIOUS_EMAIL_DOCUMENT: self._suspicious_document,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generate_ip(trusted=False):
        if trusted:
            prefix = random.choice(["10.0", "172.16", "192.168"])
            return f"{prefix}.{random.randint(1, 254)}.{random.randint(1, 254)}"

        return (
            f"{random.randint(20, 220)}.{random.randint(1, 254)}."
            f"{random.randint(1, 254)}.{random.randint(1, 254)}"
        )

    def _base_event(self, event_type, trusted_ip=False):
        self.sequence += 1
        return {
            "id": self.sequence,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user": random.choice(USERS),
            "department": random.choice(DEPARTMENTS),
            "source": self.generate_ip(trusted_ip),
            "type": event_type,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, forced_type=None):
        """Generate a suspicious event (random or of the given type)."""
        event_type = forced_type or random.choices(
            list(EVENT_TYPES), weights=list(EVENT_TYPES.values()), k=1
        )[0]

        event = self._base_event(event_type)
        event.update(self._builders[event_type](event))
        return event

    def generate_normal(self):
        """Generate a normal activity event."""
        event = self._base_event(NORMAL_EVENT_TYPE, trusted_ip=True)
        event.update({
            "severity": SEVERITY_INFO,
            "message": random.choice(NORMAL_MESSAGES),
            "detail": "Activity considered normal",
            "action": ACTION_NONE,
        })
        return event

    # ------------------------------------------------------------------
    # Per-type builders (return the fields to add to the event)
    # ------------------------------------------------------------------

    def _failed_login(self, event):
        user = event["user"]
        attempts = random.randint(5, 14)
        self.login_failures[user] = self.login_failures.get(user, 0) + attempts

        return {
            "severity": SEVERITY_CRITICAL if attempts >= 10 else SEVERITY_HIGH,
            "message": f"{attempts} failed login attempts in 2 minutes",
            "detail": f"User={user} | IP={event['source']}",
            "action": ACTION_BLOCK_IP,
        }

    def _password_change(self, event):
        user = event["user"]
        self.password_changes[user] = datetime.now()

        return {
            "severity": SEVERITY_HIGH,
            "message": "Password change detected shortly after another change",
            "detail": f"User={user} | Suspicious time pattern",
            "action": ACTION_FORCE_REVIEW,
        }

    def _untrusted_ip(self, event):
        return {
            "severity": random.choice(
                [SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL]
            ),
            "message": "Connection from untrusted IP address",
            "detail": f"User={event['user']} | Source={event['source']}",
            "action": ACTION_BLOCK_IP,
        }

    def _off_hours_user(self, event):
        hour = random.choice([0, 1, 2, 3, 4, 22, 23])
        timestamp = f"{hour:02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"

        return {
            "timestamp": timestamp,
            "severity": SEVERITY_HIGH,
            "message": "User created outside business hours",
            "detail": f"Account={event['user']}_new | Time={timestamp}",
            "action": ACTION_DEACTIVATE_USER,
        }

    def _malicious_link(self, event):
        domain = random.choice(MALICIOUS_DOMAINS)

        return {
            "severity": SEVERITY_CRITICAL,
            "message": "Email contains a potentially malicious link",
            "detail": f"Recipient={event['user']} | Domain={domain}",
            "action": ACTION_ISOLATE_EMAIL,
        }

    def _suspicious_document(self, event):
        extension = random.choice([".docm", ".xlsm", ".zip", ".html"])
        filename = f"Report_{random.randint(10, 99)}{extension}"

        return {
            "severity": SEVERITY_HIGH,
            "message": "Suspicious document received by email",
            "detail": f"Recipient={event['user']} | File={filename}",
            "action": ACTION_QUARANTINE,
        }
