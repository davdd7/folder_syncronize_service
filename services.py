import time
from typing import List, Dict

from managers import YandexAPIManager, LocalManager
from db_work import DBManager

import threading

class SyncService:
    yandex_manager = YandexAPIManager()
    db_manager = DBManager()
    local_manager = LocalManager()

    def _starting(self):
        self.local_manager.create_local_folder()
        self.yandex_manager.create_folder()
        self.db_manager.create_tables()

        yandex_list = self.yandex_manager.detail()
        yandex_json_detail = self.yandex_manager.detail(json_t=True)
        files_dir_list = self.local_manager.dir_file_names()
        files_dir_json = self.local_manager.get_info()

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

        if not delta_dir and not delta_ya:
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
                print(f"ФАЙЛ УДАЛЕН {file_name}")

            for file_name in list(delta_ya) + changed_files:
                print(f"FILENAME ДЛЯ ЗАГРУЗКИ С ДИСКА {file_name}")
                upload_thread = threading.Thread(
                    target=self.yandex_manager.load_from_disk,
                    args=(file_name, ),
                    daemon=True,
                )
                upload_thread.start()
        elif answer == "l":
            # Удаляем чего нет в диске и перезаписываем измененные
            for file_name in delta_ya:
                delete_thread = threading.Thread(
                    target=self.yandex_manager.delete,
                    args=(file_name, ),
                    daemon=True,
                )
                delete_thread.start()

            for file_name in list(delta_dir) + changed_files:
                upload_thread = threading.Thread(
                    target=self.yandex_manager.load_to_disk,
                    args=(file_name, ),
                    daemon=True,
                )
                upload_thread.start()

        time.sleep(5)




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

        flag = True

        if added_list:

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
            print(f"UNCHANGEDLIST {unchanged_list}")
            changed_list = []
            for file_name in unchanged_list:
                if md5_check:
                    print(f"MD5 OLD: {old_info_dict[file_name].get("md_5")}")
                    print(f"MD5 NE: {new_info_dict[file_name].get("md_5")}")
                    if old_info_dict[file_name].get("md_5") != new_info_dict[file_name].get("md_5"):
                        changed_list.append(file_name)
                else:
                    print(f"OLD INFO: {old_info_dict[file_name]}")
                    print(f"NEW INFO: {new_info_dict[file_name]}")
                    if old_info_dict[file_name] != new_info_dict[file_name]:
                        changed_list.append(file_name)

            if changed_list:
                for cl in changed_list:
                    self.db_manager.write_file_data(cl, new_info_dict.get(cl))
                    add_thread = threading.Thread(
                        target=self.yandex_manager.load_to_disk,
                        args=(cl,),
                        daemon=True,
                    )
                    add_thread.start()

                print(f"Внёс изменения в файлы {changed_list}")

                flag = False

        # НЕ УЧТЕНО ЕСЛИ ФАЙЛ ОТКРЫТ В ЯНДЕКСЕ! ВЫДАЕТ ОШИБКИ!
        # НУЖН СТАВИТЬ ПЕРЕЗАПУСК ФУНКЦИИ И КАЖДЫЕ 20 СЕКУНД СРАВНИВАТЬ С ДИСКОМ! АКТУАЛЬНОСТЬ ДАННЫХ СВЕРЯТЬ С БД
        if flag:
            print("Изменений нет!")

    def run(self):
        self._starting()
        count = 0
        while True:
            count += 1
            if count > 3:
                print("СРАВНЕНИЕ С ДИСКОМ ЯД")
                count = 0
                new_names_list = self.local_manager.dir_file_names()
                new_info_dict = self.local_manager.get_info()
                old_names_list = self.yandex_manager.detail()
                old_info_dict = self.yandex_manager.detail(json_t=True)

                print(f"ЛОКАЛЬНЫЙ m_time: {new_info_dict}")
                print(f"ЯНДЕКС m_time: {old_info_dict}")

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


