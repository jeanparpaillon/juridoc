from PySide6.QtWidgets import QStyle

class StyleFactory():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StyleFactory, cls).__new__(cls)
        return cls._instance

    def init(self, app):
        self.error_icon = app.style().standardIcon(QStyle.SP_MessageBoxCritical)
