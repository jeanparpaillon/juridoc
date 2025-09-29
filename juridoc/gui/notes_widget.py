from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)

class NotesWidget(QWidget):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo
        layout = QVBoxLayout()
        label = QLabel(f"Notes directory:\n{self.repo.notes_dir}")
        layout.addWidget(label)
        self.setLayout(layout)

