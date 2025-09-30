from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)

class NotesWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout()
        label = QLabel(f"Notes pane")
        self.layout.addWidget(label)
        self.setLayout(self.layout)

    def refresh(self):
        pass

