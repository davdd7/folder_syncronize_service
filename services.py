from typing import List, Dict

from managers import YandexAPIManager, LocalManager
from db_work import DBManager

import threading

class SyncService:
    yandex_manager = YandexAPIManager()
    db_manager = DBManager()
    local_manager = LocalManager()

    def check_starter_diff(self):
        yandex_list = self.yandex_manager.detail()
        files_dir_list = self.local_manager.dir_file_names()

        ya_set = set(yandex_list)
        dir_set = set(files_dir_list)

        delta_ya = ya_set - dir_set
        delta_dir = dir_set - ya_set
        docs = ya_set & dir_set

        if len(delta_dir) == 0 and len(delta_ya) == 0:
            return

        # Принты при запуске

        print(f"Документы, которых нет в диске: {list(delta_dir)}")
        print(f"Документы, которых нет локально: {list(delta_ya)}")
        print("Какие документы актуальны?")

        def check_input_type():

            res = input("Введите y - yandex, l - local: ")
            if res not in ["l", "y"]:
                print("Некорректный ввод!")
                check_input_type()
            else:
                return res

        answer = check_input_type()

        print(answer)


    def _check_differences(
            self,
            new_names_list: List,
            new_info_dict: Dict,
            old_names_list: List,
            old_info_dict: Dict):

        old_set = set(old_names_list)
        new_set = set(new_names_list)

        added_list = list(new_set - old_set)
        deleted_list = list(old_set - new_set)
        unchanged_list = list(new_set & old_set)

        # Здесь проверяем изменения в неизмененных названиях файлов

        flag = True

        if added_list:
            # логирование
            for al in added_list:
                self.db_manager.write_file_data(al)
                add_thread = threading.Thread(
                    target=self.yandex_manager.load,
                    args=(al,),
                    daemon=True,
                )
                add_thread.start()
            flag = False

        if deleted_list:
            # Логирование
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
            # Логирование?
            changed_list = []
            for file_name in unchanged_list:

                if old_info_dict[file_name] != new_info_dict[file_name]:
                    changed_list.append(file_name)

            if changed_list:
                for cl in changed_list:
                    self.db_manager.write_file_data(cl)
                    add_thread = threading.Thread(
                        target=self.yandex_manager.load,
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
        count = 0
        while True:

