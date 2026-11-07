"""Entry point: python run.py (or python -m monitor from the parent folder)"""

import sys

from PyQt6.QtWidgets import QApplication

from .config import APP_NAME
from .dashboard import SecurityDashboard


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = SecurityDashboard()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
