"""Side panel with active alerts."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..config import ACTION_NONE, ALERT_SEVERITIES, SEVERITY_COLORS

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

        if event["action"] != ACTION_NONE:
            action = QPushButton(event["action"])
            action.clicked.connect(
                lambda checked=False, e=event: self.action_requested.emit(e)
            )
            row.addWidget(action)

        ignore = QPushButton("Ignore")
        ignore.clicked.connect(self.deleteLater)

        row.addWidget(ignore)
        return row


class AlertPanel(QFrame):
    action_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AlertPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("ACTIVE ALERTS")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # Alerts live inside a scroll area so accumulating cards can never
        # increase the minimum height of the dashboard window.  That growth is
        # what used to push the intrusion overlay out of place after the first
        # alert.
        self.scroll = QScrollArea(self)
        self.scroll.setObjectName("AlertScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll.setMinimumHeight(0)

        self.body = QWidget()
        self.body.setObjectName("AlertScrollBody")
        self.body.setMinimumHeight(0)
        self.container = QVBoxLayout(self.body)
        self.container.setContentsMargins(0, 0, 4, 0)
        self.container.setSpacing(8)
        # Keep the body at least as tall as its content so the scroll area
        # scrolls instead of squeezing the cards.
        self.container.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.container.addStretch()

        self.scroll.setWidget(self.body)
        layout.addWidget(self.scroll, 1)

    def set_events(self, events):
        self._clear()

        alerts = [e for e in events if e["severity"] in ALERT_SEVERITIES][:MAX_ALERTS]

        if not alerts:
            label = QLabel("No active alerts.")
            label.setStyleSheet("color:#64748b;padding:15px;")
            self.container.insertWidget(0, label)
            return

        for index, event in enumerate(alerts):
            card = AlertCard(event)
            card.action_requested.connect(self.action_requested)
            self.container.insertWidget(index, card)

    def _clear(self):
        # Remove widgets and spacer items, keeping the trailing stretch.
        while self.container.count() > 1:
            item = self.container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
