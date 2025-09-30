import logging
import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow,
    QPushButton, QFileDialog, QTabWidget, QToolBar
)
from PySide6.QtCore import QSize, Qt

from juridoc import Config
from juridoc import Db
from juridoc import Repo
from juridoc.gui import SourcesWidget
from juridoc.gui import NotesWidget

from .style_factory import StyleFactory

logger = logging.getLogger(__name__)

SRC_TAB = '0'
NOTES_TAB = '1'

class JuridocGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.repo = Repo()
        sources_dir = Config().get('sources_dir')
        if sources_dir:
            self.repo.set_sources_dir(sources_dir)

        notes_dir = Config().get('notes_dir')
        if notes_dir:
            self.repo.set_notes_dir(notes_dir)

        self.setWindowTitle("Juridoc")
        self.setGeometry(100, 100, 1000, 600)
        
        # --- Toolbar ---
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(120, 40))  # large icons/buttons
        self.addToolBar(toolbar)

        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setMinimumSize(120, 40)
        self.save_btn.clicked.connect(lambda: self.save_db())
        toolbar.addWidget(self.save_btn)

        # Sources button
        self.sources_btn = QPushButton("Sources…")
        self.sources_btn.setMinimumSize(120, 40)
        self.sources_btn.clicked.connect(lambda: self.set_sources_dir())
        toolbar.addWidget(self.sources_btn)

        # Notes button
        self.notes_btn = QPushButton("Notes…")
        self.notes_btn.setMinimumSize(120, 40)
        self.notes_btn.clicked.connect(lambda: self.set_notes_dir())
        toolbar.addWidget(self.notes_btn)

        # --- Central Tabs ---
        self.tabs = QTabWidget()
        
        self.sources_tab = SourcesWidget()
        self.sources_tab_idx = self.tabs.addTab(self.sources_tab, "Sources")
        
        self.notes_tab = NotesWidget()
        self.notes_tab_idx = self.tabs.addTab(self.notes_tab, "Notes")

        self.tabs.setCurrentIndex(self.sources_tab_idx)

        # Update Sources tab content once created
        self.sources_tab.refresh()

        self.setCentralWidget(self.tabs)

        # Keep track of tabs we’ve created
        self.tab_refs = {}

    def set_sources_dir(self):
        directory = QFileDialog.getExistingDirectory(self, f"Select Sources Directory")
        if not directory:
            return

        self.repo.set_sources_dir(directory)
        self.sources_tab.refresh()
        self.tabs.setCurrentIndex(self.sources_tab_idx)

    def set_notes_dir(self):
        directory = QFileDialog.getExistingDirectory(self, f"Select Notes Directory")
        if not directory:
            return

        self.repo.set_notes_dir(directory)
        self.notes_tab.refresh()
        self.tabs.setCurrentIndex(self.notes_tab_idx)

    def save_db(self):
        filename, _filter = QFileDialog.getSaveFileName(self, f"Select project filename", filter="Juridoc Project (*.jd)")
        Db().save(filename)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q and event.modifiers() & Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)

def run():
    logger.info("Start juridoc GUI")
    
    app = QApplication(sys.argv)
    StyleFactory().init(app)
    
    if len(sys.argv) > 1:
        Db().load(sys.argv[1])

    window = JuridocGUI()
    window.show()
    app.exec()
