"""Side panel with active alerts."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ..config import ALERT_SEVERITIES, SEVERITY_COLORS

MAX_ALERTS = 8


class AlertCard(QFrame):
    """Single alert with action and ignore buttons."""

    action_requested = pyqtSignal(dict)

    def __init__(self, event, parent=None):
        super().__init__(parent)
        self.setObjectName("AlertCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(5)

        layout.addLayout(self._build_header(event))
        layout.addWidget(self._build_description(event))
        layout.addWidget(self._build_detail(event))
        layout.addLayout(self._build_buttons(event))

    @staticmethod
    def _build_header(event):
        row = QHBoxLayout()

        severity = QLabel(event["severity"])
        severity.setStyleSheet(
            f"color:{SEVERITY_COLORS[event['severity']]};"
            "font-weight:700;font-size:10px;"
        )

        time = QLabel(event["timestamp"])
        time.setStyleSheet("color:#64748b;font-size:10px;")

        row.addWidget(severity)
        row.addStretch()
        row.addWidget(time)
        return row

    @staticmethod
    def _build_description(event):
        label = QLabel(event["message"])
        label.setWordWrap(True)
        label.setStyleSheet("font-weight:600;color:#e5e7eb;")
        return label

    @staticmethod
    def _build_detail(event):
        label = QLabel(f"{event['user']} • {event['source']}")
        label.setStyleSheet("color:#94a3b8;font-size:10px;")
        return label

    def _build_buttons(self, event):
        row = QHBoxLayout()

        action = QPushButton(event["action"])
        action.clicked.connect(
            lambda checked=False, e=event: self.action_requested.emit(e)
        )

        ignore = QPushButton("Ignore")
        ignore.clicked.connect(self.deleteLater)

        row.addWidget(action)
        row.addWidget(ignore)
        return row


class AlertPanel(QFrame):
    action_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AlertPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        title = QLabel("ACTIVE ALERTS")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.container = QVBoxLayout()
        self.container.setSpacing(8)
        layout.addLayout(self.container)
        layout.addStretch()

    def set_events(self, events):
        self._clear()

        alerts = [e for e in events if e["severity"] in ALERT_SEVERITIES][:MAX_ALERTS]

        if not alerts:
            label = QLabel("No active alerts.")
            label.setStyleSheet("color:#64748b;padding:15px;")
            self.container.addWidget(label)
            return

        for event in alerts:
            card = AlertCard(event)
            card.action_requested.connect(self.action_requested)
            self.container.addWidget(card)

    def _clear(self):
        while self.container.count():
            widget = self.container.takeAt(0).widget()
            if widget:
                widget.deleteLater()
