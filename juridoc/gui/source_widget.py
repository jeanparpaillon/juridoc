import logging
import os

from PySide6.QtWidgets import (
    QLabel, QFrame, QGraphicsColorizeEffect
)
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtCore import Qt, QSize

from juridoc import Repo, Source

from .pdf_thumbnailer import PdfThumbnailer

logger = logging.getLogger(__name__)

class SourceWidget(QLabel):
    def __init__(self, source, size=QSize(120, 160), parent=None):
        super().__init__(parent)

        self.source = source
        self.renderer = None
        
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setFixedSize(size)
        self.setStyleSheet("background: #eee;")

        if self.source.thumbnail:
            self.setPixmap(self.source.thumbnail)
        else:
            self.renderer = PdfThumbnailer(self.source.fullpath(), 0, self, size, self)
            self.renderer.thumbnail_ready.connect(self.on_thumbnail_ready)

        self._set_xref_effect()
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        Repo().source_changed.connect(self.on_source_changed)

    def _set_xref_effect(self):
        if self.source.xref:
            self.setGraphicsEffect(None)
        else:
            effect = QGraphicsColorizeEffect()
            effect.setColor(QColor(128,128,128))
            effect.setStrength(0.5)
            self.setGraphicsEffect(effect)
    
    def on_source_changed(self, source, changes):
        if self.source.id == source.id:
            if Source.XREF in changes:
                self._set_xref_effect()

    def on_thumbnail_ready(self, id, pixmap):
        if self.renderer.id == id:
            self.setPixmap(pixmap)
            self.source.thumbnail = pixmap
            self.renderer = None
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent.select_source(self.source)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent.open_source_tab(self.source)
