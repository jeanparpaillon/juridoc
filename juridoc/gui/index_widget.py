from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)

class IndexWidget(QWidget):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo
        layout = QVBoxLayout()
        label = QLabel(f"Index")
        layout.addWidget(label)
        self.setLayout(layout)

