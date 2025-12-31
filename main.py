import os
from pathlib import Path
import time
import threading

from db_work import DBManager
from managers import YandexAPIManager, LocalManager
from services import SyncService

home = Path.home()
folder = home / "Desktop" / "SyncFolder"



if __name__ == "__main__":
    if not os.path.exists(folder):
        os.mkdir(path=folder)
    count = 0
    yandex_manager = YandexAPIManager()
    yandex_manager.create_folder()
    local_manager = LocalManager()
    db_manager = DBManager()
    sync_service = SyncService()

    db_manager.create_tables()

    sync_service.check_starter_diff()

    while True:
        count += 1
        if count > 3:
            count = 0
            db_info = db_manager.get_info()
            db_names_list = db_info.keys()
            ya_info = yandex_manager.detail(json_t=True)
            ya_names_list = ya_info.keys()

            db_set = set(db_names_list)
            ya_set = set(ya_names_list
                         )
            added_list = list(db_set - ya_set)
            deleted_list = list(ya_set - db_set)
            unchanged_list = list(ya_set & db_set)

        else:

            new_files_list = local_manager.dir_file_names()
            old_names_list = db_manager.get_file_names()
            # Запихнуть в отдельную функцию
            db_info = db_manager.get_info()
            local_info = local_manager.get_info()
            old_set = set(old_names_list)
            new_set = set(new_files_list)

            added_list = list(new_set - old_set)
            deleted_list = list(old_set - new_set)
            unchanged_list = list(new_set & old_set)

            # Здесь проверяем изменения в неизмененных названиях файлов

            flag = True

            if added_list:
                # логирование
                for al in added_list:
                    db_manager.write_file_data(al)
                    add_thread = threading.Thread(
                        target=yandex_manager.load,
                        args=(al, ),
                        daemon=True,
                    )
                    add_thread.start()
                flag = False

            if deleted_list:
                # Логирование
                for dl in deleted_list:
                    db_manager.delete_file_data(dl)
                    del_thread = threading.Thread(
                        target=yandex_manager.delete,
                        args=(dl, ),
                        daemon=True,
                    )
                    del_thread.start()
                flag = False

            if unchanged_list:
                # Логирование?
                changed_list = []
                for file_name in unchanged_list:

                    if db_info[file_name] != local_info[file_name]:
                        changed_list.append(file_name)

                if changed_list:
                    for cl in changed_list:
                        db_manager.write_file_data(cl)
                        add_thread = threading.Thread(
                            target=yandex_manager.load,
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
            time.sleep(5)