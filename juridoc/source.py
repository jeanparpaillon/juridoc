import logging

from PySide6.QtCore import QObject, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QPixmap

from .db import Db
from .utils import *

logger = logging.getLogger(__name__)

class Source(QObject):
    HASH = 0
    PATH = 1
    XREF = 2

    def __init__(self, sources_dir, path, hash=None, xref=False, id=None, parent=None):
        super().__init__(parent)

        # path is relative to sources_dir
        self.id = id
        self.hash = hash
        self.sources_dir = sources_dir
        self.relpath = path
        self.xref = xref
        self.thumbnail = None

    def set_id(self, id):
        self.id = id

    def set_hash(self, hash):
        if self.hash == hash:
            return False
        else:
            self.hash = hash
            self.thumbnail = None
            return True

    def set_path(self, sources_dir, path):
        if self.sources_dir == sources_dir and self.relpath == path:
            return False
        else:
            self.sources_dir = sources_dir
            self.relpath = path
            return True
        
    def set_xref(self, xref):
        if self.xref == xref:
            return False
        else:
            self.xref = xref
            return True

    def set_thumbnail(self, data):
        if self.thumbnail == None and data == b'':
            return False
        elif data == b'':
            self.thumbnail = None
            return True
        else:
            ba = QByteArray(data)
            self.thumbnail = QPixmap()
            self.thumbnail.loadFromData(ba, "PNG")
            return True

    def save(self, conn=Db().get_conn()):
        if not self.hash:
            raise ValueError("Source must be loaded before saving")

        ba = QByteArray()
        if self.thumbnail:
            buffer = QBuffer(ba)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            self.thumbnail.save(buffer, "PNG")
            buffer.close()

        id = None
        with conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT  INTO source (id, hash, sources_dir, path, image)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    hash=excluded.hash,
                    sources_dir=excluded.sources_dir,
                    path=excluded.path,
                    image=excluded.image
            ''', (self.id, self.hash, self.sources_dir, self.relpath, ba.data()))
            id = cur.lastrowid
        
        return id
    
