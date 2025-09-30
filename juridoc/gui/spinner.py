from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QColor

class Spinner(QWidget):
    def __init__(self, parent=None, line_count=12, line_length=8, line_width=3, inner_radius=10, speed=100):
        """
        line_count: number of spokes
        line_length: length of each spoke
        line_width: thickness of each spoke
        inner_radius: radius of empty center
        speed: rotation speed (ms per step)
        """
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.rotate)
        self._line_count = line_count
        self._line_length = line_length
        self._line_width = line_width
        self._inner_radius = inner_radius
        self._color = QColor(50, 150, 255)
        self._speed = speed

        self.setMinimumSize((self._inner_radius + self._line_length) * 2,
                            (self._inner_radius + self._line_length) * 2)

    def start(self):
        if not self._timer.isActive():
            self._timer.start(self._speed)
            self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def rotate(self):
        self._angle = (self._angle + 1) % self._line_count
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for i in range(self._line_count):
            painter.save()
            painter.translate(self.width() / 2, self.height() / 2)
            painter.rotate(360 * i / self._line_count)
            painter.translate(0, -self._inner_radius)

            alpha = 255 * ((i + self._angle) % self._line_count) / self._line_count
            color = QColor(self._color)
            color.setAlpha(int(alpha))

            pen = QPen(color)
            pen.setWidth(self._line_width)
            painter.setPen(pen)

            painter.drawLine(0, 0, 0, -self._line_length)
            painter.restore()
