"""Simulation and Arduino control bar."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config import (
    ARDUINO_AUTO_PORT,
    GENERATION_MODES,
    MAX_INTERVAL_MS,
    MIN_INTERVAL_MS,
    REFRESH_MS,
)


class ControlBar(QWidget):
    interval_changed = pyqtSignal(int)
    generate_requested = pyqtSignal()
    clear_requested = pyqtSignal()

    port_changed = pyqtSignal(str)
    ports_refresh_requested = pyqtSignal()
    demo_attempt_requested = pyqtSignal()
    demo_reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        layout.addLayout(self._build_simulation_row())
        layout.addLayout(self._build_arduino_row())

    def _build_simulation_row(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

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

        row.addWidget(QLabel("Generation:"))
        row.addWidget(self.mode)
        row.addWidget(QLabel("Interval:"))
        row.addWidget(self.interval)
        row.addWidget(generate)
        row.addWidget(clear)
        row.addStretch()
        return row

    def _build_arduino_row(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.port = QComboBox()
        self.port.setMinimumWidth(240)
        self.port.addItem(ARDUINO_AUTO_PORT, ARDUINO_AUTO_PORT)
        self.port.currentIndexChanged.connect(self._emit_port)

        refresh = QPushButton("Refresh ports")
        refresh.clicked.connect(self.ports_refresh_requested)

        attempt = QPushButton("Simular intento")
        attempt.setToolTip("Muestra la alerta sin usar la placa Arduino")
        attempt.clicked.connect(self.demo_attempt_requested)

        reset = QPushButton("Simular RESET")
        reset.setToolTip("Simula el botón físico de reinicio")
        reset.clicked.connect(self.demo_reset_requested)

        row.addWidget(QLabel("Arduino:"))
        row.addWidget(self.port)
        row.addWidget(refresh)
        row.addSpacing(14)
        row.addWidget(QLabel("Demo:"))
        row.addWidget(attempt)
        row.addWidget(reset)
        row.addStretch()
        return row

    @property
    def current_port(self):
        return self.port.currentData() or ARDUINO_AUTO_PORT

    @property
    def current_mode(self):
        return self.mode.currentText()

    def set_ports(self, ports):
        """Replace the port list while preserving the selected port."""
        selected = self.current_port

        self.port.blockSignals(True)
        self.port.clear()
        self.port.addItem(ARDUINO_AUTO_PORT, ARDUINO_AUTO_PORT)

        for device, description in ports:
            self.port.addItem(f"{device} — {description}", device)

        index = self.port.findData(selected)
        self.port.setCurrentIndex(index if index >= 0 else 0)
        self.port.blockSignals(False)

        if index < 0 and selected != ARDUINO_AUTO_PORT:
            self.port_changed.emit(ARDUINO_AUTO_PORT)

    def _emit_port(self, _index):
        self.port_changed.emit(self.current_port)
