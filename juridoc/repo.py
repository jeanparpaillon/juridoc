import logging
import os
import shutil

from .db import Db
from .sources_index import SourcesIndex
from .note import Note
from .source import Source

logger = logging.getLogger(__name__)

class Repo():
    notes_output_subdir = "notes"
    index_filename = "index.ods"
    sources_subdir = "sources"

    def __init__(self):
        super().__init__()

        self.sources_dir = None
        self.notes_dir = None
        self.index_path = None
        self.output_dir = None

    def set_sources_dir(self, sources_dir):
        self.sources_dir = sources_dir
        self._load()
        return self

    def set_notes_dir(self, notes_dir):
        self.notes_dir = notes_dir
        self._load()
        return self

    def set_output_dir(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        return self

    def export_notes(self):
        output_notes_dir = os.path.join(self.output_dir, self.notes_output_subdir)
        os.makedirs(output_notes_dir, exist_ok=True)
    
        with Db().get_conn() as conn:
            for row in conn.execute('SELECT id, filepath FROM notes ORDER BY id'):
                note = Note(self.notes_dir, row['filepath'])
                note.process(output_notes_dir)

    def export_index(self):
        index = SourcesIndex().load()
        index.export(os.path.join(self.output_dir, self.index_filename))

    def export_sources(self):
        output_sources_dir = os.path.join(self.output_dir, self.sources_subdir)
        os.makedirs(output_sources_dir, exist_ok=True)

        with Db().get_conn() as conn:
            for row in conn.execute('''
                    SELECT source.filepath
                    FROM source 
                    LEFT JOIN xref ON source.hash = xref.source_hash 
                    GROUP BY source.id
                    '''):
                src_path = os.path.join(self.sources_dir, row['filepath'])
                dest_path = os.path.join(output_sources_dir, row['filepath'])
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)
                logging.info(f"Copied source: {row['filepath']}")

    def _load(self):
        self._load_sources()
        self._load_notes()
        return self

    def _load_sources(self):
        if self.sources_dir is None:
            return self
        
        with Db().get_conn() as conn:
            conn.execute('DELETE FROM source')

            for dirpath, _, filenames in os.walk(self.sources_dir):
                for filename in sorted(filenames):
                    filepath = os.path.join(dirpath, filename)
                    Source(self.sources_dir, os.path.relpath(filepath, self.sources_dir)).load().save(conn)

        return self

    def _load_notes(self):
        if self.notes_dir is None:
            return self
        
        with Db().get_conn() as conn:
            conn.execute('DELETE FROM notes')

            for dirpath, _, filenames in os.walk(self.notes_dir):
                for filename in sorted(filenames):
                    filepath = os.path.join(dirpath, filename)
                    Note(self.notes_dir, os.path.relpath(filepath, self.notes_dir)).load().save(conn)

        return self
