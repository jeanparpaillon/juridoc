#!/usr/bin/env python3
import juridoc
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTabWidget
)

class JuridocGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Juridoc GUI")
        self.setGeometry(100, 100, 700, 400)
        self.init_ui()

    def init_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self.create_pdf_split_pane(), "PDF Split")
        tabs.addTab(self.create_commands_pane(), "Commands")
        self.setCentralWidget(tabs)

    def create_pdf_split_pane(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.pdf_status = QLabel("Ready.")
        layout.addWidget(self.pdf_status)

        self.pdf_btn = QPushButton("Select PDF for Split")
        self.pdf_btn.clicked.connect(self.select_pdf)
        layout.addWidget(self.pdf_btn)

        self.ranges_input = QLineEdit() 
        self.ranges_input.setPlaceholderText("Enter ranges (e.g. 2-3,5,7-9)")
        layout.addWidget(self.ranges_input)

        self.split_btn = QPushButton("Split PDF")
        self.split_btn.clicked.connect(self.split_pdf)
        layout.addWidget(self.split_btn)

        widget.setLayout(layout)
        self.selected_pdf = None
        return widget

    def create_commands_pane(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.cmd_status = QLabel("Ready.")
        layout.addWidget(self.cmd_status)

        self.dir_btn = QPushButton("Select Directory")
        self.dir_btn.clicked.connect(self.select_directory)
        layout.addWidget(self.dir_btn)

        self.index_btn = QPushButton("Update Index")
        self.index_btn.clicked.connect(self.update_index)
        layout.addWidget(self.index_btn)

        self.compile_btn = QPushButton("Compile Sources")
        self.compile_btn.clicked.connect(self.compile_sources)
        layout.addWidget(self.compile_btn)

        self.notes_btn = QPushButton("Generate Notes")
        self.notes_btn.clicked.connect(self.generate_notes)
        layout.addWidget(self.notes_btn)

        widget.setLayout(layout)
        self.selected_dir = None
        return widget

    def select_pdf(self):
        pdf_path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if pdf_path:
            self.selected_pdf = pdf_path
            self.pdf_status.setText(f"Selected PDF: {pdf_path}")

    def split_pdf(self):
        try:
            if not self.selected_pdf:
                self.pdf_status.setText("No PDF selected.")
                return
            ranges_str = self.ranges_input.text().strip()
            if not ranges_str:
                self.pdf_status.setText("No ranges specified.")
                return
            ranges = juridoc.parse_ranges(ranges_str)
            juridoc.split_pdf(self.selected_pdf, ranges)
            self.pdf_status.setText("PDF split completed.")
        except Exception as e:
            self.pdf_status.setText(f"Error: {e}")

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.selected_dir = dir_path
            self.cmd_status.setText(f"Selected directory: {dir_path}")

    def update_index(self):
        try:
            if not self.selected_dir:
                self.cmd_status.setText("No directory selected.")
                return
            repo = juridoc.load_repo(self.selected_dir)
            juridoc.gen_index(repo['index'])
            self.cmd_status.setText("Index updated.")
        except Exception as e:
            self.cmd_status.setText(f"Error: {e}")

    def compile_sources(self):
        try:
            if not self.selected_dir:
                self.cmd_status.setText("No directory selected.")
                return
            repo = juridoc.load_repo(self.selected_dir)
            juridoc.copy_sources(repo)
            self.cmd_status.setText("Sources compiled.")
        except Exception as e:
            self.cmd_status.setText(f"Error: {e}")

    def generate_notes(self):
        try:
            if not self.selected_dir:
                self.cmd_status.setText("No directory selected.")
                return
            repo = juridoc.load_repo(self.selected_dir)
            juridoc.process_notes(repo)
            self.cmd_status.setText("Notes generated.")
        except Exception as e:
            self.cmd_status.setText(f"Error: {e}")


def main():
    app = QApplication(sys.argv)
    window = JuridocGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
