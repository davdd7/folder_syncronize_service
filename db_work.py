import os
from pathlib import Path
import sqlite3

# Добавить логирование

class DBManager:
    folder = Path.home() / "Desktop" / "SyncFolder"
    database_name = "database.db"

    def _execution_function(self, query: str, parameters = (), fetch=False, fetch_names=False):
        with sqlite3.connect(self.database_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, parameters)

            if fetch:
                result = cursor.fetchall()
                if result:
                    return {dict(row)["name"]: {
                        "size": dict(row)["size"],
                        "m_time": dict(row)["m_time"]
                    } for row in result}
                else:
                    return {}
            if fetch_names:
                result = cursor.fetchall()
                if result:
                    return [dict(row)["name"] for row in result]
                else:
                    return []
            else:
                conn.commit()
                return

    def create_tables(self):
        self._execution_function('''
        CREATE TABLE IF NOT EXISTS local (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            m_time REAL NOT NULL,
            size INTEGER NOT NULL
            
        )''')

    def write_file_data(self, fi_name):
        query = '''INSERT OR REPLACE INTO local (name, m_time, size)
        VALUES (?, ?, ?)'''
        file_path = self.folder / fi_name
        parameters = (
            fi_name,
            os.path.getmtime(file_path),
            os.path.getsize(file_path),
        )

        self._execution_function(query, parameters)

    def delete_file_data(self, fi_name):
        query = '''
        DELETE FROM local WHERE name = ?
        '''
        parameters = (fi_name, )
        self._execution_function(query, parameters)

    def get_info(self):
        query = '''
        SELECT * FROM local
        '''
        data_dict = self._execution_function(query, fetch=True)
        return data_dict

    def get_file_names(self):
        query = '''
        SELECT name FROM local
        '''
        name_list = self._execution_function(query, fetch_names=True)
        return name_list
