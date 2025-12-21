import os
from pathlib import Path
import time
import threading

# это меняется на БД
base_list = []
files_info = {}
files_info_new = {}

# Пример хранения
m = {
    "file_name":
        {
        "file_size": 123,
        "file_mtime": 321,
        },
}

home = Path.home()
folder = home / "Desktop" / "SyncFolder"

def add_new_file():
    pass


def delete_file():
    
    pass


def is_file_changed(fi_name):

    # file_path = folder / fi_name
    # new_size = os.path.getsize(file_path)
    # new_mtime = os.path.getmtime(file_path)
    #
    # # ЛОГИКА НА JSON ОБЪЕКТЕ, ИСПРАВИТЬ НА SQL
    # json_data = json_list.get(fi_name)
    # file_size = json_data.get("file_size")
    # file_mtime = json_data.get("file_mtime")
    pass


def write_new_files_data(file_name_list):
    for f_name in file_name_list:
        write_file_data(f_name, files_info)


def delete_files_data(file_name_list):
    for f_name in file_name_list:
        delete_file_data(f_name, files_info)


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


def changed_name():
    pass


def is_file_busy():
    pass


if __name__ == "__main__":
    if not os.path.exists(folder):
        os.mkdir(path=folder)
    while True:
        new_files_list = []

        with os.scandir(folder) as it:
            for fi in it:

                file_name = fi.name
                new_files_list.append(file_name)

        # Запихнуть в отдельную функцию
        print(f"BASELIST {base_list}")
        print(f"NEWLIST {new_files_list}")

        old_set = set(base_list)
        new_set = set(new_files_list)

        added_list = list(new_set - old_set)
        deleted_list = list(old_set - new_set)
        unchanged_list = list(new_set & old_set)

        base_list = added_list + unchanged_list

        flag = True

        if len(added_list) != 0:
            print(f"Добавлены: {added_list}")
            add_thread = threading.Thread(target=write_new_files_data, args=(added_list,), daemon=True)
            add_thread.start()
            flag = False
        if len(deleted_list) != 0:
            print(f"Удалены: {deleted_list}")
            del_thread = threading.Thread(target=delete_files_data, args=(deleted_list,), daemon=True)
            del_thread.start()
            flag = False

        if flag:
            print("Изменений нет!")

        time.sleep(5)