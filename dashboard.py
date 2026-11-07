"""Main window of the security monitor."""

from collections import deque

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .config import (
    INITIAL_NORMAL_EVENTS,
    MAX_EVENTS,
    REFRESH_MS,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
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
    LineChart,
    StatCard,
)


class SecurityDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.generator = EventGenerator()
        self.telemetry = Telemetry()
        self.state = SecurityState()
        self.events = deque(maxlen=MAX_EVENTS)

        self.setWindowTitle(f"{UNIVERSITY} - Security Event Monitor")
        self.resize(1450, 900)

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(REFRESH_MS)

        for _ in range(INITIAL_NORMAL_EVENTS):
            self.add_event(self.generator.generate_normal())

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        root.addLayout(self._build_header())
        root.addLayout(self._build_stats())
        root.addWidget(self._build_controls())
        root.addLayout(self._build_charts())
        root.addLayout(self._build_content(), 1)

    def _build_header(self):
        header = QHBoxLayout()
        titles = QVBoxLayout()

        title = QLabel("SECURITY CENTER")
        title.setObjectName("MainTitle")

        subtitle = QLabel("Event monitor • Nova University • SIMULATION")
        subtitle.setObjectName("Subtitle")

        titles.addWidget(title)
        titles.addWidget(subtitle)

        self.status_label = QLabel("● SYSTEM OPERATIONAL")
        self.status_label.setObjectName("SystemStatus")

        header.addLayout(titles)
        header.addStretch()
        header.addWidget(self.status_label)
        return header

    def _build_stats(self):
        self.card_events = StatCard("Events processed", "0", "#38bdf8")
        self.card_critical = StatCard("Critical", "0", "#ef4444")
        self.card_high = StatCard("High alerts", "0", "#f97316")
        self.card_users = StatCard("Active users", "0", "#22c55e")
        self.card_blocked = StatCard("Blocked IPs", "0", "#a78bfa")

        row = QHBoxLayout()
        for card in (
            self.card_events,
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
        self.card_critical.set_value(count_by_severity(self.events, SEVERITY_CRITICAL))
        self.card_high.set_value(count_by_severity(self.events, SEVERITY_HIGH))
        self.card_users.set_value(len(self.telemetry.active_users))
        self.card_blocked.set_value(len(self.state.blocked_ips))
