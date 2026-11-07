"""Charts drawn with QPainter."""

from collections import deque

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

FONT_FAMILY = "Segoe UI"


class BaseChart(QWidget):
    """Background and title shared by all charts."""

    BACKGROUND = QColor("#111827")
    TITLE_COLOR = QColor("#e5e7eb")

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.setMinimumHeight(190)

    def _begin_paint(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.BACKGROUND)

        painter.setPen(self.TITLE_COLOR)
        painter.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.DemiBold))
        painter.drawText(16, 22, self.title)
        return painter


class LineChart(BaseChart):
    LINE_COLOR = QColor("#38bdf8")

    def __init__(self, title, suffix="", parent=None):
        super().__init__(title, parent)
        self.suffix = suffix
        self.values = deque(maxlen=35)

    def add_value(self, value):
        self.values.append(value)
        self.update()

    def paintEvent(self, event):
        painter = self._begin_paint()

        if not self.values:
            painter.setPen(QColor("#64748b"))
            painter.drawText(16, 100, "Waiting for data...")
            return

        chart = QRectF(18, 42, self.width() - 34, self.height() - 65)
        maximum = max(max(self.values), 1)

        self._draw_grid(painter, chart)
        points = self._compute_points(chart, maximum)
        self._draw_series(painter, points)
        self._draw_maximum(painter, chart, maximum)

    @staticmethod
    def _draw_grid(painter, chart):
        painter.setPen(QPen(QColor("#253044"), 1))
        for i in range(1, 5):
            y = int(chart.top() + chart.height() * i / 5)
            painter.drawLine(int(chart.left()), y, int(chart.right()), y)

    def _compute_points(self, chart, maximum):
        count = len(self.values)
        points = []

        for i, value in enumerate(self.values):
            x = chart.left() if count == 1 else chart.left() + chart.width() * i / (count - 1)
            y = chart.bottom() - (value / maximum) * chart.height()
            points.append(QPointF(float(x), float(y)))

        return points

    def _draw_series(self, painter, points):
        painter.setPen(QPen(self.LINE_COLOR, 2))
        for start, end in zip(points, points[1:]):
            painter.drawLine(start, end)

        painter.setBrush(self.LINE_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        for point in points:
            painter.drawEllipse(point, 2.5, 2.5)

    def _draw_maximum(self, painter, chart, maximum):
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont(FONT_FAMILY, 8))
        painter.drawText(
            int(chart.right() - 80),
            int(chart.top() - 5),
            f"{int(maximum)}{self.suffix}",
        )


class BarChart(BaseChart):
    BAR_COLOR = QColor("#6366f1")
    MAX_BARS = 7

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.data = {}

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = self._begin_paint()

        if not self.data:
            return

        labels = list(self.data)[: self.MAX_BARS]
        values = [self.data[label] for label in labels]
        maximum = max(values + [1])

        area = QRectF(20, 50, self.width() - 40, self.height() - 72)
        bar_width = area.width() / max(len(labels), 1) * 0.55

        for i, (label, value) in enumerate(zip(labels, values)):
            x = area.left() + (i + 0.5) * area.width() / len(labels) - bar_width / 2
            height = value / maximum * area.height()
            y = area.bottom() - height

            self._draw_bar(painter, x, y, bar_width, height)
            self._draw_value(painter, x, y, bar_width, value)
            self._draw_label(painter, x, area.bottom(), bar_width, label)

    def _draw_bar(self, painter, x, y, width, height):
        painter.setBrush(self.BAR_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(x, y, width, height), 4, 4)

    @staticmethod
    def _draw_value(painter, x, y, width, value):
        painter.setPen(QColor("#e5e7eb"))
        painter.drawText(
            QRectF(x, y - 20, width, 18),
            Qt.AlignmentFlag.AlignCenter,
            str(value),
        )

    @staticmethod
    def _draw_label(painter, x, bottom, width, label):
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont(FONT_FAMILY, 7))
        painter.drawText(
            QRectF(x - 18, bottom + 5, width + 36, 28),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            label.replace("_", " ")[:13],
        )
