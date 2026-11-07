"""Statistic card widget."""

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, title, value="0", accent="#38bdf8"):
        super().__init__()
        self.setObjectName("StatCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.title = QLabel(title.upper())
        self.title.setStyleSheet(
            "color:#94a3b8;font-size:10px;font-weight:600;"
        )

        self.value = QLabel(str(value))
        self.value.setStyleSheet(
            f"color:{accent};font-size:25px;font-weight:700;"
        )

        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(self, value):
        self.value.setText(str(value))
