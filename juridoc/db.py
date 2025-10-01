import logging
import sqlite3
import sys

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

        logger.debug(f"Opening DB: {db} (thread safety={sqlite3.threadsafety})")
        self.conn = sqlite3.connect(path, check_same_thread=(sqlite3.threadsafety != 3))
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

    def is_threadsafe(self):
        return sqlite3.threadsafety == 3

    def dump_threadsafety_infos(self):
        logger.info(f"Python version : {sys.version.split()[0]}")
        logger.info(f"sqlite3 module : {sqlite3.version}")
        logger.info(f"SQLite library : {sqlite3.sqlite_version}")
        logger.info(f"DB-API threadsafety : {sqlite3.threadsafety}")

        # Map DB-API level to description
        levels = {
            0: "Not thread-safe at all",
            1: "Module safe, but not connections",
            2: "Connections may be shared (not used in sqlite3)",
            3: "Module, connections and cursors are safe"
        }
        logger.info(f"Meaning : {levels.get(sqlite3.threadsafety, 'Unknown')}")

        # Try to get compile options
        try:
            conn = sqlite3.connect(":memory:")
            options = [row[0] for row in conn.execute("PRAGMA compile_options")]
            conn.close()
            ts_opts = [opt for opt in options if opt.startswith("THREADSAFE")]
            if ts_opts:
                logger.info(f"Compile option : {ts_opts[0]}")
            else:
                logger.info("Compile option : not available")
        except Exception as e:
            logger.info(f"Compile option : could not query ({e})")
