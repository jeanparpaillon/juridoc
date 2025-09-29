import logging
import os
from .utils import *

logger = logging.getLogger(__name__)

class Source():
    def __init__(self, sources_dir, path):
        # path is relative to sources_dir
        self.sources_dir = sources_dir
        self.relpath = path
        self.idx = None
        self.hash = None
        self.xref = False

    def load(self):
        path = os.path.join(self.sources_dir, self.relpath)

        try:
            h = file_hash(path)
            self.hash = h
            logger.info(f"Loaded source {self.hash}: {self.relpath}")
        except Exception as e:
            logger.error(f"ERROR {self.relpath}: {e}")
            return None

        return self

    def save(self, conn):
        if not self.hash:
            raise ValueError("Source must be loaded before saving")

        with conn:
            conn.execute('''
                INSERT OR IGNORE INTO source (hash, sources_dir, filepath)
                VALUES (?, ?, ?)
            ''', (self.hash, self.sources_dir, self.relpath))
        return self
