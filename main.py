import os
from pathlib import Path
import time
import threading

from managers import SyncManager, LocalManager
from services import check_diff, write_new_files_data, delete_files_data

home = Path.home()
folder = home / "Desktop" / "SyncFolder"

# это меняется на БД
base_list = []

files_info_new = {}

# Пример хранения
m = {
    "file_name":
        {
        "file_size": 123,
        "file_mtime": 321,
        },
}

# headers
#
# headers = {
#     "Authorization": f"OAuth {TOKEN}",
#     "Accept": "application/json",
#     "Content-Type": "application/json"
# }
#
# disk_path = {
#     "path": "/sync_folder"
# }
#
#
#
#
# def get_yandex_files_list():
#     response = requests.get(
#         "https://cloud-api.yandex.net/v1/disk/resources",
#         headers=headers,
#         params={
#             "path": "/sync_folder"
#         }
#     )
#     yandex_files_list = []
#     items = response.json().get("_embedded").get("items")
#
#     for item in items:
#         yandex_files_list.append(item.get("name"))
#
#     return yandex_files_list


# def get_dir_files_names():
#     dir_files_list = []
#     with os.scandir(folder) as it:
#         for fi in it:
#             file_name = fi.name
#             dir_files_list.append(file_name)
#     return dir_files_list


# def create_yandex_folder():
#         response = requests.put(
#             "https://cloud-api.yandex.net/v1/disk/resources",
#             headers=headers,
#             params=disk_path,
#         )
#
#         if response.status_code == [201, 409]:
#             return True
#         else:
#             print(f"Status code: {response.status_code}")
#             print(f"Message: {response.json().get('message')}")
#
#
# def upload_file(fi_name):
#     response = requests.get(
#         "https://cloud-api.yandex.net/v1/disk/resources/upload",
#         headers=headers,
#         params={
#             "path": f"/sync_folder/{fi_name}",
#             "overwrite": "true",
#         },
#     )
#
#     if response.status_code != 200:
#         return
#
#     href = response.json().get("href")
#
#     with open(folder / fi_name, "rb") as f:
#         upload_response = requests.put(
#             href,
#             files={
#                 "file": f,
#             },
#         )
#
#         if upload_response.status_code == 201:
#             print(f"Файл {fi_name!r} загружен")
#         else:
#             print(f"Ошибка {upload_response.json().get('message')}")
#
#
# def delete_file(fi_name):
#     response = requests.delete(
#         "https://cloud-api.yandex.net/v1/disk/resources",
#         headers=headers,
#         params={
#             "path": f"/sync_folder/{fi_name}",
#             "permanently": "true",
#             "force_async": "true",
#         },
#     )
#
#     if response.status_code == 204:
#         print(f"УСПЕШНО УДАЛЯЕТСЯ С ДИСКА {fi_name}")
#     else:
#         print(f"error message: {response.json().get('message')}")
#
#
# def is_file_changed(fi_name):
#
#     # file_path = folder / fi_name
#     # new_size = os.path.getsize(file_path)
#     # new_mtime = os.path.getmtime(file_path)
#     #
#     # # ЛОГИКА НА JSON ОБЪЕКТЕ, ИСПРАВИТЬ НА SQL
#     # json_data = json_list.get(fi_name)
#     # file_size = json_data.get("file_size")
#     # file_mtime = json_data.get("file_mtime")
#     pass

# СЛЕДУЮЩИЕ 4 ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАПИСЬЮ И УДАЛЕНИЕМ ИЗ БД


if __name__ == "__main__":
    if not os.path.exists(folder):
        os.mkdir(path=folder)
    yandex_manager = SyncManager()
    yandex_manager.create_folder()
    local_manager = LocalManager()

    check_diff(yandex_manager, local_manager)

    while True:
        new_files_list = local_manager.detail()
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
            add_thread = threading.Thread(target=write_new_files_data, args=(yandex_manager, added_list,), daemon=True)
            add_thread.start()
            flag = False

        if len(deleted_list) != 0:
            print(f"Удалены: {deleted_list}")
            del_thread = threading.Thread(target=delete_files_data, args=(yandex_manager, deleted_list,), daemon=True)
            del_thread.start()
            flag = False

        if flag:
            print("Изменений нет!")

        time.sleep(5)