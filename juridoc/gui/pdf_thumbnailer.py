import logging

from PySide6.QtCore import Qt, QObject, QSize, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtPdf import QPdfDocument, QPdfPageRenderer
from PySide6.QtWidgets import QLabel

from .spinner import Spinner
from .style_factory import StyleFactory

logger = logging.getLogger(__name__)

class PdfThumbnailer(QObject):
    thumbnail_ready = Signal(int, QPixmap)

    def __init__(self, filename: str, page: int, target: QLabel, target_size=QSize(48, 48), parent=None):
        super().__init__(parent)
        self.target = target
        self.icon_size = target_size.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio)

        self.doc = QPdfDocument()
        self.doc.load(filename)
        self.filename = filename
        self.id = None

        # --- Show spinner while rendering ---
        self.spinner = Spinner(self.target)
        self.spinner.setFixedSize(self.icon_size)
        self.spinner.start()
        self.target.setPixmap(QPixmap())  # clear old pixmap

        # Create renderer with this object as parent
        self.renderer = QPdfPageRenderer(self)
        self.renderer.setDocument(self.doc)

        # Connect signals
        self.renderer.pageRendered.connect(self.on_page_rendered)

        # Kick off rendering
        thumbnail_size = (
            self
            .doc
            .pagePointSize(page)
            .scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio)
            .toSize()
        )
        self.id = self.renderer.requestPage(page, thumbnail_size)
        
    def on_page_rendered(self, _page, _size, image, _options, _request_id):
        self.spinner.stop()
        self.spinner.hide()

        if image.isNull():
            icon = StyleFactory().error_icon.pixmap(self.icon_size)
            self.thumbnail_ready.emit(self.id, icon)
        else:
            self.thumbnail_ready.emit(self.id, QPixmap.fromImage(image))

        self.cleanup()

    def cleanup(self):
        # Disconnect signals and delete this object
        self.renderer.pageRendered.disconnect(self.on_page_rendered)
        self.deleteLater()
