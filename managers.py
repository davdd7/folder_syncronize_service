from pathlib import Path
import os
import hashlib

import requests


class LocalManager:

    def __init__(self, local_folder, buffer_size, logger):
        self.logger = logger
        self.local_folder = Path.home() / local_folder
        self.buffer_size = int(buffer_size)

    def dir_file_names(self):
        dir_files_list = []
        with os.scandir(self.local_folder) as it:
            for fi in it:
                file_name = fi.name
                if file_name.startswith("~$"):
                    continue
                dir_files_list.append(file_name)
        return dir_files_list

    def get_info(self):
        dir_files_info = {}
        with os.scandir(self.local_folder) as it:
            for fi in it:
                file_name = fi.name
                if file_name.startswith("~$"):
                    continue
                dir_files_info[file_name] = {
                    "size": os.path.getsize(self.local_folder / file_name),
                    "m_time": os.path.getmtime(self.local_folder / file_name),
                    "md_5": self._get_hash(file_name),
                }
        return dir_files_info

    def delete_file(self, file_name):
        # Может быть проблема с доступом к файлу
        if os.path.exists(self.local_folder / file_name):
            os.remove(self.local_folder / file_name)

    def create_local_folder(self):
        if not os.path.exists(self.local_folder):
            os.mkdir(path=self.local_folder)

    def _get_hash(self, file_name):
        md5_hash = hashlib.md5()

        with open(self.local_folder / file_name, "rb") as fi:
            while chunk := fi.read(self.buffer_size):
                md5_hash.update(chunk)
            return md5_hash.hexdigest()





class YandexAPIManager:
    # Хедеры для отправки
    def __init__(self, token, disk_folder, local_folder, logger):
        self.logger = logger
        self.ya_headers = {
            "Authorization": f"OAuth {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.ya_disk_path = disk_folder
        self.local_folder = Path.home() / local_folder

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

    def load_to_disk(self, file_name):
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

    def load_from_disk(self, file_name):
        print(f"НАЧИНАЕТСЯ АГРУЗКА ФАЙЛА С ДИСКА!!! {file_name}")
        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/download",
            headers=self.ya_headers,
            params={
                "path": f"{self.ya_disk_path}/{file_name}",
            },
        )
        print(f"RESPONSE STATUS CODE! {response.status_code}")

        if response.status_code != 200:
            print(f"ERRORRR!!! {response.json()}")
            return

        href = response.json().get("href")
        print(f"ПОЛУЧИЛ ССЫЛКУ ДЛЯ ЗАГРУЗКИ {href}")
        with requests.get(href, stream=True) as file_response:
            print(f"Начинается загрузка {file_response.content}")

            with open(self.local_folder / file_name, "wb") as fi:
                for chunk in file_response.iter_content(chunk_size=8192):
                    fi.write(chunk)

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

    def detail(self, json_t=False):
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
        print(f"ИТЕМЫ В ЯНДЕКСЕ: {items}")

        if json_t:
            jsonify_data = {}
            for item in items:
                jsonify_data[item["name"]] = {
                    "m_time": item.get("modified"),
                    "size": item.get("size"),
                    "md_5": item.get("md5"),
                }
            return jsonify_data

        for item in items:
            yandex_files_list.append(item.get("name"))

        return yandex_files_list


# modified
# size