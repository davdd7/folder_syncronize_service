import os
from pathlib import Path
import time

# это меняется на БД
base_list = []
new_files_list = []

files_info = {}

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


def changed_name():
    pass


def is_file_busy():
    pass


if __name__ == "__main__":
    if not os.path.exists(folder):
        os.mkdir(path=folder)
    while True:



        with os.scandir(folder) as it:
            for fi in it:

                file_name = fi.name
                new_files_list.append(file_name)

        # Запихнуть в отдельную функцию

        old_set = set(base_list)
        new_set = set(new_files_list)

        added_list = list(new_set - old_set)
        deleted_list = list(old_set - new_set)
        unchanged_list = list(new_set & old_set)

        base_list = added_list + unchanged_list

        flag = True

        if len(added_list) != 0:
            print(f"Добавлены: {added_list}")
            flag = False
        if len(deleted_list) != 0:
            print(f"Удалены: {deleted_list}")
            flag = False

        if flag:
            print("Изменений нет!")

        time.sleep(5)