import sqlite3

class Db:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Db, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row

        with self.conn:
            # Config table
            self.conn.execute('''
                CREATE TABLE config (
                    key TEXT NOT NULL UNIQUE,
                    value TEXT              
                )
            ''')

            # Source table
            self.conn.execute('''
                CREATE TABLE source (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT NOT NULL UNIQUE,
                    sources_dir TEXT,
                    path TEXT UNIQUE,
                    image BLOB
                )
            ''')
            self.conn.execute('''CREATE INDEX idx_source_hash ON source(hash)''')

            # Notes table
            self.conn.execute('''
                CREATE TABLE notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notes_dir TEXT,
                    path TEXT UNIQUE
                )
            ''')

            # Xref table
            self.conn.execute('''
                CREATE TABLE xref (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_hash TEXT,
                    note_id INTEGER,
                    FOREIGN KEY (source_hash) REFERENCES source(hash),
                    FOREIGN KEY (note_id) REFERENCES notes(id),
                    UNIQUE(source_hash, note_id)
                )
            ''')

    def get_conn(self):
        return self.conn
    
    def load(self, path):
        file_conn = sqlite3.connect(path)
        file_conn.row_factory = sqlite3.Row
        file_conn.backup(self.conn)
        file_conn.close()
        return self
    
    def save(self, path):
        file_conn = sqlite3.connect(path)
        self.conn.backup(file_conn)
        self.conn = file_conn
        return self
