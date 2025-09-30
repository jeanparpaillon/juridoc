from juridoc import Db
from juridoc.note import Note
from juridoc.source import Source

def load_sources():
    data = []
    with Db().get_conn() as conn:
        for row in conn.execute('''
                SELECT s.id AS idx, s.hash AS hash, s.sources_dir AS sources_dir, s.filepath AS relpath, CASE WHEN x.id IS NOT NULL THEN 1 ELSE 0 END AS xref
                FROM source AS s
                LEFT JOIN xref AS x ON s.hash = x.source_hash
                GROUP BY s.id
                '''):
            data.append(Source(row['sources_dir'], row['relpath'], row['hash'], bool(row['xref']), row['idx']))

    return data

def load_notes():
    data = []
    with Db().get_conn() as conn:
        for row in conn.execute('''
                        SELECT id, notes_dir, filepath FROM notes ORDER BY id
                    '''):
            data.append(Note(row['notes_dir'], row['filepath'], row['id']))
    return data