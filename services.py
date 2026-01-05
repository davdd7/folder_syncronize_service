import time
from typing import List, Dict
from venv import logger

from managers import YandexAPIManager, LocalManager
from db_work import DBManager

import threading
import configparser
import logging
import datetime
import sys


def setup_logger():
    some_logger = logging.getLogger("SyncService")

    some_logger.setLevel(level=logging.DEBUG)

    formatter_info = logging.Formatter(
        "[%(asctime)s] - [%(levelname)s] :> %(message)s",
        datefmt="%H:%M:%S",
    )

    formatter_error = logging.Formatter(
        "[%(asctime)s] - [%(levelname)s] - "
        "FUNCTION [%(funcName)s] - LINE [%(lineno)s] :> "
        "%(message)s",
        datefmt="%H:%M:%S",
    )

    file_handler = logging.FileHandler(
        datetime.date.today().isoformat() + "-sync.log",
        encoding="UTF-8",
    )
    file_handler.setLevel(level=logging.DEBUG)
    file_handler.setFormatter(formatter_info)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level=logging.WARNING)
    console_handler.setFormatter(formatter_error)

    some_logger.addHandler(file_handler)
    some_logger.addHandler(console_handler)

    return some_logger


class SyncService:

    def __init__(self, config_file_path):
        self.sync_logger = setup_logger()

        cfg = configparser.ConfigParser()
        cfg.read(config_file_path)

        self.db_manager = DBManager(database_name=cfg["database"]["name"], logger=self.sync_logger)
        self.local_manager = LocalManager(
            local_folder=cfg["local_data"]["local_folder"],
            buffer_size=cfg["local_data"]["buffer_size"],
            logger=self.sync_logger,
        )
        self.yandex_manager = YandexAPIManager(
            token=cfg["yandex_data"]["token"],
            disk_folder=cfg["yandex_data"]["disk_folder"],
            local_folder=cfg["local_data"]["local_folder"],
            logger=self.sync_logger,
        )

    def _starting(self):
        try:
            self.local_manager.create_local_folder()
            self.yandex_manager.create_folder()
            self.db_manager.create_tables()
            logger.warning("Хранилища и БД созданы!")

            yandex_list = self.yandex_manager.detail()
            yandex_json_detail = self.yandex_manager.detail(json_t=True)
            files_dir_list = self.local_manager.dir_file_names()
            files_dir_json = self.local_manager.get_info()

            self.sync_logger.info(msg="Документы в облачном хранилище: {}".format(yandex_json_detail))
            self.sync_logger.info(msg="Документы на локальном хранилище: {}".format(files_dir_json))

            ya_set = set(yandex_list)
            dir_set = set(files_dir_list)

            delta_ya = ya_set - dir_set
            delta_dir = dir_set - ya_set
            docs = ya_set & dir_set

            changed_files = []

            if docs:
                for file_name in docs:
                    if yandex_json_detail[file_name].get("md_5") != files_dir_json[file_name].get("md_5"):
                        changed_files.append(file_name)

            if not delta_dir and not delta_ya and not changed_files:
                return

            # Принты при запуске

            print(f"Документы, которых нет в диске: {list(delta_dir)}")
            print(f"Документы, которых нет локально: {list(delta_ya)}")
            print(f"Изменены документы {changed_files}")
            print("Какие документы актуальны?")

            def check_input_type():

                res = input("Введите y - yandex, l - local: ")
                if res not in ["l", "y"]:
                    print("Некорректный ввод!")
                    check_input_type()
                else:
                    return res

            answer = check_input_type()

            if answer == "y":
                # Удаляем то, чего нет в яндексе и обновляем измененные файлы
                for file_name in list(delta_dir) + changed_files:

                    self.local_manager.delete_file(file_name)
                    self.sync_logger.info(
                        msg="Удаляем файл на локальном хранилище : {!r}".format(file_name),
                    )

                for file_name in list(delta_ya) + changed_files:
                    self.sync_logger.info(
                        msg="Отправляем в загрузку с облака: {!r}".format(file_name),
                    )
                    upload_thread = threading.Thread(
                        target=self.yandex_manager.load_from_disk,
                        args=(file_name, ),
                        daemon=True,
                    )
                    upload_thread.start()
            elif answer == "l":
                # Удаляем чего нет в диске и перезаписываем измененные
                for file_name in delta_ya:
                    self.sync_logger.info(
                        msg="Удаляем из облака: {!r}".format(file_name),
                    )
                    delete_thread = threading.Thread(
                        target=self.yandex_manager.delete,
                        args=(file_name, ),
                        daemon=True,
                    )
                    delete_thread.start()

                for file_name in list(delta_dir) + changed_files:
                    self.sync_logger.info(
                        msg="Загружаем на диск: {!r}".format(file_name),
                    )
                    upload_thread = threading.Thread(
                        target=self.yandex_manager.load_to_disk,
                        args=(file_name, ),
                        daemon=True,
                    )
                    upload_thread.start()

            time.sleep(5)
        except Exception as e:
            self.sync_logger.error(msg="ERROR! {}". format(e))
            raise



    def _check_differences(
            self,
            new_names_list: List,
            new_info_dict: Dict,
            old_names_list: List,
            old_info_dict: Dict,
            md5_check=False):

        old_set = set(old_names_list)
        new_set = set(new_names_list)

        added_list = list(new_set - old_set)
        deleted_list = list(old_set - new_set)
        unchanged_list = list(new_set & old_set)

        # Здесь проверяем изменения в неизмененных названиях файлов
        try:
            flag = True

            if added_list:
                self.sync_logger.info(
                    msg="Добавлены файлы: {}".format(added_list),
                )
                for al in added_list:
                    self.db_manager.write_file_data(al, new_info_dict.get(al))
                    add_thread = threading.Thread(
                        target=self.yandex_manager.load_to_disk,
                        args=(al,),
                        daemon=True,
                    )
                    add_thread.start()

                flag = False

            if deleted_list:
                self.sync_logger.info(
                    msg="Удалены файлы: {}".format(deleted_list),
                )
                for dl in deleted_list:
                    self.db_manager.delete_file_data(dl)
                    del_thread = threading.Thread(
                        target=self.yandex_manager.delete,
                        args=(dl,),
                        daemon=True,
                    )
                    del_thread.start()

                flag = False

            if unchanged_list:
                # Если есть список неизмененных по первоначальным параметрам
                # проверяем по хешу
                changed_list = []
                for file_name in unchanged_list:
                    if md5_check:
                        if old_info_dict[file_name].get("md_5") != new_info_dict[file_name].get("md_5"):
                            changed_list.append(file_name)
                    else:
                        if old_info_dict[file_name] != new_info_dict[file_name]:
                            changed_list.append(file_name)

                if changed_list:
                    self.sync_logger.info(
                        msg="Измененные документы: {}".format(changed_list),
                    )
                    for cl in changed_list:
                        self.db_manager.write_file_data(cl, new_info_dict.get(cl))
                        add_thread = threading.Thread(
                            target=self.yandex_manager.load_to_disk,
                            args=(cl,),
                            daemon=True,
                        )
                        add_thread.start()

                    flag = False

            if flag:
                self.sync_logger.info(
                    msg="Изменений нет!",
                )
        except Exception as e:
            self.sync_logger.error(msg="ERROR! {}". format(e))
            raise


    def run(self):
        try:
            self._starting()
            count = 0
            while True:
                count += 1
                if count > 5:
                    self.sync_logger.info(
                        msg="Сравнение с данными из облака напрямую",
                    )
                    count = 0
                    new_names_list = self.local_manager.dir_file_names()
                    new_info_dict = self.local_manager.get_info()
                    old_names_list = self.yandex_manager.detail()
                    old_info_dict = self.yandex_manager.detail(json_t=True)

                    self.sync_logger.info(
                        msg="Данные на локальном хранилище: {}".format(new_info_dict),
                    )
                    self.sync_logger.info(
                        msg="Данные в облачном хранилище: {}".format(old_info_dict),
                    )

                    self._check_differences(
                        new_names_list, new_info_dict, old_names_list, old_info_dict, md5_check=True
                    )
                else:
                    new_names_list = self.local_manager.dir_file_names()
                    new_info_dict = self.local_manager.get_info()
                    old_names_list = self.db_manager.get_file_names()
                    old_info_dict = self.db_manager.get_info()

                    self._check_differences(
                        new_names_list, new_info_dict, old_names_list, old_info_dict
                    )

                time.sleep(5)

        except Exception as e:
            self.sync_logger.error(msg="ERROR! {}".format(e))
            raise
