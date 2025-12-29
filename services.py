from managers import SyncManager, LocalManager

from db_work import write_file_data, delete_file_data


files_info = {}


def check_diff(yandex_manager: SyncManager, local_manager: LocalManager):
    yandex_list = yandex_manager.detail()
    files_dir_list = local_manager.detail()

    ya_set = set(yandex_list)
    dir_set = set(files_dir_list)

    delta_ya = ya_set - dir_set
    delta_dir = dir_set - ya_set
    docs = ya_set & dir_set

    if len(delta_dir) == 0 and len(delta_ya) == 0:
        return

    print(f"Документы, которых нет в диске: {list(delta_dir)}")
    print(f"Документы, которых нет локально: {list(delta_ya)}")

    def check_input_type():
        res = input("Какие документы актуальны? y - yandex, l - local")
        if res not in ["l", "y"]:
            check_input_type()
        else:
            return res

    answer = check_input_type()

    print(answer)


def write_new_files_data(yandex_manager: SyncManager, file_name_list):
    for f_name in file_name_list:
        write_file_data(f_name, files_info)
        yandex_manager.load(f_name)


def delete_files_data(yandex_manager: SyncManager, file_name_list):
    for f_name in file_name_list:
        delete_file_data(f_name, files_info)
        yandex_manager.delete(f_name)
