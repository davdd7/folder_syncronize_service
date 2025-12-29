from pathlib import Path
import os

import requests

from config import TOKEN


class LocalManager:
    # Путь на локальном диске
    local_folder = Path.home() / "Desktop" / "SyncFolder"

    def detail(self):
        dir_files_list = []
        with os.scandir(self.local_folder) as it:
            for fi in it:
                file_name = fi.name
                dir_files_list.append(file_name)
        return dir_files_list


class SyncManager:
    # Хедеры для отправки
    YA_TOKEN = TOKEN
    ya_headers = {
        "Authorization": f"OAuth {YA_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    # Путь до диска на облачном сервисе
    ya_disk_path = "/sync_folder"
    # Путь на локальном диске
    local_folder = Path.home() / "Desktop" / "SyncFolder"

    def create_folder(self):
        """
        Создание папки на диске
        :return:
        """
        response = requests.put(
            "https://cloud-api.yandex.net/v1/disk/resources",
            headers=self.ya_headers,
            params={
                "path": self.ya_disk_path,
            },
        )

        if response.status_code == [201, 409]:
            return True
        else:
            # Сделать логирование
            print(f"Status code: {response.status_code}")
            print(f"Message: {response.json().get('message')}")
            return False

    def load(self, file_name):
        """
        Загрузка файлов на диск
        :param file_name:
        :return:
        """
        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/upload",
            headers=self.ya_headers,
            params={
                "path": f"{self.ya_disk_path}/{file_name}",
                "overwrite": "true",
            },
        )

        if response.status_code != 200:
            return

        href = response.json().get("href")

        with open(self.local_folder / file_name, "rb") as f:
            upload_response = requests.put(
                href,
                files={
                    "file": f,
                },
            )
            # Тоже добавить логи
            if upload_response.status_code == 201:
                print(f"Файл {file_name!r} загружен")
            else:
                print(f"Ошибка {upload_response.json().get('message')}")

    def delete(self, file_name):
        """
        Удаление файла с облачного диска
        :param file_name:
        :return:
        """
        response = requests.delete(
            "https://cloud-api.yandex.net/v1/disk/resources",
            headers=self.ya_headers,
            params={
                "path": f"{self.ya_disk_path}/{file_name}",
                "permanently": "true",
                "force_async": "true",
            },
        )

        if response.status_code == 204:
            print(f"УСПЕШНО УДАЛЯЕТСЯ С ДИСКА {file_name}")
        else:
            print(f"error message: {response.json().get('message')}")

    def detail(self):
        """
        Список файлов яндекса
        :return:
        """
        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources",
            headers=self.ya_headers,
            params={
                "path": self.ya_disk_path
            }
        )
        yandex_files_list = []
        items = response.json().get("_embedded").get("items")

        print(response.json())

        for item in items:
            yandex_files_list.append(item.get("name"))

        return yandex_files_list
