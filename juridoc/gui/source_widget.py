import logging
import os

from PySide6.QtWidgets import (
    QLabel, QFrame, QGraphicsColorizeEffect
)
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtCore import Qt, QSize, QMargins

from .pdf_thumbnailer import PdfThumbnailer

logger = logging.getLogger(__name__)

class SourceWidget(QLabel):
    def __init__(self, source, size=QSize(120, 160), parent=None):
        super().__init__(parent)

        self.source = source

        filepath = os.path.join(source.sources_dir, source.relpath)
        self.renderer = PdfThumbnailer(filepath, 0, self, size)
        
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setFixedSize(size)
        self.setStyleSheet("background: #eee;")

        if not source.xref:
            self.setGraphicsEffect(self._grey_effect())
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _grey_effect(self):
        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(128,128,128))
        effect.setStrength(0.5)
        return effect
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent().select_source(self.source)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent().open_source_tab(self.source)
