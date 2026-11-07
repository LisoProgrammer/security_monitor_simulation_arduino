"""Application dialogs."""

from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class ActionDialog(QDialog):
    """Asks for confirmation before running a simulated action."""

    def __init__(self, event, action, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm action")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        title = QLabel(f"Action: {action}")
        title.setStyleSheet("font-size:16px;font-weight:700;")

        information = QLabel(
            f"Event #{event['id']}\n"
            f"User: {event['user']}\n"
            f"IP: {event['source']}\n"
            f"Severity: {event['severity']}\n\n"
            f"{event['message']}"
        )
        information.setWordWrap(True)

        confirm = QPushButton("Run simulated action")
        cancel = QPushButton("Cancel")
        confirm.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

        layout.addWidget(title)
        layout.addWidget(information)
        layout.addSpacing(10)
        layout.addWidget(confirm)
        layout.addWidget(cancel)
