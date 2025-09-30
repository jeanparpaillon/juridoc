import logging

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QScrollArea
)

from juridoc.db_loader import load_sources
from .source_widget import SourceWidget

logger = logging.getLogger(__name__)

class SourcesWidget(QWidget):
    def __init__(self):
        super().__init__()
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

    def clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def populate_grid(self):
        row, col = 0, 0
        for src in load_sources():
            if src.relpath.lower().endswith('.pdf'):
                label = SourceWidget(src, size=self.label_size, parent=self)
                self.grid.addWidget(label, row, col)
                col += 1
                if col >= self.max_cols:
                    col = 0
                    row += 1

    def refresh(self):
        self.clear_grid()
        self.populate_grid()

    def select_source(self, source):
        self.selected_source = source
        # highlight or handle selection

    def open_source_tab(self, source):
        # emit signal or call parent to open tab
        pass
