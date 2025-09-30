from .db import Db

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def get(self, key):
        with Db().get_conn() as conn:
            ret = conn.execute('SELECT value FROM config WHERE key = ?', (key,)).fetchone()
            if ret:
                return ret[0]
        return None

    def set(self, key, value):
        with Db().get_conn() as conn:
            ret = conn.execute('''
                    INSERT OR REPLACE INTO config (key, value)
                    VALUES (?, ?)
                  ''', (key, value))
            conn.commit()