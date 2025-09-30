import logging
import os

from PySide6.QtCore import QObject, QFileSystemWatcher, Signal

from .config import Config
from .db import Db
from .sources_index import SourcesIndex
from .note import Note
from .source import Source
from .utils import file_hash

logger = logging.getLogger(__name__)

class Repo(QObject):
    notes_output_subdir = "notes"
    index_filename = "index.ods"
    sources_subdir = "sources"

    source_added = Signal(Source)
    source_changed = Signal(Source, list)
    source_deleted = Signal(Source)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sources_dir = None
        self.notes_dir = None
        self.output_dir = None

        self.sources = {}

        self.sources_watcher = None
        self.notes_watcher = None

        Config().config_changed.connect(self._on_config_changed)
        Config().load()

    def _on_config_changed(self, key, value):
        logger.debug(f"Config change: {key}={value}")
        if key == 'sources_dir':
            self.set_sources_dir(value)
        elif key == 'notes_dir':
            self.set_notes_dir(value)

    def set_sources_dir(self, sources_dir):
        sources_dir = os.path.realpath(sources_dir)
        logger.info(f"Set sources dir: {sources_dir}")

        if sources_dir == self.sources_dir:
            return self
        
        if sources_dir is None:
            self._cleanup_sources_dir(self.sources_dir)
            self.sources_dir = None
            return self
        
        self.sources_dir = sources_dir

        if self.sources_watcher is not None:
            self.sources_watcher.deleteLater()
        
        self.sources_watcher = QFileSystemWatcher(self)
        self.sources_watcher.fileChanged.connect(self._on_source_file_changed)
        self.sources_watcher.directoryChanged.connect(self._on_source_dir_changed)

        self._traverse_source_dir(sources_dir)

        return self
    
    def _traverse_source_dir(self, dir):
        sources_paths = []
        to_delete_ids = set()
        normdir = os.path.normpath(dir)

        with Db().get_conn() as conn:
            cur = conn.cursor()
            ret = cur.execute('''
                    SELECT id 
                    FROM source
                    WHERE (sources_dir || '/' || path) GLOB ?
                ''', (f"{normdir}/*",)).fetchall()
            to_delete_ids = set([row['id'] for row in ret])

            for dirpath, _, filenames in os.walk(normdir):
                self.sources_watcher.addPath(dirpath)
                self.sources_watcher.addPaths(filenames)

                for filename in sorted(filenames):
                    filepath = os.path.join(dirpath, filename)
                    relpath = os.path.relpath(filepath, self.sources_dir)
                    sources_paths.append(relpath)
                    id = self._process_source(relpath, conn)
                    to_delete_ids.discard(id)

            self._cleanup_source_db(to_delete_ids, conn)

        return self

    def _cleanup_source_db(self, to_delete_ids, conn=Db().get_conn()):
        with conn:
            to_delete = ", ".join("?" * len(to_delete_ids))
            sql = f"DELETE FROM source WHERE id IN ({to_delete})"
            conn.execute(sql, list(to_delete_ids))
            conn.commit()

        return self
    
    def _process_source(self, relpath, conn=Db().get_conn()):
        id = None

        with conn:
            hash = file_hash(os.path.join(self.sources_dir, relpath))
            row = conn.execute('''
                    SELECT s.id AS id, s.hash AS hash, s.sources_dir AS sources_dir, s.path AS path, s.image AS image, CASE WHEN x.id IS NOT NULL THEN 1 ELSE 0 END AS xref
                    FROM source AS s
                    LEFT JOIN xref AS x ON s.hash = x.source_hash
                    WHERE s.hash = ? OR (s.sources_dir = ? AND s.path = ?)
                    GROUP BY s.id
                ''', (hash, self.sources_dir, relpath)).fetchone()

            source = None
            changes = []

            if row:
                id = row['id']
                if id in self.sources:
                    source = self.sources[id]
                else:
                    source = Source(self.sources_dir, relpath, id=id, parent=self)

                if source.set_hash(row['hash']):
                    logger.info(f"Source content changed: {source.relpath}")
                    changes.append(Source.HASH)
                else:
                    source.set_thumbnail(row['image'])

                if source.set_path(row['sources_dir'], row['path']):
                    logger.info(f"Source renamed: {source.relpath}")
                    changes.append(Source.PATH)

                if source.set_xref(bool(row['xref'])):
                    changes.append(Source.XREF)
                    
                if id in self.sources:
                    source.save(conn)
                    if len(changes) > 0:
                        self.source_changed.emit(source, changes)
                else:
                    source.save(conn)
                    self.sources[id] = source
                    self.source_added.emit(source)
            else:
                # Not in DB
                logger.info(f"Source added: {relpath}")
                source = Source(self.sources_dir, relpath, hash=hash, parent=self)
                id = source.save(conn)
                source.set_id(id)
                self.sources[id] = source
                self.source_added.emit(source)

        return id
    
    def _cleanup_sources_dir(self, dir, conn=Db().get_conn()):
        normpath = os.path.normpath(dir)
        
        with conn:
            cur = conn.cursor()
            ret = cur.execute('''
                    SELECT path FROM source
                    WHERE (sources_dir || '/' || path) GLOB '?/%'
                ''', (normpath,))
            for path in ret:
                self._cleanup_source(os.path.relpath(path, self.sources_dir))

        self.sources_watcher.removePath(normpath)

    def _cleanup_source(self, relpath, conn=Db().get_conn()):
        logger.info(f"Source removed: {relpath}")

        id = None
        with conn:
            cur = conn.cursor()
            cur.execute('''
                    DELETE FROM source
                    WHERE sources_dir = ? AND path = ?
                    RETURNING id
                ''', (self.sources_dir, relpath))
            id = cur.fetchone()[0]

        self.sources_watcher.removePath(os.path.join(self.sources_dir, relpath))

        if id:
            source = self.sources[id]
            source.deleteLater()
            self.source_deleted.emit(source)

    def _on_source_file_changed(self, path):
        if os.path.exists(path):
            self._process_source(os.path.relpath(path, self.sources_dir))
        else:
            with Db().get_conn() as conn:
                self._cleanup_source(path, conn)

    def _on_source_dir_changed(self, path):
        if os.path.exists(path):
            self._traverse_source_dir(path)
        else:
            self._cleanup_sources_dir(path)

    def set_notes_dir(self, notes_dir):
        self.notes_dir = notes_dir
        self._analyse_notes()
        return self

    def set_output_dir(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        return self

    def export_notes(self):
        output_notes_dir = os.path.join(self.output_dir, self.notes_output_subdir)
        os.makedirs(output_notes_dir, exist_ok=True)
    
        #for note in load_notes():
        #    note.process(output_notes_dir)

    def export_index(self):
        index = SourcesIndex().load()
        index.export(os.path.join(self.output_dir, self.index_filename))

    def export_sources(self):
        output_sources_dir = os.path.join(self.output_dir, self.sources_subdir)
        os.makedirs(output_sources_dir, exist_ok=True)

        #for source in load_sources():
        #    src_path = os.path.join(self.sources_dir, source.relpath)
        #    dest_path = os.path.join(output_sources_dir, source.relpath)
        #    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        #    shutil.copy2(src_path, dest_path)
        #    logging.info(f"Copied source: {source.relpath}")

    def _analyse_notes(self):
        if self.notes_dir is None:
            return self
        
        with Db().get_conn() as conn:
            conn.execute('DELETE FROM notes')

            for dirpath, _, filenames in os.walk(self.notes_dir):
                for filename in sorted(filenames):
                    filepath = os.path.join(dirpath, filename)
                    Note(self.notes_dir, os.path.relpath(filepath, self.notes_dir)).analyse().save(conn)
            conn.commit()

        return self
