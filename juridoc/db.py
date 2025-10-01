import logging
import sqlite3

logger = logging.getLogger(__name__)

class Db:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Db, cls).__new__(cls)
            cls._instance.conn = None
        return cls._instance
    
    def init(self, path):
        self.open(path)

        with self.conn as conn:
            # Config table
            self._safe_create("table 'config'", '''
                CREATE TABLE config (
                    key TEXT PRIMARY KEY,
                    value TEXT              
                )
            ''', conn)

            # Source table
            self._safe_create("table 'source'", '''
                CREATE TABLE IF NOT EXISTS source (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT NOT NULL UNIQUE,
                    sources_dir TEXT,
                    path TEXT UNIQUE,
                    image BLOB
                )
            ''', conn)
            
            self._safe_create("index 'source <> hash'", '''
                CREATE INDEX IF NOT EXISTS idx_source_hash ON source(hash)
            ''', conn)

            # Notes table
            self._safe_create("table 'notes'", '''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notes_dir TEXT,
                    path TEXT UNIQUE
                )
            ''', conn)

            # Xref table
            self._safe_create("table 'xref'", '''
                CREATE TABLE IF NOT EXISTS xref (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_hash TEXT,
                    note_id INTEGER,
                    FOREIGN KEY (source_hash) REFERENCES source(hash),
                    FOREIGN KEY (note_id) REFERENCES notes(id),
                    UNIQUE(source_hash, note_id)
                )
            ''', conn)

    def _safe_create(self, name, sql, conn):
        try:
            conn.execute(sql)
            logger.info(f"Created {name}")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                pass
            else:
                raise

    def open(self, path):
        if path == ':memory:':
            db = "(RAM)"
        else:
            db = path

        logger.debug(f"Opening DB: {db}")
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

    def get_conn(self):
        return self.conn
    
    def save(self, path):
        logger.debug(f"Set DB path: {path}")

        file_conn = sqlite3.connect(path)
        self.conn.backup(file_conn)
        file_conn.close()
        self.conn.close()

        self.open(path)

    def close(self):
        logger.debug("Closing DB")
        self.conn.commit()
        self.conn.close()
