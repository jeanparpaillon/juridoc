from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)

class SourcesWidget(QWidget):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo
        layout = QVBoxLayout()
        label = QLabel(f"Sources directory:\n{self.repo.sources_dir}")
        layout.addWidget(label)
        self.setLayout(layout)

