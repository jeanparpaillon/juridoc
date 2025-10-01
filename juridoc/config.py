import logging

from PySide6.QtCore import QObject, Signal

from .db import Db

logger = logging.getLogger(__name__)

class Config(QObject):
    _instance = None
    _initialized = False

    config_changed = Signal(str, str)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            super().__init__()
            self._initialized = True

    def load(self):
        with Db().get_conn() as conn:
            for row in conn.execute('SELECT key, value FROM config'):
                key = row['key']
                value = row['value']
                logger.debug(f"Read config: {key}={value}")
                self.config_changed.emit(key, value)

    def get(self, key: str) -> str:
        value = None

        with Db().get_conn() as conn:
            ret = conn.execute('SELECT value FROM config WHERE key = ?', (key,)).fetchone()
            if ret:
                value = ret[0]

        return value

    def set(self, key: str, value: str) -> None:
        with Db().get_conn() as conn:
            conn.execute('''
                    INSERT INTO config (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value=excluded.value
                  ''', (key, value))
            
        self.config_changed.emit(key, value)