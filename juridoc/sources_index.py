import os
import pyexcel

from .db import Db

class SourcesIndex():
    headers = ['uri', 'path']

    def __init__(self):
        self.data = []

    def load(self):
        with Db().get_conn() as conn:
            for row in conn.execute('''
                    SELECT source.hash AS uri, source.filepath AS path, CASE WHEN xref.id IS NOT NULL THEN 1 ELSE 0 END AS xref
                    FROM source 
                    LEFT JOIN xref ON source.hash = xref.source_hash 
                    GROUP BY source.id
                    '''):
                self.data.append(row)

    def export(self, path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        pyexcel.save_as(array=self.data, dest_file_name=path)
