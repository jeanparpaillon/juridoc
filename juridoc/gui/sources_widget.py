import logging
import os

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QScrollArea
)

from .source_widget import SourceWidget

logger = logging.getLogger(__name__)

class SourcesWidget(QWidget):
    def __init__(self, repo, parent=None):
        super().__init__(parent)
        self.repo = repo
        repo.source_added.connect(self._on_source_added)
        repo.source_changed.connect(self._on_source_changed)
        repo.source_deleted.connect(self._on_source_deleted)

        self.selected_source = None

        logger.info("Creates sources widget")

        self.label_size = QSize(120, 160)
        self.max_cols = 6

        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.setAcceptDrops(not self.repo.sources_dir)

    def _on_source_added(self, source):
        logger.info(f"Source added: {source.id}")

    def _on_source_changed(self, source, changes):
        logger.info(f"Source changed: {source.id}: {changes}")

    def _on_source_deleted(self, source):
        logger.info(f"Source removed: {source.id}")

    def clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def dragEnterEvent(self, event):
        if not self.repo.sources_dir:
            urls = event.mimeData().urls()
            if len(urls) == 1:
                url = urls[0]
                if url.isLocalFile():
                    path = url.toLocalFile()
                    logger.debug(f"Event: {path}")
                    if os.path.isdir(path):
                        event.acceptProposedAction()
                        return

        event.ignore()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        path = url.toLocalFile()
        if os.path.isdir(path):
            self.repo.set_sources_dir(path)
            self.setAcceptDrops(False)

    #def populate_grid(self):
    #    row, col = 0, 0
    #    for src in load_sources():
    #        if src.relpath.lower().endswith('.pdf'):
    #            label = SourceWidget(src, size=self.label_size, parent=self)
    #            self.grid.addWidget(label, row, col)
    #            col += 1
    #            if col >= self.max_cols:
    #                col = 0
    #                row += 1

    def select_source(self, source):
        self.selected_source = source
        # highlight or handle selection

    def open_source_tab(self, source):
        # emit signal or call parent to open tab
        pass
