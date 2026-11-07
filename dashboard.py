"""Main window of the security monitor."""

from collections import deque
from datetime import datetime

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .arduino_link import (
    ArduinoReader,
    level_for_attempts,
    list_serial_ports,
    parse_arduino_line,
)
from .config import (
    ACTION_NONE,
    ALERT_LEVEL_HIGH,
    ALERT_LEVEL_SEVERITIES,
    ARDUINO_AUTO_PORT,
    BLOCKED_MESSAGE_MS,
    INITIAL_NORMAL_EVENTS,
    MAX_EVENTS,
    PHYSICAL_EVENT_TYPE,
    PHYSICAL_RESET_TYPE,
    REFRESH_MS,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    UNIVERSITY,
)
from .event_generator import EventGenerator
from .simulation import Telemetry, next_event
from .state import SecurityState, count_by_category, count_by_severity
from .theme import STYLESHEET
from .widgets import (
    ActionDialog,
    AlertPanel,
    BarChart,
    ControlBar,
    EventTable,
    IntrusionOverlay,
    LineChart,
    StatCard,
)

PORTS_REFRESH_MS = 4000


class SecurityDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.generator = EventGenerator()
        self.telemetry = Telemetry()
        self.state = SecurityState()
        self.events = deque(maxlen=MAX_EVENTS)

        self.arduino_attempts = 0
        self.arduino_connected = False
        self.arduino_port = ""

        self.setWindowTitle(f"{UNIVERSITY} - Security Event Monitor")
        self._fit_initial_window()

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(REFRESH_MS)

        self.blocked_timer = QTimer(self)
        self.blocked_timer.setSingleShot(True)
        self.blocked_timer.timeout.connect(self.hide_blocked_overlay)

        self.ports_timer = QTimer(self)
        self.ports_timer.timeout.connect(self.refresh_ports)
        self.ports_timer.start(PORTS_REFRESH_MS)

        self.arduino_reader = ArduinoReader(parent=self)
        self.arduino_reader.line_received.connect(self.handle_arduino_line)
        self.arduino_reader.connection_changed.connect(
            self.handle_arduino_connection
        )
        self.arduino_reader.status_message.connect(self.handle_arduino_message)
        self.arduino_reader.start()

        self.refresh_ports()

        for _ in range(INITIAL_NORMAL_EVENTS):
            self.add_event(self.generator.generate_normal())

    def _fit_initial_window(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1450, 900)
            return

        available = screen.availableGeometry()
        self.resize(
            min(1450, available.width() - 28),
            min(900, available.height() - 60),
        )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.dashboard_page = QWidget()
        root = QVBoxLayout(self.dashboard_page)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        root.addLayout(self._build_header())
        root.addLayout(self._build_stats())
        root.addWidget(self._build_controls())
        root.addLayout(self._build_charts())
        root.addLayout(self._build_content(), 1)

        self.overlay = IntrusionOverlay()
        self.overlay.demo_reset_requested.connect(self.demo_reset)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.overlay)
        self.stack.setCurrentWidget(self.dashboard_page)

    def _build_header(self):
        header = QHBoxLayout()
        titles = QVBoxLayout()

        title = QLabel("SECURITY CENTER")
        title.setObjectName("MainTitle")

        subtitle = QLabel("Event monitor • Nova University • SIMULATION + ARDUINO")
        subtitle.setObjectName("Subtitle")

        titles.addWidget(title)
        titles.addWidget(subtitle)

        self.arduino_label = QLabel("● ARDUINO: BUSCANDO…")
        self.arduino_label.setObjectName("ArduinoStatus")
        self._style_arduino_label(False, "", "BUSCANDO…")

        self.status_label = QLabel("● SYSTEM OPERATIONAL")
        self.status_label.setObjectName("SystemStatus")

        header.addLayout(titles)
        header.addStretch()
        header.addWidget(self.arduino_label)
        header.addWidget(self.status_label)
        return header

    def _build_stats(self):
        self.card_events = StatCard("Events processed", "0", "#38bdf8")
        self.card_intentos = StatCard("Physical attempts", "0", "#38bdf8")
        self.card_critical = StatCard("Critical", "0", "#ef4444")
        self.card_high = StatCard("High alerts", "0", "#f97316")
        self.card_users = StatCard("Active users", "0", "#22c55e")
        self.card_blocked = StatCard("Blocked IPs", "0", "#a78bfa")

        row = QHBoxLayout()
        for card in (
            self.card_events,
            self.card_intentos,
            self.card_critical,
            self.card_high,
            self.card_users,
            self.card_blocked,
        ):
            row.addWidget(card)
        return row

    def _build_controls(self):
        self.controls = ControlBar()
        self.controls.interval_changed.connect(self.on_interval_changed)
        self.controls.generate_requested.connect(self.manual_event)
        self.controls.clear_requested.connect(self.clear_log)
        self.controls.port_changed.connect(self.change_arduino_port)
        self.controls.ports_refresh_requested.connect(self.refresh_ports)
        self.controls.demo_attempt_requested.connect(self.demo_attempt)
        self.controls.demo_reset_requested.connect(self.demo_reset)
        return self.controls

    def _build_charts(self):
        self.traffic_chart = LineChart("NETWORK TRAFFIC", " MB/s")
        self.users_chart = LineChart("ACTIVE USERS")
        self.type_chart = BarChart("EVENTS BY CATEGORY")

        row = QHBoxLayout()
        for chart in (self.traffic_chart, self.users_chart, self.type_chart):
            row.addWidget(chart, 1)
        return row

    def _build_content(self):
        self.event_table = EventTable()

        self.alert_panel = AlertPanel()
        self.alert_panel.action_requested.connect(self.execute_action)

        row = QHBoxLayout()
        row.addWidget(self.event_table, 3)
        row.addWidget(self.alert_panel, 1)
        return row

    # ------------------------------------------------------------------
    # Arduino link
    # ------------------------------------------------------------------

    def refresh_ports(self):
        # Do not rebuild the list while the user has the dropdown open.
        if self.controls.port.view().isVisible():
            return
        self.controls.set_ports(list_serial_ports())

    def change_arduino_port(self, port):
        self.arduino_reader.set_port(port)

        if port == ARDUINO_AUTO_PORT:
            self._style_arduino_label(False, "", "BUSCANDO…")
        else:
            self._style_arduino_label(False, port, "CONECTANDO…")

    def handle_arduino_connection(self, connected, port):
        self.arduino_connected = connected
        self.arduino_port = port or ""
        self._style_arduino_label(connected, self.arduino_port)
        self.overlay.set_connection_state(connected, self.arduino_port)

    def handle_arduino_message(self, message):
        self.arduino_label.setToolTip(message)
        self.statusBar().showMessage(message, 8000)

    def handle_arduino_line(self, line):
        event = parse_arduino_line(line)
        kind = event["kind"]

        if kind == "attempt":
            attempts = event["attempts"]
            level = event["level"]
            self.arduino_attempts = attempts

            self.show_intrusion(attempts, level, simulated=False)
            self.log_physical_attempt(attempts, level, simulated=False)

        elif kind == "level":
            self.overlay.set_level(event["level"])

        elif kind == "alarm":
            self.overlay.set_level(ALERT_LEVEL_HIGH)

        elif kind == "reset":
            self.arduino_attempts = 0
            self.card_intentos.set_value(0)
            self.show_access_blocked(simulated=False)
            self.log_physical_reset(simulated=False)

    def _style_arduino_label(self, connected, port, state=None):
        if connected:
            text = f"● ARDUINO: {port}"
            color = "#22c55e"
            background = "#10251a"
            border = "#1f4d2c"
        elif state:
            text = f"● ARDUINO: {state}" if not port else f"● ARDUINO: {state} {port}"
            color = "#f59e0b"
            background = "#2a1d05"
            border = "#78560d"
        else:
            text = "● ARDUINO: DESCONECTADO"
            color = "#f59e0b"
            background = "#2a1d05"
            border = "#78560d"

        self.arduino_label.setText(text)
        self.arduino_label.setStyleSheet(
            f"color:{color};background:{background};border:1px solid {border};"
            "padding:8px 12px;border-radius:7px;font-size:10px;font-weight:700;"
        )

    # ------------------------------------------------------------------
    # Physical intrusion alerts
    # ------------------------------------------------------------------

    def show_intrusion(self, attempts, level, simulated=False):
        self.blocked_timer.stop()
        self.card_intentos.set_value(attempts)

        self.overlay.show_attempt(attempts, level, simulated=simulated)
        self.overlay.set_connection_state(self.arduino_connected, self.arduino_port)
        self.stack.setCurrentWidget(self.overlay)

        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()
        QApplication.alert(self, 0)

    def show_access_blocked(self, simulated=False):
        self.blocked_timer.stop()

        self.overlay.show_blocked(simulated=simulated)
        self.overlay.set_connection_state(self.arduino_connected, self.arduino_port)
        self.stack.setCurrentWidget(self.overlay)
        self.blocked_timer.start(BLOCKED_MESSAGE_MS)

    def hide_blocked_overlay(self):
        if self.stack.currentWidget() is self.overlay:
            self.stack.setCurrentWidget(self.dashboard_page)

    def demo_attempt(self):
        self.arduino_attempts += 1
        level = level_for_attempts(self.arduino_attempts)
        self.show_intrusion(self.arduino_attempts, level, simulated=True)
        self.log_physical_attempt(self.arduino_attempts, level, simulated=True)

    def demo_reset(self):
        self.arduino_attempts = 0
        self.card_intentos.set_value(0)
        self.show_access_blocked(simulated=True)
        self.log_physical_reset(simulated=True)

    def log_physical_attempt(self, attempts, level, simulated):
        source = "DEMO" if simulated else (self.arduino_port or "Arduino serial")
        self.add_event({
            "id": f"P-{attempts}",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user": "physical",
            "department": "Physical security",
            "source": source,
            "type": PHYSICAL_EVENT_TYPE,
            "severity": ALERT_LEVEL_SEVERITIES[level],
            "message": f"Physical access attempt #{attempts} · alert level {level}",
            "detail": f"Arduino button | attempts={attempts} | level={level}",
            "action": ACTION_NONE,
        })

    def log_physical_reset(self, simulated):
        source = "DEMO" if simulated else (self.arduino_port or "Arduino serial")
        self.add_event({
            "id": "P-RESET",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user": "physical",
            "department": "Physical security",
            "source": source,
            "type": PHYSICAL_RESET_TYPE,
            "severity": SEVERITY_INFO,
            "message": "Access blocked from the physical RESET button",
            "detail": "Arduino RESET button | counter restarted at 0",
            "action": ACTION_NONE,
        })

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def on_interval_changed(self, value):
        self.timer.setInterval(value)

    def tick(self):
        event = next_event(self.generator, self.controls.current_mode)
        self.add_event(event)

        self.traffic_chart.add_value(self.telemetry.sample_traffic(event))
        self.users_chart.add_value(self.telemetry.update_users(event))

        self.update_stats()

    def manual_event(self):
        self.add_event(self.generator.generate())

    def add_event(self, event):
        self.events.appendleft(event)
        self.refresh_views()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def execute_action(self, event):
        dialog = ActionDialog(event, event["action"], self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.state.apply_action(event)

        QMessageBox.information(
            self,
            "Action executed",
            f"{event['action']}\n\n"
            "SIMULATION:\n"
            "The action does not modify any real system.",
        )

        self.update_stats()

    def clear_log(self):
        self.events.clear()
        self.state.reset()
        self.refresh_views()

    # ------------------------------------------------------------------
    # View updates
    # ------------------------------------------------------------------

    def refresh_views(self):
        self.event_table.set_events(self.events)
        self.alert_panel.set_events(self.events)
        self.type_chart.set_data(count_by_category(self.events))
        self.update_stats()

    def update_stats(self):
        self.card_events.set_value(len(self.events))
        self.card_intentos.set_value(self.arduino_attempts)
        self.card_critical.set_value(count_by_severity(self.events, SEVERITY_CRITICAL))
        self.card_high.set_value(count_by_severity(self.events, SEVERITY_HIGH))
        self.card_users.set_value(len(self.telemetry.active_users))
        self.card_blocked.set_value(len(self.state.blocked_ips))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self.arduino_reader.stop()
        super().closeEvent(event)
