import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTabWidget, QToolBar
)
from PySide6.QtCore import QSize

from juridoc import Repo
from juridoc.gui import SourcesWidget
from juridoc.gui import NotesWidget

class JuridocGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.repo = Repo()

        self.setWindowTitle("Juridoc")
        self.setGeometry(100, 100, 1000, 600)
        
        # --- Toolbar ---
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(120, 40))  # large icons/buttons
        self.addToolBar(toolbar)

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
        self.setCentralWidget(self.tabs)

        # Keep track of tabs we’ve created
        self.tab_refs = {}

    def set_sources_dir(self):
        directory = QFileDialog.getExistingDirectory(self, f"Select Sources Directory")
        if not directory:
            return

        self.repo.set_sources_dir(directory)
        if 'src_tab' in self.tab_refs:
            idx = self.tabs.indexOf(self.tab_refs['src_tab'])
            if idx != -1:
                widget = self.tab_refs['src_tab']
                self.tabs.setCurrentIndex(idx)
        else:
            widget = SourcesWidget(self.repo)
            idx = self.tabs.addTab(widget, "Sources")
            self.tab_refs['src_tab'] = widget
            self.tabs.setCurrentIndex(idx)

    def set_notes_dir(self):
        directory = QFileDialog.getExistingDirectory(self, f"Select Notes Directory")
        if not directory:
            return

        self.repo.set_notes_dir(directory)
        if 'notes_tab' in self.tab_refs:
            idx = self.tabs.indexOf(self.tab_refs['notes_tab'])
            if idx != -1:
                widget = self.tab_refs['notes_tab']
                self.tabs.setCurrentIndex(idx)
        else:
            widget = NotesWidget(self.repo)
            idx = self.tabs.addTab(widget, "Notes")
            self.tab_refs['notes_tab'] = widget
            self.tabs.setCurrentIndex(idx)

def run():
    app = QApplication(sys.argv)
    window = JuridocGUI()
    window.show()
    app.exec()
