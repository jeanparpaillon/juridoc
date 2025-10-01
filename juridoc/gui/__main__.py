import logging
import os
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

class JuridocGUI(QMainWindow):
    def __init__(self):
        super().__init__()

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
        
        self.sources_tab = SourcesWidget(parent=self)
        self.sources_tab_idx = self.tabs.addTab(self.sources_tab, "Sources")
        
        self.notes_tab = NotesWidget(parent=self)
        self.notes_tab_idx = self.tabs.addTab(self.notes_tab, "Notes")

        self.tabs.setCurrentIndex(self.sources_tab_idx)

        self.setCentralWidget(self.tabs)

        # Keep track of tabs we’ve created
        self.tab_refs = {}

    def set_sources_dir(self):
        directory = QFileDialog.getExistingDirectory(self, f"Select Sources Directory")
        if not directory:
            return

        Config().set('sources_dir', directory)
        self.tabs.setCurrentIndex(self.sources_tab_idx)

    def set_notes_dir(self):
        directory = QFileDialog.getExistingDirectory(self, f"Select Notes Directory")
        if not directory:
            return

        Config().set('notes_dir', directory)
        self.tabs.setCurrentIndex(self.notes_tab_idx)

    def save_db(self):
        filename, _filter = QFileDialog.getSaveFileName(self, f"Select project filename", filter="Juridoc Project (*.jd)")
        Db().save(filename)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q and event.modifiers() & Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)

def on_quit():
    logger.info("About to quit")
    Db().close()


RETURN_BADARG=1
RETURN_THREADSAFETY=2

def run():
    logger.info("Start juridoc GUI")
    
    # DB init
    if not Db().is_threadsafe():
        Db().dump_threadsafety_infos()

        if not os.environ.get('IGNORE_THREADSAFETY') == '1':
            logger.error("Dont't play with that !")
            return RETURN_THREADSAFETY

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if os.path.exists(db_path):
            Db().init(db_path)
        else:
            logger.error(f"Invalid DB path: {db_path}")
            return RETURN_BADARG
    else:
        Db().init(':memory:')

    # App init
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(on_quit)
    StyleFactory().init(app)
    
    window = JuridocGUI()
    window.show()

    # Repo init
    Repo().start()

    # Config must be last to load
    Config().load()

    app.exec()
