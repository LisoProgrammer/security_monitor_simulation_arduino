"""Event log table."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..config import SEVERITY_COLORS, VISIBLE_ROWS

COLUMNS = [
    ("Time", "timestamp"),
    ("Severity", "severity"),
    ("User", "user"),
    ("Source", "source"),
    ("Event", "type"),
    ("Description", "message"),
    ("Action", "action"),
]
SEVERITY_COLUMN = 1


class EventTable(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("EVENT LOG")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([name for name, _ in COLUMNS])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def set_events(self, events):
        visible = list(events)[:VISIBLE_ROWS]
        self.table.setRowCount(len(visible))

        for row, event in enumerate(visible):
            for column, (_, key) in enumerate(COLUMNS):
                item = QTableWidgetItem(str(event[key]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)

                if column == SEVERITY_COLUMN:
                    self._style_severity(item, event["severity"])

                self.table.setItem(row, column, item)

    @staticmethod
    def _style_severity(item, severity):
        item.setForeground(QColor(SEVERITY_COLORS.get(severity, "#ffffff")))
        item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
