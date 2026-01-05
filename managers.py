from logging import Logger
from pathlib import Path
import os
import hashlib
from typing import List, Dict, Tuple

import requests


class LocalManager:

    def __init__(self, local_folder: str, buffer_size: str, file_size_limit: str, logger: Logger):
        self.logger = logger
        self.local_folder = Path.home() / local_folder
        self.buffer_size = int(buffer_size)
        self.file_size_limit = int(file_size_limit)

    def dir_file_names(self) -> List:
        """
        Получение списка имен и проверка файлов в директории
        :return: список
        """
        dir_files_list = []
        try:
            with os.scandir(self.local_folder) as it:
                for fi in it:
                    # Если папка - нужно пропустить
                    if fi.is_dir():
                        self.logger.warning(
                            msg="{!r} - папка. Не будет загружена!".format(fi.name),
                        )
                        continue
                    file_name = fi.name
                    # Если файл открыт - пропустить
                    if file_name.startswith("~$"):
                        continue
                    file_size = os.path.getsize(self.local_folder / file_name)
                    # Если больше лимита - пропустить
                    if file_size > self.file_size_limit:
                        self.logger.warning(
                            msg="Вес файла {!r} - {:.2f}Мб больше допустимых {:.2f}Мб! Он не будет загружен!"
                            .format(
                                file_name,
                                file_size / 1024 / 1024,
                                self.file_size_limit /1024 /1024,
                            )
                        )
                        continue

                    dir_files_list.append(file_name)
            return dir_files_list
        except Exception as e:
            self.logger.error(
                msg="ERROR! {}".format(e),
            )
            raise


    def get_info(self, file_name_list: List) -> Dict:
        """
        Выдаёт информацию по файлам из списка
        :param file_name_list: Список файлов директории
        :return: данные по файлам
        """
        dir_files_info = {}

        for file_name in file_name_list:
            try:
                dir_files_info[file_name] = {
                    "size": os.path.getsize(self.local_folder / file_name),
                    "m_time": os.path.getmtime(self.local_folder / file_name),
                    "md_5": self._get_hash(file_name),
                }
            except Exception as e:
                self.logger.error(
                    msg="Не удается получить доступ к файлу {}! ERROR! {}"
                    .format(file_name, e)
                )
                continue

        return dir_files_info

    def delete_file(self, file_name: str) -> None:
        """
        Удаление файла
        :param file_name: имя удаляемого файла
        :return: None
        """
        try:
            if os.path.exists(self.local_folder / file_name):
                os.remove(self.local_folder / file_name)
            self.logger.info(
                msg="Файл {} удалён!".format(file_name)
            )
        except Exception as e:
            self.logger.error(
                msg="ERROR! Файл {} не удалён! {}".format(file_name, e)
            )

    def create_local_folder(self) -> None:
        """
        Создание локальной папки
        :return: None
        """
        try:
            if not os.path.exists(self.local_folder):
                os.mkdir(path=self.local_folder)
        except Exception as e:
            self.logger.error(
                msg="ERROR! Локальная папка не создана! {}".format(e)
            )
            raise

    def _get_hash(self, file_name: str) -> str:
        """
        Получение хеша файла
        :param file_name: имя файла для получения хеша
        :return: хеш файла
        """
        md5_hash = hashlib.md5()
        try:
            with open(self.local_folder / file_name, "rb") as fi:
                while chunk := fi.read(self.buffer_size):
                    md5_hash.update(chunk)
                return md5_hash.hexdigest()
        except Exception as e:
            self.logger.error(
                msg="Не удается получить доступ к файлу {}!".format(e)
            )
            raise


