"""Full-window intrusion alert shown when the Arduino button is pressed."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..config import (
    ALERT_LEVEL_HIGH,
    ALERT_LEVEL_LOW,
    ALERT_LEVEL_MEDIUM,
    ALERT_LEVEL_COLORS,
)

LEVEL_BACKGROUNDS = {
    ALERT_LEVEL_LOW: "#04150c",
    ALERT_LEVEL_MEDIUM: "#1b1203",
    ALERT_LEVEL_HIGH: "#1d0508",
}

LEVEL_HINTS = {
    ALERT_LEVEL_LOW: "Nivel bajo · actividad dentro de lo normal.",
    ALERT_LEVEL_MEDIUM: "Nivel intermedio · advertencia, el acceso sigue en riesgo.",
    ALERT_LEVEL_HIGH: "Nivel alto · alarma sonora activa, umbral de seguridad superado.",
}

MODE_ALERT = "alert"
MODE_BLOCKED = "blocked"

# Design reference: the overlay was laid out for a 1450 x 900 window.  The
# whole block is scaled down on smaller screens so the alert never spills out
# of the visible area.
BASE_WIDTH = 1450
BASE_HEIGHT = 900
MIN_SCALE = 0.62
MAX_SCALE = 1.35


class IntrusionOverlay(QWidget):
    """Large, unmissable page that replaces the dashboard during an alert."""

    demo_reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IntrusionOverlay")

        self._mode = MODE_ALERT
        self._level = ALERT_LEVEL_LOW
        self._attempts = 0
        self._simulated = False
        self._connected = False
        self._port = ""
        self._pulse = False
        self._scale = 1.0

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(550)
        self._pulse_timer.timeout.connect(self._toggle_pulse)

        self._build_ui()
        self._apply_style()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(64, 42, 64, 44)
        root.setSpacing(14)

        top = QVBoxLayout()
        top.setSpacing(4)

        self.eyebrow = QLabel("ALERTA DE SEGURIDAD")
        self.eyebrow.setObjectName("AlertEyebrow")
        self.eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.connection = QLabel("Arduino Uno · sin conexión")
        self.connection.setObjectName("AlertConnection")
        self.connection.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top.addWidget(self.eyebrow)
        top.addWidget(self.connection)
        root.addLayout(top)

        # Fixed spacer instead of a flexible stretch: the alert always starts
        # at the same height, even after several consecutive alerts.
        self._top_spacer = QSpacerItem(
            0, 28, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        root.addSpacerItem(self._top_spacer)

        self.shield = QLabel("⚠")
        self.shield.setObjectName("AlertShield")
        self.shield.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel("Alguien está intentando ingresar al sistema")
        self.title.setObjectName("AlertTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)

        self.attempts = QLabel("Intentos (0)")
        self.attempts.setObjectName("AlertAttempts")
        self.attempts.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.level = QLabel("Alerta: Baja")
        self.level.setObjectName("AlertLevel")
        self.level.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.instruction = QLabel(
            "Presiona el botón de RESET para bloquear el acceso"
        )
        self.instruction.setObjectName("AlertInstruction")
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction.setWordWrap(True)

        self.footer = QLabel(LEVEL_HINTS[ALERT_LEVEL_LOW])
        self.footer.setObjectName("AlertFooter")
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer.setWordWrap(True)

        self.demo_reset = QPushButton("Simular RESET (demo)")
        self.demo_reset.setObjectName("DemoReset")
        self.demo_reset.clicked.connect(lambda: self.demo_reset_requested.emit())
        self.demo_reset.hide()

        root.addWidget(self.shield)
        root.addWidget(self.title)
        root.addSpacing(4)
        root.addWidget(self.attempts)
        root.addWidget(self.level, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addSpacing(8)
        root.addWidget(self.instruction)
        root.addWidget(self.footer)
        root.addSpacing(4)
        root.addWidget(self.demo_reset, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_attempt(self, attempts, level, simulated=False):
        self._mode = MODE_ALERT
        self._attempts = attempts
        self._level = level
        self._simulated = simulated

        self.eyebrow.setText("ALERTA DE SEGURIDAD")
        self.shield.setText("⚠")
        self.title.setText("Alguien está intentando ingresar al sistema")
        self.attempts.setText(f"Intentos ({attempts})")
        self.level.setText(f"Alerta: {level}")
        self.instruction.setText(
            "Presiona el botón de RESET para bloquear el acceso"
        )
        self.footer.setText(LEVEL_HINTS.get(level, ""))
        self.demo_reset.setVisible(simulated)
        self._refresh_state()

    def show_blocked(self, simulated=False):
        self._mode = MODE_BLOCKED
        self._attempts = 0
        self._level = ALERT_LEVEL_LOW
        self._simulated = simulated

        self.eyebrow.setText("ACCESO BLOQUEADO")
        self.shield.setText("✓")
        self.title.setText("Sistema reiniciado")
        self.attempts.setText("Intentos (0)")
        self.level.setText("Contador restablecido")
        self.instruction.setText("El acceso quedó bloqueado.")
        self.footer.setText(
            "Botón RESET recibido desde Arduino Uno. "
            "La alerta se cerrará automáticamente."
        )
        self.demo_reset.hide()
        self._refresh_state()

    def set_level(self, level):
        """Update the level when the Arduino sends a later NIVEL line."""
        if self._mode != MODE_ALERT or level == self._level:
            return

        self._level = level
        self.level.setText(f"Alerta: {level}")
        self.footer.setText(LEVEL_HINTS.get(level, ""))
        self._refresh_state()

    def set_connection_state(self, connected, port=""):
        self._connected = connected
        self._port = port or ""
        self._update_connection_label()

    # ------------------------------------------------------------------
    # Appearance
    # ------------------------------------------------------------------

    def _refresh_state(self):
        self._update_connection_label()
        self._apply_style()
        self._update_pulse()

        # Force a fresh layout calculation so repeated alerts never inherit
        # the geometry of the previous state.
        layout = self.layout()
        if layout is not None:
            layout.invalidate()
            layout.activate()
        self.updateGeometry()

    def _update_connection_label(self):
        if self._simulated:
            self.connection.setText("MODO DEMOSTRACIÓN · sin hardware")
        elif self._connected:
            self.connection.setText(
                f"Arduino Uno · {self._port} · monitoreo en tiempo real"
            )
        else:
            self.connection.setText(
                "Arduino Uno · sin conexión (mostrando la última alerta)"
            )

    def _current_scale(self):
        width, height = self.width(), self.height()
        parent = self.parentWidget()
        if parent is not None:
            width, height = parent.width(), parent.height()

        width = max(width, 640)
        height = max(height, 480)
        scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
        return max(MIN_SCALE, min(MAX_SCALE, scale))

    def _apply_metrics(self, scale):
        layout = self.layout()
        if layout is not None:
            horizontal = max(8, round(64 * scale))
            layout.setContentsMargins(
                horizontal,
                max(6, round(42 * scale)),
                horizontal,
                max(6, round(44 * scale)),
            )
            layout.setSpacing(max(3, round(14 * scale)))

        self._top_spacer.changeSize(
            0,
            max(2, round(28 * scale)),
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )

    def _apply_style(self):
        scale = self._current_scale()
        self._scale = scale
        self._apply_metrics(scale)

        def px(value):
            return max(1, round(value * scale))

        if self._mode == MODE_BLOCKED:
            color = ALERT_LEVEL_COLORS[ALERT_LEVEL_LOW]
            background = "#04170d"
            border = color
        else:
            color = ALERT_LEVEL_COLORS.get(self._level, "#ef4444")
            background = LEVEL_BACKGROUNDS.get(self._level, "#1d0508")
            border = color
            if self._level == ALERT_LEVEL_HIGH:
                if self._pulse:
                    color = "#fecaca"
                    background = "#30070c"
                    border = "#fecaca"

        border_px = max(1, round(2 * scale))

        self.setStyleSheet(
            f"""
            QWidget#IntrusionOverlay {{
                background-color: {background};
            }}
            QLabel#AlertEyebrow {{
                color: {color};
                font-size: {px(17)}px;
                font-weight: 800;
            }}
            QLabel#AlertConnection {{
                color: #94a3b8;
                font-size: {px(12)}px;
            }}
            QLabel#AlertShield {{
                color: {color};
                font-size: {px(92)}px;
                font-weight: 900;
            }}
            QLabel#AlertTitle {{
                color: #f8fafc;
                font-size: {px(52)}px;
                font-weight: 800;
            }}
            QLabel#AlertAttempts {{
                color: #f8fafc;
                font-size: {px(68)}px;
                font-weight: 900;
            }}
            QLabel#AlertLevel {{
                color: {color};
                background-color: rgba(0, 0, 0, 90);
                border: {border_px}px solid {color};
                border-radius: {px(18)}px;
                padding: {px(10)}px {px(38)}px;
                font-size: {px(44)}px;
                font-weight: 900;
            }}
            QLabel#AlertInstruction {{
                color: #f8fafc;
                background-color: #111827;
                border: {border_px}px solid {border};
                border-radius: {px(14)}px;
                padding: {px(16)}px {px(32)}px;
                font-size: {px(29)}px;
                font-weight: 700;
            }}
            QLabel#AlertFooter {{
                color: #94a3b8;
                font-size: {px(13)}px;
            }}
            QPushButton#DemoReset {{
                color: #e5e7eb;
                background-color: #111827;
                border: {border_px}px solid {border};
                border-radius: {px(8)}px;
                padding: {px(8)}px {px(20)}px;
                font-size: {px(12)}px;
                font-weight: 700;
            }}
            QPushButton#DemoReset:hover {{
                background-color: #1f2937;
            }}
            """
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        scale = self._current_scale()
        if abs(scale - self._scale) > 0.01:
            self._scale = scale
            self._refresh_state()

    def _update_pulse(self):
        should_pulse = (
            self._mode == MODE_ALERT and self._level == ALERT_LEVEL_HIGH
        )

        if should_pulse and not self._pulse_timer.isActive():
            self._pulse_timer.start()
        elif not should_pulse:
            self._pulse_timer.stop()
            self._pulse = False

    def _toggle_pulse(self):
        self._pulse = not self._pulse
        self._apply_style()
