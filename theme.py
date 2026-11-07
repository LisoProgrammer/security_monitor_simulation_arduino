"""Application stylesheet."""

STYLESHEET = """
QMainWindow, QWidget {
    background: #0b1120;
    color: #e5e7eb;
    font-family: "Segoe UI";
}

/* Labels must not paint the global dark background: inside cards they would
   show as black boxes around every title.  Specific label styles that do want
   a background (for example #SystemStatus) still override this rule. */
QLabel {
    background: transparent;
}

QFrame#StatCard {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
}

QLabel#MainTitle {
    color: #f8fafc;
    font-size: 23px;
    font-weight: 750;
}

QLabel#Subtitle {
    color: #64748b;
    font-size: 11px;
}

QLabel#SystemStatus {
    color: #22c55e;
    background: #10251a;
    border: 1px solid #1f4d2c;
    padding: 8px 12px;
    border-radius: 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel#SectionTitle {
    color: #cbd5e1;
    font-size: 11px;
    font-weight: 700;
}

QFrame#AlertPanel {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
}

QFrame#AlertCard {
    background: #111827;
    border: 1px solid #293548;
    border-radius: 8px;
}

QScrollArea#AlertScroll {
    background: transparent;
    border: none;
}

QScrollArea#AlertScroll > QWidget > QWidget {
    background: transparent;
}

QWidget#AlertScrollBody {
    background: transparent;
}

QPushButton {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 10px;
}

QPushButton:hover {
    background: #334155;
}

QComboBox, QSpinBox {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px;
    color: #e5e7eb;
}

QTableWidget {
    background: #0f172a;
    border: 1px solid #1e293b;
    gridline-color: #1e293b;
    border-radius: 8px;
    selection-background-color: #1e3a5f;
    alternate-background-color: #111827;
}

QHeaderView::section {
    background: #111827;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #1e293b;
    padding: 8px;
    font-size: 9px;
    font-weight: 700;
}

QTableWidget::item {
    padding: 5px;
    border-bottom: 1px solid #182234;
    color: #cbd5e1;
    font-size: 10px;
}

QScrollBar:vertical {
    background: #0b1120;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
}

QStatusBar {
    background: #0f172a;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    font-size: 10px;
}

QStatusBar::item {
    border: none;
}
"""
