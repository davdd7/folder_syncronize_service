import sqlite3

# Добавить логирование

class DBManager:

    def __init__(self, database_name, logger):
        self.logger = logger
        self.database_name = database_name

    def _execution_function(self, query: str, parameters = (), fetch=False, fetch_names=False):
        try:
            with sqlite3.connect(self.database_name) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, parameters)

                if fetch:
                    result = cursor.fetchall()
                    if result:
                        return {dict(row)["name"]: {
                            "size": dict(row)["size"],
                            "m_time": dict(row)["m_time"],
                            "md_5": dict(row)["md_5"],
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
        except Exception as e:
            self.logger.error(
                msg="Ошибка запроса к БД! {}".format(e)
            )
            raise

    def create_tables(self):
        try:
            self._execution_function('''
            CREATE TABLE IF NOT EXISTS local (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                m_time REAL NOT NULL,
                size INTEGER NOT NULL,
                md_5 TEXT NOT NULL
            )''')
        except Exception as e:
            self.logger.error(
                msg="Не удалось создать БД! {}".format(e)
            )
            raise

    def write_file_data(self, file_name, file_data):
        try:
            query = '''INSERT OR REPLACE INTO local (name, m_time, size, md_5)
            VALUES (?, ?, ?, ?)'''

            parameters = (
                file_name,
                file_data.get("m_time"),
                file_data.get("size"),
                file_data.get("md_5"),
            )

            self._execution_function(query, parameters)
            self.logger.info(
                msg="Данные по файлу {!r} записаны!".format(file_name)
            )
        except Exception as e:
            self.logger.error(
                msg="Не удается записать данные! {}".format(e)
            )


    def delete_file_data(self, fi_name):
        try:
            query = '''
            DELETE FROM local WHERE name = ?
            '''
            parameters = (fi_name, )
            self._execution_function(query, parameters)
            self.logger.info(
                msg="Файл {!r} удален".format(fi_name),
            )
        except Exception as e:
            self.logger.error(
                msg="Не удается удалить файл {!r} из БД. ERROR: {}"
                .format(fi_name, e),
            )

    def get_info(self):
        try:
            query = '''
            SELECT * FROM local
            '''
            data_dict = self._execution_function(query, fetch=True)
            return data_dict
        except Exception as e:
            self.logger.error(
                msg="Не получить данные из БД! {}".format(e)
            )

    def get_file_names(self):
        try:
            query = '''
            SELECT name FROM local
            '''
            name_list = self._execution_function(query, fetch_names=True)
            return name_list
        except Exception as e:
            self.logger.error(
                msg="Не получить данные из БД! {}".format(e)
            )
