"""Simulation control bar."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)

from ..config import (
    GENERATION_MODES,
    MAX_INTERVAL_MS,
    MIN_INTERVAL_MS,
    REFRESH_MS,
)


class ControlBar(QWidget):
    interval_changed = pyqtSignal(int)
    generate_requested = pyqtSignal()
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.mode = QComboBox()
        self.mode.addItems(GENERATION_MODES)

        self.interval = QSpinBox()
        self.interval.setRange(MIN_INTERVAL_MS, MAX_INTERVAL_MS)
        self.interval.setValue(REFRESH_MS)
        self.interval.setSuffix(" ms")
        self.interval.valueChanged.connect(self.interval_changed)

        generate = QPushButton("+ Generate event")
        generate.clicked.connect(self.generate_requested)

        clear = QPushButton("Clear log")
        clear.clicked.connect(self.clear_requested)

        layout.addWidget(QLabel("Generation:"))
        layout.addWidget(self.mode)
        layout.addWidget(QLabel("Interval:"))
        layout.addWidget(self.interval)
        layout.addWidget(generate)
        layout.addWidget(clear)
        layout.addStretch()

    @property
    def current_mode(self):
        return self.mode.currentText()