class YandexAPIManager:
    # Хедеры для отправки
    def __init__(self, token: str, disk_folder: str, local_folder: str, file_size_limit: str, logger: Logger):
        self.logger = logger
        self.ya_headers = {
            "Authorization": f"OAuth {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.ya_disk_path = disk_folder
        self.file_size_limit = int(file_size_limit)
        self.local_folder = Path.home() / local_folder

    def create_folder(self) -> None:
        """
        Создание папки на диске
        :return: None
        """
        response = requests.put(
            "https://cloud-api.yandex.net/v1/disk/resources",
            headers=self.ya_headers,
            params={
                "path": self.ya_disk_path,
            },
        )

        resp_st_code = response.status_code

        if resp_st_code == 201:
            self.logger.info(
                msg="Создана папка в облаке {}".format(self.ya_disk_path)
            )
        elif resp_st_code == 409:
            self.logger.info(
                msg="В облаке уже существует папка {}".format(self.ya_disk_path)
            )
        else:
            # Сделать логирование
            self.logger.error(
                msg="ERROR! Status code: {}. Message: {}".format(
                    resp_st_code,
                    response.json().get('message'),
                ),
            )
            raise

    def load_to_disk(self, file_name: str) -> None:
        """
        Загрузка файлов на диск
        :param file_name: имя файла
        :return: None
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
            self.logger.error(
                msg="Не удается загрузить файл {!r}.Message: {}"
                .format(
                    file_name,
                    response.json().get("message"),
                ),
            )
            raise

        href = response.json().get("href")
        try:
            with open(self.local_folder / file_name, "rb") as f:
                upload_response = requests.put(
                    href,
                    files={
                        "file": f,
                    },
                )
                # Тоже добавить логи
                if upload_response.status_code == 201:
                    self.logger.info(
                        msg="Файл {!r} загружен".format(file_name)
                    )
                else:
                    self.logger.error(
                        msg="Не удается загрузить файл {!r}.Message: {}"
                        .format(
                            file_name,
                            response.json().get("message"),
                        ),
                    )
                    raise
        except:
            self.logger.error(
                msg="Не удается загрузить файл {!r}.Message: {}"
                .format(
                    file_name,
                    response.json().get("message"),
                ),
            )
            raise

    def load_from_disk(self, file_name: str) -> None:
        """
        Скачивание файла с диска
        :param file_name: имя файла
        :return: None
        """

        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/download",
            headers=self.ya_headers,
            params={
                "path": f"{self.ya_disk_path}/{file_name}",
            },
        )

        if response.status_code != 200:
            self.logger.error(
                msg="Не удается загрузить файл {!r}.Message: {}"
                .format(
                    file_name,
                    response.json().get("message"),
                ),
            )
            raise

        href = response.json().get("href")
        try:
            with requests.get(href, stream=True) as file_response:


                with open(self.local_folder / file_name, "wb") as fi:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        fi.write(chunk)
            self.logger.info(
                msg="Файл {!r} успешно скачан!".format(file_name),
            )
        except Exception as e:
            self.logger.error(
                msg="Не удается скачать файл {!r}.Message: {}"
                .format(file_name, e)

            )
            raise

    def delete(self, file_name) -> None:
        """
        Удаление файла с облачного диска
        :param file_name: имя удаляемого файла с диска
        :return: None
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
            self.logger.info(
                msg="Файл {!r} успешно удален из облака".format(file_name),
            )
        elif response.status_code == 202:
            self.logger.info(
                msg="Начинается удаление файла с облака {!r}".format(file_name),
            )
        else:
            self.logger.error(
                msg="Файл не удается удалить! StatusCode: {} Message: {}"
                .format(response.status_code,
                        response.json().get('message'),
                ),
            )
            raise

    def detail(self) -> Tuple:
        """
        Получение списка имён и информации файлов в диске
        :return: список и детализацию
        """

        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources",
            headers=self.ya_headers,
            params={
                "path": self.ya_disk_path
            }
        )
        if response.status_code != 200:
            self.logger.error(
                msg="Нет доступа к серверу! message: {}".format(response.json().get("message"))
            )
            raise
        items = response.json().get("_embedded").get("items")

        yandex_files_list = []
        jsonify_data = {}
        for item in items:
            name = item.get("name")
            size = item.get("size")
            if size > int(self.file_size_limit):
                self.logger.warning(
                    msg="Вес {!r} {:.2f} Мб. Допустимый - {:.2f}. Он не будет скачан. "
                )
                continue
            jsonify_data[name] = {
                "m_time": item.get("modified"),
                "size": size,
                "md_5": item.get("md5"),
            }
            yandex_files_list.append(name)


        return yandex_files_list, jsonify_data
