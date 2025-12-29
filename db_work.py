import os
from pathlib import Path
import sqlite3

folder = Path.home() / "Desktop" / "SyncFolder"

def execution_function(query: str, parameters = ()):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(query, parameters)


def create_tables():
    execution_function('''
    CREATE TABLE IF NOT EXISTS local (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        m_time REAL NOT NULL,
        size INTEGER NOT NULL
        
    ''')
    execution_function('''
        CREATE TABLE IF NOT EXISTS share (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            m_time REAL NOT NULL,
            size INTEGER NOT NULL

        ''')


def write_file_data(fi_name, json_list) -> None:
    """
    Пишет данные по файлу для БД. Заменить на SQL позже
    :param json_list: база хранения данных
    :param fi_name: имя файла
    :return: None
    """
    file_path = folder / fi_name
    json_list[fi_name] = {
        "file_size": os.path.getsize(file_path),
        "file_mtime": os.path.getmtime(file_path),
    }

    print(f"Записал файл {fi_name}")


def delete_file_data(fi_name, json_list) -> None:
    """
    Удаление информации из БД. Переделать на SQL
    :param json_list: база хранения данных
    :param fi_name: Имя файла
    :return: None
    """
    json_list.pop(fi_name)

    print(f"Информация о файле удалена {fi_name}")