import logging
import os
import re
import shutil

import odfdo

from .db import Db

logger = logging.getLogger(__name__)

class Note():
    def __init__(self, notes_dir, path):
        # path is relative to notes_dir
        self.notes_dir = notes_dir
        self.relpath = path
        self.xrefs = []

    def load(self):
        path = os.path.join(self.notes_dir, self.relpath)

        try:
            if path.endswith('.odt'):
                self._lookup_odt_note(path)
            logging.info(f"Loaded note: {self.relpath}")
        except Exception as e:
            logging.error(f"ERROR loading note {self.relpath}: {e}")

        return self
    
    def process(self, out_dir):
        with Db().get_conn() as conn:
            ret = conn.execute('''
                SELECT CASE WHEN xref.id IS NOT NULL THEN 1 ELSE 0 END AS xref
                FROM xref
                JOIN notes ON xref.note_id = notes.id
                WHERE notes.filepath = ?
            ''', (self.relpath,)).fetchone()

            if ret and ret['xref']:
                self._render(self, out_dir, conn)
            else:
                self._copy(out_dir)

        return self
    
    def _render(self, out_dir):
        """
        Replace xref (src:<hex>) in the document with idx from index, save to OUT/notes.
        """
        doc = odfdo.Document(os.path.join(self.notes_dir, self.relpath))
        out_path = os.path.join(out_dir, self.relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        conn = Db().get_conn()

        for a in doc.body.get_elements("//text:a"):
            href = a.get_attribute("xlink:href")
            if href:
                replacement = self._format_xref(href, conn)
                a.parent.replace_element(a, odfdo.Span(replacement))

        doc.save(out_path)
        logging.info(f"Rendered note: {out_path}")

        return self
    
    def _copy(self, out_dir):
        """
        Copy note file to OUT/notes dir as is.
        """
        out_path = os.path.join(out_dir, self.relpath)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        shutil.copy2(os.path.join(self.notes_dir, self.relpath), out_path)
        logging.info(f"Copied note: {out_path}")

        return self

    def _format_xref(href, conn):
        m = re.match(r'^src:([0-9a-fA-F]+)$', href)
        if m:
            hexkey = m.group(1)
            ret = conn.execute('''
                    SELECT source.idx
                    FROM source
                    WHERE source.hash = ?
            ''', (hexkey,)).fetchone()
            if ret:
                return f"{ret['idx']}"
            else:
                return href
    
    def _lookup_odt_note(self, filepath):
        doc = odfdo.Document(filepath)
        conn = Db().get_conn()
        sources = conn.execute('SELECT hash FROM source').fetchall()

        # Find references to sources
        for elem in doc.body.get_elements('//text:a'):
            href = elem.get_attribute('xlink:href')
            uri = self._find_source(href, sources)
            if uri:
                sources[uri].update({'xref': True})
                self.xrefs.append(uri)

        return self

    def _find_source(self, href, sources):
        """
        If href matches 'src:<hex>' and <hex> is a key in sources, returns <hex>, else None.
        """
        m = re.match(r'^src:([0-9a-fA-F]+)$', href)
        if m:
            hexkey = m.group(1)
            if hexkey in sources:
                return hexkey

        return None
    
    def save(self, conn):
        with conn:
            cursor = conn.execute('''
                INSERT OR IGNORE INTO notes (notes_dir, filepath)
                VALUES (?, ?)
            ''', (self.notes_dir, self.relpath))
            note_id = cursor.lastrowid

            for xref in self.xrefs:
                conn.execute('''
                    INSERT INTO xref (source_hash, note_id)
                    VALUES (?, ?)
                ''', (xref, note_id))

        return self